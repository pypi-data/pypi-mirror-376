"""
Django CFG Template Manager

Manages template archiving and extraction for CLI operations.
Creates compressed archives of django_sample for distribution.
"""

import zipfile
import os
import shutil
from pathlib import Path
from typing import List, Optional
import tempfile
import logging
import tomlkit

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages Django CFG project templates."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize template manager.
        
        Args:
            project_root: Root directory of the django-cfg project
        """
        if project_root is None:
            # Auto-detect project root (where this script is located)
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.django_sample_path = self.project_root / "django_sample"
        self.archive_dir = self.project_root / "src" / "django_cfg" / "archive"
        self.archive_path = self.archive_dir / "django_sample.zip"
        
        # Files and directories to exclude from template
        self.exclude_patterns = {
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
            ".git",
            ".gitignore",
            "db/",
            "cache/",
            "node_modules/",
            "*.sqlite3",
            "poetry.lock",
            "pnpm-lock.yaml", 
            "package-lock.json",
            ".venv/",
            ".env",
            ".env.*",
            "docker/volumes/",
        }
    
    def should_exclude(self, file_path: Path, relative_path: Path) -> bool:
        """
        Check if a file should be excluded from the template.
        
        Args:
            file_path: Absolute path to the file
            relative_path: Relative path from django_sample root
            
        Returns:
            True if file should be excluded
        """
        # Check if it's a directory we want to exclude
        for part in relative_path.parts:
            if part in {"__pycache__", "node_modules", "db", "cache", ".venv", ".git"}:
                return True
        
        # Check specific patterns
        file_name = file_path.name
        
        # Exclude cache files
        if file_name.endswith(('.pyc', '.pyo')):
            return True
            
        # Exclude lock files
        if file_name in {"poetry.lock", "pnpm-lock.yaml", "package-lock.json"}:
            return True
            
        # Exclude database files
        if file_name.endswith('.sqlite3'):
            return True
            
        # Exclude environment files
        if file_name.startswith('.env'):
            return True
            
        # Exclude system files
        if file_name in {'.DS_Store', 'Thumbs.db'}:
            return True
            
        # Exclude docker volumes
        if "docker/volumes" in str(relative_path):
            return True
            
        return False
    
    def create_template_archive(self, force: bool = False) -> Path:
        """
        Create a ZIP archive of the django_sample template.
        
        Args:
            force: Overwrite existing archive if it exists
            
        Returns:
            Path to the created archive
            
        Raises:
            FileNotFoundError: If django_sample directory doesn't exist
            FileExistsError: If archive exists and force=False
        """
        if not self.django_sample_path.exists():
            raise FileNotFoundError(f"Template source not found: {self.django_sample_path}")
        
        if self.archive_path.exists() and not force:
            raise FileExistsError(f"Archive already exists: {self.archive_path}")
        
        # Ensure archive directory exists
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temporary archive first, then move to final location
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            files_added = 0
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for root, dirs, files in os.walk(self.django_sample_path):
                    # Filter out excluded directories
                    dirs[:] = [d for d in dirs if not self._should_exclude_dir(Path(root) / d)]
                    
                    for file in files:
                        file_path = Path(root) / file
                        relative_path = file_path.relative_to(self.django_sample_path)
                        
                        if not self.should_exclude(file_path, relative_path):
                            # Clean pyproject.toml files before adding to archive
                            if file_path.name == 'pyproject.toml':
                                with tempfile.NamedTemporaryFile(mode='w+', suffix='.toml', delete=False) as temp_toml:
                                    temp_toml_path = Path(temp_toml.name)
                                
                                try:
                                    # Copy and clean
                                    shutil.copy2(file_path, temp_toml_path)
                                    self._clean_pyproject_for_template(temp_toml_path)
                                    archive.write(temp_toml_path, relative_path)
                                    files_added += 1
                                finally:
                                    temp_toml_path.unlink(missing_ok=True)
                            else:
                                archive.write(file_path, relative_path)
                                files_added += 1
            
            # Move temp file to final location
            if self.archive_path.exists():
                self.archive_path.unlink()
            shutil.move(temp_path, self.archive_path)
            
            logger.info(f"Created template archive: {self.archive_path}")
            logger.info(f"Files included: {files_added}")
            logger.info(f"Archive size: {self.archive_path.stat().st_size / 1024:.1f} KB")
            
            return self.archive_path
            
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """Check if a directory should be excluded."""
        dir_name = dir_path.name
        return dir_name in {"__pycache__", "node_modules", "db", "cache", ".venv", ".git"}
    
    def extract_template(self, target_path: Path, project_name: str) -> None:
        """
        Extract template archive to target directory.
        
        Args:
            target_path: Directory where to extract the template
            project_name: Name of the new project (for replacements)
            
        Raises:
            FileNotFoundError: If archive doesn't exist
        """
        if not self.archive_path.exists():
            raise FileNotFoundError(f"Template archive not found: {self.archive_path}")
        
        target_path = Path(target_path)
        target_path.mkdir(parents=True, exist_ok=True)
        
        files_extracted = 0
        with zipfile.ZipFile(self.archive_path, 'r') as archive:
            for member in archive.namelist():
                # Extract file
                archive.extract(member, target_path)
                files_extracted += 1
                
                # Apply project name replacements
                extracted_file = target_path / member
                if extracted_file.is_file() and self._should_process_file(extracted_file):
                    # Clean pyproject.toml files first, then apply replacements
                    if extracted_file.name == 'pyproject.toml':
                        self._clean_pyproject_for_template(extracted_file)
                    self._replace_project_name(extracted_file, project_name)
        
        logger.info(f"Extracted template to: {target_path}")
        logger.info(f"Files extracted: {files_extracted}")
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed for name replacements."""
        text_extensions = {'.py', '.yaml', '.yml', '.json', '.toml', '.txt', '.md', '.html', '.css', '.js'}
        return file_path.suffix.lower() in text_extensions
    
    def _clean_pyproject_for_template(self, file_path: Path) -> None:
        """Remove local-dev blocks from pyproject.toml for template distribution."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = tomlkit.load(f)
            
            modified = False
            
            # Remove Poetry local-dev blocks
            poetry = content.get('tool', {}).get('poetry', {})
            if 'extras' in poetry and 'local-dev' in poetry['extras']:
                del poetry['extras']['local-dev']
                modified = True
            if 'group' in poetry and 'local-dev' in poetry['group']:
                del poetry['group']['local-dev']
                modified = True
            
            # Remove PEP 621 local-dev blocks
            project = content.get('project', {})
            if 'optional-dependencies' in project and 'local-dev' in project['optional-dependencies']:
                del project['optional-dependencies']['local-dev']
                modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    tomlkit.dump(content, f)
                logger.info(f"Cleaned local-dev blocks from {file_path.name}")
                
        except Exception as e:
            logger.warning(f"Failed to clean {file_path.name}: {e}")
    
    def _replace_project_name(self, file_path: Path, project_name: str) -> None:
        """Replace template project names with actual project name."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Define replacements
            replacements = {
                "Django CFG Sample": project_name,
                "django-cfg-sample": project_name.lower().replace(" ", "-"),
                "django_cfg_sample": project_name.lower().replace(" ", "_").replace("-", "_"),
                "DjangoCfgSample": "".join(word.capitalize() for word in project_name.replace("-", " ").replace("_", " ").split()),
            }
            
            # Apply replacements
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except (UnicodeDecodeError, PermissionError):
            # Skip binary files or files we can't process
            pass
    
    def get_archive_info(self) -> dict:
        """
        Get information about the template archive.
        
        Returns:
            Dictionary with archive information
        """
        if not self.archive_path.exists():
            return {
                "exists": False,
                "path": str(self.archive_path),
            }
        
        stat = self.archive_path.stat()
        
        # Count files in archive
        file_count = 0
        try:
            with zipfile.ZipFile(self.archive_path, 'r') as archive:
                file_count = len(archive.namelist())
        except zipfile.BadZipFile:
            file_count = -1
        
        return {
            "exists": True,
            "path": str(self.archive_path),
            "size_bytes": stat.st_size,
            "size_kb": stat.st_size / 1024,
            "file_count": file_count,
            "modified": stat.st_mtime,
        }
    
    def validate_archive(self) -> bool:
        """
        Validate that the template archive is valid.
        
        Returns:
            True if archive is valid
        """
        if not self.archive_path.exists():
            return False
        
        try:
            with zipfile.ZipFile(self.archive_path, 'r') as archive:
                # Test the archive
                archive.testzip()
                
                # Check that it contains expected files
                files = archive.namelist()
                required_files = ['manage.py', 'api/config.py', 'api/settings.py']
                
                for required in required_files:
                    if required not in files:
                        logger.warning(f"Required file missing from archive: {required}")
                        return False
                
                return True
                
        except (zipfile.BadZipFile, Exception) as e:
            logger.error(f"Archive validation failed: {e}")
            return False


def main():
    """CLI interface for template manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Django CFG Template Manager")
    parser.add_argument("command", choices=["create", "info", "validate", "extract"])
    parser.add_argument("--force", action="store_true", help="Force overwrite existing archive")
    parser.add_argument("--target", help="Target directory for extraction")
    parser.add_argument("--project-name", help="Project name for extraction")
    parser.add_argument("--clean", action="store_true", help="Clean local-dev dependencies from pyproject.toml files")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    manager = TemplateManager()
    
    if args.command == "create":
        try:
            archive_path = manager.create_template_archive(force=args.force)
            print(f"✅ Template archive created: {archive_path}")
        except Exception as e:
            print(f"❌ Error creating archive: {e}")
            exit(1)
    
    elif args.command == "info":
        info = manager.get_archive_info()
        if info["exists"]:
            print(f"📦 Archive: {info['path']}")
            print(f"📏 Size: {info['size_kb']:.1f} KB")
            print(f"📄 Files: {info['file_count']}")
        else:
            print("❌ Archive does not exist")
    
    elif args.command == "validate":
        if manager.validate_archive():
            print("✅ Archive is valid")
        else:
            print("❌ Archive is invalid")
            exit(1)
    
    elif args.command == "extract":
        if not args.target or not args.project_name:
            print("❌ --target and --project-name required for extract")
            exit(1)
        
        try:
            manager.extract_template(Path(args.target), args.project_name)
            print(f"✅ Template extracted to: {args.target}")
        except Exception as e:
            print(f"❌ Error extracting template: {e}")
            exit(1)


if __name__ == "__main__":
    main()
