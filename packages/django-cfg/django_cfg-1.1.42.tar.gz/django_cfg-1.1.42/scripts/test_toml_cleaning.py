#!/usr/bin/env python3
"""Test TOML cleaning - removes local-dev blocks from pyproject.toml"""

import sys
import tempfile
from pathlib import Path
import tomlkit

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.template_manager import TemplateManager

def test_cleaning():
    """Test local-dev block removal."""
    content = """[tool.poetry.extras]
local-dev = []

[tool.poetry.group.local-dev]
optional = true

[tool.poetry.group.local-dev.dependencies]
django-cfg = {path = "../", develop = true}

[project.optional-dependencies]
local-dev = ["django-cfg @ file:///path/to/local"]
"""
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.toml', delete=False) as f:
        f.write(content)
        test_file = Path(f.name)
    
    try:
        # Clean the file
        manager = TemplateManager()
        manager._clean_pyproject_for_template(test_file)
        
        # Check results
        with open(test_file, 'r') as f:
            cleaned = tomlkit.load(f)
        
        # Verify removal
        poetry = cleaned.get('tool', {}).get('poetry', {})
        project = cleaned.get('project', {})
        
        poetry_clean = (
            'local-dev' not in poetry.get('extras', {}) and
            'local-dev' not in poetry.get('group', {})
        )
        pep621_clean = 'local-dev' not in project.get('optional-dependencies', {})
        
        if poetry_clean and pep621_clean:
            print("✅ TOML cleaning works!")
            return True
        else:
            print("❌ TOML cleaning failed")
            return False
            
    finally:
        test_file.unlink()

if __name__ == "__main__":
    success = test_cleaning()
    sys.exit(0 if success else 1)
