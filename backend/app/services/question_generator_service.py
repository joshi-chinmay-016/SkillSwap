import json
import logging
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.models.assessment import AssessmentQuestion
from app.repositories.verification_repository import create_assessment_question

logger = logging.getLogger(__name__)

# Fallback structured question banks for common skill categories if LLM is unavailable
SKILL_QUESTION_TEMPLATES = {
    "python": [
        # Easy
        ("What is the primary difference between a list and a tuple in Python?", ["Lists are mutable, tuples are immutable", "Lists are immutable, tuples are mutable", "Tuples can only hold numbers", "Lists cannot be nested"], 0, "Lists in Python can be modified after creation, while tuples cannot.", "EASY"),
        ("Which keyword is used to define a function in Python?", ["function", "def", "func", "define"], 1, "The 'def' keyword introduces a function definition in Python.", "EASY"),
        ("What is the output of bool([]) in Python?", ["True", "False", "None", "Error"], 1, "An empty list evaluates to False in boolean context.", "EASY"),
        # Medium
        ("Which standard module or decorator is commonly used for function memoization in Python?", ["@functools.lru_cache", "@sys.memoize", "@os.cache", "@itertools.cache"], 0, "functools.lru_cache wraps a function with a memoizing callable.", "INTERMEDIATE"),
        ("What does the *args parameter in a Python function definition do?", ["Passes keyword arguments as a dictionary", "Passes positional arguments as a tuple", "Pointers to memory addresses", "Enforces type checking"], 1, "*args allows passing a variable number of positional arguments as a tuple.", "INTERMEDIATE"),
        ("How does a Python generator differ from a regular function returning a list?", ["Generators use 'yield' to produce items lazily one at a time", "Generators run on a separate CPU core", "Generators cannot handle loops", "Generators convert all items to strings"], 0, "Generators use yield to produce values on-the-fly without holding all in memory.", "INTERMEDIATE"),
        ("What is the time complexity of looking up a key in a Python dictionary (on average)?", ["O(n)", "O(log n)", "O(1)", "O(n^2)"], 2, "Python dictionaries are implemented using hash tables, giving O(1) average lookup time.", "INTERMEDIATE"),
        # Hard
        ("How does the Global Interpreter Lock (GIL) impact CPython thread execution?", ["Prevents multiple native threads from executing Python bytecodes concurrently", "Disables memory management for multi-threading", "Accelerates multi-threaded matrix operations", "Automatically parallelizes for loops"], 0, "The GIL prevents multiple threads from executing Python bytecode simultaneously in CPython.", "HARD"),
        ("In Python's descriptor protocol, which method is invoked when accessing an attribute on an instance?", ["__get__", "__getattr__", "__setattr__", "__call__"], 0, "Descriptors define __get__, __set__, or __delete__ to override attribute access behavior.", "HARD"),
        ("What is the result of using metaclasses in Python?", ["They define how classes themselves are constructed", "They replace global variables with local scope", "They prevent inheritance", "They automatically convert code to C extensions"], 0, "Metaclasses are the 'classes of classes' that define how classes are constructed.", "HARD"),
    ],
    "react": [
        # Easy
        ("What is the primary purpose of React JSX?", ["Syntax extension allowing HTML-like template syntax in JS", "A database query engine", "A CSS preprocessor", "A server-side routing protocol"], 0, "JSX allows writing HTML-like markup inside JavaScript files.", "EASY"),
        ("Which hook is used to handle local state in functional components?", ["useEffect", "useState", "useContext", "useReducer"], 1, "useState allows functional components to manage local state.", "EASY"),
        ("What is the role of 'props' in React components?", ["Read-only inputs passed from parent to child components", "Internal mutable state", "Global database connections", "CSS class definitions"], 0, "Props are read-only properties passed down from parent components.", "EASY"),
        # Medium
        ("Why should key props be unique among sibling elements in React lists?", ["Helps React's diffing algorithm identify which items changed, added, or removed", "Keys format element text content", "Keys enforce CSS flexbox alignment", "Keys sort array elements in alphabetical order"], 0, "Keys give elements stable identity across re-renders for efficient DOM updates.", "INTERMEDIATE"),
        ("What is the purpose of the useEffect hook in React?", ["Perform side effects like data fetching and subscriptions in components", "Compile JSX to native DOM nodes", "Handle user form input validation", "Manage global state Redux stores"], 0, "useEffect handles side effects and synchronization with external systems.", "INTERMEDIATE"),
        ("When does React trigger a component re-render?", ["When state or props change", "Every 100 milliseconds automatically", "Only on page refresh", "When CSS styles are modified"], 0, "React component re-renders when its state or received props change.", "INTERMEDIATE"),
        ("What is the main advantage of React.memo?", ["Prevents re-rendering of a component if its props haven't changed", "Memoizes database queries on the server", "Compresses bundle size automatically", "Translates React code to WebAssembly"], 0, "React.memo skips re-rendering when props remain shallowly equal.", "INTERMEDIATE"),
        # Hard
        ("How does React 18's Concurrent Rendering improve UI responsiveness?", ["By breaking rendering work into yieldable chunks without blocking the main UI thread", "By executing Javascript on multiple CPU threads simultaneously", "By replacing Virtual DOM with direct DOM mutation", "By eliminating all async state updates"], 0, "Concurrent React can interrupt, pause, or resume rendering work to keep the main thread responsive.", "HARD"),
        ("What is the difference between useLayoutEffect and useEffect?", ["useLayoutEffect runs synchronously after DOM mutations before browser paint", "useLayoutEffect runs asynchronously after browser paint", "useLayoutEffect only works on mobile devices", "useEffect cannot access DOM refs"], 0, "useLayoutEffect fires synchronously after all DOM mutations, before paint.", "HARD"),
        ("What is the role of Reconciliation in React Fiber architecture?", ["The process of diffing the Virtual DOM tree to calculate minimal real DOM updates", "Compiling React JSX to static HTML on build", "Managing OAuth user authentication sessions", "Optimizing image loading times"], 0, "Reconciliation compares old and new fiber trees to compute minimal DOM operations.", "HARD"),
    ],
    "javascript": [
        # Easy
        ("What is the difference between 'let' and 'var' scoping in JavaScript?", ["'let' is block-scoped, 'var' is function-scoped", "'var' is block-scoped, 'let' is function-scoped", "They are identical in scope", "'let' cannot be reassigned"], 0, "let is scoped to the block ({}), whereas var is scoped to the enclosing function.", "EASY"),
        ("What does the 'typeof' operator return for an array in JavaScript?", ["'object'", "'array'", "'list'", "'undefined'"], 0, "Arrays in JavaScript are specialized objects, so typeof returns 'object'.", "EASY"),
        ("Which method converts a JSON string into a JavaScript object?", ["JSON.parse()", "JSON.stringify()", "JSON.toObject()", "Object.fromJSON()"], 0, "JSON.parse() parses a JSON string into a JS object.", "EASY"),
        # Medium
        ("What is a closure in JavaScript?", ["A function bundled together with references to its surrounding lexical environment", "A syntax to close browser tabs", "A method to terminate async loops", "An HTML element closing tag"], 0, "A closure gives access to an outer function's scope from an inner function.", "INTERMEDIATE"),
        ("How does the Event Loop handle asynchronous promises vs setTimeout callbacks?", ["Promises enter Microtask queue (higher priority); setTimeout enters Macrotask queue", "setTimeout has higher priority than promises", "Both enter the exact same synchronous stack", "Promises bypass the event loop entirely"], 0, "Microtasks (Promises) are executed immediately after current script, before Macrotasks (setTimeout).", "INTERMEDIATE"),
        ("What is event delegation in DOM manipulation?", ["Attaching a single event listener to a parent element to manage events on children", "Sending HTTP events to a remote server", "Delegating event handling to a Web Worker", "Blocking propagation of keyboard events"], 0, "Event delegation uses event bubbling to handle events on parent containers.", "INTERMEDIATE"),
        ("What is the value of 'this' inside an arrow function?", ["Inherited lexically from the enclosing execution context", "Always bound to global window/globalThis", "Bound to the DOM element that fired the event", "Undefined in all strict mode functions"], 0, "Arrow functions do not bind their own 'this'; they inherit it lexically.", "INTERMEDIATE"),
        # Hard
        ("What happens during the Hoisting phase in JavaScript execution context?", ["Variable and function declarations are put into memory during compilation before code execution", "DOM nodes are created in memory", "CSS stylesheets are evaluated", "Garbage collection purges unreferenced memory"], 0, "Hoisting stores function declarations and variable names in memory before code runs.", "HARD"),
        ("What is the purpose of WeakMap compared to standard Map in JavaScript?", ["WeakMap keys must be objects and are held as weak references, allowing garbage collection", "WeakMap executes faster for primitive strings", "WeakMap supports iteration with for...of loops", "WeakMap stores data on disk memory"], 0, "WeakMap keys are weakly referenced, enabling GC if no other references to key exist.", "HARD"),
        ("How does Prototype Chain inheritance work when accessing an object property?", ["JS traverses up the [[Prototype]] chain until the property is found or null is reached", "JS searches all global variables simultaneously", "JS converts the object to a C struct", "JS re-instantiates the parent class constructor on every access"], 0, "Properties are looked up recursively up the __proto__ / [[Prototype]] chain.", "HARD"),
    ]
}


def generate_fallback_questions_for_skill(skill_name: str) -> list[dict]:
    normalized_name = skill_name.lower().strip()
    
    # Check exact/partial match in templates
    for key, q_list in SKILL_QUESTION_TEMPLATES.items():
        if key in normalized_name or normalized_name in key:
            return [
                {
                    "question_text": text,
                    "options": json.dumps(opts),
                    "correct_option": correct,
                    "explanation": exp,
                    "difficulty": diff
                }
                for text, opts, correct, exp, diff in q_list
            ]
    
    # Generic high quality 10-question template for any domain skill
    return [
        # Easy (3)
        (f"What is the foundational definition of {skill_name} in its domain?", [f"A core discipline/tool set focused on {skill_name} principles", "A legacy database backup format", "A deprecated network hardware driver", "An operating system kernel component"], 0, f"{skill_name} refers to foundational domain principles and techniques.", "EASY"),
        (f"Which of the following is a primary best practice when starting with {skill_name}?", ["Following modular structure and standardized conventions", "Ignoring error handling and logging", "Hardcoding secret values directly", "Avoiding version control systems"], 0, "Standardized conventions and modular design ensure maintainable practice.", "EASY"),
        (f"What is a key benefit of mastering {skill_name}?", ["Enhanced problem solving and industry efficiency", "Increased hardware disk usage", "Slower execution times", "Decreased code readability"], 0, "Mastery improves capability, design quality, and efficiency.", "EASY"),
        # Medium (4)
        (f"When optimizing a workflow or project using {skill_name}, what is a critical consideration?", ["Performance profiling, resource efficiency, and modularity", "Adding redundant duplicate loops", "Disabling automated tests", "Removing documentation"], 0, "Performance and modularity are essential optimization criteria.", "INTERMEDIATE"),
        (f"In {skill_name}, how should edge cases and exception handling generally be managed?", ["Proactively catching expected errors and validating inputs", "Swallowing all exceptions silently", "Allowing crashes to happen without logs", "Hardcoding default 0 fallback values everywhere"], 0, "Proactive validation and explicit error handling prevent system failures.", "INTERMEDIATE"),
        (f"What role does architectural modularity play when working with {skill_name}?", ["Decouples components for testability and reusability", "Increases coupling between unrelated modules", "Prevents code refactoring", "Compiles code into binary executables"], 0, "Decoupled modules enhance testability, maintenance, and reuse.", "INTERMEDIATE"),
        (f"Which metric is most relevant for assessing effectiveness in {skill_name} implementation?", ["Correctness, execution speed, and maintainability", "Number of lines of code written", "File extension length", "Color scheme of editor"], 0, "Correctness, speed, and maintainability determine implementation quality.", "INTERMEDIATE"),
        # Hard (3)
        (f"How do advanced practitioners resolve scale or high-concurrency challenges in {skill_name}?", ["By leveraging asynchronous patterns, caching, and load distribution", "By forcing single-threaded synchronous processing", "By increasing global lock contention", "By removing database indexes"], 0, "Scaling requires async execution, effective caching, and distributed workload management.", "HARD"),
        (f"In complex {skill_name} systems, what is the primary risk of tightly coupled state management?", ["Cascading side-effects, difficult regression testing, and poor scalability", "Excessive code comments", "Faster compilation times", "Automatic memory deallocation"], 0, "Tight coupling creates unexpected side effects and makes systems hard to scale and test.", "HARD"),
        (f"What is the recommended strategy for maintaining backwards compatibility in {skill_name} system upgrades?", ["Semantic versioning, deprecation warnings, and migration pathways", "Deleting old API endpoints immediately", "Changing function signatures without notice", "Removing version tags"], 0, "Semantic versioning and migration pathways prevent breaking downstream users.", "HARD")
    ]
    return [
        {
            "question_text": text,
            "options": json.dumps(opts),
            "correct_option": correct,
            "explanation": exp,
            "difficulty": diff
        }
        for text, opts, correct, exp, diff in template_tuples
    ]


def ensure_ten_questions_for_skill(db: Session, skill: Skill) -> list[AssessmentQuestion]:
    existing = db.query(AssessmentQuestion).filter(AssessmentQuestion.skill_id == skill.id).all()
    
    if len(existing) >= 10:
        return sort_questions_by_difficulty(existing[:10])

    needed = 10 - len(existing)
    logger.info(f"Skill '{skill.name}' (ID: {skill.id}) has {len(existing)} questions. Generating {needed} more...")

    generated_data = generate_fallback_questions_for_skill(skill.name)

    existing_texts = {q.question_text.lower() for q in existing}
    added = []

    for item in generated_data:
        if len(existing) + len(added) >= 10:
            break

        # Convert item if tuple or dict
        if isinstance(item, dict):
            q_text = item["question_text"]
            opts = item["options"]
            c_opt = item["correct_option"]
            exp = item["explanation"]
            diff = item["difficulty"]
        else:
            q_text, opts_list, c_opt, exp, diff = item
            opts = json.dumps(opts_list)

        if q_text.lower() not in existing_texts:
            new_q = AssessmentQuestion(
                skill_id=skill.id,
                question_text=q_text,
                options=opts,
                correct_option=c_opt,
                explanation=exp,
                difficulty=diff
            )
            created = create_assessment_question(db, new_q)
            added.append(created)
            existing_texts.add(q_text.lower())

    all_questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.skill_id == skill.id).all()
    return sort_questions_by_difficulty(all_questions[:10])


def sort_questions_by_difficulty(questions: list[AssessmentQuestion]) -> list[AssessmentQuestion]:
    diff_order = {"EASY": 1, "BEGINNER": 1, "INTERMEDIATE": 2, "MEDIUM": 2, "ADVANCED": 3, "HARD": 3}
    return sorted(questions, key=lambda q: diff_order.get(q.difficulty.upper(), 2))
