import sys
import os
import importlib

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def smoke_test_ui():
    print("🛡️ Starting UI Integrity Smoke Test...")
    print("-" * 50)
    
    directories = ["src/views", "src/components"]
    failed = []
    
    for directory in directories:
        print(f"📁 Scanning {directory}...")
        for file in os.listdir(directory):
            if file.endswith(".py") and not file.startswith("__"):
                module_rel = file[:-3]
                module_path = f"{directory.replace('/', '.')}.{module_rel}"
                try:
                    importlib.import_module(module_path)
                    print(f"  ✅ {module_rel}: OK")
                except Exception as e:
                    print(f"  ❌ {module_rel}: FAILED ({type(e).__name__}: {e})")
                    failed.append((module_path, e))

    print("-" * 50)
    if failed:
        print(f"🚨 CRITICAL: {len(failed)} module(s) failed load test!")
        for mod, err in failed:
            print(f"   -> {mod}: {err}")
        sys.exit(1)
    else:
        print("🏆 SUCCESS: All UI modules are syntactically valid.")
        sys.exit(0)

if __name__ == "__main__":
    smoke_test_ui()
