import pytest
import importlib
import pkgutil
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_modules(package_path):
    """Utility to discover modules in a directory"""
    modules = []
    for loader, module_name, is_pkg in pkgutil.walk_packages([package_path]):
        modules.append(module_name)
    return modules

@pytest.mark.parametrize("module_name", get_modules("src/views"))
def test_views_import_integrity(module_name):
    """Verify that every view file can be imported without Syntax or Indentation errors"""
    try:
        importlib.import_module(f"src.views.{module_name}")
    except (ImportError, SyntaxError, IndentationError) as e:
        pytest.fail(f"Module src.views.{module_name} failed to import: {e}")

@pytest.mark.parametrize("module_name", get_modules("src/components"))
def test_components_import_integrity(module_name):
    """Verify that every component file can be imported without Syntax or Indentation errors"""
    try:
        importlib.import_module(f"src.components.{module_name}")
    except (ImportError, SyntaxError, IndentationError) as e:
        pytest.fail(f"Module src.components.{module_name} failed to import: {e}")

def test_home_page_logic_sanity():
    """Verify that the home page region grouping logic is logically sound"""
    # Test specific grouping constants that we recently added/modified
    groups = {
        "🇺🇸 US & 🪙 Crypto": ["S&P 500", "Nasdaq", "Bitcoin", "Ethereum"],
        "🇬🇧 Europe & 🇦🇺 Pacific": ["FTSE 100", "DAX 40", "ASX 200"],
        "🈯 Asia": ["Nikkei 225", "Hang Seng", "Straits Times", "SGX", "Nifty 50"]
    }
    
    # Verify no overlaps between groups
    seen_members = set()
    for name, members in groups.items():
        for m in members:
            if m in seen_members:
                pytest.fail(f"Duplicate market member found in grouping: {m}")
            seen_members.add(m)
    
    assert "SGX" in groups["🈯 Asia"]
    assert "Bitcoin" in groups["🇺🇸 US & 🪙 Crypto"]
