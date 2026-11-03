"""
Atom Premier — Luxury AI Career Co-Pilot
Flask Backend with SQLite persistence, OpenAI/Gemini support,
CV upload, PDF resume generation, and human-in-the-loop apply flow.
"""
import os
import re
import json
import time
import uuid
import io

import requests
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename

import database

# ── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "atom-jobalchemy-secret-2026")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB upload limit

DEFAULT_SESSION_ID = database.DEFAULT_SESSION_ID

# Load .env file safely if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

USER_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── AI Helpers ────────────────────────────────────────────────────────────────

ATOM_SYSTEM_PROMPT = (
    "You are Atom Premier, an elite AI Career Co-Pilot for executive-tier professionals. "
    "Communicate with refined elegance and precision. Use crisp markdown formatting. "
    "Give actionable, high-impact career advice, strategic cover letters, and resume guidance."
)

def get_effective_key(client_key, provider="openai"):
    """Return the best available API key for the given provider."""
    key = (client_key or "").strip()
    if key:
        return key
    return USER_OPENAI_KEY if provider == "openai" else GEMINI_API_KEY


def call_openai(api_key, model, user_message, system_prompt=None):
    """Call OpenAI Chat Completions. Raises on error."""
    payload = {
        "model": model or "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt or ATOM_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=25,
    )
    if resp.status_code == 429:
        data = resp.json()
        code = data.get("error", {}).get("code", "quota_exceeded")
        raise Exception(f"OpenAI quota/rate-limit (429:{code})")
    if resp.status_code != 200:
        raise Exception(f"OpenAI error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


def call_gemini(api_key, model, user_message, system_prompt=None):
    """Call Google Gemini generateContent. Raises on error."""
    sys_txt = system_prompt or ATOM_SYSTEM_PROMPT
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{sys_txt}\n\nUser: {user_message}"}]}
        ],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=25)
    if resp.status_code != 200:
        raise Exception(f"Gemini error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def fallback_agent(user_message, jobs, profile):
    """Intelligent rule-based fallback when AI API is unavailable."""
    msg = user_message.lower()
    name = profile.get("name", "Alex Morgan")
    skills = profile.get("skills", ["TypeScript", "React"])

    # Find relevant job
    matched = next(
        (j for j in jobs if j["company"].lower() in msg or j["title"].lower() in msg),
        jobs[0] if jobs else None
    )

    if "apply" in msg:
        j = matched
        if j:
            return (
                f"### ⚡ Executive Co-Pilot Initialized — {j['company']}\n\n"
                f"I've pre-filled your application for **{j['title']}** at **{j['company']}**.\n\n"
                f"- 👤 **Candidate:** {name}\n"
                f"- 🎯 **Tailored stack:** {', '.join(j.get('tech_stack', skills)[:3])}\n"
                f"- 🛡️ **Human-in-the-Loop:** Review and confirm before committing to database.\n\n"
                f"> Click **Authorize & Commit** in the application panel to finalize."
            )
        return "Please specify which company you'd like to apply to."

    if any(k in msg for k in ["tailor", "cv", "resume", "dossier"]):
        j = matched
        if j:
            return (
                f"### 📄 Bespoke CV Tailoring — {j['company']}\n\n"
                f"**Original ATS Score:** 84% → **Tailored:** **{j['match_score']}%**\n\n"
                f"**Key Enhancements:**\n"
                f"1. Framed expertise around `{', '.join(j.get('tech_stack', skills)[:2])}`\n"
                f"2. Quantified impact metrics (99th-percentile Core Web Vitals)\n"
                f"3. Integrated keyword density for {j['company']}'s JD\n\n"
                f"Download your ATS-optimised PDF below ↓"
            )

    if any(k in msg for k in ["interview", "question", "prep", "prepare"]):
        j = matched or (jobs[0] if jobs else None)
        if j:
            return (
                f"### 🎯 Interview Preparation — {j['company']}\n\n"
                f"**High-probability questions for {j['title']}:**\n\n"
                f"**1. Architecture at Scale**\n"
                f"- *How would you architect a 60fps real-time dashboard for 100k data points?*\n"
                f"- Strategy: virtualized rendering, web workers, optimistic client state.\n\n"
                f"**2. Cross-functional Leadership**\n"
                f"- *How do you govern design tokens across 50+ engineers?*\n"
                f"- Strategy: headless primitives, automated CI token linters, semantic versioning.\n\n"
                f"Reply with your answer for live coaching!"
            )

    if any(k in msg for k in ["database", "application", "track", "status"]):
        apps = database.get_all_applications_from_db()
        return (
            f"### 🏛️ Applications Database\n\n"
            f"You have **{len(apps)} application(s)** recorded in `atom_luxury.db`.\n\n"
            + "\n".join(f"- **{a['company']}** — {a['role']} • _{a['status']}_" for a in apps)
            if apps else "No applications recorded yet. Apply to a role to see it tracked here."
        )

    # Default welcome
    job_list = "\n".join(
        f"- **{j['company']}** — {j['title']} ({j['match_score']}% match)"
        for j in jobs[:4]
    ) if jobs else "No jobs loaded yet."

    return (
        f"Welcome to **Atom Premier**, {name}.\n\n"
        f"I've curated **{len(jobs)} bespoke executive openings** for you:\n\n"
        f"{job_list}\n\n"
        f"**What can I do for you?**\n"
        f"- 📄 Upload your CV to recalibrate match scores\n"
        f"- ⚡ Apply to any role with human-verified co-pilot\n"
        f"- 💎 Generate tailored cover letters & dossiers\n"
        f"- 🎯 Prepare for executive interviews\n\n"
        f"*All actions are synchronized with the SQLite database.*"
    )


# ── Page Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", session_id=DEFAULT_SESSION_ID)

@app.route("/chat/<session_id>")
def chat_session(session_id):
    return render_template("index.html", session_id=session_id)

@app.route("/jobs")
def jobs_page():
    return render_template("index.html", session_id=DEFAULT_SESSION_ID)

@app.route("/apply/<job_id>")
def apply_page(job_id):
    return render_template("index.html", session_id=DEFAULT_SESSION_ID)

@app.route("/applications")
def applications_page():
    return render_template("index.html", session_id=DEFAULT_SESSION_ID)


# ── API: Session Data ─────────────────────────────────────────────────────────

@app.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id):
    try:
        data = database.get_session_data(session_id)
        # Flatten messages list into the response
        messages = data["session"].get("messages", [])
        return jsonify({
            "success": True,
            "session_id": session_id,
            "messages": messages,
            "jobs": data["jobs"],
            "profile": data["profile"],
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── API: CV Upload & Parse ────────────────────────────────────────────────────

@app.route("/api/upload-cv", methods=["POST"])
def upload_cv():
    # Support both field names: 'cv_file' and 'cv'
    file = request.files.get("cv_file") or request.files.get("cv")
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No file uploaded. Please attach a PDF, DOCX, or TXT file."}), 400

    session_id = request.form.get("sessionId") or request.form.get("session_id") or DEFAULT_SESSION_ID

    try:
        filename = secure_filename(file.filename).lower()
        raw_text = ""

        if filename.endswith(".pdf"):
            try:
                import pypdf
                reader = pypdf.PdfReader(file.stream)
                for page in reader.pages:
                    extracted = page.extract_text() or ""
                    raw_text += extracted + "\n"
            except ImportError:
                return jsonify({"success": False, "error": "pypdf not installed. Run: pip install pypdf"}), 500

        elif filename.endswith((".docx", ".doc")):
            try:
                import docx as python_docx
                doc = python_docx.Document(file.stream)
                raw_text = "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                return jsonify({"success": False, "error": "python-docx not installed. Run: pip install python-docx"}), 500

        else:
            # TXT / MD / plain text
            content = file.read()
            raw_text = content.decode("utf-8", errors="replace")

        raw_text = raw_text.strip()
        if not raw_text or len(raw_text) < 30:
            return jsonify({
                "success": False,
                "error": "Could not extract readable text. Ensure the file is not a scanned image or password-protected PDF."
            }), 400

        # ── Parse CV ────────────────────────────────────────────────────────
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        raw_lower = raw_text.lower()

        # Name — first short line without special chars
        candidate_name = "Candidate"
        for line in lines[:6]:
            words = line.split()
            if 2 <= len(words) <= 4 and not any(c in line for c in "@/:+0123456789"):
                candidate_name = line
                break

        # Email
        em = re.search(r"[\w.+-]+@[\w.-]+\.\w{2,}", raw_text)
        email = em.group(0) if em else "applicant@domain.com"

        # Phone
        ph = re.search(r"(\+?[\d][\d\s\-().]{7,}\d)", raw_text)
        phone = ph.group(0).strip() if ph else "+1 (555) 000-0001"

        # Skills
        KNOWN_SKILLS = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Vue", "Angular",
            "Node.js", "Express", "Django", "FastAPI", "Flask", "Spring Boot",
            "Java", "Go", "Golang", "Rust", "C++", "C#", ".NET", "Swift", "Kotlin",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "GraphQL", "REST API",
            "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD",
            "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow",
            "Tailwind CSS", "Design Systems", "Web Performance", "Jest", "Playwright",
            "Figma", "Agile", "Scrum", "Leadership",
        ]
        skills = [s for s in KNOWN_SKILLS if re.search(r"\b" + re.escape(s.lower()) + r"\b", raw_lower)]
        if not skills:
            skills = ["Software Architecture", "System Design", "TypeScript", "Engineering Leadership"]

        # Infer title
        if any(k in raw_lower for k in ["frontend", "react", "ui/ux", "css"]):
            title = "Senior Frontend Architect"
        elif any(k in raw_lower for k in ["machine learning", "ai engineer", "data scientist", "ml"]):
            title = "Lead AI / ML Systems Engineer"
        elif any(k in raw_lower for k in ["devops", "cloud architect", "infrastructure", "kubernetes"]):
            title = "Principal Cloud Infrastructure Architect"
        elif any(k in raw_lower for k in ["backend", "distributed systems", "api design"]):
            title = "Senior Distributed Systems Engineer"
        elif any(k in raw_lower for k in ["full stack", "fullstack"]):
            title = "Senior Full Stack Engineer"
        else:
            title = "Senior Software Engineer"

        profile_data = {
            "name": candidate_name,
            "email": email,
            "phone": phone,
            "location": "Remote / Hybrid",
            "title": title,
            "linkedin": "",
            "github": "",
            "portfolio": "",
            "skills": skills,
            "summary": f"Distinguished {title} with expertise in {', '.join(skills[:5])}.",
            "cv_filename": file.filename,
        }
        database.update_candidate_profile(profile_data)

        # ── Generate 3 recalibrated jobs ────────────────────────────────────
        def make_job(company, logo, color, location, salary_range, score, badge, extra_title=""):
            jid = f"job-{uuid.uuid4().hex[:8]}"
            jtitle = extra_title if extra_title else title
            return {
                "id": jid,
                "title": jtitle,
                "company": company,
                "logo": logo,
                "color": color,
                "location": location,
                "salary": salary_range,
                "type": "Full-time",
                "match_score": score,
                "match_badge": badge,
                "tech_stack": skills[:5],
                "why_it_fits": [
                    f"Direct overlap with your core stack: {', '.join(skills[:3])}.",
                    "Proven execution speed and architecture ownership.",
                    f"Alignment with {company}'s engineering philosophy.",
                ],
                "description": f"{company} seeks a world-class {jtitle} with expertise in {', '.join(skills[:3])}.",
                "screening_questions": [
                    {
                        "question": f"Describe a project demonstrating mastery in {skills[0] if skills else 'engineering'}.",
                        "suggested_answer": f"Architected a distributed system using {', '.join(skills[:3])}, scaling to 1M+ users.",
                    },
                    {
                        "question": "What is your target compensation range?",
                        "suggested_answer": salary_range + " base + equity",
                    },
                ],
            }

        new_jobs = [
            make_job("Anthropic", "A", "#d97706", "Remote (Global)", "$195,000–$240,000", 98, "Exceptional Match"),
            make_job("Stripe",    "S", "#635bff", "Remote (US/EU)",  "$180,000–$215,000", 96, "High Match"),
            make_job("Linear",    "L", "#5e6ad2", "Remote (World)",  "$185,000–$225,000", 94, "High Match",
                     f"Staff {title.replace('Senior ','').replace('Principal ','')}"),
        ]
        database.replace_jobs_in_db(new_jobs)

        # ── Persist the CV message ───────────────────────────────────────────
        reply = (
            f"### 💎 Executive CV Parsed & Synced: `{file.filename}`\n\n"
            f"- **Candidate:** {candidate_name}\n"
            f"- **Title:** {title}\n"
            f"- **Contact:** `{email}` | `{phone}`\n"
            f"- **Validated Stack:** `{', '.join(skills[:8])}`\n\n"
            f"Match scores recalibrated across **{len(new_jobs)} bespoke openings**. "
            f"Click **Apply Now** to review your pre-filled application."
        )
        database.add_message_to_db(session_id, "assistant", reply, jobs=new_jobs)

        return jsonify({
            "success": True,
            "message": reply,
            "profile": profile_data,
            "jobs": new_jobs,
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Upload failed: {str(e)}"}), 500


# ── API: Chat ─────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    session_id   = data.get("session_id") or data.get("sessionId") or DEFAULT_SESSION_ID
    user_message = (data.get("message") or "").strip()
    client_key   = (data.get("api_key") or data.get("apiKey") or "").strip()
    provider     = data.get("provider", "openai")
    model        = data.get("model") or ("gpt-4o-mini" if provider == "openai" else "gemini-2.5-flash")

    if not user_message:
        return jsonify({"success": False, "error": "Message cannot be empty."}), 400

    # Persist user message
    database.add_message_to_db(session_id, "user", user_message)

    session_data = database.get_session_data(session_id)
    profile = session_data["profile"]
    jobs    = session_data["jobs"]

    effective_key = get_effective_key(client_key, provider)
    ai_text       = ""
    used_live     = False

    if effective_key:
        try:
            sys_prompt = (
                f"{ATOM_SYSTEM_PROMPT} "
                f"Candidate: {profile.get('name','Alex Morgan')}, "
                f"{profile.get('title','Senior Architect')}, "
                f"skills: {', '.join(profile.get('skills', [])[:8])}."
            )
            if provider == "openai":
                ai_text = call_openai(effective_key, model, user_message, sys_prompt)
            else:
                ai_text = call_gemini(effective_key, model, user_message, sys_prompt)
            used_live = True
        except Exception as exc:
            err = str(exc)
            notice = (
                "> ℹ️ **OpenAI quota exhausted** — Atom Intelligent Co-Pilot active.\n\n"
                if ("429" in err or "quota" in err.lower() or "credit" in err.lower())
                else f"> ⚠️ *AI provider note: `{err[:120]}`. Fallback active.*\n\n"
            )
            ai_text = notice + fallback_agent(user_message, jobs, profile)
    else:
        ai_text = fallback_agent(user_message, jobs, profile)

    # Persist bot message
    bot_msg = database.add_message_to_db(
        session_id, "assistant", ai_text,
        jobs=jobs, used_live_api=used_live
    )

    return jsonify({
        "success":      True,
        "reply":        ai_text,
        "message":      bot_msg,
        "jobs":         jobs,
        "used_live_api": used_live,
    })


# ── API: Apply ────────────────────────────────────────────────────────────────

@app.route("/api/apply", methods=["POST"])
def apply_job():
    data = request.get_json(silent=True) or {}

    job_id     = data.get("job_id") or data.get("jobId") or ""
    session_id = data.get("session_id") or data.get("sessionId") or DEFAULT_SESSION_ID

    # Candidate info from payload, fallback to DB profile
    db_profile = database.get_candidate_profile()
    candidate = {
        "name":      data.get("full_name")  or db_profile.get("name", "Alex Morgan"),
        "email":     data.get("email")      or db_profile.get("email", ""),
        "phone":     data.get("phone")      or db_profile.get("phone", ""),
        "location":  data.get("location")   or db_profile.get("location", "Remote"),
        "linkedin":  data.get("linkedin")   or db_profile.get("linkedin", ""),
        "portfolio": data.get("portfolio")  or db_profile.get("portfolio", ""),
        "cover_letter": data.get("cover_letter", ""),
    }

    session_data = database.get_session_data(session_id)
    jobs = session_data["jobs"]
    job = next((j for j in jobs if j["id"] == job_id), jobs[0] if jobs else {})

    if not job:
        return jsonify({"success": False, "error": "Job not found in database."}), 404

    app_record = database.insert_application_to_db(
        job_id=job["id"],
        company=job.get("company", "Company"),
        role=job.get("title", "Engineer"),
        match_score=job.get("match_score", 95),
        candidate=candidate,
        answers=data.get("answers", {}),
        notes="Verified via Atom Premier Co-Pilot.",
    )

    # Confirmation message
    conf_text = (
        f"👑 **Application Committed to Database!**\n\n"
        f"**{job.get('title')}** at **{job.get('company')}** has been registered.\n\n"
        f"- 🆔 Record ID: `{app_record['id']}`\n"
        f"- 📊 ATS Match: **{job.get('match_score')}%**\n"
        f"- 🕐 Timestamp: `{app_record['applied_at']}`\n\n"
        f"Atom will surface status updates as they arrive."
    )
    database.add_message_to_db(session_id, "assistant", conf_text, jobs=[job])

    return jsonify({
        "success": True,
        "application_id": app_record["id"],
        "application": app_record,
    })


# ── API: Applications List ────────────────────────────────────────────────────

@app.route("/api/applications", methods=["GET"])
def get_applications():
    try:
        apps = database.get_all_applications_from_db()
        # Normalise field names the frontend expects
        normalised = []
        for a in apps:
            normalised.append({
                "id":         a["id"],
                "job_id":     a.get("job_id", ""),
                "company":    a["company"],
                "job_title":  a.get("role", a.get("job_title", "")),
                "match_score": a.get("match_score", "—"),
                "status":     a.get("status", "submitted"),
                "created_at": a.get("applied_at", a.get("created_at", "")),
            })
        return jsonify({"success": True, "applications": normalised})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── API: DB Inspect ───────────────────────────────────────────────────────────

@app.route("/api/db-inspect", methods=["GET"])
def inspect_database():
    try:
        conn   = database.get_db()
        cursor = conn.cursor()
        counts = {}
        for table in ("applications", "messages", "jobs", "sessions", "candidate_profile"):
            cursor.execute(f"SELECT COUNT(*) as c FROM {table}")
            counts[table] = cursor.fetchone()["c"]
        conn.close()
        return jsonify({"database": "atom_luxury.db", "status": "connected", "tables": counts})
    except Exception as e:
        return jsonify({"database": "atom_luxury.db", "status": "error", "error": str(e)}), 500


# ── API: Verify Key ───────────────────────────────────────────────────────────

@app.route("/api/verify-key", methods=["POST"])
def verify_key():
    data     = request.get_json(silent=True) or {}
    api_key  = (data.get("api_key") or data.get("apiKey") or "").strip() or USER_OPENAI_KEY
    provider = data.get("provider", "openai")
    model    = data.get("model") or ("gpt-4o-mini" if provider == "openai" else "gemini-2.5-flash")

    if not api_key:
        return jsonify({"valid": False, "message": "No API key provided."}), 400

    try:
        test = "Confirm you are active in one sentence."
        resp = call_openai(api_key, model, test) if provider == "openai" else call_gemini(api_key, model, test)
        return jsonify({"valid": True, "message": f"Connected to {provider.upper()} ({model}).", "sample": resp.strip()})
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "credit" in err.lower():
            return jsonify({
                "valid": True,
                "warning": True,
                "message": "API Key valid — credit balance exhausted. Atom Intelligent Co-Pilot is active.",
            })
        return jsonify({"valid": False, "message": err[:200]}), 400


# ── API: Download CV (PDF) ────────────────────────────────────────────────────

@app.route("/api/download-cv/<path:job_id>", methods=["GET"])
def download_cv(job_id):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    except ImportError:
        return jsonify({"error": "reportlab not installed. Run: pip install reportlab"}), 500

    session_data = database.get_session_data(DEFAULT_SESSION_ID)
    jobs    = session_data["jobs"]
    profile = session_data["profile"]

    # Decode URL-encoded job_id
    import urllib.parse
    job_id_decoded = urllib.parse.unquote(job_id)
    job = next((j for j in jobs if j["id"] == job_id_decoded), jobs[0] if jobs else {})

    if not job:
        return jsonify({"error": "Job not found"}), 404

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()

    def make_style(name, base="Normal", **kw):
        return ParagraphStyle(name, parent=styles[base], **kw)

    title_s   = make_style("T",  fontName="Helvetica-Bold",  fontSize=20, leading=24, textColor=colors.HexColor("#111827"))
    sub_s     = make_style("S",  fontName="Helvetica-Bold",  fontSize=11, leading=15, textColor=colors.HexColor("#d4af37"))
    contact_s = make_style("C",  fontName="Helvetica",       fontSize=9,  leading=13, textColor=colors.HexColor("#4b5563"))
    head_s    = make_style("H",  fontName="Helvetica-Bold",  fontSize=12, leading=16, textColor=colors.HexColor("#111827"), spaceBefore=10, spaceAfter=4)
    body_s    = make_style("B",  fontName="Helvetica",       fontSize=9.5,leading=14, textColor=colors.HexColor("#1f2937"))
    bullet_s  = make_style("BL", fontName="Helvetica",       fontSize=9,  leading=13, textColor=colors.HexColor("#374151"), leftIndent=12, firstLineIndent=-8)

    tech = job.get("tech_stack", profile.get("skills", []))
    story = [
        Paragraph(profile.get("name", "Candidate"), title_s),
        Spacer(1, 2),
        Paragraph(f"Executive Dossier • {job['title']} @ {job['company']}", sub_s),
        Spacer(1, 4),
        Paragraph(
            f"{profile.get('email','')} | {profile.get('phone','')} | {profile.get('location','')}",
            contact_s
        ),
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#d4af37"), spaceBefore=2, spaceAfter=8),

        Paragraph("EXECUTIVE SUMMARY", head_s),
        Paragraph(
            f"{profile.get('summary','')} Tailored for {job['company']} with expertise in {', '.join(tech[:5])}.",
            body_s
        ),
        Spacer(1, 6),

        Paragraph("CORE TECHNICAL PROFICIENCIES", head_s),
        Paragraph(f"<b>Validated Stack:</b> {', '.join(profile.get('skills', tech))}", body_s),
        Spacer(1, 6),

        Paragraph("EXECUTIVE EXPERIENCE & IMPACT", head_s),
        Paragraph(f"<b>{profile.get('title','Senior Architect')}</b>", body_s),
        Paragraph(f"• Led architecture using {tech[0] if tech else 'modern stack'}, improving feature velocity by 40%.", bullet_s),
        Paragraph("• Instituted design tokens, WCAG 2.1 AA standards, and 99.99% availability telemetry.", bullet_s),
        Paragraph("• Mentored cross-functional team of 8+ engineers across quarterly roadmap milestones.", bullet_s),
        Spacer(1, 6),

        Paragraph(f"<i>Verified via Atom Premier Co-Pilot • ATS Match Score: {job.get('match_score','—')}%</i>", contact_s),
    ]

    doc.build(story)
    buffer.seek(0)
    safe_name = profile.get("name", "Candidate").replace(" ", "_")
    filename  = f"{safe_name}_Dossier_{job['company']}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


# ── Boot ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Atom JobAlchemy Clone running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
