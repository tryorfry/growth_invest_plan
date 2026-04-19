import os
import re
import pytest

# Paths to critical files
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOME_PAGE = os.path.join(BASE_DIR, 'src/views/home.py')
SIDEBAR = os.path.join(BASE_DIR, 'src/views/sidebar.py')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@pytest.mark.parametrize("landmark", [
    "🌍 Global Market Snapshot",
    "🛠️ Chart Strategy & Indicators",
    "Show EMAs (20, 50, 200)",
    "Show High Volume Nodes (HVN)",
    "MacroSource.fetch_global_snapshot()",
    "cached_analyze_stock",
    "render_news_catalysts"
])
def test_home_page_landmarks(landmark):
    """Ensure essential UI components exist in home.py"""
    content = read_file(HOME_PAGE)
    assert landmark in content, f"CRITICAL UI LANDMARK MISSING: '{landmark}' not found in home.py"

@pytest.mark.parametrize("landmark", [
    "🔍 Analyze",
    "on_analyze_click",
    "analysis_started"
])
def test_sidebar_landmarks(landmark):
    """Ensure essential UI components exist in sidebar.py"""
    content = read_file(SIDEBAR)
    assert landmark in content, f"CRITICAL UI LANDMARK MISSING: '{landmark}' not found in sidebar.py"

def test_no_duplicated_snapshots():
    """Ensure we don't have duplicated Global Market Snapshot expanders"""
    content = read_file(HOME_PAGE)
    matches = re.findall(r'st\.expander\("🌍 Global Market Snapshot"', content)
    assert len(matches) == 1, f"UI DUPLICATION ERROR: Found {len(matches)} Global Market Snapshot expanders"

if __name__ == "__main__":
    # Allow running directly for quick feedback
    try:
        test_home_page_landmarks("🌍 Global Market Snapshot")
        test_home_page_landmarks("🛠️ Chart Strategy & Indicators")
        test_no_duplicated_snapshots()
        print("✅ UI Landmarks Verification: PASSED")
    except AssertionError as e:
        print(f"❌ UI Landmarks Verification: FAILED - {e}")
