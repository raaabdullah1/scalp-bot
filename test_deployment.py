#!/usr/bin/env python3
"""
Deployment Test Script
Tests that all required components are present and working correctly
"""

import sys
import os
import importlib

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    # Core dependencies
    try:
        import ccxt
        print("✅ ccxt")
    except ImportError as e:
        print(f"❌ ccxt: {e}")
        return False
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        import feedparser
        print("✅ feedparser")
    except ImportError as e:
        print(f"❌ feedparser: {e}")
        return False
    
    try:
        import textblob
        print("✅ textblob")
    except ImportError as e:
        print(f"❌ textblob: {e}")
        return False
    
    try:
        import flask
        print("✅ flask")
    except ImportError as e:
        print(f"❌ flask: {e}")
        return False
    
    try:
        import dotenv
        print("✅ dotenv")
    except ImportError as e:
        print(f"❌ dotenv: {e}")
        return False
    
    try:
        import pandas
        print("✅ pandas")
    except ImportError as e:
        print(f"❌ pandas: {e}")
        return False
    
    try:
        import numpy
        print("✅ numpy")
    except ImportError as e:
        print(f"❌ numpy: {e}")
        return False
    
    return True

def test_core_modules():
    """Test core module imports"""
    print("\n🔍 Testing core modules...")
    
    core_modules = [
        'core.signal_engine',
        'core.risk',
        'core.notifier',
        'core.scanner',
        'core.sentiment',
        'core.indicators',
        'core.logger',
        'core.liquidation',
        'core.dark_pool',
        'core.market_regime',
        'core.strategy_trap',
        'core.strategy_smc',
        'core.strategy_scalp'
    ]
    
    for module in core_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False
    
    return True

def test_file_structure():
    """Test that all required files are present"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        'final_bot.py',
        'requirements.txt',
        'Procfile',
        'runtime.txt',
        'secrets.py',
        '.env',
        'README.md',
        'DEPLOYMENT_README.md',
        'setup.sh',
        'start.sh'
    ]
    
    required_dirs = [
        'core',
        'templates'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} not found")
            return False
    
    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✅ {directory}/")
        else:
            print(f"❌ {directory}/ not found")
            return False
    
    # Check core modules
    core_modules = [
        'dark_pool.py',
        'indicators.py',
        'liquidation.py',
        'logger.py',
        'market_regime.py',
        'notifier.py',
        'risk.py',
        'scanner.py',
        'sentiment.py',
        'signal_engine.py',
        'strategy_scalp.py',
        'strategy_smc.py',
        'strategy_trap.py'
    ]
    
    for module in core_modules:
        module_path = os.path.join('core', module)
        if os.path.exists(module_path):
            print(f"✅ {module_path}")
        else:
            print(f"❌ {module_path} not found")
            return False
    
    # Check templates
    template_files = [
        'dashboard.html'
    ]
    
    for template in template_files:
        template_path = os.path.join('templates', template)
        if os.path.exists(template_path):
            print(f"✅ {template_path}")
        else:
            print(f"❌ {template_path} not found")
            return False
    
    return True

def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing environment configuration...")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except Exception as e:
        print(f"⚠️  Environment variables not loaded: {e}")
    
    # Check if secrets.py can be imported
    try:
        import secrets
        print("✅ secrets.py imported")
    except Exception as e:
        print(f"❌ secrets.py import failed: {e}")
        return False
    
    return True

def main():
    """Run all deployment tests"""
    print("🚀 SCALPBOT DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Environment Configuration", test_environment),
        ("Imports", test_imports),
        ("Core Modules", test_core_modules)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name}: PASS")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAIL")
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
            failed += 1
        
        print("-" * 30)
    
    print("\n" + "=" * 50)
    print(f"📊 VERIFICATION RESULTS")
    print("=" * 50)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The deployment package is ready!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check the errors above and fix them before deployment.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
