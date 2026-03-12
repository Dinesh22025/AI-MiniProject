#!/usr/bin/env python3
"""
Unified Driver AI Co-Pilot Application Launcher
Builds frontend and starts the integrated Flask server
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, cwd=cwd, shell=shell, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_dependencies():
    """Check if all dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Node.js
    success, _ = run_command("node --version")
    if not success:
        print("❌ Node.js not found. Please install Node.js first.")
        return False
    
    # Check Python
    success, _ = run_command("python --version")
    if not success:
        print("❌ Python not found. Please install Python first.")
        return False
    
    print("✅ Dependencies check passed")
    return True

def install_dependencies():
    """Install all project dependencies"""
    print("📦 Installing dependencies...")
    
    # Install root dependencies
    print("  Installing root dependencies...")
    success, output = run_command("npm install")
    if not success:
        print(f"❌ Failed to install root dependencies: {output}")
        return False
    
    # Install frontend dependencies
    print("  Installing frontend dependencies...")
    success, output = run_command("npm install", cwd="frontend")
    if not success:
        print(f"❌ Failed to install frontend dependencies: {output}")
        return False
    
    # Install backend dependencies
    print("  Installing backend dependencies...")
    success, output = run_command("pip install -r requirements.txt", cwd="backend")
    if not success:
        print(f"❌ Failed to install backend dependencies: {output}")
        return False
    
    print("✅ All dependencies installed successfully")
    return True

def build_frontend():
    """Build the React frontend"""
    print("🏗️  Building frontend...")
    
    success, output = run_command("npm run build", cwd="frontend")
    if not success:
        print(f"❌ Frontend build failed: {output}")
        return False
    
    # Check if dist folder was created
    dist_path = Path("frontend/dist")
    if not dist_path.exists():
        print("❌ Frontend build completed but dist folder not found")
        return False
    
    print("✅ Frontend built successfully")
    return True

def start_server():
    """Start the integrated Flask server"""
    print("🚀 Starting Driver AI Co-Pilot server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🎯 Frontend and API are now unified!")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the Flask server
        subprocess.run(["python", "run.py"], cwd="backend", check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    
    return True

def main():
    """Main application launcher"""
    print("=" * 60)
    print("🚗 Driver AI Co-Pilot - Unified Application Launcher")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("frontend") or not os.path.exists("backend"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if dependencies need to be installed
    if not os.path.exists("node_modules") or not os.path.exists("frontend/node_modules"):
        if not install_dependencies():
            sys.exit(1)
    
    # Build frontend
    if not build_frontend():
        sys.exit(1)
    
    # Start the server
    if not start_server():
        sys.exit(1)
    
    print("✅ Application shutdown complete")

if __name__ == "__main__":
    main()