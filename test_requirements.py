#!/usr/bin/env python3
"""
Test script to verify requirements.txt is valid
"""

import subprocess
import sys
import tempfile
import os

def test_requirements():
    """Test if requirements.txt can be installed"""
    print("🧪 Testing requirements.txt...")
    
    try:
        # Read requirements file
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip()
        
        print(f"📋 Requirements found:\n{requirements}")
        
        # Create a temporary virtual environment
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"🔧 Creating temporary environment in {temp_dir}")
            
            # Create virtual environment
            subprocess.run([
                sys.executable, '-m', 'venv', os.path.join(temp_dir, 'venv')
            ], check=True)
            
            # Activate virtual environment and install requirements
            if os.name == 'nt':  # Windows
                pip_path = os.path.join(temp_dir, 'venv', 'Scripts', 'pip')
            else:  # Unix/Linux
                pip_path = os.path.join(temp_dir, 'venv', 'bin', 'pip')
            
            # Install requirements
            result = subprocess.run([
                pip_path, 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Requirements installed successfully!")
                
                # List installed packages
                list_result = subprocess.run([
                    pip_path, 'list'
                ], capture_output=True, text=True)
                
                print("📦 Installed packages:")
                print(list_result.stdout)
                
            else:
                print("❌ Failed to install requirements:")
                print(result.stderr)
                return False
                
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False
    except Exception as e:
        print(f"❌ Error testing requirements: {e}")
        return False
    
    return True

def main():
    print("🔍 Testing requirements.txt validity...")
    
    if test_requirements():
        print("\n✅ All requirements are valid!")
        print("🚀 Ready for Docker builds")
    else:
        print("\n❌ Requirements test failed!")
        print("🔧 Please fix the requirements.txt file")
        sys.exit(1)

if __name__ == "__main__":
    main() 