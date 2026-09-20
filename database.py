import json
from models import db, User, Subject, Topic, StudyMaterial, MaterialChunk, Quiz, QuizQuestion, QuizAttempt


def chunk_text(text, chunk_size=350, overlap=50):
    """Split text into overlapping word chunks for RAG."""
    words = text.split()
    chunks = []
    if not words:
        return chunks

    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def init_db(app):
    with app.app_context():
        db.create_all()
        seed_data()


def seed_data():
    # Only seed if no subjects exist
    if Subject.query.first() is not None:
        return

    print("[Database] Seeding initial academic curriculum, notes, and quizzes...")

    # 1. Users
    admin = User(
        username="admin",
        email="admin@tutor.ai",
        role="admin",
        learning_level="advanced",
        explanation_style="detailed",
    )
    admin.set_password("admin123")
    db.session.add(admin)

    student = User(
        username="student",
        email="student@tutor.ai",
        role="student",
        learning_level="intermediate",
        explanation_style="detailed",
    )
    student.set_password("student123")
    db.session.add(student)
    db.session.commit()

    # 2. Subjects, Topics, Study Materials, and Quizzes

    # =========================================================================
    # SUBJECT 1: OPERATING SYSTEMS
    # =========================================================================
    os_sub = Subject(
        name="Operating Systems",
        code="CS301",
        icon="cpu",
        description="Core concepts of modern operating systems including processes, memory management, scheduling, concurrency, and virtual memory.",
    )
    db.session.add(os_sub)
    db.session.flush()

    top_os_proc = Topic(
        subject_id=os_sub.id,
        name="Process Management & CPU Scheduling",
        description="Processes vs threads, Process Control Block (PCB), context switching, and scheduling algorithms.",
        order=1,
    )
    top_os_mem = Topic(
        subject_id=os_sub.id,
        name="Memory Management & Virtual Memory",
        description="Logical vs physical address space, paging, segmentation, TLB, page replacement, and thrashing.",
        order=2,
    )
    top_os_dead = Topic(
        subject_id=os_sub.id,
        name="Deadlocks & Concurrency Control",
        description="The four Coffman conditions, Banker's Algorithm, semaphores, mutexes, and critical sections.",
        order=3,
    )
    db.session.add_all([top_os_proc, top_os_mem, top_os_dead])
    db.session.flush()

    # OS Materials
    mat_os_1 = StudyMaterial(
        subject_id=os_sub.id,
        topic_id=top_os_proc.id,
        title="Comprehensive Guide to Process Management and Scheduling",
        content="""# Process Management & CPU Scheduling

A **Process** is defined as an active program in execution. Unlike a passive program stored on a storage drive, a process contains state, program counter, stack, data section, and registers.

### 1. Process Control Block (PCB)
Each process is represented in the operating system by a Process Control Block (PCB). The PCB contains:
- **Process ID (PID)**: Unique numerical identifier.
- **Process State**: New, Ready, Running, Waiting (Blocked), or Terminated.
- **Program Counter (PC)**: Memory address of the next machine instruction to be executed.
- **CPU Registers**: Accumulators, index registers, stack pointers, and general-purpose registers.
- **CPU Scheduling Information**: Process priority and scheduling queue pointers.
- **Memory Management Information**: Base and limit registers, page tables, or segment tables.
- **Accounting & I/O Status**: Accumulated CPU execution time, opened files, and allocated I/O devices.

### 2. Context Switching
Context switching is the mechanism of saving the state of the currently executing process and loading the saved state of another process so that CPU execution can resume seamlessly. The time spent during context switching is pure overhead because the CPU performs no useful computational work.

### 3. CPU Scheduling Algorithms
The CPU scheduler selects a process from the Ready Queue according to a scheduling discipline:
- **First-Come, First-Served (FCFS)**: Non-preemptive. Simple FIFO queue. Suffers from the **Convoy Effect**, where short processes wait behind a long CPU-burst process.
- **Shortest Job First (SJF)**: Selects process with smallest next CPU burst. Optimal for minimizing average turnaround time, but requires predicting future CPU bursts and can cause starvation for long jobs.
- **Round Robin (RR)**: Preemptive scheduling designed for time-sharing systems. Each process is allocated a fixed slice of CPU time called a **Time Quantum** (typically 10-100 ms). If the process burst exceeds the quantum, it is pre-empted and moved to the tail of the Ready Queue.
- **Priority Scheduling**: CPU is assigned to the process with the highest priority. Can lead to starvation (solved via **Aging**, where priority gradually increases as waiting time increases).""",
        summary="Overview of Process concepts, PCB components, context switching costs, and CPU scheduling algorithms (FCFS, SJF, Round Robin).",
    )

    mat_os_2 = StudyMaterial(
        subject_id=os_sub.id,
        topic_id=top_os_mem.id,
        title="Memory Management, Paging, and Virtual Memory",
        content="""# Memory Management & Virtual Memory

Memory management enables an operating system to allocate physical RAM dynamically among executing processes while providing memory protection and isolation.

### 1. Logical vs Physical Address Space
- **Logical Address (Virtual Address)**: Generated by the CPU during program execution.
- **Physical Address**: The actual hardware memory address loaded into the memory address register (MAR) of RAM.
- **Memory Management Unit (MMU)**: Hardware device that maps virtual addresses to physical addresses at runtime.

### 2. Paging Mechanism
Paging is a memory-management scheme that eliminates the need for contiguous physical memory allocation:
- Physical memory is broken down into fixed-sized blocks called **Frames** (commonly 4 KB).
- Logical memory is divided into blocks of the exact same size called **Pages**.
- A **Page Table** maps each logical page number ($p$) to a physical frame number ($f$).
- **Offset ($d$)**: Specifies the exact byte within the page/frame and remains unchanged during address translation.
- **Translation Lookaside Buffer (TLB)**: High-speed associative hardware cache that stores recent page-to-frame translations to avoid multiple RAM lookups.

### 3. Virtual Memory & Page Faults
Virtual memory allows execution of processes that are not completely loaded into physical memory:
- **Demand Paging**: Pages are loaded into RAM only when referenced during program execution.
- **Page Fault**: An interrupt raised by hardware when a program accesses a page marked invalid (not currently in RAM). The OS traps to kernel mode, finds a free frame, reads the page from swap disk, updates the page table, and restarts the instruction.
- **Thrashing**: Occurs when the system spends more time servicing page faults and swapping than executing actual application code, typically because physical RAM is overcommitted.""",
        summary="Memory hierarchy, MMU translation, paging vs frames, TLB caching, demand paging, and thrashing.",
    )
    db.session.add_all([mat_os_1, mat_os_2])
    db.session.flush()

    # OS Quiz
    quiz_os = Quiz(
        subject_id=os_sub.id,
        topic_id=top_os_proc.id,
        title="Operating Systems: Process & Memory Mastery",
        description="Evaluate your knowledge of CPU scheduling, PCB structures, paging, and virtual memory.",
        difficulty="medium",
        time_limit_mins=10,
    )
    db.session.add(quiz_os)
    db.session.flush()

    q_os_1 = QuizQuestion(
        quiz_id=quiz_os.id,
        question_text="Which CPU scheduling algorithm gives the theoretical minimum average waiting time for a given set of processes?",
        option_a="First-Come, First-Served (FCFS)",
        option_b="Round Robin (RR)",
        option_c="Shortest Job First (SJF)",
        option_d="Priority Scheduling without Preemption",
        correct_option="C",
        explanation="Shortest Job First (SJF) is provably optimal because scheduling the process with the shortest burst time first minimizes total cumulative waiting time.",
    )
    q_os_2 = QuizQuestion(
        quiz_id=quiz_os.id,
        question_text="What hardware component speeds up virtual-to-physical address translation by caching recent page table entries?",
        option_a="Direct Memory Access (DMA)",
        option_b="Translation Lookaside Buffer (TLB)",
        option_c="Program Counter (PC)",
        option_d="Accumulator Register",
        correct_option="B",
        explanation="The Translation Lookaside Buffer (TLB) is a fast associative cache within the MMU that stores recent page-table mappings, reducing memory access latency.",
    )
    q_os_3 = QuizQuestion(
        quiz_id=quiz_os.id,
        question_text="What phenomenon describes a condition where the OS spends significantly more time swapping pages into RAM than executing instructions?",
        option_a="Convoy Effect",
        option_b="Deadlock",
        option_c="Starvation",
        option_d="Thrashing",
        correct_option="D",
        explanation="Thrashing happens when the working set of all active processes exceeds physical memory, causing continuous page faults and severe CPU utilization drop.",
    )
    q_os_4 = QuizQuestion(
        quiz_id=quiz_os.id,
        question_text="Which of the following is NOT stored inside the Process Control Block (PCB)?",
        option_a="Program Counter",
        option_b="Source Code file contents",
        option_c="CPU Register states",
        option_d="Process State",
        correct_option="B",
        explanation="The PCB stores management metadata like PID, state, PC, and registers. The actual code resides in the process memory address space (Text segment).",
    )
    q_os_5 = QuizQuestion(
        quiz_id=quiz_os.id,
        question_text="How can starvation in priority scheduling be systematically prevented?",
        option_a="Using shorter time quantums",
        option_b="Aging technique (gradually increasing priority of waiting processes)",
        option_c="Converting to non-preemptive FCFS",
        option_d="Doubling physical RAM",
        correct_option="B",
        explanation="Aging prevents indefinite blocking (starvation) by progressively increasing the priority of processes that wait in the ready queue for prolonged periods.",
    )
    db.session.add_all([q_os_1, q_os_2, q_os_3, q_os_4, q_os_5])

    # =========================================================================
    # SUBJECT 2: DATA STRUCTURES & ALGORITHMS
    # =========================================================================
    dsa_sub = Subject(
        name="Data Structures & Algorithms",
        code="CS201",
        icon="code",
        description="Fundamental linear and non-linear data structures, asymptotic time complexity, recursion, and algorithm design paradigms.",
    )
    db.session.add(dsa_sub)
    db.session.flush()

    top_dsa_1 = Topic(
        subject_id=dsa_sub.id,
        name="Asymptotic Analysis & Linear Structures",
        description="Big-O notation, Dynamic Arrays, Singly/Doubly Linked Lists, Stacks (LIFO), and Queues (FIFO).",
        order=1,
    )
    top_dsa_2 = Topic(
        subject_id=dsa_sub.id,
        name="Trees, Heaps & Graph Traversal",
        description="Binary Search Trees (BST), AVL trees, Min/Max Binary Heaps, Breadth-First Search (BFS), and Depth-First Search (DFS).",
        order=2,
    )
    db.session.add_all([top_dsa_1, top_dsa_2])
    db.session.flush()

    mat_dsa_1 = StudyMaterial(
        subject_id=dsa_sub.id,
        topic_id=top_dsa_1.id,
        title="Comprehensive Notes on Big-O and Linear Structures",
        content="""# Asymptotic Notation & Linear Data Structures

### 1. Asymptotic Complexity (Big-O Notation)
Big-O characterizes the growth rate of an algorithm's execution time or memory footprint as input size $n$ approaches infinity:
- $O(1)$: Constant time (e.g., hash map lookup, array index access).
- $O(\\log n)$: Logarithmic time (e.g., binary search on sorted array).
- $O(n)$: Linear time (e.g., linear search).
- $O(n \\log n)$: Linearithmic time (e.g., Merge Sort, Heap Sort).
- $O(n^2)$: Quadratic time (e.g., Bubble Sort, Insertion Sort).

### 2. Arrays vs Linked Lists
- **Array**: Contiguous block of memory. Fast random access ($O(1)$ by index). Insertions or deletions in the middle require shifting elements ($O(n)$).
- **Linked List**: Dispersed nodes containing data and pointers. Dynamic sizing. Sequential access ($O(n)$). Insertions/deletions at known node references take $O(1)$ time.

### 3. Stacks & Queues
- **Stack (LIFO - Last In, First Out)**: Supported operations: `push(x)` ($O(1)$) and `pop()` ($O(1)$). Used in call stack execution, undo mechanisms, and parsing balanced parentheses.
- **Queue (FIFO - First In, First Out)**: Supported operations: `enqueue(x)` ($O(1)$) and `dequeue()` ($O(1)$). Used in CPU process scheduling and Breadth-First Search (BFS) graph traversal.""",
        summary="Big-O asymptotic classification, Arrays vs Linked Lists trade-offs, and Stack (LIFO) vs Queue (FIFO) mechanics.",
    )
    db.session.add(mat_dsa_1)
    db.session.flush()

    quiz_dsa = Quiz(
        subject_id=dsa_sub.id,
        topic_id=top_dsa_1.id,
        title="DSA: Complexity & Fundamental Structures",
        description="Test your grasp of Big-O complexity, tree properties, and queue/stack applications.",
        difficulty="medium",
        time_limit_mins=10,
    )
    db.session.add(quiz_dsa)
    db.session.flush()

    q_dsa_1 = QuizQuestion(
        quiz_id=quiz_dsa.id,
        question_text="What is the average and worst-case time complexity of finding an element in a balanced Binary Search Tree (AVL / Red-Black)?",
        option_a="Average O(1), Worst O(n)",
        option_b="Average O(log n), Worst O(log n)",
        option_c="Average O(n), Worst O(n log n)",
        option_d="Average O(log n), Worst O(n)",
        correct_option="B",
        explanation="In self-balancing binary search trees (AVL or Red-Black), tree height is strictly maintained at O(log n), guaranteeing both average and worst-case search times of O(log n).",
    )
    q_dsa_2 = QuizQuestion(
        quiz_id=quiz_dsa.id,
        question_text="Which data structure is fundamentally utilized to implement Breadth-First Search (BFS) on a graph?",
        option_a="Stack",
        option_b="Priority Queue",
        option_c="Queue (FIFO)",
        option_d="Binary Heap",
        correct_option="C",
        explanation="Breadth-First Search explores vertices level by level using a FIFO Queue to ensure closer neighbors are processed before moving deeper.",
    )
    q_dsa_3 = QuizQuestion(
        quiz_id=quiz_dsa.id,
        question_text="What is the time complexity of building a Binary Heap of size N from an unsorted array of N elements using Floyd's build-heap algorithm?",
        option_a="O(N log N)",
        option_b="O(N)",
        option_c="O(N^2)",
        option_d="O(log N)",
        correct_option="B",
        explanation="Bottom-up heap construction (sift-down on internal nodes) runs in linear O(N) time due to the converging summation of node depths and heights.",
    )
    q_dsa_4 = QuizQuestion(
        quiz_id=quiz_dsa.id,
        question_text="Which sorting algorithm is stable and guarantees O(N log N) worst-case time complexity?",
        option_a="Quick Sort",
        option_b="Heap Sort",
        option_c="Merge Sort",
        option_d="Selection Sort",
        correct_option="C",
        explanation="Merge Sort always divides and merges in O(N log N) time in all cases (best, average, worst) and maintains relative ordering of duplicate keys (stability).",
    )
    q_dsa_5 = QuizQuestion(
        quiz_id=quiz_dsa.id,
        question_text="What is the primary condition required to solve an optimization problem using Dynamic Programming?",
        option_a="Sorted input data and unique keys",
        option_b="Optimal substructure and overlapping subproblems",
        option_c="Greedy choice property with monotonic growth",
        option_d="Linear dependencies between elements",
        correct_option="B",
        explanation="Dynamic Programming is applicable when a problem exhibits both Optimal Substructure (optimal global solution comes from optimal sub-solutions) and Overlapping Subproblems.",
    )
    db.session.add_all([q_dsa_1, q_dsa_2, q_dsa_3, q_dsa_4, q_dsa_5])

    # =========================================================================
    # SUBJECT 3: DATABASE MANAGEMENT SYSTEMS
    # =========================================================================
    dbms_sub = Subject(
        name="Database Management Systems",
        code="CS302",
        icon="database",
        description="Relational database design, SQL querying, schema normalization (1NF to BCNF), and transaction processing with ACID.",
    )
    db.session.add(dbms_sub)
    db.session.flush()

    top_dbms_1 = Topic(
        subject_id=dbms_sub.id,
        name="Relational Model & Normalization",
        description="Primary/Foreign keys, functional dependencies, 1NF, 2NF, 3NF, and Boyce-Codd Normal Form (BCNF).",
        order=1,
    )
    top_dbms_2 = Topic(
        subject_id=dbms_sub.id,
        name="Transactions, Concurrency & ACID",
        description="ACID properties, serializability, two-phase locking (2PL), write-ahead logging (WAL), and isolation levels.",
        order=2,
    )
    db.session.add_all([top_dbms_1, top_dbms_2])
    db.session.flush()

    mat_dbms_1 = StudyMaterial(
        subject_id=dbms_sub.id,
        topic_id=top_dbms_1.id,
        title="Mastering Database Normalization & ACID Properties",
        content="""# Database Normalization & Transaction Processing

### 1. Database Normalization
Normalization is the process of organizing data in a relational database to reduce data redundancy and eliminate insert, update, and delete anomalies.
- **First Normal Form (1NF)**: All column values must be atomic (no repeating groups, arrays, or comma-separated lists).
- **Second Normal Form (2NF)**: Must be in 1NF and have NO Partial Dependencies (all non-key attributes must be fully functionally dependent on the entire primary key).
- **Third Normal Form (3NF)**: Must be in 2NF and have NO Transitive Dependencies ($A \\to B$ and $B \\to C$ where $C$ depends on $A$ through $B$).
- **Boyce-Codd Normal Form (BCNF)**: For every functional dependency $X \\to Y$, $X$ must be a super key.

### 2. ACID Properties of Transactions
A database transaction is a logical unit of work executed against a database.
- **Atomicity (All-or-Nothing)**: The transaction either executes completely or is entirely rolled back. Managed via transaction logs / rollback segments.
- **Consistency**: The database transitions from one valid consistent state satisfying all integrity constraints to another valid state.
- **Isolation**: Concurrent execution of transactions yields the same database state as if they were executed serially. Controlled via isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable).
- **Durability**: Once a transaction is committed, its modifications persist permanently even in the event of system crashes or power failures. Ensured using Write-Ahead Logging (WAL).""",
        summary="Detailed breakdown of 1NF, 2NF, 3NF, BCNF rules and comprehensive ACID transaction properties.",
    )
    db.session.add(mat_dbms_1)
    db.session.flush()

    quiz_dbms = Quiz(
        subject_id=dbms_sub.id,
        topic_id=top_dbms_1.id,
        title="DBMS: Normalization and Transactions Challenge",
        description="Validate your understanding of database normal forms, ACID guarantees, and SQL concurrency.",
        difficulty="medium",
        time_limit_mins=10,
    )
    db.session.add(quiz_dbms)
    db.session.flush()

    q_dbms_1 = QuizQuestion(
        quiz_id=quiz_dbms.id,
        question_text="A relation where a non-prime attribute depends on only a portion of a composite candidate key violates which normal form?",
        option_a="First Normal Form (1NF)",
        option_b="Second Normal Form (2NF)",
        option_c="Third Normal Form (3NF)",
        option_d="Fourth Normal Form (4NF)",
        correct_option="B",
        explanation="2NF requires eliminating partial dependencies where non-key attributes depend on only part of a composite primary key.",
    )
    q_dbms_2 = QuizQuestion(
        quiz_id=quiz_dbms.id,
        question_text="Which ACID property ensures that committed transactions survive subsequent hardware crashes or power cuts?",
        option_a="Atomicity",
        option_b="Consistency",
        option_c="Isolation",
        option_d="Durability",
        correct_option="D",
        explanation="Durability guarantees that once a transaction commits, its changes are written to non-volatile storage (via Write-Ahead Logging) and will not be lost.",
    )
    q_dbms_3 = QuizQuestion(
        quiz_id=quiz_dbms.id,
        question_text="What is the strictest SQL transaction isolation level that completely prevents dirty reads, non-repeatable reads, and phantom reads?",
        option_a="Read Uncommitted",
        option_b="Read Committed",
        option_c="Repeatable Read",
        option_d="Serializable",
        correct_option="D",
        explanation="Serializable isolation ensures transactions execute as if strictly serialized one after another, eliminating all concurrency anomalies.",
    )
    q_dbms_4 = QuizQuestion(
        quiz_id=quiz_dbms.id,
        question_text="In BCNF, for every functional dependency X -> Y, what must X be?",
        option_a="A prime attribute",
        option_b="A Super Key",
        option_c="A Foreign Key",
        option_d="An atomic attribute",
        correct_option="B",
        explanation="Boyce-Codd Normal Form requires that in every non-trivial functional dependency X -> Y, determinant X must be a super key.",
    )
    q_dbms_5 = QuizQuestion(
        quiz_id=quiz_dbms.id,
        question_text="What data structure is standardly used by relational database engines for table B-tree indexes?",
        option_a="B+ Tree",
        option_b="Binary Search Tree",
        option_c="Red-Black Tree",
        option_d="Trie",
        correct_option="A",
        explanation="B+ Trees are universally used for database indexing because internal nodes store only routing keys, while leaf nodes contain all data records linked sequentially for fast range scans.",
    )
    db.session.add_all([q_dbms_1, q_dbms_2, q_dbms_3, q_dbms_4, q_dbms_5])

    # =========================================================================
    # SUBJECT 4: ARTIFICIAL INTELLIGENCE & MACHINE LEARNING
    # =========================================================================
    ai_sub = Subject(
        name="AI & Machine Learning",
        code="CS401",
        icon="brain",
        description="Principles of artificial intelligence, search algorithms, supervised/unsupervised machine learning, neural networks, and LLM transformers.",
    )
    db.session.add(ai_sub)
    db.session.flush()

    top_ai_1 = Topic(
        subject_id=ai_sub.id,
        name="AI Search & Machine Learning Fundamentals",
        description="Heuristic search, A* algorithm, Supervised vs Unsupervised learning, overfitting, bias-variance tradeoff.",
        order=1,
    )
    top_ai_2 = Topic(
        subject_id=ai_sub.id,
        name="Deep Learning & Transformer Models",
        description="Multi-layer Perceptrons, backpropagation, Self-Attention mechanism, Transformer encoders/decoders, and RAG.",
        order=2,
    )
    db.session.add_all([top_ai_1, top_ai_2])
    db.session.flush()

    mat_ai_1 = StudyMaterial(
        subject_id=ai_sub.id,
        topic_id=top_ai_1.id,
        title="Foundations of Artificial Intelligence & Machine Learning",
        content="""# Foundations of AI & Machine Learning

### 1. What is Artificial Intelligence?
Artificial Intelligence (AI) is the branch of computer science focused on creating systems capable of performing tasks that traditionally require human intelligence. These tasks include logical reasoning, knowledge representation, planning, learning, natural language processing, and perception.

### 2. Machine Learning Paradigms
- **Supervised Learning**: Model trains on labeled dataset $(X, y)$ to learn mapping function $f(X) \\approx y$. Subdivided into:
  - *Classification*: Categorical target output (e.g., spam detection, image classification).
  - *Regression*: Continuous numerical target output (e.g., house price forecasting).
- **Unsupervised Learning**: Model detects hidden patterns, distributions, or groupings in unlabeled data $(X)$. Includes clustering ($k$-Means, DBSCAN) and dimensionality reduction (PCA).
- **Reinforcement Learning (RL)**: An agent learns optimal action policies through reward-penalty interactions with an environment (Markov Decision Process).

### 3. Bias-Variance Tradeoff
- **High Bias (Underfitting)**: Model is overly simplistic and fails to capture genuine relationships in the training data.
- **High Variance (Overfitting)**: Model memorizes training noise and generalizes poorly to unseen test data.
- **Remedies for Overfitting**: Regularization ($L_1$ Lasso, $L_2$ Ridge), cross-validation, dropout in neural networks, and increasing training dataset size.

### 4. Transformer Architectures & Retrieval-Augmented Generation (RAG)
Modern large language models are built on the **Transformer** architecture introduced in "Attention Is All You Need" (Vaswani et al., 2017).
- **Self-Attention**: Calculates attention weights between all token pairs in a sequence using Query ($Q$), Key ($K$), and Value ($V$) matrices:
  $$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V$$
- **Retrieval-Augmented Generation (RAG)**: RAG combines an external knowledge retrieval mechanism with a generative language model. Instead of relying solely on the static weights of the LLM, the system dynamically searches verified reference documents, injects the retrieved context into the prompt, and generates grounded, factual answers with source citations.""",
        summary="Comprehensive review of AI definitions, Supervised vs Unsupervised ML, Bias-Variance tradeoff, Self-Attention mechanism, and RAG architecture.",
    )
    db.session.add(mat_ai_1)
    db.session.flush()

    quiz_ai = Quiz(
        subject_id=ai_sub.id,
        topic_id=top_ai_1.id,
        title="AI & Machine Learning Concepts Quiz",
        description="Test your conceptual understanding of AI paradigms, heuristics, transformers, and RAG pipelines.",
        difficulty="medium",
        time_limit_mins=10,
    )
    db.session.add(quiz_ai)
    db.session.flush()

    q_ai_1 = QuizQuestion(
        quiz_id=quiz_ai.id,
        question_text="What primary advantage does Retrieval-Augmented Generation (RAG) provide over standard standalone LLMs?",
        option_a="It reduces the number of parameters needed in the GPU",
        option_b="It grounds answers in external, up-to-date verified documents and reduces hallucinations with verifiable citations",
        option_c="It eliminates the need for tokenization",
        option_d="It speeds up model pre-training by 100x",
        correct_option="B",
        explanation="RAG fetches relevant passages from an external verified knowledge base at query time, injecting domain-specific context so the model provides accurate answers with citations instead of hallucinating.",
    )
    q_ai_2 = QuizQuestion(
        quiz_id=quiz_ai.id,
        question_text="What mathematical mechanism allows Transformers to weigh the relevance of every word against every other word in a sentence simultaneously?",
        option_a="Recurrent Gating (LSTM)",
        option_b="Convolutional Kernel Stride",
        option_c="Self-Attention mechanism",
        option_d="K-Nearest Neighbors",
        correct_option="C",
        explanation="Scaled Dot-Product Self-Attention computes relational weights between all token pairs in parallel, capturing long-range semantic dependencies without recurrent loops.",
    )
    q_ai_3 = QuizQuestion(
        quiz_id=quiz_ai.id,
        question_text="Which machine learning paradigm uses reward and penalty feedback signals rather than explicit supervisory labels?",
        option_a="Supervised Learning",
        option_b="Unsupervised Learning",
        option_c="Semi-Supervised Learning",
        option_d="Reinforcement Learning",
        correct_option="D",
        explanation="In Reinforcement Learning, an agent takes actions within an environment and updates its policy based on scalar rewards or penalties received.",
    )
    q_ai_4 = QuizQuestion(
        quiz_id=quiz_ai.id,
        question_text="What condition occurs when a machine learning model achieves near-zero error on training data but performs very poorly on unseen test data?",
        option_a="Underfitting (High Bias)",
        option_b="Overfitting (High Variance)",
        option_c="Vanishing Gradient",
        option_d="Data Imbalance",
        correct_option="B",
        explanation="Overfitting happens when a model learns noise and idiosyncrasies of the training set rather than the underlying generalizable patterns, resulting in high test variance.",
    )
    q_ai_5 = QuizQuestion(
        quiz_id=quiz_ai.id,
        question_text="Which heuristic search algorithm is both complete and optimal when the heuristic function h(n) is admissible (never overestimates true cost)?",
        option_a="Breadth-First Search (BFS)",
        option_b="Depth-First Search (DFS)",
        option_c="A* Search Algorithm",
        option_d="Greedy Best-First Search",
        correct_option="C",
        explanation="A* search evaluates f(n) = g(n) + h(n). When h(n) is admissible, A* is mathematically guaranteed to return the optimal shortest path.",
    )
    db.session.add_all([q_ai_1, q_ai_2, q_ai_3, q_ai_4, q_ai_5])
    db.session.commit()

    # 3. Chunk all study materials into MaterialChunk for RAG indexing
    all_materials = StudyMaterial.query.all()
    for mat in all_materials:
        chunks = chunk_text(mat.content, chunk_size=200, overlap=40)
        for idx, text_chunk in enumerate(chunks):
            # Extract basic keywords
            words = [w.strip(".,;:()#-*`").lower() for w in text_chunk.split() if len(w) > 3]
            keywords = ",".join(list(set(words))[:15])
            chunk_obj = MaterialChunk(
                material_id=mat.id,
                chunk_index=idx,
                chunk_text=text_chunk,
                keywords=keywords,
            )
            db.session.add(chunk_obj)
    db.session.commit()

    print(f"[Database] Seeding complete! Populated 4 subjects, 8 topics, {len(all_materials)} study guides, 4 quizzes (20 questions), and indexed RAG chunks.")
