#!/usr/bin/env python3
"""
CLI tool for AI Video Automation Pipeline management.

This script provides convenient commands for development, testing, and deployment.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command with proper error handling."""
    console.print(f"[blue]Running:[/blue] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=False)
        return result
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Command failed with exit code {e.returncode}[/red]")
        sys.exit(e.returncode)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """AI Video Automation Pipeline CLI Tool."""
    pass


@cli.group()
def setup():
    """Setup and installation commands."""
    pass


@setup.command("dev")
def setup_dev():
    """Set up development environment."""
    console.print("[green]Setting up development environment...[/green]")
    
    # Create .env if it doesn't exist
    if not Path(".env").exists():
        run_command(["cp", ".env.example", ".env"])
        console.print("[yellow]Created .env file from .env.example[/yellow]")
        console.print("[yellow]Please edit .env with your configuration[/yellow]")
    
    # Install dependencies
    run_command(["pip", "install", "-r", "requirements-dev.txt"])
    
    # Set up pre-commit
    run_command(["pre-commit", "install"])
    
    console.print("[green]Development environment setup complete![/green]")


@setup.command("prod")
def setup_prod():
    """Set up production environment."""
    console.print("[green]Setting up production environment...[/green]")
    run_command(["pip", "install", "-r", "requirements-prod.txt"])
    console.print("[green]Production environment setup complete![/green]")


@cli.group()
def dev():
    """Development commands."""
    pass


@dev.command("run")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, default=True, help="Enable auto-reload")
def dev_run(host: str, port: int, reload: bool):
    """Run the FastAPI development server."""
    cmd = ["uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    if reload:
        cmd.append("--reload")
    run_command(cmd)


@dev.command("worker")
def dev_worker():
    """Run Celery worker."""
    run_command(["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"])


@dev.command("beat")
def dev_beat():
    """Run Celery beat scheduler."""
    run_command(["celery", "-A", "app.tasks.celery_app", "beat", "--loglevel=info"])


@dev.command("flower")
def dev_flower():
    """Run Flower monitoring."""
    run_command(["celery", "-A", "app.tasks.celery_app", "flower"])


@cli.group()
def test():
    """Testing commands."""
    pass


@test.command("run")
@click.option("--cov", is_flag=True, help="Run with coverage")
@click.option("--html", is_flag=True, help="Generate HTML coverage report")
def test_run(cov: bool, html: bool):
    """Run the test suite."""
    cmd = ["pytest", "tests/", "-v"]
    if cov:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
        if html:
            cmd.append("--cov-report=html")
    run_command(cmd)


@test.command("unit")
def test_unit():
    """Run unit tests only."""
    run_command(["pytest", "tests/unit/", "-v"])


@test.command("integration")
def test_integration():
    """Run integration tests only."""
    run_command(["pytest", "tests/integration/", "-v"])


@cli.group()
def db():
    """Database management commands."""
    pass


@db.command("migrate")
@click.argument("message", required=False)
def db_migrate(message: Optional[str]):
    """Create a new migration."""
    if message:
        run_command(["alembic", "revision", "--autogenerate", "-m", message])
    else:
        run_command(["alembic", "current"])
        run_command(["alembic", "history"])


@db.command("upgrade")
def db_upgrade():
    """Run database migrations."""
    run_command(["alembic", "upgrade", "head"])


@db.command("downgrade")
def db_downgrade():
    """Downgrade database by one migration."""
    run_command(["alembic", "downgrade", "-1"])


@cli.group()
def lint():
    """Code quality commands."""
    pass


@lint.command("check")
def lint_check():
    """Run all linting checks."""
    console.print("[blue]Running linting checks...[/blue]")
    
    # Black
    console.print("[blue]Checking code formatting with Black...[/blue]")
    run_command(["black", "--check", "app/", "tests/"], check=False)
    
    # isort
    console.print("[blue]Checking import sorting with isort...[/blue]")
    run_command(["isort", "--check-only", "app/", "tests/"], check=False)
    
    # flake8
    console.print("[blue]Running flake8...[/blue]")
    run_command(["flake8", "app/", "tests/"], check=False)
    
    # mypy
    console.print("[blue]Running mypy...[/blue]")
    run_command(["mypy", "app/"], check=False)


@lint.command("fix")
def lint_fix():
    """Fix linting issues automatically."""
    console.print("[blue]Fixing linting issues...[/blue]")
    
    # Black
    run_command(["black", "app/", "tests/"])
    
    # isort
    run_command(["isort", "app/", "tests/"])
    
    console.print("[green]Linting fixes applied![/green]")


@cli.group()
def docker():
    """Docker commands."""
    pass


@docker.command("build")
def docker_build():
    """Build Docker image."""
    run_command(["docker", "build", "-t", "ai-video-automation", "."])


@docker.command("up")
@click.option("--dev", is_flag=True, help="Use development configuration")
def docker_up(dev: bool):
    """Start services with Docker Compose."""
    if dev:
        run_command(["docker-compose", "-f", "docker-compose.dev.yml", "up", "-d"])
    else:
        run_command(["docker-compose", "up", "-d"])


@docker.command("down")
def docker_down():
    """Stop Docker services."""
    run_command(["docker-compose", "down"])


@cli.command("status")
def status():
    """Show project status."""
    console.print("[green]AI Video Automation Pipeline Status[/green]")
    
    table = Table(title="Environment Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python", "✓", python_version)
    
    # Check if .env exists
    env_status = "✓" if Path(".env").exists() else "✗"
    table.add_row(".env file", env_status, "Configuration file")
    
    # Check dependencies
    try:
        import fastapi
        table.add_row("FastAPI", "✓", f"v{fastapi.__version__}")
    except ImportError:
        table.add_row("FastAPI", "✗", "Not installed")
    
    try:
        import celery
        table.add_row("Celery", "✓", f"v{celery.__version__}")
    except ImportError:
        table.add_row("Celery", "✗", "Not installed")
    
    console.print(table)


if __name__ == "__main__":
    cli()