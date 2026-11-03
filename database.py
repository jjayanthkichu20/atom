import sqlite3
import json
import time
import uuid
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "atom_luxury.db")

DEFAULT_SESSION_ID = "029c1815-a1a1-48e6-929b-1f6909f28fd5"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        role_filter TEXT DEFAULT '',
        location_filter TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        pinned INTEGER DEFAULT 0
    )
    """)

    # 2. Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        jobs_json TEXT DEFAULT '[]',
        used_live_api INTEGER DEFAULT 0,
        action TEXT DEFAULT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """)

    # 3. Jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        logo TEXT NOT NULL,
        color TEXT NOT NULL,
        location TEXT NOT NULL,
        salary TEXT NOT NULL,
        type TEXT NOT NULL,
        match_score INTEGER NOT NULL,
        match_badge TEXT NOT NULL,
        tech_stack_json TEXT NOT NULL,
        why_fits_json TEXT NOT NULL,
        description TEXT NOT NULL,
        screening_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 4. Candidate Profile table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidate_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        location TEXT NOT NULL,
        title TEXT NOT NULL,
        linkedin TEXT DEFAULT '',
        github TEXT DEFAULT '',
        portfolio TEXT DEFAULT '',
        experience_years INTEGER DEFAULT 6,
        skills_json TEXT NOT NULL,
        summary TEXT NOT NULL,
        cv_filename TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    )
    """)

    # 5. Applications table (Real database for job applications)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        company TEXT NOT NULL,
        role TEXT NOT NULL,
        match_score INTEGER NOT NULL,
        status TEXT NOT NULL,
        applied_at TEXT NOT NULL,
        candidate_json TEXT NOT NULL,
        answers_json TEXT NOT NULL,
        notes TEXT DEFAULT ''
    )
    """)

    conn.commit()

    # Seed initial candidate profile if empty
    cursor.execute("SELECT COUNT(*) as count FROM candidate_profile")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
        INSERT INTO candidate_profile (id, name, email, phone, location, title, linkedin, github, portfolio, experience_years, skills_json, summary, updated_at)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Alex Morgan",
            "alex.morgan.dev@gmail.com",
            "+1 (555) 234-5678",
            "San Francisco, CA (Remote)",
            "Senior Frontend & Full Stack Architect",
            "https://linkedin.com/in/alexmorgandev",
            "https://github.com/alexmorgandev",
            "https://alexmorgan.dev",
            6,
            json.dumps(["React", "TypeScript", "Next.js", "Node.js", "GraphQL", "Tailwind CSS", "Design Systems", "Web Performance", "Jest", "CI/CD", "PostgreSQL"]),
            "Executive-tier Senior Software Engineer specializing in high-performance web applications, scalable design systems, and frontend architecture. Led UI performance revamp reducing initial bundle size by 38% and Core Web Vitals to 99th percentile.",
            time.strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()

    # Seed initial jobs if empty
    cursor.execute("SELECT COUNT(*) as count FROM jobs")
    if cursor.fetchone()["count"] == 0:
        initial_jobs = [
            (
                "job-stripe-01",
                "Senior Frontend Engineer",
                "Stripe",
                "S",
                "#635bff",
                "Remote (US / Global)",
                "$175,000 - $210,000",
                "Full-time",
                96,
                "Exceptional Match",
                json.dumps(["React", "TypeScript", "Design Systems", "Web Performance", "GraphQL"]),
                json.dumps([
                    "Your 6+ years React & TypeScript background aligns with Stripe's UI infrastructure.",
                    "Strong track record in design systems and accessible component libraries.",
                    "Experience optimizing Core Web Vitals matches Stripe's high-reliability dashboard focus."
                ]),
                "At Stripe, we are looking for a Senior Frontend Engineer to build the next generation of our Core Dashboard, used daily by millions of businesses worldwide to process billions of dollars in volume.",
                json.dumps([
                    {
                        "question": "Describe an engineering challenge you solved involving frontend performance or complex UI state.",
                        "suggested_answer": "At Starlight Labs, I architected a normalized state cache using Zustand and web workers for real-time financial telemetry, reducing client render lag by 65% and eliminating unnecessary re-renders across 40+ widgets."
                    },
                    {
                        "question": "What is your experience collaborating with design teams on design tokens and component systems?",
                        "suggested_answer": "I created and maintained our internal design system adopted by 50+ engineers, implementing Figma-to-code automated token synchronization and strict WCAG 2.1 AA accessibility standards."
                    },
                    {
                        "question": "What is your target compensation and availability?",
                        "suggested_answer": "My target is within the $185,000 - $205,000 base range, with immediate availability following a standard 2-week notice period."
                    }
                ]),
                time.strftime("%Y-%m-%d %H:%M:%S")
            ),
            (
                "job-linear-02",
                "Staff UI Systems Engineer",
                "Linear",
                "L",
                "#5e6ad2",
                "Remote (Worldwide)",
                "$180,000 - $225,000",
                "Full-time",
                94,
                "High Match",
                json.dumps(["TypeScript", "React", "Local-first", "Tailwind CSS", "WebGL"]),
                json.dumps([
                    "Demonstrated passion for buttery-smooth 60fps keyboard-driven interfaces.",
                    "Deep mastery of TypeScript, canvas/WebGL optimizations, and local-first architecture.",
                    "High autonomous ownership in fast-moving product teams."
                ]),
                "Linear builds tools for high-performing product teams. We are seeking a Staff UI Systems Engineer to lead performance and interaction design on the core issue tracker and project management platform.",
                json.dumps([
                    {
                        "question": "How do you achieve 60fps rendering in data-heavy web applications?",
                        "suggested_answer": "Through virtualized rendering, avoiding forced synchronous layouts, isolating mutation observers, and offloading heavy index lookups to IndexedDB with optimistic client updates."
                    },
                    {
                        "question": "Link to a project or repository showcasing your craft and attention to detail.",
                        "suggested_answer": "https://github.com/alexmorgandev/fast-table-engine - an open-source zero-dependency high-throughput data grid supporting 100k rows with 120fps scrolling."
                    }
                ]),
                time.strftime("%Y-%m-%d %H:%M:%S")
            ),
            (
                "job-anthropic-03",
                "Lead AI Interface Engineer",
                "Anthropic",
                "A",
                "#d97706",
                "San Francisco, CA (Hybrid / Remote)",
                "$190,000 - $235,000",
                "Full-time",
                93,
                "High Match",
                json.dumps(["React", "TypeScript", "Claude AI API", "Streaming SSE", "Next.js"]),
                json.dumps([
                    "Extensive experience building responsive real-time streaming interfaces.",
                    "Deep focus on safety, human-AI alignment, and intuitive feedback mechanisms."
                ]),
                "Anthropic is an AI safety and research company. We build reliable, beneficial AI systems like Claude. We are seeking a Lead Interface Engineer to craft cutting-edge developer platforms and conversational workspaces.",
                json.dumps([
                    {
                        "question": "What principles guide your approach to AI-assisted user experiences?",
                        "suggested_answer": "Providing continuous human-in-the-loop control, transparent system thought disclosure, low-latency streaming feedback, and non-blocking background task orchestration."
                    }
                ]),
                time.strftime("%Y-%m-%d %H:%M:%S")
            ),
            (
                "job-vercel-04",
                "Lead Frontend Platform Engineer",
                "Vercel",
                "▲",
                "#ffffff",
                "Remote",
                "$170,000 - $205,000",
                "Full-time",
                91,
                "Strong Match",
                json.dumps(["Next.js", "React Server Components", "TypeScript", "Edge Runtime"]),
                json.dumps([
                    "Extensive production expertise with Next.js App Router, Server Components, and Edge functions.",
                    "Active open-source contributor and technical writer on modern web platform architecture."
                ]),
                "Help craft the future of the web platform at Vercel. You will work on developer experience, deployment telemetry, and collaborative preview features.",
                json.dumps([
                    {
                        "question": "What excites you most about Server Components and streaming SSR?",
                        "suggested_answer": "The ability to eliminate large client JS bundles for static layout portions while retaining instant streaming boundaries for async data without waterfall requests."
                    }
                ]),
                time.strftime("%Y-%m-%d %H:%M:%S")
            )
        ]

        cursor.executemany("""
        INSERT INTO jobs (id, title, company, logo, color, location, salary, type, match_score, match_badge, tech_stack_json, why_fits_json, description, screening_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_jobs)
        conn.commit()

    # Seed default session if empty
    cursor.execute("SELECT id FROM sessions WHERE id = ?", (DEFAULT_SESSION_ID,))
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO sessions (id, title, role_filter, location_filter, created_at, pinned)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (
            DEFAULT_SESSION_ID,
            "Senior Frontend Engineer • Remote",
            "Senior Frontend Engineer",
            "Remote",
            "Today at 01:00 AM"
        ))
        
        # Fetch seeded jobs to embed in initial message
        cursor.execute("SELECT * FROM jobs")
        seeded_jobs = [format_job_row(row) for row in cursor.fetchall()]

        cursor.execute("""
        INSERT INTO messages (id, session_id, role, content, jobs_json, used_live_api, action, created_at)
        VALUES (?, ?, ?, ?, ?, 0, NULL, ?)
        """, (
            "msg-0",
            DEFAULT_SESSION_ID,
            "assistant",
            "Welcome to **Atom Luxury Edition**. I've synchronized your candidate portfolio with live private executive openings.\n\nBelow are **4 bespoke high-tier roles** exceeding 90% compatibility. Use our **Elite Co-Pilot** to inspect tailored dossiers, prepare cover letters, or authorize one-click human-in-the-loop verified submissions.",
            json.dumps(seeded_jobs),
            "01:00 AM"
        ))

        # Seed 1 initial tracked application in database
        cursor.execute("""
        INSERT INTO applications (id, job_id, company, role, match_score, status, applied_at, candidate_json, answers_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "app-001",
            "job-stripe-01",
            "Stripe",
            "Senior Frontend Engineer",
            96,
            "Under Review (Executive Tier)",
            time.strftime("%Y-%m-%d %H:%M"),
            json.dumps({"name": "Alex Morgan", "email": "alex.morgan.dev@gmail.com"}),
            json.dumps({"question_0": "Verified via Atom Luxury Co-Pilot"}),
            "Autofilled by Atom Co-pilot. Human review verified."
        ))

        conn.commit()

    conn.close()

def format_job_row(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "company": row["company"],
        "logo": row["logo"],
        "color": row["color"],
        "location": row["location"],
        "salary": row["salary"],
        "type": row["type"],
        "match_score": row["match_score"],
        "match_badge": row["match_badge"],
        "tech_stack": json.loads(row["tech_stack_json"]),
        "why_it_fits": json.loads(row["why_fits_json"]),
        "description": row["description"],
        "screening_questions": json.loads(row["screening_json"])
    }

def get_candidate_profile():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidate_profile WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    return {
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "location": row["location"],
        "title": row["title"],
        "linkedin": row["linkedin"],
        "github": row["github"],
        "portfolio": row["portfolio"],
        "experience_years": row["experience_years"],
        "skills": json.loads(row["skills_json"]),
        "summary": row["summary"],
        "cv_filename": row["cv_filename"]
    }

def update_candidate_profile(data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE candidate_profile
    SET name = ?, email = ?, phone = ?, location = ?, title = ?, linkedin = ?, github = ?, skills_json = ?, summary = ?, cv_filename = ?, updated_at = ?
    WHERE id = 1
    """, (
        data.get("name", "Candidate"),
        data.get("email", "candidate@domain.com"),
        data.get("phone", "+1 (555) 000-0000"),
        data.get("location", "Remote"),
        data.get("title", "Senior Engineer"),
        data.get("linkedin", ""),
        data.get("github", ""),
        json.dumps(data.get("skills", [])),
        data.get("summary", ""),
        data.get("cv_filename", ""),
        time.strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_session_data(session_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        # Create session
        cursor.execute("""
        INSERT INTO sessions (id, title, role_filter, location_filter, created_at, pinned)
        VALUES (?, ?, '', '', ?, 0)
        """, (session_id, "Executive Career Search", time.strftime("%I:%M %p")))
        conn.commit()
        session_row = {"id": session_id, "title": "Executive Career Search", "created_at": "Just now", "pinned": 0}

    # Fetch messages
    cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY rowid ASC", (session_id,))
    msg_rows = cursor.fetchall()
    messages = []
    for m in msg_rows:
        messages.append({
            "id": m["id"],
            "role": m["role"],
            "content": m["content"],
            "jobs": json.loads(m["jobs_json"]) if m["jobs_json"] else [],
            "used_live_api": bool(m["used_live_api"]),
            "action": m["action"],
            "timestamp": m["created_at"]
        })

    # Fetch jobs
    cursor.execute("SELECT * FROM jobs ORDER BY match_score DESC")
    jobs = [format_job_row(row) for row in cursor.fetchall()]

    profile = get_candidate_profile()
    conn.close()

    return {
        "session": {
            "id": session_row["id"],
            "title": session_row["title"],
            "created_at": session_row["created_at"],
            "pinned": bool(session_row["pinned"]),
            "messages": messages
        },
        "profile": profile,
        "jobs": jobs
    }

def add_message_to_db(session_id, role, content, jobs=None, used_live_api=False, action=None):
    conn = get_db()
    cursor = conn.cursor()
    msg_id = str(uuid.uuid4())
    now_str = time.strftime("%I:%M %p")
    jobs_json = json.dumps(jobs) if jobs else "[]"
    cursor.execute("""
    INSERT INTO messages (id, session_id, role, content, jobs_json, used_live_api, action, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, session_id, role, content, jobs_json, 1 if used_live_api else 0, action, now_str))
    conn.commit()
    conn.close()
    return {
        "id": msg_id,
        "role": role,
        "content": content,
        "jobs": jobs or [],
        "used_live_api": used_live_api,
        "action": action,
        "timestamp": now_str
    }

def insert_application_to_db(job_id, company, role, match_score, candidate, answers, notes=""):
    conn = get_db()
    cursor = conn.cursor()
    app_id = f"app-{str(uuid.uuid4())[:8]}"
    applied_at = time.strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
    INSERT INTO applications (id, job_id, company, role, match_score, status, applied_at, candidate_json, answers_json, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        app_id,
        job_id,
        company,
        role,
        match_score,
        "Applied (Human Verified)",
        applied_at,
        json.dumps(candidate),
        json.dumps(answers),
        notes
    ))
    conn.commit()
    conn.close()
    return {
        "id": app_id,
        "job_id": job_id,
        "company": company,
        "role": role,
        "match_score": match_score,
        "status": "Applied (Human Verified)",
        "applied_at": applied_at,
        "candidate": candidate,
        "answers": answers
    }

def get_all_applications_from_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications ORDER BY applied_at DESC")
    rows = cursor.fetchall()
    apps = []
    for r in rows:
        apps.append({
            "id": r["id"],
            "job_id": r["job_id"],
            "company": r["company"],
            "role": r["role"],
            "match_score": r["match_score"],
            "status": r["status"],
            "applied_at": r["applied_at"],
            "candidate": json.loads(r["candidate_json"]),
            "answers": json.loads(r["answers_json"]),
            "notes": r["notes"]
        })
    conn.close()
    return apps

def replace_jobs_in_db(new_jobs):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs")
    for j in new_jobs:
        cursor.execute("""
        INSERT INTO jobs (id, title, company, logo, color, location, salary, type, match_score, match_badge, tech_stack_json, why_fits_json, description, screening_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            j["id"],
            j["title"],
            j["company"],
            j["logo"],
            j["color"],
            j["location"],
            j["salary"],
            j["type"],
            j["match_score"],
            j["match_badge"],
            json.dumps(j["tech_stack"]),
            json.dumps(j["why_it_fits"]),
            j["description"],
            json.dumps(j["screening_questions"]),
            time.strftime("%Y-%m-%d %H:%M:%S")
        ))
    conn.commit()
    conn.close()

# Auto-initialize on import
init_db()
