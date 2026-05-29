#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
import yaml
from pathlib import Path

def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text(encoding='utf-8')
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."

    return True, "Skill is valid!"


def lint_skill_design(skill_path):
    """Return a list of design lint warning strings for a skill."""
    skill_path = Path(skill_path)
    warnings = []

    # Check SKILL.md for pre-flight / collaborative condition checking patterns
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8').lower()
        if "pre-flight check" not in content and "collaborative condition checking" not in content:
            warnings.append(
                "SKILL.md does not mention 'Pre-flight Check' or "
                "'Collaborative Condition Checking'. Consider adding a pre-flight "
                "section to validate prerequisites before execution."
            )

    # Check for learnings.md
    learnings_path = skill_path / "learnings.md"
    if not learnings_path.exists():
        warnings.append(
            "No learnings.md found. Consider creating one to capture "
            "lessons learned and common pitfalls."
        )
    else:
        try:
            size_bytes = learnings_path.stat().st_size
            content = learnings_path.read_text(encoding='utf-8')
            num_lines = len(content.splitlines())
            
            compression_prompt = (
                "Please merge duplicated errors, remove resolved environment issues, "
                "retain only active environmental traps and highly valuable success patterns. "
                "Output as a maximum of 10 concise bullet points."
            )
            
            if size_bytes > 2048:
                warnings.append(f"learnings.md is large ({size_bytes} bytes). [AGENT GUIDANCE]: {compression_prompt}")
            elif num_lines > 50:
                warnings.append(f"learnings.md has {num_lines} lines. [AGENT GUIDANCE]: {compression_prompt}")
        except OSError:
            pass

    # Check scripts for [AGENT GUIDANCE]
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists() and scripts_dir.is_dir():
        script_extensions = {".py", ".sh", ".ps1", ".js", ".ts"}
        for script_file in scripts_dir.iterdir():
            if script_file.is_file() and script_file.suffix in script_extensions:
                try:
                    script_content = script_file.read_text(errors="replace")
                    if "[AGENT GUIDANCE]" not in script_content:
                        warnings.append(
                            f"Script '{script_file.name}' does not contain "
                            f"[AGENT GUIDANCE]. Consider adding guidance output "
                            f"so the calling agent knows what to do next."
                        )
                except OSError:
                    pass

    return warnings


def check_python_interpreter():
    """Check if the Python interpreter is the Microsoft Store stub."""
    import sys
    import shutil
    from pathlib import Path

    # Check current interpreter
    executable_path = Path(sys.executable)
    if "WindowsApps" in executable_path.parts:
        return (
            f"Active Python interpreter seems to be the Microsoft Store stub: {sys.executable}\n"
            "[AGENT GUIDANCE — PYTHON STUB DETECTED]\n"
            "The Microsoft Store Python stub can cause issues, exit code 1, or open the App Store.\n"
            "Troubleshooting Steps:\n"
            "1. Install Python from python.org or via winget: `winget install Python.Python.3.11`\n"
            "2. Disable App Execution Aliases: Search Windows for 'Manage app execution aliases' and toggle off 'Python' and 'Python3'.\n"
            "3. Update your PATH environment variable to prioritize the real Python installation."
        )

    # Check python/python3 in PATH
    for cmd in ["python", "python3"]:
        which_path = shutil.which(cmd)
        if which_path and "WindowsApps" in Path(which_path).parts:
            return (
                f"Command '{cmd}' resolves to the Microsoft Store stub: {which_path}\n"
                "[AGENT GUIDANCE — PYTHON STUB DETECTED]\n"
                "The Microsoft Store Python stub in PATH can cause silent failure in subprocesses.\n"
                "Troubleshooting Steps:\n"
                "1. Install Python from python.org or via winget: `winget install Python.Python.3.11`\n"
                "2. Disable App Execution Aliases: Search Windows for 'Manage app execution aliases' and toggle off 'Python' and 'Python3'.\n"
                "3. Update your PATH environment variable to prioritize the real Python installation."
            )
    return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)

    # Check interpreter
    stub_warning = check_python_interpreter()
    if stub_warning:
        print(f"WARNING: {stub_warning}\n", file=sys.stderr)

    valid, message = validate_skill(sys.argv[1])
    print(message)

    # Run design lint (warnings only — do NOT affect exit code)
    warnings = lint_skill_design(sys.argv[1])
    if warnings:
        print()
        for w in warnings:
            print(f"WARNING: {w}")

    # Agent guidance
    guidance = (
        "[AGENT GUIDANCE]\n"
        "1. Fix any validation errors (FAIL) immediately.\n"
        "2. Review ⚠️ WARNING items — they are recommendations that improve skill reliability."
    )
    print(guidance, file=sys.stderr)

    sys.exit(0 if valid else 1)