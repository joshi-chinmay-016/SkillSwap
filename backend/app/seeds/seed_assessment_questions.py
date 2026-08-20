import json
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.skill import Skill
from app.models.assessment import AssessmentQuestion


QUESTIONS_DATA = {
    "Python": [
        {
            "question_text": "What is the primary difference between a list and a tuple in Python?",
            "options": json.dumps([
                "Lists are immutable, tuples are mutable",
                "Lists are mutable, tuples are immutable",
                "Tuples can only store integers",
                "Lists cannot be nested"
            ]),
            "correct_option": 1,
            "explanation": "Lists in Python are mutable (can be changed in-place), whereas tuples are immutable once defined.",
            "difficulty": "BEGINNER"
        },
        {
            "question_text": "Which built-in Python function or library decorator is commonly used for memoization?",
            "options": json.dumps([
                "@functools.lru_cache",
                "@sys.memoize",
                "@os.cache",
                "@itertools.cache"
            ]),
            "correct_option": 0,
            "explanation": "functools.lru_cache wraps a function with a memoizing callable that saves up to maxsize results.",
            "difficulty": "INTERMEDIATE"
        },
        {
            "question_text": "How does GIL (Global Interpreter Lock) impact CPython execution?",
            "options": json.dumps([
                "Prevents multiple processes from accessing the disk",
                "Allows multiple threads to execute Python bytecode simultaneously across all cores",
                "Prevents multiple native threads from executing Python bytecodes at once in a single process",
                "Automatically compiles Python code into native machine code at runtime"
            ]),
            "correct_option": 2,
            "explanation": "In CPython, the GIL is a mutex that prevents multiple native threads from executing Python bytecodes concurrently.",
            "difficulty": "ADVANCED"
        }
    ],
    "React": [
        {
            "question_text": "What is the primary purpose of the useEffect hook in React?",
            "options": json.dumps([
                "To manage synchronous local component state",
                "To perform side effects in functional components",
                "To define global routing rules",
                "To compile JSX into HTML strings"
            ]),
            "correct_option": 1,
            "explanation": "useEffect lets you synchronize a component with an external system and execute side effects like data fetching or subscriptions.",
            "difficulty": "BEGINNER"
        },
        {
            "question_text": "Why should keys be unique among sibling elements when rendering lists in React?",
            "options": json.dumps([
                "Keys format the text content of the list items",
                "Keys help React identify which items have changed, been added, or been removed during reconciliation",
                "Keys automatically sort elements alphabetically",
                "Keys are required by CSS layout specifications"
            ]),
            "correct_option": 1,
            "explanation": "Keys give elements a stable identity across renders, allowing React's diffing algorithm to correctly track DOM elements.",
            "difficulty": "INTERMEDIATE"
        }
    ],
    "JavaScript": [
        {
            "question_text": "What does the event loop in JavaScript manage?",
            "options": json.dumps([
                "Garbage collection of unused objects",
                "Execution of multiple threads simultaneously",
                "Execution of code, collecting and processing events, and executing queued sub-tasks",
                "CSS rendering and layout passes"
            ]),
            "correct_option": 2,
            "explanation": "JavaScript single-threaded runtime relies on the event loop to execute asynchronous callbacks from the task queue.",
            "difficulty": "INTERMEDIATE"
        },
        {
            "question_text": "What is the difference between '==' and '===' in JavaScript?",
            "options": json.dumps([
                "'==' performs strict type equality without coercion",
                "'===' performs type conversion before comparison",
                "'==' performs type coercion, while '===' checks both value and type without coercion",
                "They are completely identical in function"
            ]),
            "correct_option": 2,
            "explanation": "'==' converts operands if they are of different types, whereas '===' (strict equality) requires both type and value to match.",
            "difficulty": "BEGINNER"
        }
    ],
    "SQL": [
        {
            "question_text": "What is the difference between WHERE and HAVING clauses in SQL?",
            "options": json.dumps([
                "WHERE filters rows before aggregation; HAVING filters aggregated groups after GROUP BY",
                "HAVING filters individual rows before grouping",
                "WHERE can only be used with SELECT statements, HAVING can be used everywhere",
                "They are aliases and perform identical operations"
            ]),
            "correct_option": 0,
            "explanation": "WHERE filters rows prior to aggregation, while HAVING filters group summaries produced by GROUP BY.",
            "difficulty": "INTERMEDIATE"
        }
    ]
}


def seed_assessment_questions(db: Session):
    print("Seeding assessment questions...")
    added_count = 0

    # Retrieve all existing skills
    skills = db.query(Skill).all()
    skill_map = {s.name.lower(): s for s in skills}

    for skill_name, q_list in QUESTIONS_DATA.items():
        matched_skill = skill_map.get(skill_name.lower())
        if not matched_skill:
            # Create the skill if missing
            matched_skill = Skill(name=skill_name, category="Programming & Web Tech", description=f"{skill_name} core competencies")
            db.add(matched_skill)
            db.commit()
            db.refresh(matched_skill)
            skill_map[skill_name.lower()] = matched_skill

        for q_data in q_list:
            existing = db.query(AssessmentQuestion).filter(
                AssessmentQuestion.skill_id == matched_skill.id,
                AssessmentQuestion.question_text == q_data["question_text"]
            ).first()

            if not existing:
                q = AssessmentQuestion(
                    skill_id=matched_skill.id,
                    question_text=q_data["question_text"],
                    options=q_data["options"],
                    correct_option=q_data["correct_option"],
                    explanation=q_data["explanation"],
                    difficulty=q_data["difficulty"]
                )
                db.add(q)
                added_count += 1

    db.commit()
    print(f"Successfully seeded {added_count} assessment questions.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_assessment_questions(db)
    finally:
        db.close()
