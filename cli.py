#!/usr/bin/env python3
"""
mega - CLI for ACP Sensitivity Analyzer

Launch and manage the mega backdoor Roth compliance analysis tool.
"""

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import click

# Project root directory
ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

# Default ports
DEFAULT_API_PORT = 8000
DEFAULT_UI_PORT = 5173  # Vite default

# Process storage for cleanup
processes = []


def get_npm_command() -> str:
    """Return the npm executable path, or an empty string if not found."""
    if sys.platform == "win32":
        candidates = ("npm.cmd", "npm.exe", "npm")
    else:
        candidates = ("npm",)
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return ""


def kill_port(port: int) -> bool:
    """Kill any process using the specified port (cross-platform)."""
    if sys.platform == "win32":
        # Windows: use netstat + taskkill
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                shell=True,
            )
            for line in result.stdout.split('\n'):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        try:
                            subprocess.run(
                                ["taskkill", "/F", "/PID", pid],
                                capture_output=True,
                                shell=True,
                            )
                            return True
                        except Exception:
                            pass
        except Exception:
            pass
    else:
        # Unix/Mac: use lsof
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except (ProcessLookupError, ValueError):
                        pass
                return True
        except FileNotFoundError:
            # lsof not available, try fuser as fallback
            try:
                subprocess.run(
                    ["fuser", "-k", f"{port}/tcp"],
                    capture_output=True,
                )
            except FileNotFoundError:
                pass
    return False


def cleanup(signum=None, frame=None):
    """Clean up background processes."""
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    if signum:
        sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
if sys.platform != "win32":
    signal.signal(signal.SIGTERM, cleanup)


@click.group()
@click.version_option(version="1.0.0", prog_name="mega")
def cli():
    """
    mega - ACP Sensitivity Analyzer CLI

    Analyze mega backdoor Roth contributions for ACP compliance testing.
    """
    pass


@cli.command()
@click.option("--api-port", default=DEFAULT_API_PORT, help="API server port")
@click.option("--ui-port", default=DEFAULT_UI_PORT, help="Frontend UI port")
@click.option("--api-only", is_flag=True, help="Start only the API server")
@click.option("--ui-only", is_flag=True, help="Start only the frontend UI")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def start(api_port, ui_port, api_only, ui_only, no_browser):
    """Start the application services."""

    # Kill any existing processes on the ports
    if not ui_only and kill_port(api_port):
        click.secho(f"  Killed existing process on port {api_port}", fg="yellow")
    if not api_only and kill_port(ui_port):
        click.secho(f"  Killed existing process on port {ui_port}", fg="yellow")

    click.secho("\n  mega backdoor ACP Sensitivity Analyzer\n", fg="cyan", bold=True)

    if api_only and ui_only:
        click.secho("Error: Cannot use both --api-only and --ui-only", fg="red")
        sys.exit(1)

    # Check if npm is available
    npm_cmd = get_npm_command()
    if not npm_cmd and not api_only:
        click.secho(
            "Error: npm is required for the frontend. Install Node.js and ensure npm is on PATH.",
            fg="red",
        )
        sys.exit(1)

    # Check if frontend dependencies are installed
    if not api_only:
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            click.secho("Installing frontend dependencies...", fg="yellow")
            result = subprocess.run(
                [npm_cmd, "install"],
                cwd=FRONTEND_DIR,
                capture_output=True,
            )
            if result.returncode != 0:
                click.secho("Failed to install frontend dependencies", fg="red")
                click.secho(result.stderr.decode(), fg="red")
                sys.exit(1)

    start_api = not ui_only
    start_ui = not api_only

    if start_api:
        click.secho(f"  API Server:  http://localhost:{api_port}", fg="green")
        click.secho(f"  API Docs:    http://localhost:{api_port}/docs", fg="green")

    if start_ui:
        click.secho(f"  React UI:    http://localhost:{ui_port}", fg="green")

    click.secho("\n  Press Ctrl+C to stop\n", fg="yellow")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    # Start API server
    if start_api:
        api_cmd = [
            sys.executable, "-m", "uvicorn",
            "app.routers.main:app",
            "--host", "0.0.0.0",
            "--port", str(api_port),
            "--reload",
        ]

        api_proc = subprocess.Popen(
            api_cmd,
            cwd=BACKEND_DIR,
            env=env,
        )
        processes.append(api_proc)
        time.sleep(2)  # Give API time to start

    # Start React frontend with Vite
    if start_ui:
        ui_cmd = [npm_cmd, "run", "dev", "--", "--port", str(ui_port), "--host"]
        if no_browser:
            ui_cmd.append("--no-open")
        else:
            ui_cmd.append("--open")

        ui_proc = subprocess.Popen(
            ui_cmd,
            cwd=FRONTEND_DIR,
            env=env,
        )
        processes.append(ui_proc)

    # Wait for processes
    try:
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    click.secho("\nA service has stopped unexpectedly.", fg="red")
                    cleanup()
                    sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


@cli.command()
@click.option("--cov", is_flag=True, help="Run with coverage report")
@click.option("--unit", is_flag=True, help="Run only unit tests")
@click.option("--integration", is_flag=True, help="Run only integration tests")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--backend", is_flag=True, help="Run only backend tests")
@click.option("--frontend", is_flag=True, help="Run only frontend type checking")
def test(cov, unit, integration, verbose, backend, frontend):
    """Run the test suite."""

    click.secho("\n  Running tests...\n", fg="cyan")

    if frontend:
        # Run frontend type checking
        click.secho("  Running frontend type check...", fg="cyan")
        npm_cmd = get_npm_command()
        if not npm_cmd:
            click.secho(
                "Error: npm is required for the frontend. Install Node.js and ensure npm is on PATH.",
                fg="red",
            )
            sys.exit(1)
        result = subprocess.run(
            [npm_cmd, "run", "typecheck"],
            cwd=FRONTEND_DIR,
        )
        sys.exit(result.returncode)

    # Backend tests
    cmd = [sys.executable, "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if cov:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])

    if unit:
        cmd.extend(["-m", "unit"])
    elif integration:
        cmd.extend(["-m", "integration"])

    result = subprocess.run(cmd, cwd=BACKEND_DIR)
    sys.exit(result.returncode)


@cli.command()
@click.option("--fix", is_flag=True, help="Auto-fix issues")
def lint(fix):
    """Run code linting with ruff."""

    click.secho("\n  Running linter...\n", fg="cyan")

    cmd = [sys.executable, "-m", "ruff", "check", "."]

    if fix:
        cmd.append("--fix")

    result = subprocess.run(cmd, cwd=ROOT_DIR)
    sys.exit(result.returncode)


@cli.command()
def info():
    """Show project information."""

    click.secho("\n  mega backdoor ACP Sensitivity Analyzer", fg="cyan", bold=True)
    click.secho("  ─" * 22, fg="cyan")
    click.echo()
    click.echo("  A compliance tool for analyzing mega backdoor Roth")
    click.echo("  contributions against IRS ACP nondiscrimination tests.")
    click.echo()
    click.secho("  Components:", fg="yellow")
    click.echo("    • FastAPI backend  - REST API for analysis")
    click.echo("    • React frontend   - Modern interactive UI")
    click.echo("    • File storage     - Workspace-based data")
    click.echo()
    click.secho("  Quick start:", fg="yellow")
    click.echo("    $ mega start")
    click.echo()


if __name__ == "__main__":
    cli()
