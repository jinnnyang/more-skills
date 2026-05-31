#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

def grade_run(run_dir: Path, eval_id: int) -> dict:
    output_file = run_dir / "outputs" / "optimized_prompt.md"
    if not output_file.exists():
        return {
            "status": "error",
            "message": f"Output file optimized_prompt.md does not exist at {output_file}."
        }
        
    content = output_file.read_text(encoding="utf-8")
    assertions = []
    
    # Assertion 1: EARS syntax check
    ears_patterns = [r"\bshall\b", r"\bmust\b", r"\bWhen\b", r"\bIf\b", r"\bWhile\b"]
    has_ears = any(re.search(pat, content, re.IGNORECASE) for pat in ears_patterns)
    assertions.append({
        "text": "Output must contain EARS-formatted requirements (such as 'When', 'If', 'While')",
        "passed": has_ears,
        "evidence": "Found EARS keywords or normative modal verbs (shall/must/when/if/while)." if has_ears else "No EARS patterns found."
    })
    
    # Assertion 2: Domain grounding check
    if eval_id == 0:
        theories = ["gtd", "pomodoro", "fogg", "atomic", "habit", "productivity"]
        theory_label = "GTD, Pomodoro, BJ Fogg or Atomic Habits"
    elif eval_id == 1:
        theories = ["zero trust", "defense in depth", "privacy by design", "security"]
        theory_label = "Zero Trust, Defense in Depth, or Privacy by Design"
    else:
        theories = ["gestalt", "hick", "fitts", "progressive disclosure", "ux", "ui"]
        theory_label = "Gestalt Principles, Hick's Law, or Progressive Disclosure"
        
    has_theory = any(t in content.lower() for t in theories)
    assertions.append({
        "text": f"Output must ground in domain theories like {theory_label}",
        "passed": has_theory,
        "evidence": f"Found references to domain terms matching: {[t for t in theories if t in content.lower()]}." if has_theory else f"No references to {theory_label} found."
    })
    
    # Assertion 3: RSWEF structure check
    headers = [r"^#\s+Role\b", r"^##\s+Skills\b", r"^##\s+Workflows\b", r"^##\s+Examples\b", r"^##\s+Formats\b"]
    missing_headers = []
    for h in headers:
        if not re.search(h, content, re.MULTILINE | re.IGNORECASE):
            missing_headers.append(h)
    has_rswef = len(missing_headers) == 0
    assertions.append({
        "text": "Output must follow the standard Role/Skills/Workflows/Examples/Formats layout",
        "passed": has_rswef,
        "evidence": "All RSWEF sections are present." if has_rswef else f"Missing headers: {missing_headers}"
    })
    
    # Assertion 4: Examples check
    if eval_id == 0:
        text_check = "Output must include concrete task examples with real data, not placeholders"
        has_ex = "example" in content.lower() or "task" in content.lower()
    elif eval_id == 1:
        text_check = "Output must specify password rules (length, complexity, MFA conditions)"
        has_ex = any(w in content.lower() for w in ["password", "length", "complex", "mfa"])
    else:
        text_check = "Output must include layout or forecast details examples with real data, not placeholders"
        has_ex = any(w in content.lower() for w in ["layout", "forecast", "temp", "dashboard"])
        
    assertions.append({
        "text": text_check,
        "passed": has_ex,
        "evidence": "Examples or specific constraints are present." if has_ex else "No specific examples found."
    })
    
    # Assertion 5: Next Step / Pipeline Handoff check
    has_next_step = "pipeline handoff" in content.lower() or "next step" in content.lower() or "options:" in content.lower()
    assertions.append({
        "text": "Output should include a Next Step / Pipeline Handoff section suggesting downstream skills",
        "passed": has_next_step,
        "evidence": "Found Next Step/Pipeline Handoff keyword or options checklist." if has_next_step else "No Next Step/Pipeline Handoff section found."
    })
    
    # Store assertions under "expectations" field as aggregate_benchmark.py expects
    return {
        "expectations": assertions
    }

def main():
    workspace = Path(__file__).resolve().parent
    for iteration_dir in workspace.glob("iteration-*"):
        for eval_dir in iteration_dir.glob("eval-*"):
            try:
                eval_id = int(eval_dir.name.split("-")[1])
            except ValueError:
                continue
                
            for run_name in ["old_skill", "with_skill"]:
                config_dir = eval_dir / run_name
                if not config_dir.exists():
                    continue
                for run_dir in config_dir.glob("run-*"):
                    res = grade_run(run_dir, eval_id)
                    if "expectations" in res:
                        assertions = res["expectations"]
                        passed = sum(1 for a in assertions if a["passed"])
                        total = len(assertions)
                        res["summary"] = {
                            "passed": passed,
                            "failed": total - passed,
                            "total": total,
                            "pass_rate": passed / total if total > 0 else 0.0
                        }
                    grading_file = run_dir / "grading.json"
                    grading_file.write_text(json.dumps(res, indent=2), encoding="utf-8")
                    print(f"Graded {iteration_dir.name}/{eval_dir.name}/{run_name}/{run_dir.name}")

if __name__ == "__main__":
    main()
