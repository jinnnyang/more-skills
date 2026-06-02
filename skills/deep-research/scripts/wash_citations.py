import os
import re
import glob

def main():
    findings_dir = "findings"
    if not os.path.exists(findings_dir):
        print(f"Directory {findings_dir} not found. Ensure you are running this from the project root.")
        return

    # Regex to match citation lines (e.g., [1] Title | https://... | Type | Date)
    line_pattern = re.compile(r'^\[\d+\]\s*(.*)$')
    url_pattern = re.compile(r'(https?://[^\s|]+)')

    unique_urls = {}
    ordered_citations = []
    global_index = 1

    md_files = glob.glob(os.path.join(findings_dir, "task-*.md"))
    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                in_sources = False
                for line in f:
                    line = line.strip()
                    if line.startswith("## Sources"):
                        in_sources = True
                        continue
                    if line.startswith("## ") and in_sources:
                        in_sources = False
                        break
                    
                    if in_sources and line.startswith("["):
                        match = line_pattern.match(line)
                        if match:
                            content = match.group(1)
                            url_match = url_pattern.search(content)
                            if url_match:
                                url = url_match.group(1)
                                if url not in unique_urls:
                                    unique_urls[url] = global_index
                                    ordered_citations.append(f"[{global_index}] {content}")
                                    global_index += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    os.makedirs("kanban", exist_ok=True)
    out_path = os.path.join("kanban", "citations_washed.md")
    try:
        with open(out_path, 'w', encoding='utf-8') as out_f:
            out_f.write("### Global Validated Citations (Citations)\n")
            for c in ordered_citations:
                out_f.write(c + "\n")
        print(f"Successfully washed {len(ordered_citations)} unique citations. Output saved to {out_path}.")
    except Exception as e:
        print(f"Error writing to {out_path}: {e}")

if __name__ == "__main__":
    main()
