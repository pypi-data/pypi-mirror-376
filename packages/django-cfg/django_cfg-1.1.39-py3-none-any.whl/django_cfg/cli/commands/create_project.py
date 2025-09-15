"""
Django CFG Create Project Command

Creates a new Django project using django-cfg sample template.
"""

import click
import shutil
import os
from pathlib import Path
from typing import Optional
import tempfile
import subprocess
import sys


def get_template_archive_path() -> Path:
    """Get the path to the django_sample template archive."""
    import sysconfig
    
    # Method 1: Try to find in installed package templates directory
    try:
        import django_cfg
        package_path = Path(django_cfg.__file__).parent
        
        # Check if template archive is in package archive directory
        template_archive = package_path / "archive" / "django_sample.zip"
        if template_archive.exists():
            return template_archive
            
        # Check if it's in site-packages shared data
        site_packages = Path(sysconfig.get_paths()["purelib"])
        shared_archive_path = site_packages / "django_cfg" / "archive" / "django_sample.zip"
        if shared_archive_path.exists():
            return shared_archive_path
            
    except ImportError:
        pass
    
    # Method 2: Development installation - check if archive exists in src
    try:
        import django_cfg
        package_path = Path(django_cfg.__file__).parent.parent.parent
        
        # Look for archive in src directory
        src_archive = package_path / "src" / "django_cfg" / "archive" / "django_sample.zip"
        if src_archive.exists():
            return src_archive
            
    except ImportError:
        pass
    
    # Method 3: Last resort - try to find it relative to this file (development)
    cli_path = Path(__file__).parent.parent.parent.parent.parent
    dev_archive = cli_path / "src" / "django_cfg" / "archive" / "django_sample.zip"
    if dev_archive.exists():
        return dev_archive
    
    raise FileNotFoundError(
        "Could not find django_sample.zip template archive. "
        "Please ensure django-cfg is properly installed or run 'python scripts/template_manager.py create' in development."
    )


def extract_template(archive_path: Path, target_path: Path, project_name: str) -> None:
    """Extract template archive to target directory with project name replacements."""
    import zipfile
    
    click.echo(f"📂 Extracting template from archive...")
    
    target_path = Path(target_path)
    target_path.mkdir(parents=True, exist_ok=True)
    
    files_extracted = 0
    try:
        with zipfile.ZipFile(archive_path, 'r') as archive:
            for member in archive.namelist():
                # Extract file
                archive.extract(member, target_path)
                files_extracted += 1
                
                # Apply project name replacements to text files
                extracted_file = target_path / member
                if extracted_file.is_file() and should_process_file_for_replacements(extracted_file):
                    replace_project_name(extracted_file, project_name)
        
        click.echo(f"✅ Extracted {files_extracted} files from template")
        
    except zipfile.BadZipFile:
        raise ValueError(f"Invalid template archive: {archive_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract template: {e}")


def should_process_file_for_replacements(file_path: Path) -> bool:
    """Check if file should be processed for project name replacements."""
    text_extensions = {'.py', '.yaml', '.yml', '.json', '.toml', '.txt', '.md', '.html', '.css', '.js', '.conf', '.sh'}
    return file_path.suffix.lower() in text_extensions


def replace_project_name(file_path: Path, project_name: str) -> None:
    """Replace template project name with actual project name."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace common template placeholders
        replacements = {
            "Django CFG Sample": project_name,
            "django-cfg-sample": project_name.lower().replace(" ", "-"),
            "django_cfg_sample": project_name.lower().replace(" ", "_").replace("-", "_"),
            "DjangoCfgSample": "".join(word.capitalize() for word in project_name.replace("-", " ").replace("_", " ").split()),
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except (UnicodeDecodeError, PermissionError, OSError):
        # Skip binary files or files we can't process
        pass


def create_gitignore(target_path: Path) -> None:
    """Create a comprehensive .gitignore file."""
    gitignore_content = """# Django CFG Project .gitignore

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
db/
cache/

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json
pnpm-lock.yaml

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Django CFG specific
static/
media/
openapi/temp/
openapi/archive/files/
openapi/clients/

# Docker
docker-compose.override.yml
.dockerignore

# Local configuration
config.local.yaml
.env.local
"""
    
    gitignore_path = target_path / ".gitignore"
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)


def create_readme(target_path: Path, project_name: str) -> None:
    """Create a README.md file for the new project."""
    readme_content = f"""# {project_name}

A Django project powered by **django-cfg** - the production-ready Django configuration framework.

## 🚀 Features

This project includes:

- **🔧 Type-safe Configuration** - Pydantic v2 models with validation
- **📱 Twilio Integration** - OTP services (WhatsApp, SMS, Email) 
- **📧 Email Services** - SendGrid integration
- **💬 Telegram Bot** - Notifications and alerts
- **🎨 Modern Admin** - Unfold admin interface
- **📊 API Documentation** - Auto-generated OpenAPI/Swagger
- **🔐 JWT Authentication** - Ready-to-use auth system
- **🗃️ Multi-database Support** - With automatic routing
- **⚡ Background Tasks** - Dramatiq task processing
- **🌐 Ngrok Integration** - Easy webhook testing
- **🐳 Docker Ready** - Complete containerization

## 📦 Quick Start

1. **Install Dependencies**
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Copy and edit configuration
   cp api/environment/config.dev.yaml api/environment/config.local.yaml
   # Edit config.local.yaml with your settings
   ```

3. **Setup Database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Populate Sample Data** (Optional)
   ```bash
   python manage.py populate_sample_data
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## 🔧 Configuration

Edit `api/environment/config.dev.yaml` (or create `config.local.yaml`) to configure:

- **Database connections** (PostgreSQL, MySQL, SQLite)
- **Email settings** (SMTP, SendGrid)
- **Twilio credentials** (Account SID, Auth Token, Verify Service SID)
- **Telegram bot** (Bot Token, Chat ID)
- **API keys** (OpenAI, OpenRouter, etc.)
- **Cache settings** (Redis)

## 📱 Twilio OTP Usage

```python
from django_cfg import send_sms_otp, send_whatsapp_otp, send_email_otp, verify_otp

# Send SMS OTP
success, message = send_sms_otp("+1234567890")

# Send WhatsApp OTP with SMS fallback
success, message = send_whatsapp_otp("+1234567890", fallback_to_sms=True)

# Send Email OTP
success, message, code = send_email_otp("user@example.com")

# Verify OTP
is_valid, result = verify_otp("+1234567890", "123456")
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or use the production setup
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

## 📚 Documentation

- **Admin Interface**: `http://localhost:8000/admin/`
- **API Documentation**: `http://localhost:8000/api/schema/swagger-ui/`
- **Django CFG Docs**: [django-cfg.unrealos.com](https://django-cfg.unrealos.com)

## 🛠️ Development

```bash
# Run with Ngrok for webhook testing
python manage.py runserver_ngrok

# Generate OpenAPI clients
python manage.py generate_openapi_clients

# Translate content (if using i18n)
python manage.py translate_content
```

## 📁 Project Structure

```
{project_name.lower().replace(" ", "_")}/
├── api/                    # Configuration and settings
│   ├── config.py          # Main django-cfg configuration
│   ├── environment/       # Environment-specific configs
│   ├── settings.py        # Generated Django settings
│   └── urls.py           # Root URL configuration
├── apps/                  # Django applications
│   ├── blog/             # Blog app example
│   ├── profiles/         # User profiles
│   └── shop/             # E-commerce example
├── core/                 # Core utilities and management commands
├── docker/               # Docker configuration
├── static/               # Static files
├── templates/            # Django templates
└── manage.py            # Django management script
```

## 🤝 Contributing

This project uses **django-cfg** for configuration management. 
For more information, visit: [https://github.com/unrealos/django-cfg](https://github.com/unrealos/django-cfg)

## 📄 License

MIT License - see LICENSE file for details.

---

**Powered by django-cfg** 🚀
"""
    
    readme_path = target_path / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)


def install_dependencies(target_path: Path, use_poetry: bool = True) -> bool:
    """Install project dependencies using Poetry or pip."""
    try:
        if use_poetry:
            click.echo("📦 Installing dependencies with Poetry...")
            subprocess.run(
                ["poetry", "install"],
                cwd=target_path,
                check=True,
                capture_output=True,
                text=True
            )
        else:
            click.echo("📦 Installing dependencies with pip...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=target_path,
                check=True,
                capture_output=True,
                text=True
            )
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"⚠️  Warning: Failed to install dependencies: {e}", err=True)
        return False
    except FileNotFoundError:
        click.echo("⚠️  Warning: Poetry/pip not found, skipping dependency installation", err=True)
        return False


@click.command()
@click.argument("project_name")
@click.option(
    "--path",
    "-p",
    type=click.Path(),
    default=".",
    help="Directory where to create the project (default: current directory)"
)
@click.option(
    "--no-deps",
    is_flag=True,
    help="Skip automatic dependency installation"
)
@click.option(
    "--use-pip",
    is_flag=True,
    help="Use pip instead of Poetry for dependency installation"
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing directory if it exists"
)
def create_project(project_name: str, path: str, no_deps: bool, use_pip: bool, force: bool):
    """
    🚀 Create a new Django project with django-cfg
    
    Creates a complete Django project with type-safe configuration,
    modern admin interface, API documentation, and production-ready setup.
    
    PROJECT_NAME: Name of the new Django project
    
    Examples:
    
        # Create project in current directory
        django-cfg create-project "My Awesome Project"
        
        # Create project in specific directory  
        django-cfg create-project "My Project" --path ./projects/
        
        # Skip dependency installation
        django-cfg create-project "My Project" --no-deps
        
        # Use pip instead of Poetry
        django-cfg create-project "My Project" --use-pip
    """
    
    # Validate project name
    if not project_name.strip():
        click.echo("❌ Project name cannot be empty", err=True)
        return
    
    # Determine target path
    base_path = Path(path).resolve()
    project_dir_name = project_name.lower().replace(" ", "_").replace("-", "_")
    target_path = base_path / project_dir_name
    
    # Check if target directory exists
    if target_path.exists():
        if not force:
            click.echo(f"❌ Directory '{target_path}' already exists. Use --force to overwrite.", err=True)
            return
        else:
            click.echo(f"⚠️  Removing existing directory '{target_path}'...")
            shutil.rmtree(target_path)
    
    try:
        # Get template archive path
        archive_path = get_template_archive_path()
        click.echo(f"📋 Using template archive: {archive_path.name}")
        
        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Extract template files
        extract_template(archive_path, target_path, project_name)
        
        # Create additional files
        create_gitignore(target_path)
        create_readme(target_path, project_name)
        
        click.echo(f"✅ Project '{project_name}' created successfully!")
        click.echo(f"📁 Location: {target_path}")
        
        # Install dependencies if requested
        if not no_deps:
            install_success = install_dependencies(target_path, not use_pip)
            if not install_success:
                click.echo("💡 You can install dependencies manually later:")
                if not use_pip:
                    click.echo("   poetry install")
                else:
                    click.echo("   pip install -r requirements.txt")
        
        # Show next steps
        click.echo("\n🎉 Your Django CFG project is ready!")
        click.echo("\n📋 Next steps:")
        click.echo(f"   cd {project_dir_name}")
        
        if no_deps:
            if not use_pip:
                click.echo("   poetry install")
            else:
                click.echo("   pip install -r requirements.txt")
        
        click.echo("   # Edit api/environment/config.dev.yaml with your settings")
        click.echo("   python manage.py migrate")
        click.echo("   python manage.py createsuperuser")
        click.echo("   python manage.py runserver")
        
        click.echo("\n💡 Features included:")
        click.echo("   🔧 Type-safe configuration with Pydantic v2")
        click.echo("   📱 Twilio integration (WhatsApp, SMS, Email OTP)")
        click.echo("   📧 Email services with SendGrid")
        click.echo("   💬 Telegram bot integration")
        click.echo("   🎨 Modern Unfold admin interface")
        click.echo("   📊 Auto-generated API documentation")
        click.echo("   🔐 JWT authentication system")
        click.echo("   🗃️ Multi-database support with routing")
        click.echo("   ⚡ Background task processing")
        click.echo("   🐳 Docker deployment ready")
        
        click.echo(f"\n📚 Documentation: https://django-cfg.unrealos.com")
        
    except FileNotFoundError as e:
        click.echo(f"❌ Template archive not found: {e}", err=True)
        click.echo("💡 Make sure django-cfg is properly installed")
        click.echo("💡 In development, run: python scripts/template_manager.py create")
        
    except (ValueError, RuntimeError) as e:
        click.echo(f"❌ Template error: {e}", err=True)
        # Clean up on error
        if target_path.exists():
            shutil.rmtree(target_path, ignore_errors=True)
        
    except Exception as e:
        click.echo(f"❌ Error creating project: {e}", err=True)
        # Clean up on error
        if target_path.exists():
            shutil.rmtree(target_path, ignore_errors=True)
