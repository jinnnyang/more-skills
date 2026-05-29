#!/usr/bin/env python3
"""
Skill Packager - Creates a distributable .skill file of a skill folder

Usage:
    python utils/package_skill.py <path/to/skill-folder> [output-directory]
    python utils/package_skill.py <path/to/skill-folder> --dry-run

Example:
    python utils/package_skill.py skills/public/my-skill
    python utils/package_skill.py skills/public/my-skill ./dist
    python utils/package_skill.py skills/public/my-skill --dry-run
"""

import argparse
import fnmatch
import sys
import zipfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quick_validate import validate_skill

# Patterns to exclude when packaging skills.
EXCLUDE_DIRS = {"__pycache__", "node_modules"}
EXCLUDE_GLOBS = {"*.pyc"}
EXCLUDE_FILES = {".DS_Store"}
# Directories excluded only at the skill root (not when nested deeper).
ROOT_EXCLUDE_DIRS = {"evals"}


def should_exclude(rel_path: Path) -> bool:
    """Check if a path should be excluded from packaging."""
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    # rel_path is relative to skill_path.parent, so parts[0] is the skill
    # folder name and parts[1] (if present) is the first subdir.
    if len(parts) > 1 and parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


def package_skill(skill_path, output_dir=None):
    """
    Package a skill folder into a .skill file.

    Args:
        skill_path: Path to the skill folder
        output_dir: Optional output directory for the .skill file (defaults to current directory)

    Returns:
        Path to the created .skill file, or None if error
    """
    skill_path = Path(skill_path).resolve()

    # Validate skill folder exists
    if not skill_path.exists():
        print(f"Error: Skill folder not found: {skill_path}")
        return None

    if not skill_path.is_dir():
        print(f"Error: Path is not a directory: {skill_path}")
        return None

    # Validate SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Error: SKILL.md not found in {skill_path}")
        return None

    # Run validation before packaging
    print("Validating skill...")
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"Validation failed: {message}")
        print("   Please fix the validation errors before packaging.")
        return None
    print(f"Valid: {message}\n")

    # Determine output location
    skill_name = skill_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    skill_filename = output_path / f"{skill_name}.skill"

    # Create the .skill file (zip format)
    try:
        with zipfile.ZipFile(skill_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the skill directory, excluding build artifacts
            for file_path in skill_path.rglob('*'):
                if not file_path.is_file():
                    continue
                arcname = file_path.relative_to(skill_path.parent)
                if should_exclude(arcname):
                    print(f"  Skipped: {arcname}")
                    continue
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")

        print(f"\nSuccessfully packaged skill to: {skill_filename}")
        return skill_filename

    except Exception as e:
        print(f"Error creating .skill file: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Package a skill folder into a distributable .skill file"
    )
    parser.add_argument(
        "skill_path",
        help="Path to the skill folder"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Optional output directory for the .skill file (defaults to current directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be included/excluded without creating the zip"
    )
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()

    print(f"Packaging skill: {args.skill_path}")
    if args.output_dir:
        print(f"   Output directory: {args.output_dir}")
    if args.dry_run:
        print("   Mode: dry-run (no zip will be created)")
    print()

    if args.dry_run:
        # Dry-run: list files without creating the zip
        if not skill_path.exists() or not skill_path.is_dir():
            print(f"Error: Skill folder not found or not a directory: {skill_path}")
            sys.exit(1)
        if not (skill_path / "SKILL.md").exists():
            print(f"Error: SKILL.md not found in {skill_path}")
            sys.exit(1)

        included = []
        excluded = []
        for file_path in skill_path.rglob("*"):
            if not file_path.is_file():
                continue
            arcname = file_path.relative_to(skill_path.parent)
            if should_exclude(arcname):
                excluded.append(str(arcname))
            else:
                included.append(str(arcname))

        print("Files that WOULD be included:")
        for f in included:
            print(f"  [INCLUDE] {f}")
        print(f"\nFiles that WOULD be excluded:")
        for f in excluded:
            print(f"  [EXCLUDE] {f}")
        print(f"\nTotal: {len(included)} included, {len(excluded)} excluded")
    else:
        result = package_skill(args.skill_path, args.output_dir)

        if result:
            guidance = (
                "[AGENT GUIDANCE]\n"
                f"1. The .skill file is ready at {result}.\n"
                "2. To install: copy to ~/.claude/commands/ or use present_files if available."
            )
            print(guidance, file=sys.stderr)
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
