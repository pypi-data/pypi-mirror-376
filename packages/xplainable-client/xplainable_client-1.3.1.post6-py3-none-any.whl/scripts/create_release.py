#!/usr/bin/env python3
"""
Release creation script for xplainable-client.

This script helps automate the process of creating a new release:
1. Validates the current state
2. Updates version numbers
3. Creates git tags
4. Pushes changes
5. Creates GitHub release
6. Triggers MCP server sync

Usage:
    python scripts/create_release.py --version 1.2.3 --type minor
    python scripts/create_release.py --auto-increment patch
"""

import os
import sys
import json
import subprocess
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

def run_command(cmd: list, capture: bool = True, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    print(f"🔄 Running: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True
    )
    
    if not capture:
        return result.returncode, "", ""
    
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def get_current_version() -> Optional[str]:
    """Get the current version from pyproject.toml or setup.py."""
    # Try pyproject.toml first
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
    
    # Try setup.py
    setup_py = Path("setup.py")
    if setup_py.exists():
        content = setup_py.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    
    # Try __init__.py
    try:
        import xplainable_client
        if hasattr(xplainable_client, '__version__'):
            return xplainable_client.__version__
    except ImportError:
        pass
    
    return None

def increment_version(current: str, increment_type: str) -> str:
    """Increment version based on semantic versioning."""
    # Remove 'v' prefix if present
    version = current.lstrip('v')
    
    # Parse version
    parts = version.split('.')
    if len(parts) < 3:
        parts.extend(['0'] * (3 - len(parts)))
    
    major, minor, patch = map(int, parts[:3])
    
    if increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    elif increment_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Unknown increment type: {increment_type}")
    
    return f"{major}.{minor}.{patch}"

def update_version_file(new_version: str) -> bool:
    """Update version in project files."""
    updated = False
    
    # Update pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        content = pyproject.read_text()
        new_content = re.sub(
            r'^version\s*=\s*["\'][^"\']+["\']',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        if new_content != content:
            pyproject.write_text(new_content)
            print(f"✅ Updated version in pyproject.toml")
            updated = True
    
    # Update setup.py
    setup_py = Path("setup.py")
    if setup_py.exists():
        content = setup_py.read_text()
        new_content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version="{new_version}"',
            content
        )
        if new_content != content:
            setup_py.write_text(new_content)
            print(f"✅ Updated version in setup.py")
            updated = True
    
    # Update __init__.py
    init_file = Path("xplainable_client/__init__.py")
    if init_file.exists():
        content = init_file.read_text()
        new_content = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content
        )
        if new_content != content:
            init_file.write_text(new_content)
            print(f"✅ Updated version in __init__.py")
            updated = True
    
    return updated

def validate_git_state() -> bool:
    """Validate that git repository is in a good state for release."""
    # Check if we're in a git repository
    code, _, _ = run_command(["git", "rev-parse", "--git-dir"])
    if code != 0:
        print("❌ Not in a git repository")
        return False
    
    # Check for uncommitted changes
    code, output, _ = run_command(["git", "status", "--porcelain"])
    if output.strip():
        print("❌ Uncommitted changes detected:")
        print(output)
        return False
    
    # Check current branch
    code, branch, _ = run_command(["git", "branch", "--show-current"])
    if branch not in ["main", "master"]:
        print(f"⚠️  Currently on branch '{branch}', recommend releasing from 'main' or 'master'")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    print("✅ Git repository is clean and ready")
    return True

def validate_mcp_tools() -> int:
    """Check how many MCP tools are decorated and ready for sync."""
    try:
        from xplainable_client.client.utils.mcp_markers import get_mcp_registry
        registry = get_mcp_registry()
        count = len(registry)
        print(f"✅ Found {count} MCP-decorated tools ready for sync")
        return count
    except ImportError:
        print("⚠️  Could not import MCP markers (tools may not sync)")
        return 0
    except Exception as e:
        print(f"⚠️  Error checking MCP tools: {e}")
        return 0

def create_changelog_entry(version: str) -> str:
    """Generate a changelog entry template."""
    return f"""## v{version} - {datetime.now().strftime('%Y-%m-%d')}

### Added
- 

### Changed
- 

### Fixed
- 

### MCP Tools
- {validate_mcp_tools()} tools available for MCP server sync

"""

def create_github_release(version: str, tag: str, changelog: str) -> bool:
    """Create GitHub release using gh CLI."""
    # Check if gh CLI is available
    code, _, _ = run_command(["gh", "--version"])
    if code != 0:
        print("⚠️  GitHub CLI not found, skipping release creation")
        print("   Install with: brew install gh")
        return False
    
    # Check if authenticated
    code, _, _ = run_command(["gh", "auth", "status"])
    if code != 0:
        print("⚠️  Not authenticated with GitHub CLI")
        print("   Run: gh auth login")
        return False
    
    # Create release
    release_notes = f"""# Release v{version}

{changelog}

## 🤖 Automated MCP Server Sync

This release will automatically trigger the MCP server sync workflow, creating a pull request to update MCP tools.

## 📦 Installation

```bash
pip install xplainable-client=={version}
```

---

*This release was created using the automated release script.*
"""
    
    cmd = [
        "gh", "release", "create", tag,
        "--title", f"v{version}",
        "--notes", release_notes,
        "--latest"
    ]
    
    code, output, error = run_command(cmd)
    if code == 0:
        print(f"✅ GitHub release created: {output}")
        return True
    else:
        print(f"❌ Failed to create GitHub release: {error}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Create a new release for xplainable-client")
    
    version_group = parser.add_mutually_exclusive_group(required=True)
    version_group.add_argument("--version", help="Specific version (e.g., 1.2.3)")
    version_group.add_argument("--auto-increment", choices=["major", "minor", "patch"], 
                              help="Auto-increment version")
    
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--publish", action="store_true", help="Publish to PyPI after building")
    parser.add_argument("--changelog", help="Custom changelog text")
    
    args = parser.parse_args()
    
    print("🚀 xplainable-client Release Script")
    print("=" * 50)
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    # Load .env from project root if available, so TWINE_* and others are picked up
    if load_dotenv is not None:
        env_loaded = load_dotenv(dotenv_path=project_root / ".env") or load_dotenv()
        if env_loaded:
            print("🔐 Loaded environment from .env")
    
    # Validate git state
    if not validate_git_state():
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    if not current_version:
        print("❌ Could not determine current version")
        sys.exit(1)
    print(f"📋 Current version: {current_version}")
    
    # Determine new version
    if args.version:
        new_version = args.version.lstrip('v')
    else:
        new_version = increment_version(current_version, args.auto_increment)
    
    tag = f"v{new_version}"
    print(f"🎯 Target version: {new_version} (tag: {tag})")
    
    # Validate MCP tools
    mcp_count = validate_mcp_tools()
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Would perform these actions:")
        print(f"   1. Update version to {new_version}")
        print(f"   2. Commit version changes")
        print(f"   3. Create git tag {tag}")
        print(f"   4. Push changes and tag")
        print(f"   5. Create GitHub release")
        print(f"   6. Trigger MCP server sync ({mcp_count} tools)")
        return
    
    # Confirm
    print(f"\n📋 Release Summary:")
    print(f"   Current: {current_version}")
    print(f"   New: {new_version}")
    print(f"   MCP Tools: {mcp_count}")
    print(f"   Tag: {tag}")
    
    if not args.dry_run:
        response = input(f"\nCreate release v{new_version}? (y/N): ")
        if response.lower() != 'y':
            print("❌ Release cancelled")
            sys.exit(1)
    
    # Run tests (unless skipped)
    if not args.skip_tests:
        print("\n🧪 Running tests...")
        code, output, error = run_command(["python", "-m", "pytest", "tests/"], capture=False)
        if code != 0:
            print("❌ Tests failed, release cancelled")
            sys.exit(1)
        print("✅ Tests passed")
    
    # Clean build artifacts
    print("\n🧹 Cleaning build artifacts...")
    import shutil
    for artifact_dir in ["build", "dist"]:
        if Path(artifact_dir).exists():
            shutil.rmtree(artifact_dir)
            print(f"   Removed {artifact_dir}/")
    
    # Remove egg-info directories
    for egg_info in Path(".").glob("*.egg-info"):
        if egg_info.exists():
            shutil.rmtree(egg_info)
            print(f"   Removed {egg_info}")
    
    # Update version
    print(f"\n📝 Updating version to {new_version}...")
    if not update_version_file(new_version):
        print("❌ Failed to update version files")
        sys.exit(1)
    
    # Commit version changes
    print("💾 Committing version changes...")
    code, _, _ = run_command(["git", "add", "."])
    code, _, _ = run_command(["git", "commit", "-m", f"chore: bump version to {new_version}"])
    
    # Create tag
    print(f"🏷️  Creating tag {tag}...")
    changelog = args.changelog or create_changelog_entry(new_version)
    code, _, _ = run_command(["git", "tag", "-a", tag, "-m", f"Release {tag}\n\n{changelog}"])
    
    # Build package
    print("📦 Building package...")
    code, output, error = run_command(["python", "-m", "build"])
    if code != 0:
        print(f"❌ Package build failed: {error}")
        sys.exit(1)
    print("✅ Package built successfully")

    # Push changes
    print("⬆️  Pushing changes...")
    code, _, _ = run_command(["git", "push"])
    code, _, _ = run_command(["git", "push", "--tags"])
    
    # Publish to PyPI if requested
    if args.publish:
        print("📦 Publishing to PyPI...")
        
        # Check for twine
        code, _, _ = run_command(["twine", "--version"])
        if code != 0:
            print("❌ twine not found")
            print("   Install with: pip install twine")
            sys.exit(1)
        
        # Check for credentials
        if not os.getenv('TWINE_PASSWORD') and not Path.home().joinpath('.pypirc').exists():
            print("❌ PyPI credentials not configured")
            print("Set up credentials with one of:")
            print("  1. Environment: export TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-...")
            print("  2. Config file: ~/.pypirc")
            print("  3. Add to .env: TWINE_USERNAME=__token__ and TWINE_PASSWORD=pypi-...")
            sys.exit(1)
        
        # Upload to PyPI
        code, output, error = run_command(["twine", "upload", "dist/*"])
        if code == 0:
            print("✅ Package published to PyPI!")
            print(f"🔗 View at: https://pypi.org/project/xplainable-client/{new_version}/")
        else:
            # Twine sometimes prints errors to stdout rather than stderr
            if error:
                print(f"❌ PyPI publish failed: {error}")
            if output:
                print(output)
            sys.exit(1)
    
    # Create GitHub release
    print("🎉 Creating GitHub release...")
    if create_github_release(new_version, tag, changelog):
        print(f"✅ Release v{new_version} created successfully!")
        print(f"🤖 MCP server sync will be triggered automatically")
    else:
        print("⚠️  GitHub release creation failed, but tag was pushed")
    
    print("\n" + "=" * 50)
    print("🎉 RELEASE COMPLETE!")
    print("=" * 50)
    print(f"📦 Version: {new_version}")
    print(f"🏷️  Tag: {tag}")
    print(f"🔗 Check: https://github.com/jtuppack/xplainable-client/releases")
    print(f"🤖 MCP Sync: Will create PR in MCP server repo")

if __name__ == "__main__":
    main()