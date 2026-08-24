import os
import glob
import re

versions_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../alembic/versions/*.py"))
for f in glob.glob(versions_dir):
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    rev_match = re.search(r"revision\s*(?::\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", content)
    down_match = re.search(r"down_revision\s*(?::\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", content)
    rev = rev_match.group(1) if rev_match else "NONE"
    down = down_match.group(1) if down_match else "NONE"
    is_too_long = len(rev) > 32 or (down != "NONE" and len(down) > 32)
    status = "[TOO LONG]" if is_too_long else "[OK]"
    print(f"{status}: rev='{rev}' ({len(rev)}), down='{down}' ({len(down)}) in {os.path.basename(f)}")
