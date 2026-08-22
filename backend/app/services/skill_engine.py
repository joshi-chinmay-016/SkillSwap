"""Generic Skill Verification Engine for SkillSwap Arena.

Provides domain-agnostic skill normalization, classification, profiling,
knowledge mapping, assessment blueprints, structured question generation,
and anti-contamination validation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import json
import logging
import re

logger = logging.getLogger("skillswap.skill_engine")


@dataclass
class SkillProfile:
    canonical_name: str
    domain: str
    category: str
    knowledge_areas: List[str]
    related_concepts: List[str]
    forbidden_contamination_concepts: List[str]
    assessment_types: List[str]
    difficulty_expectations: Dict[str, int] = field(
        default_factory=lambda: {"EASY": 3, "INTERMEDIATE": 4, "HARD": 3}
    )


@dataclass
class GeneratedQuestion:
    skill: str
    knowledge_area: str
    question_type: str  # conceptual, scenario, troubleshooting, code_reasoning, situational_judgment, architecture
    difficulty: str     # EASY, INTERMEDIATE, HARD
    question_text: str
    options: List[str]
    correct_option: int  # 0..3
    explanation: str
    expected_concepts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill": self.skill,
            "knowledge_area": self.knowledge_area,
            "question_type": self.question_type,
            "difficulty": self.difficulty,
            "question_text": self.question_text,
            "options": json.dumps(self.options),
            "correct_option": self.correct_option,
            "explanation": self.explanation,
            "expected_concepts": self.expected_concepts,
        }


@dataclass
class ValidationResult:
    is_valid: bool
    rejection_reason: Optional[str] = None


class SkillNormalizer:
    """Normalizes raw user-entered skill strings into canonical representations."""

    TAXONOMY: Dict[str, Dict[str, Any]] = {
        "java": {
            "canonical": "Java",
            "domain": "Technology",
            "category": "Programming Language",
            "aliases": ["core java", "java 8", "java 11", "java 17", "java 21", "java enterprise", "j2se"],
            "knowledge_areas": [
                "OOP & Core Semantics",
                "JVM Architecture & Memory Model",
                "Collections & Generics",
                "Concurrency & Thread Safety",
                "Exception Handling & I/O",
                "Modern Java Features & Streams"
            ],
            "forbidden": ["dom", "document.", "window.", "react", "jsx", "css", "html", "event bubbling", "let vs var", "pip install", "malloc", "pointer arithmetic", "javascript", "typeof", "event loop", "prototype chain", "weakmap", "hoisting", "arrow function"],
            "assessment_types": ["code_reasoning", "conceptual", "troubleshooting", "scenario"]
        },
        "python": {
            "canonical": "Python",
            "domain": "Technology",
            "category": "Programming Language",
            "aliases": ["python 3", "cpython", "py", "core python"],
            "knowledge_areas": [
                "Data Structures & Mutability",
                "Functions, Generators & Iterators",
                "OOP, Dunder Methods & Descriptors",
                "Concurrency, AsyncIO & GIL",
                "Memory Management & Scoping",
                "Standard Library & Packaging"
            ],
            "forbidden": ["jvm", "public static void main", "pointer arithmetic", "dom manipulation", "jsx", "system.out.println"],
            "assessment_types": ["code_reasoning", "conceptual", "troubleshooting", "scenario"]
        },
        "javascript": {
            "canonical": "JavaScript",
            "domain": "Technology",
            "category": "Programming Language",
            "aliases": ["js", "es6", "ecmascript", "vanilla js", "modern javascript"],
            "knowledge_areas": [
                "Scope, Closures & Lexical Context",
                "Event Loop, Promises & Async/Await",
                "Prototypes & Object Model",
                "DOM & Browser APIs",
                "Type Coercion & ES6+ Features",
                "Error Handling & Memory Leaks"
            ],
            "forbidden": ["jvm", "pointer arithmetic", "cpython gil", "public static void main", "django orm"],
            "assessment_types": ["code_reasoning", "conceptual", "troubleshooting", "scenario"]
        },
        "devops": {
            "canonical": "DevOps",
            "domain": "Technology",
            "category": "DevOps & Cloud Infrastructure",
            "aliases": ["dev-ops", "dev ops", "site reliability engineering", "sre", "cloud devops"],
            "knowledge_areas": [
                "CI/CD Pipelines & Automation",
                "Containerization & Docker",
                "Kubernetes & Container Orchestration",
                "Infrastructure as Code (IaC)",
                "Monitoring, Logging & Observability",
                "Linux Fundamentals & Networking Security"
            ],
            "forbidden": ["java inheritance", "react state", "css flexbox", "python list slicing", "event bubbling in dom"],
            "assessment_types": ["scenario", "troubleshooting", "architecture", "conceptual"]
        },
        "backend": {
            "canonical": "Backend Development",
            "domain": "Technology",
            "category": "Backend Engineering",
            "aliases": ["backend", "backend engineering", "server side development", "api development"],
            "knowledge_areas": [
                "RESTful & RPC API Design",
                "Database Architecture & Indexing",
                "Authentication, Authorization & Security",
                "Caching Strategies & Distributed Systems",
                "Message Queues & Event-Driven Architecture",
                "Scalability, Concurrency & Rate Limiting"
            ],
            "forbidden": ["css selectors", "color palette", "speech pacing", "crop irrigation"],
            "assessment_types": ["architecture", "scenario", "troubleshooting", "conceptual"]
        },
        "machine_learning": {
            "canonical": "Machine Learning",
            "domain": "Technology",
            "category": "Artificial Intelligence & ML",
            "aliases": ["ml", "machine learning", "deep learning", "applied ai", "data science"],
            "knowledge_areas": [
                "Supervised & Unsupervised Learning",
                "Feature Engineering & Preprocessing",
                "Model Evaluation Metrics & Cross-Validation",
                "Overfitting, Regularization & Bias-Variance",
                "Optimization & Gradient Descent",
                "Neural Networks & Deep Learning Architectures"
            ],
            "forbidden": ["dom element", "css padding", "container orchestration", "speech stage presence"],
            "assessment_types": ["conceptual", "scenario", "model_selection", "troubleshooting"]
        },
        "system_design": {
            "canonical": "System Design",
            "domain": "Technology",
            "category": "Architecture & Distributed Systems",
            "aliases": ["system design", "distributed systems", "software architecture", "high level design", "hld"],
            "knowledge_areas": [
                "Scalability, Load Balancing & Partitioning",
                "CAP Theorem & Consistency Models",
                "Database Sharding & Replication",
                "Caching Architectures & Invalidation",
                "Message Brokers & Stream Processing",
                "Reliability, Failover & Rate Limiting"
            ],
            "forbidden": ["css margin", "camera aperture", "soil ph level", "stage vocal projection"],
            "assessment_types": ["architecture", "scenario", "trade_off_analysis", "conceptual"]
        },
        "dsa": {
            "canonical": "Data Structures & Algorithms",
            "domain": "Technology",
            "category": "Computer Science Core",
            "aliases": ["dsa", "algorithms", "data structures", "competitive programming", "algo"],
            "knowledge_areas": [
                "Asymptotic Complexity & Big-O Analysis",
                "Linear Data Structures (Arrays, Lists, Stacks, Queues)",
                "Non-Linear Data Structures (Trees, BST, Heaps, Graphs)",
                "Sorting, Searching & Divide and Conquer",
                "Dynamic Programming & Memoization",
                "Graph Algorithms (BFS, DFS, Dijkstra, TopoSort)"
            ],
            "forbidden": ["marketing conversion", "camera iso", "crop pest control", "html div tag"],
            "assessment_types": ["code_reasoning", "conceptual", "complexity_analysis", "scenario"]
        },
        "public_speaking": {
            "canonical": "Public Speaking",
            "domain": "Professional Skills",
            "category": "Communication & Oratory",
            "aliases": ["public speaking", "speech", "oratory", "presentation skills", "keynote speaking"],
            "knowledge_areas": [
                "Speech Structure, Hooks & Storytelling",
                "Vocal Variety, Tone & Pacing",
                "Body Language, Eye Contact & Stage Presence",
                "Managing Speech Anxiety & Impromptu Speaking",
                "Audience Analysis & Engagement",
                "Handling Q&A & Challenging Questions"
            ],
            "forbidden": ["pointer arithmetic", "sql query", "docker container", "compiler optimization"],
            "assessment_types": ["situational_judgment", "scenario", "conceptual"]
        },
        "problem_solving": {
            "canonical": "Problem Solving",
            "domain": "Professional Skills",
            "category": "Cognitive & Analytical Thinking",
            "aliases": ["problem solving", "critical thinking", "analytical reasoning", "root cause analysis"],
            "knowledge_areas": [
                "Problem Framing & Decomposition",
                "Root Cause Analysis (5 Whys, Fishbone)",
                "Hypothesis Testing & Validation",
                "Decision Matrices & Trade-off Prioritization",
                "Lateral Thinking & Solution Generation",
                "Execution Planning & Risk Mitigation"
            ],
            "forbidden": ["css styles", "camera shutter speed", "soil irrigation"],
            "assessment_types": ["scenario", "situational_judgment", "root_cause_analysis", "conceptual"]
        },
        "ui_ux": {
            "canonical": "UI/UX Design",
            "domain": "Creative Arts",
            "category": "Product & Interface Design",
            "aliases": ["ui/ux", "ui ux", "user experience", "user interface", "product design", "ux design"],
            "knowledge_areas": [
                "User Research & Personas",
                "Information Architecture & Wireframing",
                "Design Systems, Typography & Color Hierarchy",
                "Usability Testing & Accessibility (WCAG)",
                "Interaction Design & Micro-animations",
                "Heuristic Evaluation & Conversion Optimization"
            ],
            "forbidden": ["jvm memory", "sql foreign key", "linux kernel", "soil fertilizer"],
            "assessment_types": ["scenario", "design_critique", "heuristic_evaluation", "conceptual"]
        },
        "agriculture": {
            "canonical": "Agriculture & Crop Cultivation",
            "domain": "Life Sciences & Agriculture",
            "category": "Agronomy & Farming",
            "aliases": ["agriculture", "farming", "agronomy", "arecanut farming", "crop management"],
            "knowledge_areas": [
                "Soil Health, pH & Nutrient Management",
                "Crop Selection, Planting & Spacing",
                "Irrigation Systems & Water Conservation",
                "Pest Management & Disease Control",
                "Harvesting, Post-Harvest & Storage",
                "Sustainable Farming & Yield Optimization"
            ],
            "forbidden": ["sql database", "docker image", "react hook", "java exception"],
            "assessment_types": ["scenario", "troubleshooting", "practical_management", "conceptual"]
        },
    }

    @classmethod
    def normalize(cls, raw_skill: str) -> Dict[str, Any]:
        cleaned = raw_skill.strip().lower()
        tokens = set(re.findall(r'[a-z0-9+#]+', cleaned))

        # Check exact key
        if cleaned in cls.TAXONOMY:
            return cls.TAXONOMY[cleaned]

        # Check aliases
        for key, entry in cls.TAXONOMY.items():
            for alias in entry["aliases"]:
                if alias.lower() == cleaned:
                    return entry
                alias_tokens = set(re.findall(r'[a-z0-9+#]+', alias.lower()))
                if alias_tokens and alias_tokens == tokens:
                    return entry

        # Check token containment rules (avoiding sub-collisions like Java vs JavaScript)
        if "javascript" in tokens or "js" in tokens or "ecmascript" in tokens:
            return cls.TAXONOMY["javascript"]
        if "java" in tokens and "javascript" not in cleaned and "js" not in tokens:
            return cls.TAXONOMY["java"]
        if "python" in tokens or "django" in tokens or "flask" in tokens or "fastapi" in tokens:
            return cls.TAXONOMY["python"]
        if "devops" in tokens or "kubernetes" in tokens or "docker" in tokens or "ci/cd" in tokens:
            return cls.TAXONOMY["devops"]
        if "backend" in tokens or "api" in tokens:
            return cls.TAXONOMY["backend"]
        if "speaking" in tokens or "speech" in tokens or "oratory" in tokens:
            return cls.TAXONOMY["public_speaking"]
        if "solving" in tokens or "problem" in tokens or "logic" in tokens:
            return cls.TAXONOMY["problem_solving"]
        if "ui" in tokens or "ux" in tokens or "figma" in tokens:
            return cls.TAXONOMY["ui_ux"]
        if "farm" in tokens or "farming" in tokens or "crop" in tokens or "arecanut" in tokens:
            return cls.TAXONOMY["agriculture"]

        # Dynamic Generic Normalization for novel/custom skills
        canonical_title = raw_skill.strip().title()
        return {
            "canonical": canonical_title,
            "domain": "Specialized Domain",
            "category": "Professional & Technical Practice",
            "aliases": [cleaned],
            "knowledge_areas": [
                f"Core Principles of {canonical_title}",
                f"Methodologies & Techniques in {canonical_title}",
                f"Troubleshooting & Error Prevention in {canonical_title}",
                f"Optimization & Efficiency in {canonical_title}",
                f"Quality Assurance & Standards for {canonical_title}",
                f"Advanced Strategy & Systems for {canonical_title}"
            ],
            "forbidden": ["unrelated database", "deprecated kernel", "fake driver"],
            "assessment_types": ["conceptual", "scenario", "troubleshooting", "practical_management"]
        }


class SkillProfiler:
    """Generates structured SkillProfiles from normalized skills."""

    @classmethod
    def get_profile(cls, raw_skill_name: str) -> SkillProfile:
        norm = SkillNormalizer.normalize(raw_skill_name)
        return SkillProfile(
            canonical_name=norm["canonical"],
            domain=norm["domain"],
            category=norm["category"],
            knowledge_areas=norm["knowledge_areas"],
            related_concepts=norm["aliases"],
            forbidden_contamination_concepts=norm["forbidden"],
            assessment_types=norm["assessment_types"],
            difficulty_expectations={"EASY": 3, "INTERMEDIATE": 4, "HARD": 3}
        )


class QuestionValidator:
    """Validates generated assessment questions for relevance, accuracy, and anti-contamination."""

    @classmethod
    def validate_question(
        cls,
        q: GeneratedQuestion,
        profile: SkillProfile,
        seen_texts: Optional[Set[str]] = None
    ) -> ValidationResult:
        # 1. Non-empty text checks
        if not q.question_text or len(q.question_text.strip()) < 15:
            return ValidationResult(False, "Question text is too short or empty.")

        # 2. Options validation
        if not q.options or len(q.options) != 4:
            return ValidationResult(False, f"Expected exactly 4 options, got {len(q.options) if q.options else 0}.")

        for idx, opt in enumerate(q.options):
            if not opt or not str(opt).strip():
                return ValidationResult(False, f"Option index {idx} is blank.")

        # Ensure options are mutually distinct
        if len(set(opt.strip().lower() for opt in q.options)) < 4:
            return ValidationResult(False, "Duplicate options detected in question.")

        # 3. Correct option bound check
        if q.correct_option < 0 or q.correct_option > 3:
            return ValidationResult(False, f"correct_option index {q.correct_option} out of valid bounds (0..3).")

        # 4. Anti-Contamination Check
        full_content = q.question_text + " " + " ".join(q.options) + " " + q.explanation
        for forbidden in profile.forbidden_contamination_concepts:
            pattern = r'(?:\b|\W)' + re.escape(forbidden.lower()) + r'(?:\b|\W)'
            if re.search(pattern, full_content.lower()):
                return ValidationResult(
                    False,
                    f"Cross-skill contamination rejected: '{forbidden}' detected in {profile.canonical_name} question."
                )

        # 5. Deduplication check
        norm_text = re.sub(r'\s+', ' ', q.question_text.lower().strip())
        if seen_texts is not None:
            if norm_text in seen_texts:
                return ValidationResult(False, "Duplicate question text detected.")
            seen_texts.add(norm_text)

        # 6. Difficulty validity
        if q.difficulty.upper() not in ["EASY", "INTERMEDIATE", "HARD", "MEDIUM", "BEGINNER", "ADVANCED"]:
            return ValidationResult(False, f"Invalid difficulty '{q.difficulty}'.")

        return ValidationResult(True)


class DomainQuestionBank:
    """Pre-built, peer-reviewed assessment banks for core domains with exact 10-question distribution (3 Easy, 4 Medium, 3 Hard)."""

    BANKS: Dict[str, List[GeneratedQuestion]] = {
        "Java": [
            # EASY (3)
            GeneratedQuestion("Java", "JVM Architecture & Memory Model", "conceptual", "EASY",
                "Which component of the Java platform is directly responsible for executing Java bytecode instructions at runtime?",
                ["Java Virtual Machine (JVM)", "Java Development Kit (JDK)", "Java Compiler (javac)", "Java Archive Tool (jar)"],
                0, "The JVM is the execution engine that interprets or compiles bytecode into native machine code at runtime.", ["JVM", "Bytecode execution"]),
            GeneratedQuestion("Java", "OOP & Core Semantics", "conceptual", "EASY",
                "What is the default initial value of an uninitialized boolean instance variable in a Java class?",
                ["false", "true", "null", "0"],
                0, "In Java, primitive boolean instance variables are automatically initialized to false by the runtime.", ["Primitives", "Default values"]),
            GeneratedQuestion("Java", "OOP & Core Semantics", "conceptual", "EASY",
                "Which Java keyword is used to prevent a method from being overridden by any subclass?",
                ["final", "static", "abstract", "private"],
                0, "The 'final' keyword on a method prevents subclasses from overriding its implementation.", ["final keyword", "Inheritance control"]),
            # INTERMEDIATE (4)
            GeneratedQuestion("Java", "Collections & Generics", "troubleshooting", "INTERMEDIATE",
                "How does Java 8+ HashMap optimize bucket lookup performance when a bucket encounters severe hash collisions (exceeding 8 nodes)?",
                ["Converts the linked list into a balanced Red-Black Tree (TreeNode)", "Switches to linear probing open-addressing", "Throws a KeyCollisionException", "Evicts older elements from the bucket"],
                0, "Java 8 converts linked list collision chains to Red-Black trees when bucket length exceeds 8 (TREEIFY_THRESHOLD), reducing search from O(n) to O(log n).", ["HashMap internals", "Treeify threshold"]),
            GeneratedQuestion("Java", "OOP & Core Semantics", "conceptual", "INTERMEDIATE",
                "What is the fundamental architectural difference between String, StringBuilder, and StringBuffer in Java?",
                ["String is immutable; StringBuilder is mutable and not thread-safe; StringBuffer is mutable and synchronized (thread-safe)", "StringBuilder is immutable; String is mutable", "StringBuffer is deprecated in modern Java", "All three share the exact same synchronization mechanics"],
                0, "String objects are immutable; StringBuilder provides fast unsynchronized mutable string operations; StringBuffer provides synchronized mutable operations.", ["String mutability", "Thread safety"]),
            GeneratedQuestion("Java", "Concurrency & Thread Safety", "conceptual", "INTERMEDIATE",
                "What memory visibility guarantee does the 'volatile' keyword provide in Java multi-threading?",
                ["Ensures reads and writes to the variable bypass CPU caches and go directly to main memory, preventing stale cache reads", "Provides mutual exclusion lock like synchronized blocks", "Guarantees atomic execution of compound operations like i++", "Prevents the object from being garbage collected"],
                0, "The volatile modifier guarantees cross-thread visibility of variable updates by establishing a happens-before relationship and preventing CPU cache inconsistency.", ["volatile", "Memory visibility"]),
            GeneratedQuestion("Java", "Exception Handling & I/O", "conceptual", "INTERMEDIATE",
                "In Java exception handling, what characterizes Checked Exceptions (subclasses of Exception excluding RuntimeException)?",
                ["They must be either explicitly handled in a try-catch block or declared in the method signature using 'throws'", "They are fatal JVM errors that cannot be caught", "They only occur during bytecode compilation", "They do not inherit from Throwable"],
                0, "Checked exceptions represent recoverable external conditions that the compiler forces developers to catch or declare in method signatures.", ["Checked exceptions", "Exception hierarchy"]),
            # HARD (3)
            GeneratedQuestion("Java", "JVM Architecture & Memory Model", "architecture", "HARD",
                "How does the G1 (Garbage-First) Garbage Collector in the HotSpot JVM achieve predictable pause times on large heaps?",
                ["Divides the heap into equal-sized regional blocks and prioritizes collecting regions containing the highest density of reclaimable garbage first", "Executes garbage collection using a single continuous stop-the-world serial sweep", "Relies strictly on reference-counting without mark-sweep phases", "Allocates all objects directly to the metaspace"],
                0, "G1 splits heap memory into equal regions and collects regions with the most garbage first ('Garbage-First') within a user-defined pause-time target.", ["G1 GC", "Region-based memory"]),
            GeneratedQuestion("Java", "Concurrency & Thread Safety", "troubleshooting", "HARD",
                "In Java's java.util.concurrent ForkJoinPool, how does the Work-Stealing algorithm maximize CPU core utilization?",
                ["Idle worker threads steal pending subtasks from the tail of the double-ended queues (deques) of busy worker threads", "Worker threads steal memory heap space from other threads", "The main thread assigns every subtask sequentially", "Tasks are randomly migrated across OS processes"],
                0, "Work-stealing allows idle worker threads to take tasks from the deques of busy threads, preventing thread starvation and maximizing parallel CPU throughput.", ["ForkJoinPool", "Work-stealing"]),
            GeneratedQuestion("Java", "JVM Architecture & Memory Model", "troubleshooting", "HARD",
                "What is the key functional difference between PhantomReference and WeakReference in the java.lang.ref package?",
                ["PhantomReference.get() always returns null and is enqueued only after the object has been finalized and collected, used for pre-mortem cleanup tracking", "WeakReference objects are never collected by the Garbage Collector", "PhantomReference prevents the object from ever being collected", "WeakReference requires manual heap deallocation"],
                0, "PhantomReference's get() method always returns null; it is enqueued into ReferenceQueue after finalization to perform precise resource deallocation.", ["PhantomReference", "WeakReference", "GC lifecycle"])
        ],
        "DevOps": [
            # EASY (3)
            GeneratedQuestion("DevOps", "Containerization & Docker", "conceptual", "EASY",
                "What is the primary role of a Docker container compared to a traditional Virtual Machine (VM)?",
                ["Containers share the host OS kernel and isolate at the process level, making them lightweight and fast to start", "Containers virtualize physical hardware and require a dedicated guest OS kernel", "Containers cannot communicate across networks", "Containers are only used for database storage"],
                0, "Containers leverage OS kernel features (namespaces, cgroups) to provide process-level isolation without running a full guest OS.", ["Docker", "Containerization"]),
            GeneratedQuestion("DevOps", "CI/CD Pipelines & Automation", "conceptual", "EASY",
                "What is the main objective of Continuous Integration (CI) in a DevOps delivery lifecycle?",
                ["Automatically building and running automated test suites on every code commit to detect integration errors early", "Deploying software directly to end-users without staging tests", "Replacing version control systems with automated backups", "Manually approving pull requests once a month"],
                0, "Continuous Integration automates compiling, linting, and testing code on each commit to catch defects early.", ["CI/CD", "Continuous Integration"]),
            GeneratedQuestion("DevOps", "Infrastructure as Code (IaC)", "conceptual", "EASY",
                "What is the key principle of Declarative Infrastructure as Code (IaC) tools like Terraform?",
                ["Defining the desired target end-state of infrastructure and letting the tool compute execution steps", "Writing sequential shell commands to configure servers step-by-step", "Manually clicking buttons in a cloud provider console", "Executing code only on local developer machines"],
                0, "Declarative IaC defines the desired end-state; the engine creates and modifies resources to match that state.", ["IaC", "Declarative config"]),
            # INTERMEDIATE (4)
            GeneratedQuestion("DevOps", "CI/CD Pipelines & Automation", "scenario", "INTERMEDIATE",
                "In a zero-downtime deployment strategy, how does Blue-Green deployment eliminate service interruption during updates?",
                ["Maintains two identical production environments; routes live traffic from Blue (current) to Green (new) via load balancer once Green is verified", "Upgrades servers in place while taking the database offline", "Rolls out changes to all users simultaneously without health checks", "Runs older software version on weekends only"],
                0, "Blue-Green deployment provisions an identical environment, tests the new release, and switches router traffic instantaneously.", ["Blue-Green deployment", "Zero-downtime"]),
            GeneratedQuestion("DevOps", "Kubernetes & Container Orchestration", "troubleshooting", "INTERMEDIATE",
                "In Kubernetes, what is the purpose of a Liveness Probe versus a Readiness Probe on a Pod container?",
                ["Liveness probe checks if container is alive (restarts it if failed); Readiness probe checks if container is ready to accept network traffic", "Liveness probe inspects CPU temperature; Readiness probe monitors memory usage", "They are identical and execute the exact same container restarts", "Readiness probe deletes the Kubernetes namespace on failure"],
                0, "Liveness probes trigger container restarts if the app is deadlocked; Readiness probes remove the pod from Service endpoints until it is healthy.", ["Kubernetes", "Health probes"]),
            GeneratedQuestion("DevOps", "Monitoring, Logging & Observability", "conceptual", "INTERMEDIATE",
                "In modern cloud observability, what are the 'Three Pillars of Observability' used to diagnose distributed system health?",
                ["Metrics, Logs, and Distributed Traces", "CPU, RAM, and Disk Space", "Ping, Traceroute, and Telnet", "HTML, CSS, and JavaScript"],
                0, "Metrics (aggregates), Logs (discrete timestamped events), and Traces (request flow through microservices) form the core of observability.", ["Observability", "Metrics Logs Traces"]),
            GeneratedQuestion("DevOps", "Linux Fundamentals & Networking Security", "scenario", "INTERMEDIATE",
                "Why should production container Dockerfiles avoid running application processes as the 'root' user?",
                ["To prevent container breakout exploits from obtaining root privileges on the underlying host operating system", "Because root users cannot access network sockets", "Because root processes consume 10x more memory", "Because Docker will refuse to build images with root user"],
                0, "Running as a non-root UID restricts damage in the event of a container escape or remote code execution vulnerability.", ["Container security", "Principle of least privilege"]),
            # HARD (3)
            GeneratedQuestion("DevOps", "Kubernetes & Container Orchestration", "architecture", "HARD",
                "When configuring Kubernetes Pod horizontal scaling (HPA) alongside Cluster Autoscaler (CA), how is node provisioning triggered?",
                ["When pods enter 'Pending' status due to insufficient CPU/memory allocatable capacity on existing nodes", "When the master node CPU utilization exceeds 99%", "When Docker hub rate limits are reached", "When an administrator manually issues a kubectl scale command"],
                0, "Cluster Autoscaler watches for pods in Pending state caused by resource constraints and provisions new cloud nodes automatically.", ["Kubernetes HPA", "Cluster Autoscaler"]),
            GeneratedQuestion("DevOps", "CI/CD Pipelines & Automation", "troubleshooting", "HARD",
                "In GitOps architectures utilizing tools like ArgoCD or Flux, what mechanism prevents configuration drift between Git and live cluster state?",
                ["An automated reconciliation loop continuously compares Git manifests with live Kubernetes state and automatically syncs or alerts on discrepancies", "A manual webhook triggers git push on every commit", "A cron job restarts all Kubernetes pods every hour", "A database trigger drops out-of-sync clusters"],
                0, "GitOps controllers continuously reconcile live cluster state against the declared state stored in Git repositories.", ["GitOps", "ArgoCD", "Reconciliation loop"]),
            GeneratedQuestion("DevOps", "Infrastructure as Code (IaC)", "troubleshooting", "HARD",
                "How does Terraform state locking (e.g. using AWS DynamoDB with S3 backend) protect distributed engineering teams?",
                ["Prevents concurrent execution of terraform apply on the same state file, eliminating race conditions and corrupted resource states", "Encrypts Terraform code files with AES-256 on local disks", "Blocks all git commits to the repository while apply is running", "Deletes previous Terraform infrastructure versions automatically"],
                0, "State locking ensures only one process can mutate a Terraform state at a time, preventing state corruption from concurrent applies.", ["Terraform state locking", "Concurrency safety"])
        ],
        "Public Speaking": [
            # EASY (3)
            GeneratedQuestion("Public Speaking", "Speech Structure, Hooks & Storytelling", "conceptual", "EASY",
                "What is the primary function of a speech 'hook' in the opening 30 seconds of a presentation?",
                ["Capture the audience's immediate attention and establish relevance to their interests", "Recite the speaker's entire biography and resume", "Apologize for being nervous or unprepared", "Deliver the final call to action immediately"],
                0, "A hook (question, story, startling fact) grabs attention and motivates the audience to listen.", ["Speech hook", "Opening technique"]),
            GeneratedQuestion("Public Speaking", "Vocal Variety, Tone & Pacing", "conceptual", "EASY",
                "How does intentional pausing enhance the effectiveness of a speaker during a presentation?",
                ["Allows key points to resonate, creates anticipation, and replaces filler words like 'um' and 'ah'", "Fills time when the speaker forgets what to say", "Signals to the audience that the speech is over", "Allows the audience to leave the room"],
                0, "Strategic pauses emphasize key ideas, give the audience processing time, and eliminate filler words.", ["Pacing", "Intentional pauses"]),
            GeneratedQuestion("Public Speaking", "Body Language, Eye Contact & Stage Presence", "conceptual", "EASY",
                "What is the recommended technique for maintaining effective eye contact with a medium-to-large audience?",
                ["Holding eye contact with individual audience members for 3-5 seconds across different sections before shifting", "Staring continuously at the back wall above people's heads", "Scanning the room rapidly without focusing on anyone", "Looking down at notes for the majority of the time"],
                0, "Focusing on individuals for 3-5 seconds creates personal connection and conveys confidence across the room.", ["Eye contact", "Audience connection"]),
            # INTERMEDIATE (4)
            GeneratedQuestion("Public Speaking", "Speech Structure, Hooks & Storytelling", "scenario", "INTERMEDIATE",
                "When structuring a persuasive speech, what sequence does Monroe's Motivated Sequence follow?",
                ["Attention -> Need -> Satisfaction -> Visualization -> Action", "Introduction -> Body Paragraphs -> Counter-argument -> Conclusion", "Problem -> Reaction -> Solution -> Execution", "Hook -> Demonstration -> Pricing -> Close"],
                0, "Monroe's Motivated Sequence moves through Attention, Need, Satisfaction, Visualization, and Action to motivate change.", ["Monroe's Sequence", "Persuasion"]),
            GeneratedQuestion("Public Speaking", "Managing Speech Anxiety & Impromptu Speaking", "scenario", "INTERMEDIATE",
                "If asked an unexpected question in an impromptu speaking situation, which framework helps structure a coherent 1-minute response?",
                ["PREP framework (Point, Reason, Example, Point)", "Immediately changing the subject to something unrelated", "Speaking as fast as possible to finish early", "Saying whatever comes to mind without structure"],
                0, "The PREP framework (Point, Reason, Example, Point) provides instant logical structure for impromptu speaking.", ["PREP framework", "Impromptu speaking"]),
            GeneratedQuestion("Public Speaking", "Audience Analysis & Engagement", "scenario", "INTERMEDIATE",
                "How should a speaker adapt their presentation when addressing a non-technical executive audience on a complex technical project?",
                ["Focus on strategic business outcomes, ROI, and key trade-offs while abstracting low-level technical jargon", "Present all database schemas and code snippets in full detail", "Assume the executives already know all technical abbreviations", "Cancel the presentation and send a 50-page document instead"],
                0, "Executive audiences require focus on high-level impact, business value, risks, and actionable decisions.", ["Audience adaptation", "Executive communication"]),
            GeneratedQuestion("Public Speaking", "Handling Q&A & Challenging Questions", "situational_judgment", "INTERMEDIATE",
                "When faced with an aggressive or hostile question from an audience member, what is the best initial approach?",
                ["Acknowledge the core question neutrally, validate their perspective, and address the substantive issue without being defensive", "Argue back emotionally to assert authority", "Ignore the questioner and ask someone else to speak", "Walk off the stage immediately"],
                0, "De-escalating by maintaining neutral composure and focusing on facts preserves speaker credibility and audience respect.", ["Q&A handling", "Conflict management"]),
            # HARD (3)
            GeneratedQuestion("Public Speaking", "Speech Structure, Hooks & Storytelling", "scenario", "HARD",
                "In high-stakes keynote storytelling, what is the 'Sparkline' structure (conceptualized by Nancy Duarte) that characterizes memorable speeches like MLK's 'I Have a Dream'?",
                ["Alternating dynamically between 'What is' (the current flawed reality) and 'What could be' (the inspiring future vision)", "Delivering a linear chronological timeline from year 1 to present", "Presenting 20 disparate case studies in rapid succession", "Maintaining a single steady emotional tone throughout"],
                0, "The Sparkline contrasts current reality with future potential, creating cognitive tension and emotional resonance.", ["Duarte Sparkline", "Keynote architecture"]),
            GeneratedQuestion("Public Speaking", "Vocal Variety, Tone & Pacing", "situational_judgment", "HARD",
                "When delivering sensitive bad news (e.g. company restructuring) to a large organization, which vocal dynamic establishes trust and stability?",
                ["Grounded lower vocal pitch, deliberate cadence, warm resonance, and steady declarative inflection", "Rapid energetic delivery with high pitch to project excitement", "Monotone whisper to minimize attention to details", "Variable pitch rising at the end of every sentence like a question"],
                0, "A lower pitch, controlled pace, and declarative downward inflection convey calm leadership and psychological safety.", ["Vocal gravitas", "Crisis communication"]),
            GeneratedQuestion("Public Speaking", "Handling Q&A & Challenging Questions", "situational_judgment", "HARD",
                "If an audience member asks a critical factual question that you genuinely do not know the answer to, what response preserves the highest credibility?",
                ["Transparently state: 'I don't have that specific data point on hand, but I will verify it with our team and follow up with you today'", "Fabricate an approximate number with high confidence", "Deflect blame to another colleague in the room", "Dismiss the question as irrelevant to the presentation"],
                0, "Integrity in admitting unknown details while committing to follow-up builds lasting trust and authority.", ["Intellectual honesty", "Executive presence"])
        ],
        "Problem Solving": [
            # EASY (3)
            GeneratedQuestion("Problem Solving", "Problem Framing & Decomposition", "conceptual", "EASY",
                "What is the first critical step in structured problem solving before attempting to brainstorm solutions?",
                ["Clearly defining and framing the problem statement and its boundaries", "Implementing the first solution that comes to mind", "Assigning blame to team members", "Writing automated code scripts"],
                0, "Accurate problem definition prevents solving the wrong issue or addressing symptoms rather than root causes.", ["Problem definition", "Problem framing"]),
            GeneratedQuestion("Problem Solving", "Root Cause Analysis", "conceptual", "EASY",
                "What is the core technique of the '5 Whys' root cause analysis method?",
                ["Iteratively asking 'Why?' five consecutive times to drill down from the surface symptom to the underlying root cause", "Asking five different people their opinion on the problem", "Waiting five days before taking action", "Testing five random solutions simultaneously"],
                0, "The 5 Whys technique repeatedly interrogates cause-and-effect relationships until the root vulnerability is uncovered.", ["5 Whys", "Root cause"]),
            GeneratedQuestion("Problem Solving", "Decision Matrices & Trade-off Prioritization", "conceptual", "EASY",
                "What is the Pareto Principle (80/20 Rule) when applied to problem solving?",
                ["Roughly 80% of problems or consequences typically originate from 20% of critical causes", "80% of team members must agree on every decision", "Problems should be solved within 80 minutes 20% of the time", "All causes contribute equally to every problem"],
                0, "The Pareto Principle guides teams to focus efforts on the vital few causes that generate the majority of issues.", ["Pareto principle", "80/20 rule"]),
            # INTERMEDIATE (4)
            GeneratedQuestion("Problem Solving", "Root Cause Analysis", "scenario", "INTERMEDIATE",
                "When using an Ishikawa (Fishbone) Diagram to diagnose a manufacturing defect, what are the primary categories analyzed?",
                ["Methods, Machines, Materials, Measurements, Manpower (People), and Mother Nature (Environment)", "Software, Hardware, Firmware, Middleware, and Network", "Past, Present, Future, Ideal, and Reality", "Sales, Marketing, Finance, Legal, and HR"],
                0, "The 6Ms (Methods, Machines, Materials, Measurements, People, Environment) provide comprehensive root-cause categorization.", ["Ishikawa Fishbone", "Cause-and-effect"]),
            GeneratedQuestion("Problem Solving", "Hypothesis Testing & Validation", "scenario", "INTERMEDIATE",
                "In scientific problem solving, why is 'Confirmation Bias' a dangerous cognitive trap during hypothesis investigation?",
                ["It causes investigators to selectively seek out and overvalue evidence that supports their existing beliefs while ignoring contradictory facts", "It forces teams to confirm all hypotheses in writing", "It guarantees the first hypothesis is always correct", "It speeds up investigation time significantly"],
                0, "Confirmation bias leads to false conclusions by blinding practitioners to disconfirming evidence.", ["Confirmation bias", "Cognitive pitfalls"]),
            GeneratedQuestion("Problem Solving", "Decision Matrices & Trade-off Prioritization", "scenario", "INTERMEDIATE",
                "When evaluating three competing solution architectures against multiple weighted criteria (e.g. Cost, Speed, Reliability), which tool provides structured scoring?",
                ["Pugh Matrix / Weighted Decision Matrix", "Linear Regression Chart", "Gantt Chart", "Venn Diagram"],
                0, "A Weighted Decision Matrix scores competing options against weighted evaluation criteria for objective selection.", ["Weighted Decision Matrix", "Multi-criteria evaluation"]),
            GeneratedQuestion("Problem Solving", "Lateral Thinking & Solution Generation", "scenario", "INTERMEDIATE",
                "What is the objective of 'First Principles Thinking' popularized by physicists and innovators?",
                ["Breaking down a complex problem to its fundamental fundamental truths that cannot be deduced any further, then reasoning up from there", "Copying existing industry solutions and making minor tweaks", "Relying strictly on historical precedent and convention", "Outsourcing decision making to third-party consultants"],
                0, "First principles thinking discards analogical thinking and rebuilds solutions from bedrock physical or logical truths.", ["First principles", "Deconstruction"]),
            # HARD (3)
            GeneratedQuestion("Problem Solving", "Problem Framing & Decomposition", "scenario", "HARD",
                "In systems thinking, what characterizes a 'Second-Order Effect' when implementing an intervention in a complex adaptive system?",
                ["The indirect, unintended consequences and downstream feedback loops that emerge after the direct first-order effect occurs", "The secondary backup plan if the first plan fails", "A minor cosmetic bug in a software interface", "A decision approved by the second-in-command leader"],
                0, "Second-order thinking anticipates the cascading chain of reactions and incentives set in motion by an initial action.", ["Second-order thinking", "Systems dynamics"]),
            GeneratedQuestion("Problem Solving", "Execution Planning & Risk Mitigation", "scenario", "HARD",
                "What is the purpose of conducting a 'Pre-Mortem' exercise before launching a major strategic initiative?",
                ["Assuming the project has already completely failed in the future, and working backwards to identify all plausible failure vectors in advance", "Analyzing why a past project failed after completion", "Conducting performance reviews after a product release", "Writing celebration speeches before project kickoff"],
                0, "A Pre-Mortem creates psychological safety for team members to identify vulnerabilities and mitigate them before execution begins.", ["Pre-mortem analysis", "Proactive risk mitigation"]),
            GeneratedQuestion("Problem Solving", "Decision Matrices & Trade-off Prioritization", "scenario", "HARD",
                "When navigating high-uncertainty decisions under the Cynefin Framework, what is the appropriate approach for 'Complex' domains?",
                ["Probe -> Sense -> Respond (Conduct safe-to-fail experiments to discover emergent patterns)", "Sense -> Categorize -> Respond (Apply known best practices)", "Act -> Sense -> Respond (Immediately establish stability in chaos)", "Do nothing and wait for complete information"],
                0, "In Complex domains with no clear cause-and-effect, practitioners must probe through small experiments, sense results, and respond adaptively.", ["Cynefin framework", "Complex domain strategy"])
        ]
    }

    @classmethod
    def get_bank(cls, canonical_name: str) -> Optional[List[GeneratedQuestion]]:
        return cls.BANKS.get(canonical_name)


class SkillEngine:
    """Unified Orchestrator: Normalizes skills, builds profiles, generates blueprints, and validates questions."""

    @classmethod
    def generate_assessment_for_skill(cls, skill_name: str) -> List[GeneratedQuestion]:
        profile = SkillProfiler.get_profile(skill_name)
        seen_texts: Set[str] = set()
        final_questions: List[GeneratedQuestion] = []

        # 1. Check if domain bank exists for canonical skill
        bank = DomainQuestionBank.get_bank(profile.canonical_name)
        if bank:
            for q in bank:
                validation = QuestionValidator.validate_question(q, profile, seen_texts)
                if validation.is_valid:
                    final_questions.append(q)

        # 2. If questions still needed (or for custom/unknown skill), generate blueprint-driven questions
        if len(final_questions) < 10:
            generated = cls._synthesize_blueprint_questions(profile, needed=10 - len(final_questions), seen_texts=seen_texts)
            for q in generated:
                val = QuestionValidator.validate_question(q, profile, seen_texts)
                if val.is_valid:
                    final_questions.append(q)
                if len(final_questions) >= 10:
                    break

        # 3. Sort strictly by difficulty: 3 Easy -> 4 Intermediate -> 3 Hard
        diff_order = {"EASY": 1, "BEGINNER": 1, "INTERMEDIATE": 2, "MEDIUM": 2, "ADVANCED": 3, "HARD": 3}
        final_questions.sort(key=lambda q: diff_order.get(q.difficulty.upper(), 2))
        return final_questions[:10]

    @classmethod
    def _synthesize_blueprint_questions(
        cls,
        profile: SkillProfile,
        needed: int,
        seen_texts: Set[str]
    ) -> List[GeneratedQuestion]:
        """Synthesizes structured, high-relevance domain questions matching the skill's knowledge areas."""
        questions: List[GeneratedQuestion] = []
        k_areas = profile.knowledge_areas if profile.knowledge_areas else [f"Core {profile.canonical_name}"]
        skill_name = profile.canonical_name

        # Blueprint templates
        blueprint_specs = [
            # Easy
            ("EASY", "conceptual", k_areas[0 % len(k_areas)],
             f"What is the foundational definition and primary role of {k_areas[0 % len(k_areas)]} in {skill_name}?",
             [f"It provides the foundational framework and core discipline for {skill_name}",
              f"It is a legacy backup mechanism with no active utility in {skill_name}",
              "It is an obsolete hardware protocol",
              "It represents an experimental unverified draft specification"],
             0,
             f"{k_areas[0 % len(k_areas)]} establishes the core structural principles required for {skill_name}.",
             ["Foundations", "Core Principles"]),

            ("EASY", "conceptual", k_areas[1 % len(k_areas)],
             f"Which of the following represents an essential industry best practice when executing {k_areas[1 % len(k_areas)]}?",
             ["Adhering to standardized conventions, modular design, and proactive validation",
              "Hardcoding environment-specific secrets and values directly",
              "Bypassing verification checks and skipping error logging",
              "Eliminating documentation and avoiding version tracking"],
             0,
             f"Standardized conventions and structured validation ensure consistency and reliability in {k_areas[1 % len(k_areas)]}.",
             ["Best Practices", "Standardization"]),

            ("EASY", "conceptual", k_areas[2 % len(k_areas)],
             f"What primary benefit is achieved by properly mastering {k_areas[2 % len(k_areas)]} in {skill_name}?",
             ["Higher quality execution, reduced error rates, and maintainable output",
              "Increased system memory leakage and redundant processing overhead",
              "Degraded execution speed and unreadable project structures",
              "Incompatibility with modern industry standards"],
             0,
             f"Proficiency in {k_areas[2 % len(k_areas)]} directly drives quality, throughput, and sustainability.",
             ["Quality Assurance", "Maintainability"]),

            # Intermediate
            ("INTERMEDIATE", "scenario", k_areas[3 % len(k_areas)],
             f"When optimizing performance and resource utilization within {k_areas[3 % len(k_areas)]}, which strategy is most effective?",
             ["Identifying bottlenecks through metric profiling, decoupling dependencies, and implementing targeted caching",
              "Adding redundant nested loops to consume available clock cycles",
              "Disabling health monitoring and suppressing all alerts",
              "Overwriting data structures without validation"],
             0,
             f"Effective optimization in {k_areas[3 % len(k_areas)]} requires objective profiling, targeted caching, and modular decoupling.",
             ["Optimization", "Profiling"]),

            ("INTERMEDIATE", "troubleshooting", k_areas[4 % len(k_areas)],
             f"In {k_areas[4 % len(k_areas)]}, how should unexpected edge cases, anomalies, and failures be systematically managed?",
             ["By implementing graceful degradation, structured fallback handling, and actionable diagnostic logs",
              "By silently swallowing all errors and continuing execution in an undefined state",
              "By crashing the entire system without preserving state or log traces",
              "By hardcoding static null responses for all operations"],
             0,
             f"Robust engineering in {k_areas[4 % len(k_areas)]} requires graceful degradation and explicit diagnostic logging.",
             ["Error Handling", "Resilience"]),

            ("INTERMEDIATE", "scenario", k_areas[5 % len(k_areas)],
             f"What is the primary architectural trade-off when designing for high modularity in {k_areas[5 % len(k_areas)]}?",
             ["Improved isolation and testability at the expense of slight interface coordination complexity",
              "Total loss of system security and corrupted data states",
              "Inability to unit-test individual components",
              "Permanent coupling between unrelated system sub-modules"],
             0,
             "Modular architectures improve testability, maintenance, and isolation while introducing minor boundary interface coordination.",
             ["Modularity", "Trade-off analysis"]),

            ("INTERMEDIATE", "conceptual", k_areas[0 % len(k_areas)],
             f"Which metric is most critical for evaluating operational success in {k_areas[0 % len(k_areas)]} within {skill_name}?",
             ["Correctness, execution reliability, and long-term maintainability",
              "Arbitrary volume of superficial lines or characters generated",
              "The specific color theme of the practitioner's workspace",
              "The file size of the project README document"],
             0,
             "Operational success is measured by correctness, reliability, safety, and sustainable maintainability.",
             ["Quality Metrics", "Success Criteria"]),

            # Hard
            ("HARD", "architecture", k_areas[1 % len(k_areas)],
             f"In advanced high-throughput environments, how do senior practitioners resolve concurrency and scale bottlenecks in {k_areas[1 % len(k_areas)]}?",
             ["By utilizing asynchronous event pipelines, distributed workload partitioning, and non-blocking I/O",
              "By enforcing strictly synchronous single-threaded global lock contention",
              "By eliminating indexes and disabling data persistence mechanisms",
              "By increasing global lock timeouts indefinitely"],
             0,
             f"Scalability in {k_areas[1 % len(k_areas)]} is achieved via async event loops, workload distribution, and non-blocking boundaries.",
             ["High Concurrency", "Workload Partitioning"]),

            ("HARD", "troubleshooting", k_areas[2 % len(k_areas)],
             f"In complex {skill_name} architectures, what is the primary structural risk of unmanaged state mutations and tight coupling in {k_areas[2 % len(k_areas)]}?",
             ["Cascading side-effects, fragile regression testing, and unpredictable runtime failures under load",
              "Excessive code documentation and comments",
              "Faster compile-time execution and smaller memory footprints",
              "Automatic memory deallocation by the operating system"],
             0,
             "Tight coupling and mutable shared state lead to hard-to-trace cascading side-effects and system fragility.",
             ["State Mutation", "Coupling Risks"]),

            ("HARD", "scenario", k_areas[3 % len(k_areas)],
             f"What is the recommended governance strategy for managing breaking version migrations and backward compatibility in {k_areas[3 % len(k_areas)]}?",
             ["Implementing semantic versioning, clear deprecation schedules, and progressive migration pathways",
              "Instantly removing legacy interfaces without advance deprecation notice",
              "Modifying core interface contracts silently across minor patches",
              "Deleting historical version tags and schema migration logs"],
             0,
             "Semantic versioning and structured deprecation pathways ensure non-breaking, predictable ecosystem evolution.",
             ["Semantic Versioning", "Migration Safety"])
        ]

        for diff, q_type, k_area, q_text, opts, correct, exp, concepts in blueprint_specs:
            q = GeneratedQuestion(
                skill=skill_name,
                knowledge_area=k_area,
                question_type=q_type,
                difficulty=diff,
                question_text=q_text,
                options=opts,
                correct_option=correct,
                explanation=exp,
                expected_concepts=concepts
            )
            questions.append(q)

        return questions
