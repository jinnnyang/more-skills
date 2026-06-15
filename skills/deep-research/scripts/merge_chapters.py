import os
import sys
import re
import glob
from datetime import datetime

def get_sort_key(filepath):
    # Extract the first sequence of digits from the filename
    basename = os.path.basename(filepath)
    match = re.search(r'(\d+)', basename)
    if match:
        return int(match.group(1))
    return 999999

def main():
    chapters_dir = "chapters"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    
    if len(sys.argv) > 1:
        topic_slug = sys.argv[1]
    else:
        topic_slug = os.path.basename(os.path.abspath(os.getcwd()))
        
    output_file = f"{topic_slug}-report-{timestamp}.md"
    
    if not os.path.exists(chapters_dir):
        print(f"Directory '{chapters_dir}' not found. No chapters to merge.")
        return

    # Gather all markdown files, explicitly excluding outline.md
    chapter_files = [f for f in glob.glob(os.path.join(chapters_dir, "*.md")) if os.path.basename(f) != "outline.md"]
    if not chapter_files:
        print(f"No markdown files found in '{chapters_dir}'.")
        return

    # Sort files numerically based on numbers in the filename
    # e.g. chapter_1.md, chapter_2.md, chapter_10.md
    chapter_files.sort(key=get_sort_key)
    
    print(f"Found {len(chapter_files)} chapters. Merging in order:")
    for f in chapter_files:
        print(f" - {os.path.basename(f)}")

    try:
        with open(output_file, "w", encoding="utf-8") as outfile:
            for filepath in chapter_files:
                with open(filepath, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n")
        print(f"Successfully merged all chapters into '{output_file}'.")
    except Exception as e:
        print(f"Error during merge: {e}")

if __name__ == "__main__":
    main()
