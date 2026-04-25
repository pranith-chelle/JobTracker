from flask import Flask, render_template, request, redirect
import sqlite3
import google.generativeai as genai
import fitz
import os

app = Flask(__name__)

genai.configure(api_key="AIzaSyC-6ruxwu8YWkb4ln7EAsEqPxq2zO7xCTI")
model = genai.GenerativeModel('gemini-2.5-flash')

def init_db():
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  company TEXT,
                  role TEXT,
                  date TEXT,
                  status TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute('SELECT * FROM jobs')
    jobs = c.fetchall()
    total = len(jobs)
    applied = len([j for j in jobs if j[4] == 'Applied'])
    interview = len([j for j in jobs if j[4] == 'Interview'])
    offer = len([j for j in jobs if j[4] == 'Offer'])
    rejected = len([j for j in jobs if j[4] == 'Rejected'])
    conn.close()
    return render_template('index.html', jobs=jobs,
                         total=total, applied=applied,
                         interview=interview, offer=offer,
                         rejected=rejected)

@app.route('/add', methods=['POST'])
def add_job():
    company = request.form['company']
    role = request.form['role']
    date = request.form['date']
    status = request.form['status']
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute('INSERT INTO jobs (company, role, date, status) VALUES (?, ?, ?, ?)',
              (company, role, date, status))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete_job(id):
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute('DELETE FROM jobs WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/analyze', methods=['POST'])
def analyze():
    job_desc = request.form['job_desc']
    resume_file = request.files['resume']
    pdf_bytes = resume_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    resume_text = ""
    for page in doc:
        resume_text += page.get_text()
    prompt = f"""
    You are a professional HR expert and career coach.
    Analyze this resume against the job description and provide:
    1. Match Score (0-100%)
    2. Matching Skills (bullet points)
    3. Missing Skills (bullet points)
    4. Improvement Suggestions (bullet points)
    5. Overall Verdict (1-2 lines)
    Resume:
    {resume_text}
    Job Description:
    {job_desc}
    Format your response clearly with headers.
    """
    response = model.generate_content(prompt)
    analysis = response.text
    return render_template('analyze.html', analysis=analysis)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)