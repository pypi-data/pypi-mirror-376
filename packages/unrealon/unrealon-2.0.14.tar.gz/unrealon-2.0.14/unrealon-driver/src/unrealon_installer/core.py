"""
Core installer logic. Clean and simple.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any

from .platform import apply_platform_fixes, check_system_requirements
from .templates import TemplateEngine
from .browser_fixes import fix_browsers, diagnose_browsers


def install_parser(parser_name: str, parser_path: str = ".") -> bool:
    """
    Install everything for a UnrealOn parser.
    
    Args:
        parser_name: Name like "upbit_concurrent"
        parser_path: Path to parser directory
    
    Returns:
        True if success, False if failed
    """
    print(f"🚀 Installing {parser_name}")
    print("=" * 40)
    
    parser_dir = Path(parser_path).resolve()
    os.chdir(parser_dir)
    
    # 1. Apply platform fixes
    print("🔧 Applying platform fixes...")
    apply_platform_fixes()
    print("✅ Platform fixes applied")
    
    # 2. Check system
    print("🔍 Checking system...")
    requirements = check_system_requirements()
    failed = [k for k, v in requirements.items() if not v]
    if failed:
        print(f"❌ Missing: {', '.join(failed)}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # 3. Install dependencies
    if not _install_dependencies():
        return False
    
    # 4. Install browsers
    if not _install_browsers():
        return False
    
    # 5. Create batch files (Windows only)
    if platform.system() == "Windows":
        _create_batch_files(parser_name)
    
    print(f"\n✅ {parser_name} installed successfully!")
    print("Run: python main.py 5 2")
    if platform.system() == "Windows":
        print("Or:  START.bat")
    
    return True


def _install_dependencies() -> bool:
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        # Check if requirements.txt exists
        if Path("requirements.txt").exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
        else:
            # Fallback to basic packages
            subprocess.run([sys.executable, "-m", "pip", "install", "unrealon", "playwright"], 
                         check=True, capture_output=True)
        
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def _install_browsers() -> bool:
    """Install Playwright browsers with smart fixing."""
    print("🌐 Installing browsers...")
    
    # First, diagnose any issues
    issues = diagnose_browsers()
    
    # If there are issues, try to fix them
    if not all(issues.values()):
        print("🔧 Detected browser issues, applying fixes...")
        if fix_browsers(force_reinstall=False):
            print("✅ Browser issues fixed")
            return True
        else:
            print("❌ Could not fix browser issues")
            return False
    
    # If no issues, just install normally
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                     check=True, capture_output=True)
        print("✅ Browsers installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Normal install failed, trying fix: {e}")
        # Try fixing as fallback
        return fix_browsers(force_reinstall=True)


def _create_batch_files(parser_name: str):
    """Create Windows batch files using Jinja2 templates."""
    print("🪟 Creating Windows batch files...")
    
    # Detect parser config
    config = _detect_parser_config()
    
    # Create template engine
    engine = TemplateEngine()
    
    # Generate batch files
    start_content = engine.render_start_bat(parser_name, config)
    Path("START.bat").write_text(start_content, encoding="utf-8")
    
    quick_content = engine.render_quick_run_bat(parser_name, config)
    Path("QUICK_RUN.bat").write_text(quick_content, encoding="utf-8")
    
    test_content = engine.render_test_bat(parser_name, config)
    Path("TEST.bat").write_text(test_content, encoding="utf-8")
    
    print("✅ Created START.bat, QUICK_RUN.bat, TEST.bat")


def _detect_parser_config() -> Dict[str, Any]:
    """Detect parser configuration from files."""
    config = {
        'browsers_needed': ['chromium'],
        'proxy_support': False,
        'supports_persistent': False
    }
    
    # Check main.py for persistent mode support
    if Path("main.py").exists():
        main_content = Path("main.py").read_text()
        if "--persistent" in main_content:
            config['supports_persistent'] = True
    
    # Check for proxy config
    if Path("src/proxy_config.py").exists() or Path("proxy_config.py").exists():
        config['proxy_support'] = True
    
    # Check pyproject.toml for browser requirements
    if Path("pyproject.toml").exists():
        toml_content = Path("pyproject.toml").read_text()
        if "firefox" in toml_content.lower():
            config['browsers_needed'].append('firefox')
    
    return config
