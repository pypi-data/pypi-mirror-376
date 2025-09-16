"""
Network output handler for TCP/UDP log transmission.
"""

import logging
import socket
import threading
import time
from queue import Empty, Queue
from typing import Optional, Tuple

from ..core.exceptions import OutputError
from ..core.interfaces import OutputHandler


class NetworkOutputHandler(OutputHandler):
    """
    Network output handler supporting TCP and UDP protocols.

    Provides reliable log transmission over network with connection
    management, retry logic, and buffering.
    """

    def __init__(
        self,
        host: str,
        port: int,
        protocol: str = "tcp",
        timeout: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        buffer_size: int = 1024,
        queue_size: int = 1000,
        encoding: str = "utf-8",
    ):
        """
        Initialize network output handler.

        Args:
            host: Target host address
            port: Target port number
            protocol: Protocol to use ('tcp' or 'udp')
            timeout: Connection timeout in seconds
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
            buffer_size: Socket buffer size
            queue_size: Internal queue size for buffering
            encoding: Text encoding
        """
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.buffer_size = buffer_size
        self.encoding = encoding

        if self.protocol not in ("tcp", "udp"):
            raise OutputError(f"Unsupported protocol: {protocol}")

        self._socket = None
        self._connected = False
        self._closed = False
        self._lock = threading.Lock()

        # Buffering for reliable delivery
        self._queue = Queue(maxsize=queue_size)
        self._worker_thread = None
        self._stop_event = threading.Event()

        # Statistics
        self._sent_count = 0
        self._failed_count = 0
        self._reconnect_count = 0

        # Initialize connection
        self._connect()

        # Start worker thread for TCP to handle queued messages
        if self.protocol == "tcp":
            self._start_worker_thread()

    def _connect(self) -> None:
        """Establish network connection."""
        try:
            if self.protocol == "tcp":
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(self.timeout)
                self._socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_SNDBUF, self.buffer_size
                )
                self._socket.connect((self.host, self.port))
            else:  # UDP
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socket.settimeout(self.timeout)
                self._socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_SNDBUF, self.buffer_size
                )

            self._connected = True

        except Exception as e:
            self._connected = False
            if self._socket:
                try:
                    self._socket.close()
                except:
                    pass
                self._socket = None
            raise OutputError(
                f"Failed to connect to {self.host}:{self.port} ({self.protocol}): {e}"
            )

    def _reconnect(self) -> bool:
        """
        Attempt to reconnect with retry logic.

        Returns:
            bool: True if reconnection successful
        """
        for attempt in range(self.max_retries):
            try:
                if self._socket:
                    try:
                        self._socket.close()
                    except:
                        pass
                    self._socket = None

                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                self._connect()
                self._reconnect_count += 1
                return True

            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(
                        f"Failed to reconnect after {self.max_retries} attempts: {e}"
                    )
                    return False

        return False

    def _start_worker_thread(self) -> None:
        """Start background worker thread for TCP message processing."""
        if self.protocol == "tcp":
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True
            )
            self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Background worker loop for processing queued messages."""
        while not self._stop_event.is_set():
            try:
                # Get message from queue with timeout
                try:
                    message = self._queue.get(timeout=1.0)
                except Empty:
                    continue

                # Try to send message
                success = self._send_message_direct(message)

                if not success:
                    # Try to reconnect and send again
                    if self._reconnect():
                        self._send_message_direct(message)
                    else:
                        self._failed_count += 1

                self._queue.task_done()

            except Exception as e:
                logging.error(f"Error in network worker thread: {e}")

    def _send_message_direct(self, message: str) -> bool:
        """
        Send message directly through socket.

        Args:
            message: Message to send

        Returns:
            bool: True if sent successfully
        """
        try:
            if not self._connected or not self._socket:
                return False

            # Encode message
            data = message.encode(self.encoding)

            if self.protocol == "tcp":
                # For TCP, send all data
                self._socket.sendall(data)
            else:
                # For UDP, send to target
                self._socket.sendto(data, (self.host, self.port))

            self._sent_count += 1
            return True

        except (socket.error, OSError) as e:
            self._connected = False
            logging.error(f"Network send error: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending message: {e}")
            return False

    def write_log(self, log_entry: str) -> None:
        """
        Write a log entry to network destination.

        Args:
            log_entry: Log entry to send
        """
        if self._closed:
            raise OutputError("Network handler is closed")

        # Ensure message ends with newline
        if not log_entry.endswith("\n"):
            log_entry += "\n"

        if self.protocol == "tcp":
            # For TCP, use queue for reliable delivery
            try:
                self._queue.put(log_entry, timeout=1.0)
            except:
                raise OutputError("Network queue is full")
        else:
            # For UDP, send directly (fire and forget)
            with self._lock:
                if not self._send_message_direct(log_entry):
                    # For UDP, we can try to reconnect once
                    if self._reconnect():
                        if not self._send_message_direct(log_entry):
                            self._failed_count += 1
                            raise OutputError("Failed to send UDP message")
                    else:
                        self._failed_count += 1
                        raise OutputError("UDP connection failed")

    def flush(self) -> None:
        """Flush any buffered messages."""
        if self.protocol == "tcp" and not self._closed:
            # Wait for queue to be empty
            self._queue.join()

    def close(self) -> None:
        """Close the network handler and clean up resources."""
        with self._lock:
            if self._closed:
                return

            self._closed = True

            # Stop worker thread
            if self._worker_thread:
                self._stop_event.set()
                self._worker_thread.join(timeout=5.0)

            # Close socket
            if self._socket:
                try:
                    if self.protocol == "tcp":
                        self._socket.shutdown(socket.SHUT_RDWR)
                    self._socket.close()
                except:
                    pass
                finally:
                    self._socket = None

            self._connected = False

    def is_connected(self) -> bool:
        """
        Check if handler is connected.

        Returns:
            bool: True if connected
        """
        return self._connected and not self._closed

    def get_statistics(self) -> dict:
        """
        Get transmission statistics.

        Returns:
            dict: Statistics including sent/failed counts
        """
        return {
            "sent_count": self._sent_count,
            "failed_count": self._failed_count,
            "reconnect_count": self._reconnect_count,
            "queue_size": self._queue.qsize() if self.protocol == "tcp" else 0,
            "connected": self._connected,
            "protocol": self.protocol,
            "target": f"{self.host}:{self.port}",
        }

    def test_connection(self) -> bool:
        """
        Test network connection.

        Returns:
            bool: True if connection test successful
        """
        try:
            test_message = "test\n"
            return self._send_message_direct(test_message)
        except Exception:
            return False


class TCPOutputHandler(NetworkOutputHandler):
    """Convenience class for TCP output."""

    def __init__(self, host: str, port: int, **kwargs):
        super().__init__(host, port, protocol="tcp", **kwargs)


class UDPOutputHandler(NetworkOutputHandler):
    """Convenience class for UDP output."""

    def __init__(self, host: str, port: int, **kwargs):
        super().__init__(host, port, protocol="udp", **kwargs)
