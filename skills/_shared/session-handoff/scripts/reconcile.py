#!/usr/bin/env python3
import os
import sys
import re
import argparse
import subprocess
import json
from datetime import datetime, timezone

# Global Templates Path relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, '..', 'templates')
DEFAULT_DOCS = ['context.md', 'task.md', 'walkthrough.md', 'open-questions.md']

def parse_frontmatter(content):
    """
    Parses YAML frontmatter and body.
    Returns (metadata dict, body string).
    """
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            yaml_str = parts[1]
            body = parts[2]
            metadata = {}
            for line in yaml_str.splitlines():
                if not line.strip() or line.strip().startswith('#'):
                    continue
                if ':' in line:
                    k, v = line.split(':', 1)
                    metadata[k.strip()] = v.strip()
            return metadata, body
    return {}, content

def serialize_frontmatter(metadata, body):
    """
    Serializes metadata dict and body back to YAML frontmatter + markdown.
    """
    yaml_lines = ["---"]
    for k, v in metadata.items():
        yaml_lines.append(f"{k}: {v}")
    yaml_lines.append("---")
    # Ensure there's a newline between frontmatter and body if body doesn't start with one
    if body and not body.startswith('\n'):
        body = '\n' + body
    return "\n".join(yaml_lines) + body

def write_atomic(filepath, content):
    """
    Writes content to filepath atomically using a .tmp file and os.replace.
    """
    dirpath = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    tmp_file = filepath + ".tmp"
    with open(tmp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp_file, filepath)

def get_git_status():
    """
    Runs git status and returns uncommitted files.
    """
    try:
        res = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, check=True)
        files = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if line:
                parts = line.split(None, 1)
                if len(parts) == 2:
                    files.append((parts[0], parts[1]))  # (status, path)
        return files
    except subprocess.CalledProcessError:
        return None

def get_git_log(n=5):
    """
    Runs git log and returns the last N commit messages.
    """
    try:
        res = subprocess.run(['git', 'log', f'-{n}', '--oneline'], capture_output=True, text=True, check=True)
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return None

def cmd_init(args):
    """
    Initializes .hermes/handoff/ directory with default files.
    """
    target_dir = args.target_dir
    os.makedirs(target_dir, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    agent = args.agent or "unknown-agent"
    session_id = args.session_id or "unknown-session"
    writer = args.writer or "migration"

    initialized = []
    skipped = []

    for doc in DEFAULT_DOCS:
        target_path = os.path.join(target_dir, doc)
        if os.path.exists(target_path):
            skipped.append(doc)
            continue
        
        template_path = os.path.join(TEMPLATES_DIR, doc)
        if not os.path.exists(template_path):
            print(f"Error: Template {template_path} not found.", file=sys.stderr)
            sys.exit(1)
            
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substitute templates placeholders
        content = content.replace('{{TIMESTAMP}}', timestamp)
        content = content.replace('{{AGENT}}', agent)
        content = content.replace('{{WRITER}}', writer)
        content = content.replace('{{SESSION_ID}}', session_id)
        
        write_atomic(target_path, content)
        initialized.append(doc)

    print(json.dumps({
        "status": "success",
        "initialized": initialized,
        "skipped": skipped
    }, indent=2))

def cmd_check_reality(args):
    """
    Checks for conflicts between handoff docs and the git/filesystem reality.
    """
    target_dir = args.target_dir
    if not os.path.exists(target_dir):
        print(json.dumps({
            "status": "error",
            "message": f"Handoff directory {target_dir} does not exist. Run init first."
        }))
        sys.exit(1)

    hard_conflicts = []
    soft_conflicts = []

    # 1. Check Git Status (uncommitted files)
    git_status = get_git_status()
    uncommitted_paths = set()
    if git_status is not None:
        uncommitted_paths = {path for _, path in git_status}

    # 2. Check last_verified timestamp
    # Look for context.md to check verification staleness
    context_path = os.path.join(target_dir, 'context.md')
    if os.path.exists(context_path):
        with open(context_path, 'r', encoding='utf-8') as f:
            meta, _ = parse_frontmatter(f.read())
        last_verified = meta.get('last_verified')
        if last_verified and last_verified != 'SKIPPED':
            try:
                dt_verified = datetime.fromisoformat(last_verified)
                dt_now = datetime.now(timezone.utc)
                delta_days = (dt_now - dt_verified).days
                if delta_days > 7:
                    soft_conflicts.append({
                        "type": "stale_verification",
                        "message": f"last_verified is {delta_days} days old (older than 7 days threshold)."
                    })
            except Exception as e:
                soft_conflicts.append({
                    "type": "invalid_timestamp",
                    "message": f"Failed to parse last_verified: {last_verified}. Error: {e}"
                })

    # 3. Check Task File Existence & Claims
    task_path = os.path.join(target_dir, 'task.md')
    if os.path.exists(task_path):
        with open(task_path, 'r', encoding='utf-8') as f:
            _, body = parse_frontmatter(f.read())
        
        # Regex search for files mentioned in task.md to check sanity existence
        # Matches absolute paths starting with / preceded by file://, whitespace, quotes, backticks, or parens
        file_patterns = re.findall(r'(?:file://|[`"\'\(\s])(/[^\s`"\'\(\)]+)', body)
        for path in file_patterns:
            # Strip hash references if any (e.g. file.md#L10)
            clean_path = path.split('#')[0].strip('`"\'()[]')
            if clean_path and clean_path.startswith('/'):
                if not os.path.exists(clean_path):
                    # Hard conflict: task mentions a file that does not exist
                    hard_conflicts.append({
                        "type": "missing_file_in_task",
                        "message": f"File referenced in task.md does not exist on filesystem: {clean_path}"
                    })

    # 4. Check Walkthrough File Claims
    walkthrough_path = os.path.join(target_dir, 'walkthrough.md')
    if os.path.exists(walkthrough_path):
        with open(walkthrough_path, 'r', encoding='utf-8') as f:
            _, body = parse_frontmatter(f.read())
            
        # Parse the <session-tools-log> section to verify git match
        tools_log_match = re.search(r'<session-tools-log>(.*?)</session-tools-log>', body, re.DOTALL)
        if tools_log_match:
            try:
                tools_log = json.loads(tools_log_match.group(1).strip() or "[]")
                # Look for file write / replacement tool calls and check if git uncommitted or git log has evidence
                # If tool says we wrote a file, but git status shows it's untracked or modified, or git log has it in recent commits, it's fine.
                # Otherwise, it's a conflict
                for call in tools_log:
                    # Let's say a write_to_file or replace_file_content was executed on target
                    tool_name = call.get('tool')
                    target_file = call.get('target')
                    if tool_name in ['write_to_file', 'replace_file_content', 'multi_replace_file_content'] and target_file:
                        # Check git presence
                        rel_path = os.path.relpath(target_file, start=os.getcwd())
                        # If not uncommitted and not recently committed, throw soft conflict
                        # (could have been committed and pushed, or git is not present)
                        if git_status is not None and rel_path not in uncommitted_paths:
                            # Check git log for recent commit with this file
                            try:
                                res = subprocess.run(['git', 'log', '-5', '--name-only', '--oneline'], capture_output=True, text=True)
                                if rel_path not in res.stdout:
                                    soft_conflicts.append({
                                        "type": "tool_call_no_git_evidence",
                                        "message": f"Walkthrough logs call to modify {rel_path}, but it is not in git status or recent 5 commits."
                                    })
                            except Exception:
                                pass
            except Exception as e:
                soft_conflicts.append({
                    "type": "invalid_tools_log",
                    "message": f"Failed to parse <session-tools-log> in walkthrough.md: {e}"
                })

    print(json.dumps({
        "status": "success",
        "hard_conflicts": hard_conflicts,
        "soft_conflicts": soft_conflicts
    }, indent=2))

def cmd_clean_up(args):
    """
    Cleans up resolved entries in walkthrough.md, open-questions.md, and review.md.
    """
    target_dir = args.target_dir
    if not os.path.exists(target_dir):
        print(json.dumps({"status": "error", "message": f"Handoff directory {target_dir} not found."}))
        sys.exit(1)

    removed_clear = []
    removed_stale = []
    unsure_items = []

    # 1. Clean Open Questions
    oq_path = os.path.join(target_dir, 'open-questions.md')
    if os.path.exists(oq_path):
        with open(oq_path, 'r', encoding='utf-8') as f:
            oq_meta, oq_body = parse_frontmatter(f.read())
        
        # Split body by markdown headers (like ## Question)
        sections = re.split(r'^(##\s+.*)$', oq_body, flags=re.MULTILINE)
        
        header = sections[0]
        new_sections = []
        
        # Parse sections: sections is [header, "## Q1", "body Q1", "## Q2", "body Q2"]
        i = 1
        while i < len(sections):
            sec_header = sections[i]
            sec_body = sections[i+1] if i+1 < len(sections) else ""
            i += 2
            
            # Skip special sections like ## Soft Conflicts
            if "Soft Conflicts" in sec_header:
                new_sections.append(sec_header + sec_body)
                continue
                
            # Check if resolved: contains "Status: resolved", strikethrough, or similar evidence
            if "resolved" in sec_body.lower() or "~~" in sec_header or "~~" in sec_body:
                removed_clear.append(sec_header.strip('# \r\n'))
            else:
                new_sections.append(sec_header + sec_body)
        
        new_body = header + "".join(new_sections)
        oq_meta['last_updated'] = datetime.now(timezone.utc).isoformat()
        write_atomic(oq_path, serialize_frontmatter(oq_meta, new_body))

    # 2. Clean Walkthrough (Active entries pruning)
    wt_path = os.path.join(target_dir, 'walkthrough.md')
    if os.path.exists(wt_path):
        with open(wt_path, 'r', encoding='utf-8') as f:
            wt_meta, wt_body = parse_frontmatter(f.read())

        # Extract <!-- entries --> block or parse by dated entries
        # For simplicity, look for dated headers e.g. "## YYYY-MM-DD — Title"
        wt_sections = re.split(r'^(##\s+\d{4}-\d{2}-\d{2}\s+.*)$', wt_body, flags=re.MULTILINE)
        
        wt_header = wt_sections[0]
        new_wt_sections = []
        
        i = 1
        while i < len(wt_sections):
            sec_header = wt_sections[i]
            sec_body = wt_sections[i+1] if i+1 < len(wt_sections) else ""
            i += 2
            
            # Extract date from header (## YYYY-MM-DD — Title)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', sec_header)
            is_stale = False
            if date_match:
                try:
                    entry_date = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                    delta_days = (datetime.now(timezone.utc).date() - entry_date).days
                    if delta_days > 30:
                        # Stale candidate!
                        # Check if referenced in task.md or context.md (simple text grep in context/task)
                        # We search target files for the title or date
                        title_clean = sec_header.strip('# \r\n')
                        in_use = False
                        for doc in ['context.md', 'task.md']:
                            doc_path = os.path.join(target_dir, doc)
                            if os.path.exists(doc_path):
                                with open(doc_path, 'r', encoding='utf-8') as f:
                                    doc_content = f.read()
                                if date_match.group(1) in doc_content or title_clean in doc_content:
                                    in_use = True
                                    break
                        if not in_use:
                            is_stale = True
                except Exception:
                    pass
            
            # Check CLEAR criteria
            is_clear = False
            # Check if body contains status: resolved or strikethrough markdown
            if "status: resolved" in sec_body.lower() or "~~" in sec_header or "~~" in sec_body:
                is_clear = True
            
            # Determine Action based on Priority: KEEP > CLEAR > STALE > UNSURE
            # If the header has "lesson", "surprise", "decision", or "keep", KEEP it
            is_keep = bool(re.search(r'\b(lesson|surprise|decision|keep)\b', sec_header, re.IGNORECASE))
            
            if is_keep:
                new_wt_sections.append(sec_header + sec_body)
            elif is_clear:
                removed_clear.append(sec_header.strip('# \r\n'))
            elif is_stale:
                removed_stale.append(sec_header.strip('# \r\n'))
            else:
                # Defaults to unsure
                unsure_items.append({
                    "header": sec_header.strip('# \r\n'),
                    "snippet": sec_body[:100].strip() + "..."
                })
                new_wt_sections.append(sec_header + sec_body)
                
        new_wt_body = wt_header + "".join(new_wt_sections)
        wt_meta['last_updated'] = datetime.now(timezone.utc).isoformat()
        write_atomic(wt_path, serialize_frontmatter(wt_meta, new_wt_body))

    print(json.dumps({
        "status": "success",
        "removed_clear": removed_clear,
        "removed_stale": removed_stale,
        "unsure_items": unsure_items
    }, indent=2))

def cmd_write_atomic(args):
    """
    Atomic write wrapper.
    """
    if not args.filepath or not args.content:
        print(json.dumps({"status": "error", "message": "Missing filepath or content."}))
        sys.exit(1)
    
    write_atomic(args.filepath, args.content)
    print(json.dumps({"status": "success", "filepath": args.filepath}))

def main():
    parser = argparse.ArgumentParser(description="Session Handoff Protocol Reconciliation & Helper Script")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    parser_init = subparsers.add_parser("init", help="Initialize handoff directory")
    parser_init.add_argument("--target-dir", default=".hermes/handoff", help="Target handoff directory")
    parser_init.add_argument("--agent", help="Last agent name")
    parser_init.add_argument("--session-id", help="Session ID")
    parser_init.add_argument("--writer", default="migration", help="Writer identity")
    parser_init.set_defaults(func=cmd_init)

    # check-reality
    parser_check = subparsers.add_parser("check-reality", help="Perform Reality Check")
    parser_check.add_argument("--target-dir", default=".hermes/handoff", help="Target handoff directory")
    parser_check.set_defaults(func=cmd_check_reality)

    # clean-up
    parser_clean = subparsers.add_parser("clean-up", help="Prune resolved entries")
    parser_clean.add_argument("--target-dir", default=".hermes/handoff", help="Target handoff directory")
    parser_clean.set_defaults(func=cmd_clean_up)

    # write-atomic
    parser_write = subparsers.add_parser("write-atomic", help="Write a file atomically")
    parser_write.add_argument("--filepath", required=True, help="Target file path")
    parser_write.add_argument("--content", required=True, help="File content string")
    parser_write.set_defaults(func=cmd_write_atomic)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
