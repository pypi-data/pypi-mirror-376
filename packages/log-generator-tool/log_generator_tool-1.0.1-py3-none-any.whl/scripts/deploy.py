#!/usr/bin/env python3
"""
Deployment script for Log Generator Tool
Handles building, testing, and publishing to PyPI
"""

import os
import subprocess
import argparse
from pathlib import Path
import shutil
import tempfile
from typing import List, Optional

from pathlib import Path
import sys
import re
import configparser

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message: str, color: str = Colors.OKGREEN):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result"""
    print_colored(f"Running: {' '.join(cmd)}", Colors.OKBLUE)
    try:
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"Command failed: {e}", Colors.FAIL)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        raise

def check_git_status():
    """Check if git working directory is clean"""
    print_colored("Checking git status...", Colors.HEADER)
    result = run_command(["git", "status", "--porcelain"])
    if result.stdout.strip():
        print_colored("Warning: Git working directory is not clean", Colors.WARNING)
        print(result.stdout)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print_colored("Git working directory is clean", Colors.OKGREEN)

def get_version() -> str:
    """
    Determine package version without requiring an installed distribution.
    Try 1) import, 2) parse log_generator/__init__.py, 3) fallback to pyproject.
    """
    # 1) import 시도
    try:
        import log_generator  # noqa: F401
        v = getattr(log_generator, "__version__", None)
        if v:
            return v
    except Exception:
        pass

    # 2) __init__.py에서 파싱
    init_path = ROOT / "log_generator" / "__init__.py"
    if init_path.exists():
        text = init_path.read_text(encoding="utf-8")
        m = re.search(r"""__version__\s*=\s*['"]([^'"]+)['"]""", text)
        if m:
            return m.group(1)

    # 3) (옵션) pyproject.toml에서 읽기
    pyproject = ROOT / "pyproject.toml"
    if pyproject.exists():
        t = pyproject.read_text(encoding="utf-8")
        m = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', t)
        if m:
            return m.group(1)

    raise RuntimeError("Could not determine package version")

def check_version_tag(version: str) -> bool:
    """Return True if tag exists; False otherwise."""
    print_colored(f"Checking version tag v{version}...", Colors.HEADER)
    try:
        run_command(["git", "rev-parse", f"v{version}"])
        print_colored(f"Tag v{version} already exists", Colors.WARNING)
        return True
    except subprocess.CalledProcessError:
        print_colored(f"Tag v{version} does not exist (good)", Colors.OKGREEN)
        return False


def run_tests():
    """Run the test suite"""
    print_colored("Running tests...", Colors.HEADER)
    run_command(["python", "-m", "pytest", "tests/", "-v", "--cov=log_generator"])

def run_quality_checks():
    """Run code quality checks with env-based toggles."""
    print_colored("Running code quality checks...", Colors.HEADER)

    autoformat = os.getenv("AUTOFORMAT", "1") == "1"
    typecheck = os.getenv("TYPECHECK", "0") == "1"
    security  = os.getenv("SECURITY",  "0") == "1"

    # --- Black ---
    print_colored("Checking code formatting (Black)...", Colors.OKBLUE)
    if autoformat:
        print_colored("AUTOFORMAT=1 → running: black log_generator/ tests/", Colors.WARNING)
        run_command(["black", "log_generator/", "tests/"])
    # always verify
    run_command(["black", "--check", "log_generator/", "tests/"])

    # --- isort ---
    print_colored("Checking import sorting (isort)...", Colors.OKBLUE)
    if autoformat:
        print_colored("AUTOFORMAT=1 → running: isort --profile black log_generator/ tests/", Colors.WARNING)
        run_command(["isort", "--profile", "black", "log_generator/", "tests/"])
    # always verify
    run_command(["isort", "--check-only", "--profile", "black", "log_generator/", "tests/"])

    # --- flake8 ---
    print_colored("Running linter (flake8)...", Colors.OKBLUE)
    run_command(["flake8", "log_generator/", "tests/"])

    # --- mypy (optional) ---
    if typecheck:
        print_colored("Running type checker (mypy)...", Colors.OKBLUE)
        run_command(["mypy", "log_generator/"])
    else:
        print_colored("Skipping mypy (set TYPECHECK=1 to enable)", Colors.WARNING)

    # --- bandit (optional) ---
    if security:
        print_colored("Running security check (bandit)...", Colors.OKBLUE)
        run_command(["bandit", "-r", "log_generator/"])
    else:
        print_colored("Skipping bandit (set SECURITY=1 to enable)", Colors.WARNING)


def clean_build_artifacts():
    """Clean build artifacts"""
    print_colored("Cleaning build artifacts...", Colors.HEADER)
    
    artifacts = [
        "build/",
        "dist/",
        "*.egg-info/",
        "__pycache__/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
    ]
    
    for pattern in artifacts:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print_colored(f"Removed directory: {path}", Colors.OKGREEN)
            elif path.is_file():
                path.unlink()
                print_colored(f"Removed file: {path}", Colors.OKGREEN)

def build_package():
    """Build the package"""
    print_colored("Building package...", Colors.HEADER)
    run_command(["python", "-m", "build"])
    
    # Check the built package
    print_colored("Checking built package...", Colors.OKBLUE)
    run_command(["twine", "check", "dist/*"])

def create_git_tag(version: str):
    """Create (or update) git tag for this version."""
    print_colored(f"Creating git tag v{version}...", Colors.HEADER)

    # 태그 존재 여부 확인
    exists = False
    try:
        run_command(["git", "rev-parse", f"v{version}"])
        exists = True
    except subprocess.CalledProcessError:
        exists = False

    if exists:
        print_colored(f"Tag v{version} already exists.", Colors.WARNING)
        choice = input("Overwrite tag (force -f)? [y]es / [s]kip: ").strip().lower()
        if choice.startswith("y"):
            # 현재 커밋을 가리키도록 강제 업데이트
            run_command(["git", "tag", "-f", f"v{version}"])
        else:
            print_colored("Skip creating tag.", Colors.WARNING)
            return
    else:
        run_command(["git", "tag", f"v{version}"])

    response = input("Push tag to remote? (y/N): ").strip().lower()
    if response == "y":
        run_command(["git", "push", "-f", "origin", f"v{version}"])



def _pypirc_has(section: str) -> bool:
    cfg = Path("~/.pypirc").expanduser()
    if not cfg.exists():
        return False
    parser = configparser.RawConfigParser()
    parser.read(cfg)
    return parser.has_section(section)


def publish_to_pypi(test: bool = False):
    """Publish package using credentials in ~/.pypirc."""
    target = "Test PyPI" if test else "PyPI"
    repo_name = "testpypi" if test else "pypi"

    print_colored(f"Publishing to {target}...", Colors.HEADER)

    # 마지막 점검
    run_command(["twine", "check", "dist/*"])

    # ~/.pypirc에 섹션이 없으면 친절히 메시지
    if not _pypirc_has(repo_name):
        print_colored(
            f"WARNING: ~/.pypirc에 [{repo_name}] 섹션이 없습니다. 기본 'pypi' 레포를 사용하거나 환경변수(TWINE_USERNAME/PASSWORD)로 인증하세요.",
            Colors.WARNING,
        )

    # 업로드 전 사용자 확인
    resp = input(f"Really upload to {target}? (y/N): ").strip().lower()
    if resp != "y":
        print_colored("Publication cancelled", Colors.WARNING)
        return

    # .pypirc 사용: --repository 만 지정하면 사용자/토큰은 pypirc에서 읽음
    cmd = ["twine", "upload", "--skip-existing"]
    # test 플래그일 땐 testpypi, 아니면 pypi
    cmd += ["--repository", repo_name]
    cmd += ["dist/*"]

    run_command(cmd)
    print_colored(f"Successfully published to {target}!", Colors.OKGREEN)
    
def build_docker_image(version: str):
    """Build Docker image"""
    print_colored("Building Docker image...", Colors.HEADER)
    
    tags = [
        f"loggenerator/log-generator-tool:{version}",
        "loggenerator/log-generator-tool:latest"
    ]
    
    for tag in tags:
        run_command(["docker", "build", "-t", tag, "."])
    
    # Test the image
    print_colored("Testing Docker image...", Colors.OKBLUE)
    run_command(["docker", "run", "--rm", f"loggenerator/log-generator-tool:{version}", 
                "log-generator", "--version"])

def push_docker_image(version: str):
    """Push Docker image to registry"""
    print_colored("Pushing Docker image...", Colors.HEADER)
    
    tags = [
        f"loggenerator/log-generator-tool:{version}",
        "loggenerator/log-generator-tool:latest"
    ]
    
    for tag in tags:
        response = input(f"Push {tag}? (y/N): ")
        if response.lower() == 'y':
            run_command(["docker", "push", tag])

def main():
    parser = argparse.ArgumentParser(description="Deploy Log Generator Tool")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-quality", action="store_true", help="Skip quality checks")
    parser.add_argument("--test-pypi", action="store_true", help="Publish to Test PyPI instead of PyPI")
    parser.add_argument("--skip-pypi", action="store_true", help="Skip PyPI publication")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker build")
    parser.add_argument("--skip-git-tag", action="store_true", help="Skip creating git tag")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build artifacts")
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print_colored("Log Generator Tool Deployment Script", Colors.HEADER)
    print_colored("=" * 50, Colors.HEADER)
    
    # Clean build artifacts
    clean_build_artifacts()
    
    if args.clean_only:
        print_colored("Cleaning completed", Colors.OKGREEN)
        return
    
    # Get version
    version = get_version()
    print_colored(f"Deploying version: {version}", Colors.OKGREEN)
    
    # Check git status
    check_git_status()
    
    # Check version tag
    if not args.skip_git_tag:
        check_version_tag(version)
    
    # Run quality checks
    if not args.skip_quality:
        run_quality_checks()
    
    # Run tests
    if not args.skip_tests:
        run_tests()
    
    # Build package
    build_package()
    
    # Create git tag
    if not args.skip_git_tag:
        create_git_tag(version)
    
    # Publish to PyPI
    if not args.skip_pypi:
        publish_to_pypi(test=args.test_pypi)
    
    # Build and push Docker image
    if not args.skip_docker:
        build_docker_image(version)
        push_docker_image(version)
    
    print_colored("Deployment completed successfully!", Colors.OKGREEN)
    print_colored("=" * 50, Colors.OKGREEN)

if __name__ == "__main__":
    main()