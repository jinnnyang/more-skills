import os
import re
import glob

def get_sort_key(filepath):
    # Extract the first sequence of digits from the filename
    basename = os.path.basename(filepath)
    match = re.search(r'(\d+)', basename)
    if match:
        return int(match.group(1))
    return 999999

def main():
    drafts_dir = "drafts"
    output_file = "report.md"
    
    if not os.path.exists(drafts_dir):
        print(f"Directory '{drafts_dir}' not found. No chapters to merge.")
        return

    # Gather all markdown files
    draft_files = glob.glob(os.path.join(drafts_dir, "*.md"))
    if not draft_files:
        print(f"No markdown files found in '{drafts_dir}'.")
        return

    # Sort files numerically based on numbers in the filename
    # e.g. chapter_1.md, chapter_2.md, chapter_10.md
    draft_files.sort(key=get_sort_key)
    
    print(f"Found {len(draft_files)} chapters. Merging in order:")
    for f in draft_files:
        print(f" - {os.path.basename(f)}")

    try:
        with open(output_file, "w", encoding="utf-8") as outfile:
            for filepath in draft_files:
                with open(filepath, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n")
        print(f"Successfully merged all chapters into '{output_file}'.")
    except Exception as e:
        print(f"Error during merge: {e}")

if __name__ == "__main__":
    main()
