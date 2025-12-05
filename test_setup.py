#!/usr/bin/env python3
"""
Test script to verify browser agent setup
Run this before recording demo video
"""

import sys
import os

def test_imports():
    """Test that all required packages are installed"""
    print("🧪 Testing imports...")

    required = [
        ("anthropic", "Anthropic"),
        ("playwright.sync_api", "sync_playwright"),
        ("bs4", "BeautifulSoup"),
        ("rich", "print as rprint"),
    ]

    failed = []
    for module, item in required:
        try:
            exec(f"from {module} import {item}")
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            failed.append(module)

    return len(failed) == 0

def test_api_key():
    """Test that API key is set"""
    print("\n🔑 Testing API key...")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ✗ ANTHROPIC_API_KEY not set")
        print("    Run: export ANTHROPIC_API_KEY='your-key'")
        return False

    if api_key.startswith("sk-ant-"):
        print(f"  ✓ API key set (starts with sk-ant-...)")
        return True
    else:
        print(f"  ⚠️  API key set but format looks wrong")
        print(f"    Should start with 'sk-ant-'")
        return False

def test_playwright():
    """Test that Playwright browsers are installed"""
    print("\n🌐 Testing Playwright...")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to get browser executable
            browser_path = p.chromium.executable_path
            print(f"  ✓ Chromium found at: {browser_path}")
            return True
    except Exception as e:
        print(f"  ✗ Playwright browser not installed: {e}")
        print("    Run: playwright install chromium")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing file structure...")

    required_files = [
        "config.py",
        "main.py",
        "agent/supervisor.py",
        "agent/tools.py",
        "requirements.txt",
    ]

    all_exist = True
    for file in required_files:
        path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(path):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} not found")
            all_exist = False

    return all_exist

def test_config():
    """Test that config loads properly"""
    print("\n⚙️  Testing configuration...")

    try:
        # Temporarily disable API key requirement for this test
        os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

        sys.path.insert(0, os.path.dirname(__file__))
        from config import MODEL, BROWSER_WIDTH, BROWSER_HEIGHT

        print(f"  ✓ Model: {MODEL}")
        print(f"  ✓ Browser size: {BROWSER_WIDTH}x{BROWSER_HEIGHT}")
        return True
    except Exception as e:
        print(f"  ✗ Config error: {e}")
        return False

def main():
    print("="*60)
    print("  Browser Agent Setup Test")
    print("="*60)
    print()

    tests = [
        ("Imports", test_imports),
        ("API Key", test_api_key),
        ("Playwright", test_playwright),
        ("File Structure", test_file_structure),
        ("Configuration", test_config),
    ]

    results = {}
    for name, test_func in tests:
        results[name] = test_func()

    print("\n" + "="*60)
    print("  Test Results")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")

    print()
    print(f"  Result: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 All tests passed! Ready to run the agent.")
        print()
        print("To start the agent:")
        print("  python main.py")
        print()
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
