import os, shutil

def test_clean_old_docs():
    old_files = [
        r"c:\SkillSwap\docs\AI_Rules.md",
        r"c:\SkillSwap\docs\API_Contracts.md",
        r"c:\SkillSwap\docs\Architecture.md",
        r"c:\SkillSwap\docs\Daily_log.md",
        r"c:\SkillSwap\docs\Database.md",
        r"c:\SkillSwap\docs\Frontend_Masterplan.md",
        r"c:\SkillSwap\docs\PRD.md",
        r"c:\SkillSwap\docs\Roadmap.md",
        r"c:\SkillSwap\docs\Task_Board.md",
    ]
    for f in old_files:
        if os.path.exists(f):
            os.remove(f)

    arch_dir = r"c:\SkillSwap\docs\architecture"
    if os.path.exists(arch_dir):
        shutil.rmtree(arch_dir, ignore_errors=True)
