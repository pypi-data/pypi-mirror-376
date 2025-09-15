# 🚀 Django CFG CLI

Command-line interface for django-cfg - the production-ready Django configuration framework.

## 📦 Installation

The CLI is automatically installed when you install django-cfg:

```bash
pip install django-cfg
# or
poetry add django-cfg
```

## 🎯 Available Commands

### `django-cfg create-project`

Creates a new Django project with django-cfg configuration and modern features.

```bash
# Basic usage
django-cfg create-project "My Awesome Project"

# Create in specific directory
django-cfg create-project "My Project" --path ./projects/

# Skip automatic dependency installation
django-cfg create-project "My Project" --no-deps

# Use pip instead of Poetry
django-cfg create-project "My Project" --use-pip

# Force overwrite existing directory
django-cfg create-project "My Project" --force
```

**Features included in generated project:**

- 🔧 **Type-safe Configuration** - Pydantic v2 models with validation
- 📱 **Twilio Integration** - OTP services (WhatsApp, SMS, Email)
- 📧 **Email Services** - SendGrid integration
- 💬 **Telegram Bot** - Notifications and alerts
- 🎨 **Modern Admin** - Unfold admin interface
- 📊 **API Documentation** - Auto-generated OpenAPI/Swagger
- 🔐 **JWT Authentication** - Ready-to-use auth system
- 🗃️ **Multi-database Support** - With automatic routing
- ⚡ **Background Tasks** - Dramatiq task processing
- 🌐 **Ngrok Integration** - Easy webhook testing
- 🐳 **Docker Ready** - Complete containerization

### `django-cfg info`

Shows information about django-cfg installation and available features.

```bash
# Basic information
django-cfg info

# Detailed information
django-cfg info --verbose
```

**Information displayed:**

- Package version and installation path
- Python version
- Template availability
- Dependency status (core, services, admin, API, tasks, development)
- Available commands
- Quick start guide

## 🏗️ Project Structure

The generated project follows this structure:

```
my_project/
├── api/                    # Configuration and settings
│   ├── config.py          # Main django-cfg configuration
│   ├── environment/       # Environment-specific configs
│   │   ├── config.dev.yaml
│   │   ├── config.prod.yaml
│   │   └── config.test.yaml
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
├── manage.py            # Django management script
├── pyproject.toml       # Poetry configuration
├── requirements.txt     # Pip requirements
└── README.md           # Project documentation
```

## ⚙️ Configuration

After creating a project, configure your environment:

1. **Edit Configuration**
   ```bash
   # Copy and customize
   cp api/environment/config.dev.yaml api/environment/config.local.yaml
   # Edit config.local.yaml with your settings
   ```

2. **Set up Services**
   ```yaml
   # api/environment/config.local.yaml
   api_keys:
     twilio:
       account_sid: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
       auth_token: "your_twilio_auth_token"
       verify_service_sid: "VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
     sendgrid_api_key: "SG.your_sendgrid_api_key"
   
   email:
     default_from: "noreply@yourapp.com"
   
   telegram:
     bot_token: "your_telegram_bot_token"
     chat_id: 123456789
   ```

3. **Install Dependencies**
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## 🔧 CLI Development

### Adding New Commands

1. Create a new command file in `src/django_cfg/cli/commands/`:

```python
# src/django_cfg/cli/commands/my_command.py
import click

@click.command()
@click.option("--option", help="Command option")
def my_command(option: str):
    """My custom command description."""
    click.echo(f"Running my command with option: {option}")
```

2. Register the command in `src/django_cfg/cli/main.py`:

```python
from .commands.my_command import my_command

# Add to cli group
cli.add_command(my_command)
```

### Template Customization

The project template is located in `django_sample/`. To customize:

1. Modify files in `django_sample/`
2. Use placeholder text that will be replaced:
   - `Django CFG Sample` → Project name
   - `django-cfg-sample` → Kebab-case project name
   - `django_cfg_sample` → Snake-case project name
   - `DjangoCfgSample` → PascalCase project name

## 🧪 Testing CLI

```bash
# Test CLI help
python -m django_cfg.cli.main --help

# Test info command
python -m django_cfg.cli.main info

# Test project creation (in temp directory)
cd /tmp
python -m django_cfg.cli.main create-project "Test Project" --no-deps
```

## 📚 Examples

### Creating Different Project Types

```bash
# Simple blog project
django-cfg create-project "My Blog" --path ./blogs/

# E-commerce project
django-cfg create-project "My Shop" --path ./shops/

# API-only project
django-cfg create-project "My API" --path ./apis/
```

### Using with Different Package Managers

```bash
# With Poetry (default)
django-cfg create-project "My Project"

# With pip
django-cfg create-project "My Project" --use-pip

# Skip dependency installation
django-cfg create-project "My Project" --no-deps
```

## 🐛 Troubleshooting

### Template Not Found

If you get "Template not found" error:

```bash
# Check installation
django-cfg info --verbose

# Reinstall django-cfg
pip uninstall django-cfg
pip install django-cfg
```

### Permission Errors

```bash
# Use --force to overwrite existing directory
django-cfg create-project "My Project" --force

# Or remove directory manually
rm -rf my_project/
django-cfg create-project "My Project"
```

### Dependency Installation Fails

```bash
# Create project without dependencies
django-cfg create-project "My Project" --no-deps

# Install manually
cd my_project/
poetry install  # or pip install -r requirements.txt
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your CLI command in `src/django_cfg/cli/commands/`
4. Register the command in `main.py`
5. Add tests
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Powered by django-cfg** 🚀
