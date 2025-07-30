#!/usr/bin/env python3
"""
Final Deployment Verification Script
Performs a comprehensive check to ensure the deployment package is ready
"""

import os
import sys
import hashlib
from datetime import datetime

def calculate_checksum(file_path):
    """Calculate MD5 checksum of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def verify_deployment_package():
    """Verify the deployment package is complete and ready"""
    print("🚀 FINAL DEPLOYMENT VERIFICATION")
    print("=" * 50)
    print(f"Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check required files
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
        'start.sh',
        'VERSION'
    ]
    
    print("📁 Checking required files...")
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            checksum = calculate_checksum(file)
            print(f"  ✅ {file} - {checksum[:8]}...")
        else:
            print(f"  ❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    # Check required directories
    required_dirs = ['core', 'templates']
    print("\n📂 Checking required directories...")
    missing_dirs = []
    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            # Count files in directory
            file_count = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
            print(f"  ✅ {directory}/ ({file_count} files)")
        else:
            print(f"  ❌ {directory}/ - MISSING")
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"\n❌ Missing directories: {', '.join(missing_dirs)}")
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
    
    print("\n🔧 Checking core modules...")
    missing_modules = []
    for module in core_modules:
        module_path = os.path.join('core', module)
        if os.path.exists(module_path):
            checksum = calculate_checksum(module_path)
            print(f"  ✅ {module} - {checksum[:8]}...")
        else:
            print(f"  ❌ {module} - MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing core modules: {', '.join(missing_modules)}")
        return False
    
    # Check templates
    template_files = ['dashboard.html']
    print("\n🎨 Checking templates...")
    missing_templates = []
    for template in template_files:
        template_path = os.path.join('templates', template)
        if os.path.exists(template_path):
            checksum = calculate_checksum(template_path)
            print(f"  ✅ {template} - {checksum[:8]}...")
        else:
            print(f"  ❌ {template} - MISSING")
            missing_templates.append(template)
    
    if missing_templates:
        print(f"\n❌ Missing templates: {', '.join(missing_templates)}")
        return False
    
    # Check deployment scripts are executable
    executable_scripts = ['setup.sh', 'start.sh']
    print("\n⚙️  Checking executable scripts...")
    for script in executable_scripts:
        if os.path.exists(script):
            # Check if file is executable
            if os.access(script, os.X_OK):
                print(f"  ✅ {script} - executable")
            else:
                print(f"  ⚠️  {script} - not executable (chmod +x recommended)")
        else:
            print(f"  ❌ {script} - MISSING")
    
    # Check version file
    print("\n🔖 Checking version info...")
    if os.path.exists('VERSION'):
        with open('VERSION', 'r') as f:
            version_info = f.read().strip()
        print(f"  ✅ VERSION file present")
        print(f"  📄 {version_info.split(chr(10))[0]}")
    else:
        print(f"  ❌ VERSION file missing")
        return False
    
    # Check deployment readme
    print("\n📚 Checking documentation...")
    if os.path.exists('DEPLOYMENT_README.md'):
        print(f"  ✅ DEPLOYMENT_README.md present")
    else:
        print(f"  ❌ DEPLOYMENT_README.md missing")
        return False
    
    if os.path.exists('README.md'):
        print(f"  ✅ README.md present")
    else:
        print(f"  ❌ README.md missing")
        return False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 50)
    print("✅ All required files present")
    print("✅ All core modules present")
    print("✅ All templates present")
    print("✅ Documentation present")
    print("✅ Version information present")
    print()
    print("🎉 DEPLOYMENT PACKAGE IS READY!")
    print()
    print("Next steps:")
    print("1. Customize .env and secrets.py with your credentials")
    print("2. Run setup.sh to install dependencies")
    print("3. Run start.sh to start the bot")
    print("4. For cloud deployment, follow DEPLOYMENT_README.md")
    
    return True

def main():
    """Main function"""
    try:
        success = verify_deployment_package()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
