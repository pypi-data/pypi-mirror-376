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


def install_parser(parser_path: str = ".") -> bool:
    """
    Install everything for a UnrealOn parser.
    
    Args:
        parser_path: Path to parser directory
    
    Returns:
        True if success, False if failed
    """
    parser_dir = Path(parser_path).resolve()
    parser_name = parser_dir.name  # Auto-detect from directory name
    
    print(f"🚀 Installing {parser_name}")
    print("=" * 40)
    
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
    
    # 3. Check if basic tools are available (optional)
    _check_tools_availability()
    
    # 4. Create batch files (Windows only)
    if platform.system() == "Windows":
        _create_batch_files(parser_name)
    
    print(f"\n✅ {parser_name} setup completed!")
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install browsers: playwright install chromium")
    print("3. Run parser: python main.py 5 2")
    if platform.system() == "Windows":
        print("   Or use: START.bat (includes setup menu)")
    
    return True


def _check_tools_availability():
    """Check if basic tools are available (non-blocking)."""
    print("🔍 Checking available tools...")
    
    # Check pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                     check=True, capture_output=True)
        print("✅ pip available")
    except:
        print("⚠️  pip not available")
    
    # Check if requirements.txt exists
    if Path("requirements.txt").exists():
        print("✅ requirements.txt found")
        print("💡 To install dependencies: pip install -r requirements.txt")
    else:
        print("⚠️  requirements.txt not found")
    
    # Check playwright
    try:
        subprocess.run([sys.executable, "-c", "import playwright"], 
                     check=True, capture_output=True)
        print("✅ playwright available")
    except:
        print("⚠️  playwright not available")
        print("💡 To install: pip install playwright && playwright install chromium")


def _create_batch_files(parser_name: str):
    """Create Windows batch files using Jinja2 templates."""
    print("🪟 Creating Windows batch files...")
    
    # Simple default config - no file reading needed
    config = {
        'browsers_needed': ['chromium'],
        'supports_persistent': True  # Assume all parsers support persistent mode
    }
    
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


