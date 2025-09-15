"""
Django CFG Info Command

Shows information about django-cfg installation and available features.
"""

import click
import sys
from pathlib import Path
from typing import Dict, Any


def get_package_info() -> Dict[str, Any]:
    """Get django-cfg package information."""
    try:
        import django_cfg
        package_path = Path(django_cfg.__file__).parent
        
        # Try to get version from package
        version = "1.0.0"  # fallback
        try:
            from importlib.metadata import version as get_version
            version = get_version("django-cfg")
        except:
            pass
        
        return {
            "version": version,
            "path": package_path,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
    except ImportError:
        return {}


def check_optional_dependencies() -> Dict[str, bool]:
    """Check which optional dependencies are installed."""
    dependencies = {
        # Core integrations
        "django": False,
        "pydantic": False,
        "pydantic-yaml": False,
        
        # Services
        "twilio": False,
        "sendgrid": False,
        "openai": False,
        "telegram-bot-api": False,
        
        # Admin & UI
        "django-unfold": False,
        "django-constance": False,
        
        # API & Documentation
        "djangorestframework": False,
        "drf-spectacular": False,
        
        # Tasks & Background Processing
        "dramatiq": False,
        "redis": False,
        
        # Development
        "ngrok": False,
        "click": False,
    }
    
    for dep in dependencies:
        try:
            __import__(dep.replace("-", "_"))
            dependencies[dep] = True
        except ImportError:
            dependencies[dep] = False
    
    return dependencies


def get_template_info() -> Dict[str, Any]:
    """Get information about available template archive."""
    import sysconfig
    import zipfile
    
    try:
        import django_cfg
        package_path = Path(django_cfg.__file__).parent
        
        # Method 1: Check if template archive is in package templates directory
        template_archive = package_path / "archive" / "django_sample.zip"
        if template_archive.exists():
            return _get_archive_info(template_archive)
            
        # Method 2: Check if it's in site-packages shared data
        site_packages = Path(sysconfig.get_paths()["purelib"])
        shared_archive = site_packages / "django_cfg" / "archive" / "django_sample.zip"
        if shared_archive.exists():
            return _get_archive_info(shared_archive)
        
        # Method 3: Development installation - check src directory
        package_path = Path(django_cfg.__file__).parent.parent.parent
        src_archive = package_path / "src" / "django_cfg" / "archive" / "django_sample.zip"
        if src_archive.exists():
            return _get_archive_info(src_archive)
            
        # Method 4: Try relative to this file (development)
        cli_path = Path(__file__).parent.parent.parent.parent.parent
        dev_archive = cli_path / "src" / "django_cfg" / "archive" / "django_sample.zip"
        if dev_archive.exists():
            return _get_archive_info(dev_archive)
            
    except:
        pass
    
    return {
        "template_available": False,
        "template_path": None,
        "template_name": None,
        "template_type": "archive"
    }


def _get_archive_info(archive_path: Path) -> Dict[str, Any]:
    """Get detailed information about template archive."""
    import zipfile
    
    try:
        stat = archive_path.stat()
        
        # Count files in archive
        file_count = 0
        is_valid = False
        try:
            with zipfile.ZipFile(archive_path, 'r') as archive:
                file_count = len(archive.namelist())
                # Test if archive is valid
                archive.testzip()
                is_valid = True
        except zipfile.BadZipFile:
            is_valid = False
        
        return {
            "template_available": True,
            "template_path": archive_path,
            "template_name": "django_sample",
            "template_type": "archive",
            "size_bytes": stat.st_size,
            "size_kb": stat.st_size / 1024,
            "file_count": file_count,
            "is_valid": is_valid,
        }
        
    except Exception:
        return {
            "template_available": False,
            "template_path": archive_path,
            "template_name": "django_sample",
            "template_type": "archive",
            "is_valid": False,
        }


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def info(verbose: bool):
    """
    📋 Show django-cfg installation and system information
    
    Displays version, installation path, available features,
    and optional dependency status.
    """
    
    click.echo("🚀 Django CFG - Production-ready Django Configuration Framework")
    click.echo("=" * 70)
    
    # Package information
    package_info = get_package_info()
    if package_info:
        click.echo(f"📦 Version: {package_info['version']}")
        click.echo(f"🐍 Python: {package_info['python_version']}")
        if verbose:
            click.echo(f"📁 Installation: {package_info['path']}")
    else:
        click.echo("❌ django-cfg not found or not properly installed")
        return
    
    click.echo()
    
    # Template information
    template_info = get_template_info()
    if template_info["template_available"]:
        click.echo("📋 Project Template:")
        template_name = template_info['template_name']
        if template_info.get("template_type") == "archive":
            size_info = f" ({template_info.get('size_kb', 0):.1f} KB, {template_info.get('file_count', 0)} files)"
            if template_info.get("is_valid", True):
                click.echo(f"   ✅ {template_name} archive - Available{size_info}")
            else:
                click.echo(f"   ⚠️  {template_name} archive - Corrupted{size_info}")
        else:
            click.echo(f"   ✅ {template_name} - Available")
        
        if verbose:
            click.echo(f"   📁 Path: {template_info['template_path']}")
            if template_info.get("template_type") == "archive":
                click.echo(f"   📦 Type: ZIP Archive")
                if "size_bytes" in template_info:
                    click.echo(f"   📏 Size: {template_info['size_bytes']} bytes")
    else:
        click.echo("📋 Project Template:")
        click.echo("   ❌ Template archive not found")
        click.echo("   💡 Run: python scripts/template_manager.py create")
    
    click.echo()
    
    # Dependencies check
    deps = check_optional_dependencies()
    
    # Core dependencies
    click.echo("🔧 Core Dependencies:")
    core_deps = ["django", "pydantic", "pydantic-yaml", "click"]
    for dep in core_deps:
        status = "✅" if deps.get(dep, False) else "❌"
        click.echo(f"   {status} {dep}")
    
    click.echo()
    
    # Service integrations
    click.echo("🌐 Service Integrations:")
    service_deps = ["twilio", "sendgrid", "openai", "telegram-bot-api"]
    for dep in service_deps:
        status = "✅" if deps.get(dep, False) else "⚪"
        click.echo(f"   {status} {dep}")
    
    click.echo()
    
    # Admin & UI
    click.echo("🎨 Admin & UI:")
    ui_deps = ["django-unfold", "django-constance"]
    for dep in ui_deps:
        status = "✅" if deps.get(dep, False) else "⚪"
        click.echo(f"   {status} {dep}")
    
    click.echo()
    
    # API & Documentation
    click.echo("📊 API & Documentation:")
    api_deps = ["djangorestframework", "drf-spectacular"]
    for dep in api_deps:
        status = "✅" if deps.get(dep, False) else "⚪"
        click.echo(f"   {status} {dep}")
    
    click.echo()
    
    # Background Processing
    click.echo("⚡ Background Processing:")
    task_deps = ["dramatiq", "redis"]
    for dep in task_deps:
        status = "✅" if deps.get(dep, False) else "⚪"
        click.echo(f"   {status} {dep}")
    
    click.echo()
    
    # Development tools
    click.echo("🛠️  Development Tools:")
    dev_deps = ["ngrok"]
    for dep in dev_deps:
        status = "✅" if deps.get(dep, False) else "⚪"
        click.echo(f"   {status} {dep}")
    
    click.echo()
    
    # Legend
    click.echo("Legend:")
    click.echo("   ✅ Installed and available")
    click.echo("   ⚪ Optional - not installed")
    click.echo("   ❌ Required - missing")
    
    click.echo()
    
    # Available commands
    click.echo("🎯 Available Commands:")
    click.echo("   django-cfg create-project <name>  - Create new Django project")
    click.echo("   django-cfg info                   - Show this information")
    click.echo("   django-cfg --help                 - Show help")
    
    click.echo()
    
    # Quick start
    click.echo("🚀 Quick Start:")
    click.echo("   # Create a new project")
    click.echo("   django-cfg create-project 'My Awesome Project'")
    click.echo()
    click.echo("   # Install optional dependencies")
    click.echo("   pip install twilio sendgrid django-unfold")
    click.echo()
    click.echo("📚 Documentation: https://django-cfg.unrealos.com")
    click.echo("🐙 GitHub: https://github.com/unrealos/django-cfg")
    
    # Warnings for missing critical dependencies
    missing_critical = [dep for dep in ["django", "pydantic"] if not deps.get(dep, False)]
    if missing_critical:
        click.echo()
        click.echo("⚠️  Warning: Missing critical dependencies:")
        for dep in missing_critical:
            click.echo(f"   pip install {dep}")
