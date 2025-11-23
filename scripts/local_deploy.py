#!/usr/bin/env python3
"""
Local Deployment Script for Thara Bot (Cross-platform)
This script sets up and runs the bot locally on any platform.
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

# Colors for output (works on Unix-like systems)
if platform.system() != 'Windows':
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'
else:
    GREEN = YELLOW = RED = BLUE = NC = ''

def print_colored(text, color=NC):
    """Print colored text."""
    print(f"{color}{text}{NC}")

def check_python_version():
    """Check if Python 3.11+ is installed."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_colored(f"❌ Python 3.11+ required. Found: {version.major}.{version.minor}", RED)
        sys.exit(1)
    print_colored(f"✅ Python {version.major}.{version.minor} found", GREEN)

def run_command(cmd, check=True, shell=False):
    """Run a shell command."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    try:
        result = subprocess.run(cmd, check=check, shell=shell, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        if check:
            print_colored(f"❌ Error: {e}", RED)
            print_colored(f"Command: {' '.join(cmd)}", YELLOW)
            print_colored(f"Output: {e.stderr}", YELLOW)
            sys.exit(1)
        return None

def setup_venv():
    """Create and activate virtual environment."""
    project_dir = Path(__file__).parent.parent
    venv_dir = project_dir / "venv"
    
    if not venv_dir.exists():
        print_colored("Creating virtual environment...", YELLOW)
        run_command([sys.executable, "-m", "venv", str(venv_dir)])
        print_colored("✅ Virtual environment created", GREEN)
    else:
        print_colored("✅ Virtual environment exists", GREEN)
    
    # Determine activation script path
    if platform.system() == 'Windows':
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    return python_exe, pip_exe

def install_dependencies(pip_exe):
    """Install Python dependencies."""
    project_dir = Path(__file__).parent.parent
    requirements = project_dir / "requirements.txt"
    
    if not requirements.exists():
        print_colored("❌ requirements.txt not found", RED)
        sys.exit(1)
    
    print_colored("Upgrading pip...", YELLOW)
    run_command([str(pip_exe), "install", "--upgrade", "pip", "--quiet"])
    
    print_colored("Installing dependencies...", YELLOW)
    run_command([str(pip_exe), "install", "-r", str(requirements)])
    print_colored("✅ Dependencies installed", GREEN)

def check_env_file():
    """Check if .env file exists and create template if needed."""
    project_dir = Path(__file__).parent.parent
    env_file = project_dir / ".env"
    
    if not env_file.exists():
        print_colored("⚠️  .env file not found. Creating template...", YELLOW)
        template = """# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# AI/LLM
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database (Neon DB or PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Google Calendar
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
TIMEZONE=UTC

# Sentry Error Tracking (Optional)
SENTRY_DSN=
SENTRY_ENABLED=False

# Default Work Hours
DEFAULT_WORK_START_HOUR=8
DEFAULT_WORK_END_HOUR=20
DEFAULT_WEEKEND_START_HOUR=10
DEFAULT_WEEKEND_END_HOUR=18

# Scheduling
CHECK_IN_INTERVAL=30
WEEKLY_REVIEW_HOUR=10

# Server
HOST=0.0.0.0
PORT=8000

# Agent Framework Selection
USE_PARLANT=False
"""
        env_file.write_text(template)
        print_colored("⚠️  Please edit .env file with your credentials", YELLOW)
        input("Press Enter to continue after editing .env file, or Ctrl+C to exit...")
    else:
        print_colored("✅ .env file found", GREEN)

def run_migrations(python_exe):
    """Run database migrations."""
    project_dir = Path(__file__).parent.parent
    
    # Check if alembic is available
    if platform.system() == 'Windows':
        alembic_exe = project_dir / "venv" / "Scripts" / "alembic.exe"
    else:
        alembic_exe = project_dir / "venv" / "bin" / "alembic"
    
    if alembic_exe.exists():
        print_colored("Running database migrations...", YELLOW)
        try:
            run_command([str(alembic_exe), "upgrade", "head"], check=False)
            print_colored("✅ Database migrations completed", GREEN)
        except:
            print_colored("⚠️  Migration failed, continuing anyway...", YELLOW)
    else:
        print_colored("⚠️  Alembic not found. Skipping migrations.", YELLOW)

def main():
    """Main deployment function."""
    print_colored("========================================", BLUE)
    print_colored("  Thara Bot - Local Deployment", BLUE)
    print_colored("========================================", BLUE)
    print()
    
    # Check Python version
    print_colored("Checking Python version...", YELLOW)
    check_python_version()
    print()
    
    # Setup virtual environment
    print_colored("Setting up virtual environment...", YELLOW)
    python_exe, pip_exe = setup_venv()
    print()
    
    # Install dependencies
    print_colored("Installing dependencies...", YELLOW)
    install_dependencies(pip_exe)
    print()
    
    # Check .env file
    print_colored("Checking environment configuration...", YELLOW)
    check_env_file()
    print()
    
    # Run migrations
    print_colored("Running database migrations...", YELLOW)
    run_migrations(python_exe)
    print()
    
    # Start bot
    project_dir = Path(__file__).parent.parent
    bot_main = project_dir / "bot_main.py"
    
    print_colored("========================================", BLUE)
    print_colored("Starting Thara Bot...", GREEN)
    print_colored("========================================", BLUE)
    print()
    print_colored("Press Ctrl+C to stop the bot", YELLOW)
    print()
    
    # Run the bot
    os.chdir(project_dir)
    run_command([str(python_exe), str(bot_main)], check=False, shell=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\nBot stopped by user", YELLOW)
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n❌ Error: {e}", RED)
        sys.exit(1)

