import streamlit as st
import google.generativeai as genai
import pymupdf
import os
import re
import sqlite3
from fpdf import FPDF
from dotenv import load_dotenv
import hashlib

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Ensure it's set in .env file.")
genai.configure(api_key=GOOGLE_API_KEY)

PROMPT = os.getenv("PROMPT", "Analyze the resume against job description and give insights with match percentage.")


def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (username TEXT, feature TEXT, score TEXT, details TEXT)''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    conn.close()
    return True

def check_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_history(username, feature, score, details):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO history (username, feature, score, details) VALUES (?, ?, ?, ?)",
              (username, feature, str(score), details))
    conn.commit()
    conn.close()

def get_history(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT feature, score, details FROM history WHERE username=?", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def extract_text_from_pdf(pdf_file):
    with pymupdf.open(stream=pdf_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text("text")
    return text

def analyze_resume(resume_text, job_desc):
    prompt = f"{PROMPT}\n\nResume: {resume_text}\n\nJob Description: {job_desc}"
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

def extract_match_percentage(text):
    match = re.search(r'(\d{1,3})%', text)
    if match:
        return min(int(match.group(1)), 100)
    return None

def generate_pdf(content, filename="resume_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.split("\n"):
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest="S").encode("latin-1")

TEMPLATES = {
    "Classic": """[Classic Resume Template]
Name: John Doe
Email: johndoe@email.com
Phone: 123-456-7890

Objective:
Recent graduate seeking entry-level position in Software Development.

Education:
B.Tech in Computer Science - XYZ University (2024)

Skills:
- Python, Java, SQL
- Problem Solving
- Communication""",
    "Modern": """[Modern Resume Template]
John Doe
📧 johndoe@email.com | 📞 123-456-7890

💡 Profile:
Motivated fresher with strong programming and analytical skills.

🎓 Education:
B.Tech in Computer Science - XYZ University (2024)

⚙️ Skills:
Python | Java | SQL | Team Collaboration

📂 Projects:
- AI Chatbot
- E-commerce Website""",
    "Creative": """[Creative Resume Template]
🌟 John Doe 🌟
Software Engineer | Problem Solver

📧 johndoe@email.com | 📞 123-456-7890

🎯 Career Goal:
To innovate and build impactful technology solutions.

🎓 Education:
XYZ University - B.Tech in Computer Science (2024)

🛠 Skills:
⚡ Python ⚡ Java ⚡ SQL ⚡ Creativity

📂 Projects:
1. Resume Analyzer AI
2. Portfolio Website"""
}


st.set_page_config(page_title="TalentMatch AI", layout="wide", page_icon="🧑‍💼")
st.title("🧑‍💼 TalentMatch AI")

init_db()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

if not st.session_state["logged_in"]:
    auth_choice = st.sidebar.radio("Login / Signup", ["Login", "Sign Up"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if auth_choice == "Sign Up":
        if st.sidebar.button("Create Account"):
            if add_user(username, password):
                st.success("✅ Account created. Please log in.")
            else:
                st.error("❌ Username already exists.")

    elif auth_choice == "Login":
        if st.sidebar.button("Login"):
            if check_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"✅ Welcome {username}!")
            else:
                st.error("❌ Invalid username or password.")

else:
    
    st.sidebar.title(f"Welcome, {st.session_state['username']} 👋")
    app_mode = st.sidebar.radio(
        "Choose Feature:",
        [
            "ATS Resume Analyzer",
            "ATS Score Checker",
            "Resume Builder",
            "Resume Templates",
            "Cover Letter Generator",
            "Interview Q&A Prep",
            "History / Dashboard"
        ]
    )
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.rerun()

    
    if app_mode == "ATS Resume Analyzer":
        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded_file = st.file_uploader("📂 Upload Resume (PDF)", type=["pdf"])
        with col2:
            job_description = st.text_area("💼 Enter Job Description")

        if st.button("🔍 Analyze Resume"):
            if uploaded_file and job_description:
                resume_text = extract_text_from_pdf(uploaded_file)
                analysis = analyze_resume(resume_text, job_description)
                match_percentage = extract_match_percentage(analysis)

                st.subheader("📊 Resume Analysis Report")
                if match_percentage:
                    st.markdown(f"🔥 **Match Score: {match_percentage}%**")
                    st.progress(match_percentage / 100)
                st.write(analysis)

                pdf_bytes = generate_pdf(analysis)
                st.download_button("📥 Download PDF Report", data=pdf_bytes, file_name="resume_analysis.pdf")

                save_history(st.session_state["username"], "Analyzer", match_percentage, analysis)

    elif app_mode == "ATS Score Checker":
        uploaded_file = st.file_uploader("📂 Upload Resume (PDF)", type=["pdf"])
        if uploaded_file and st.button("⚡ Check ATS Score"):
            resume_text = extract_text_from_pdf(uploaded_file)
            analysis = analyze_resume(resume_text, "Generic Job Description for ATS Check")
            score = extract_match_percentage(analysis)
            st.write("📊 ATS Score:", score if score else "N/A")
            save_history(st.session_state["username"], "ATS Score", score, analysis)

    elif app_mode == "Resume Builder":
        st.subheader("📝 Build Your Resume")
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        education = st.text_area("Education")
        skills = st.text_area("Skills")
        projects = st.text_area("Projects")

        if st.button("📄 Generate Resume"):
            content = f"""
            {name}\n{email} | {phone}\n
            Education:\n{education}\n
            Skills:\n{skills}\n
            Projects:\n{projects}
            """
            pdf_bytes = generate_pdf(content)
            st.download_button("📥 Download Resume", data=pdf_bytes, file_name="my_resume.pdf")
            save_history(st.session_state["username"], "Resume Builder", "N/A", content)

    elif app_mode == "Resume Templates":
        st.subheader("🎨 Choose a Resume Template")
        template_choice = st.selectbox("Select Template", list(TEMPLATES.keys()))
        st.text_area("📄 Preview", TEMPLATES[template_choice], height=300)
        if st.button("📥 Download Template"):
            pdf_bytes = generate_pdf(TEMPLATES[template_choice])
            st.download_button("📥 Download PDF", data=pdf_bytes, file_name=f"{template_choice}_resume.pdf")

    elif app_mode == "Cover Letter Generator":
        job_title = st.text_input("Job Title")
        company = st.text_input("Company Name")
        skills = st.text_area("Skills to Highlight")
        if st.button("✍️ Generate Cover Letter"):
            prompt = f"Write a professional cover letter for {job_title} role at {company}, highlighting skills: {skills}."
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            st.write(response.text)
            save_history(st.session_state["username"], "Cover Letter", "N/A", response.text)

    elif app_mode == "Interview Q&A Prep":
        job_role = st.text_input("Job Role")
        if st.button("🎤 Generate Q&A"):
            prompt = f"Generate 5 common interview questions and answers for {job_role}."
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            st.write(response.text)
            save_history(st.session_state["username"], "Interview Prep", "N/A", response.text)

    elif app_mode == "History / Dashboard":
        st.subheader("📜 Your History")
        history = get_history(st.session_state["username"])
        if history:
            for idx, (feature, score, details) in enumerate(history, 1):
                st.write(f"**{idx}.** {feature} | Score: {score}")
                with st.expander("View Details"):
                    st.write(details)
        else:
            st.info("No history yet.")
