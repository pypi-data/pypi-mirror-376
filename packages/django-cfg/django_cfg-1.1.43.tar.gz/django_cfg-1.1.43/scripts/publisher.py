#!/usr/bin/env python3
"""
Django-CFG Publisher

Interactive CLI for publishing the package to PyPI or TestPyPI.
"""

import os
import sys
import subprocess
import questionary
import tomlkit
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.version_manager import VersionManager
from scripts.template_manager import TemplateManager

console = Console()


def clean_pyproject_for_publishing():
    """Temporarily remove local-dev dependencies for PyPI publishing."""
    pyproject_path = Path("pyproject.toml")
    backup_path = Path("pyproject.toml.backup")
    
    # Create backup
    shutil.copy2(pyproject_path, backup_path)
    console.print("[yellow]📝 Created backup of pyproject.toml[/yellow]")
    
    # Load and modify pyproject.toml
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = tomlkit.load(f)
    
    # Remove local-dev from optional-dependencies
    if 'project' in content and 'optional-dependencies' in content['project']:
        optional_deps = content['project']['optional-dependencies']
        if 'local-dev' in optional_deps:
            del optional_deps['local-dev']
            console.print("[yellow]🗑️  Removed local-dev dependencies for PyPI compatibility[/yellow]")
    
    # Write cleaned version
    with open(pyproject_path, 'w', encoding='utf-8') as f:
        tomlkit.dump(content, f)
    
    return backup_path


def create_template_archive():
    """Create template archive before building."""
    console.print("[yellow]📦 Creating template archive...[/yellow]")
    
    try:
        manager = TemplateManager()
        # Force create archive with cleaned pyproject.toml files
        archive_path = manager.create_template_archive(force=True)
        
        info = manager.get_archive_info()
        console.print(f"[green]✅ Template archive created: {info['size_kb']:.1f} KB ({info['file_count']} files)[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Failed to create template archive: {e}[/red]")
        return False


def restore_pyproject(backup_path):
    """Restore original pyproject.toml from backup."""
    pyproject_path = Path("pyproject.toml")
    if backup_path.exists():
        shutil.move(backup_path, pyproject_path)
        console.print("[green]✅ Restored original pyproject.toml[/green]")


def main():
    console.print(
        Panel(
            "[bold blue]Django-CFG Publisher[/bold blue]\nInteractive package publishing to PyPI",
            title="🚀 PyPI Publisher",
            border_style="blue",
        )
    )

    # Initialize version manager
    version_manager = VersionManager()

    # Show current version
    current_version = version_manager.get_current_version()
    console.print(f"[blue]Current version: {current_version}[/blue]")

    # Version bump selection
    bump_version = questionary.confirm(
        "Do you want to bump the version before publishing?", default=True
    ).ask()

    if bump_version:
        bump_type = questionary.select(
            "What type of version bump?",
            choices=[
                questionary.Choice("Patch (1.0.1 → 1.0.2)", value="patch"),
                questionary.Choice("Minor (1.0.1 → 1.1.0)", value="minor"),
                questionary.Choice("Major (1.0.1 → 2.0.0)", value="major"),
                questionary.Choice("Cancel", value=None),
            ],
        ).ask()

        if bump_type:
            try:
                new_version = version_manager.bump_version(bump_type)
                console.print(f"[green]✅ Version bumped to: {new_version}[/green]")

                # Validate version consistency
                if not version_manager.validate_version_consistency():
                    console.print(
                        "[red]❌ Version inconsistencies found! Please fix before publishing.[/red]"
                    )
                    return 1

            except Exception as e:
                console.print(f"[red]❌ Failed to bump version: {e}[/red]")
                return 1
        else:
            console.print("❌ Publishing cancelled.")
            return 0

    # Repository selection
    repo = questionary.select(
        "Where do you want to publish the package?",
        choices=[
            questionary.Choice("PyPI (production)", value="pypi"),
            questionary.Choice("TestPyPI (test)", value="testpypi"),
            questionary.Choice("Cancel", value=None),
        ],
    ).ask()
    if not repo:
        console.print("❌ Publishing cancelled.")
        return 0

    # Confirmation
    confirm = questionary.confirm(
        f"Publish to {'PyPI' if repo == 'pypi' else 'TestPyPI'}?", default=True
    ).ask()
    if not confirm:
        console.print("❌ Publishing cancelled.")
        return 0

    # Cleanup old build artifacts
    for pattern in ["build", "dist", "*.egg-info"]:
        for path in Path().glob(pattern):
            if path.exists():
                console.print(f"[blue]Removing old {path}...[/blue]")
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    # Generate requirements files before building
    console.print("[yellow]Generating requirements files...[/yellow]")
    try:
        requirements_result = subprocess.run([
            sys.executable, "scripts/generate_requirements.py"
        ], check=True, capture_output=True, text=True)
        console.print("✅ Requirements files generated from pyproject.toml")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Requirements generation failed: {e}[/red]")
        if e.stdout:
            console.print(f"[red]stdout: {e.stdout}[/red]")
        if e.stderr:
            console.print(f"[red]stderr: {e.stderr}[/red]")
        return 1

    # Create template archive before building
    if not create_template_archive():
        console.print("[red]❌ Template archive creation failed. Cannot proceed with publishing.[/red]")
        return 1

    # Clean pyproject.toml for PyPI publishing
    backup_path = clean_pyproject_for_publishing()
    
    try:
        # Build step
        console.print("[yellow]Building the package...[/yellow]")
        build_result = subprocess.run(
            [sys.executable, "-m", "build"], capture_output=True, text=True
        )
        console.print(build_result.stdout)
        if build_result.returncode != 0:
            console.print(f"[red]❌ Build failed![/red]\n{build_result.stderr}")
            return build_result.returncode

        # Check dist/ folder
        if not Path("dist").is_dir():
            console.print("[red]dist/ folder not found! Please build the package first.[/red]")
            return 1

        # Run publishing with twine
        console.print("[yellow]Publishing with twine...[/yellow]")
        twine_cmd = (
            ["twine", "upload", "--repository", repo, "dist/*"]
            if repo == "testpypi"
            else ["twine", "upload", "dist/*"]
        )
        result = subprocess.run(twine_cmd, check=False)
        if result.returncode == 0:
            console.print("[green]✅ Package published successfully![/green]")
        else:
            console.print(f"[red]❌ Publishing failed. Return code: {result.returncode}[/red]")
        return result.returncode
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        return 1
    finally:
        # Always restore the original pyproject.toml
        restore_pyproject(backup_path)


if __name__ == "__main__":
    sys.exit(main())