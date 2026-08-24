import os
import re
import glob

def check_all_markdown_links():
    md_files = ["README.md"] + glob.glob("docs/**/*.md", recursive=True)
    all_valid = True
    total_checked = 0

    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        base_dir = os.path.dirname(md_file)
        # Match markdown links: [text](path) or ![alt](path)
        matches = re.findall(r'!?\[.*?\]\(([^http#][^\)]+)\)', content)
        for link in matches:
            clean_link = link.split("#")[0].strip()
            if not clean_link:
                continue
            # Resolve relative path
            target_path = os.path.normpath(os.path.join(base_dir, clean_link))
            total_checked += 1
            if not os.path.exists(target_path):
                print(f"[BROKEN LINK] in {md_file}: {link} -> {target_path}")
                all_valid = False

    if all_valid:
        print(f"[SUCCESS] All {total_checked} markdown links across {len(md_files)} files verified and valid!")
    else:
        exit(1)

if __name__ == "__main__":
    check_all_markdown_links()
