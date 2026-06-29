from flask import Flask, render_template, request, redirect, flash, session, url_for
import os
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps

app = Flask(__name__)

# SECRET_KEY ab Railway Environment Variable se aayega
app.secret_key = os.environ.get('SECRET_KEY', "fallback_secret_key_change_me")

# ADMIN PASSWORD bhi Railway Variable se aayega
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', "admin@123")

# Login Required Decorator - Admin pages ko protect karta hai
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Pehle Login Karo!")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# रेलवे के PostgreSQL से कनेक्ट करने का फंक्शन
def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        import sqlite3
        return sqlite3.connect("database.db")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            roll_no TEXT PRIMARY KEY, name TEXT, math INTEGER, science INTEGER,
            english INTEGER, hindi INTEGER, social_science INTEGER, total INTEGER,
            percentage REAL, status TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

with app.app_context():
    init_db()

# Admin Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash("Login Successful!")
            return redirect('/admin/view')
        else:
            flash("Galat Password!")
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Logout Ho Gaya")
    return redirect('/')

# होम पेज - Student Search - Public hai
@app.route('/')
def index():
    return render_template('index.html')

# Result Search - Public hai
@app.route('/search', methods=['POST'])
def search():
    roll_no = request.form.get('roll_no').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scores WHERE roll_no = %s", (roll_no,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    if student:
        student_data = {
            "roll_no": student[0], "name": student[1], "math": student[2],
            "science": student[3], "english": student[4], "hindi": student[5],
            "social_science": student[6], "total": student[7],
            "percentage": student[8], "status": student[9]
        }
        return render_template('result.html', student=student_data)
    else:
        flash("Roll Number नहीं मिला!")
        return redirect('/')

# Admin Panel - PASSWORD PROTECTED
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no').strip()
        name = request.form.get('name').strip()
        math = int(request.form.get('math'))
        science = int(request.form.get('science'))
        english = int(request.form.get('english'))
        hindi = int(request.form.get('hindi'))
        social_science = int(request.form.get('social_science'))

        total = math + science + english + hindi + social_science
        percentage = round((total / 500) * 100, 2)

        if math < 33 or science < 33 or english < 33 or hindi < 33 or social_science < 33:
            status = "FAILED"
        elif percentage >= 60: status = "1st DIVISION"
        elif percentage >= 45: status = "2nd DIVISION"
        elif percentage >= 33: status = "3rd DIVISION"
        else: status = "FAILED"

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scores (roll_no, name, math, science, english, hindi, social_science, total, percentage, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (roll_no) DO UPDATE SET
                    name = EXCLUDED.name, math = EXCLUDED.math, science = EXCLUDED.science,
                    english = EXCLUDED.english, hindi = EXCLUDED.hindi,
                    social_science = EXCLUDED.social_science, total = EXCLUDED.total,
                    percentage = EXCLUDED.percentage, status = EXCLUDED.status
            ''', (roll_no, name, math, science, english, hindi, social_science, total, percentage, status))
            conn.commit()
            cursor.close()
            conn.close()
            flash(f"Roll No {roll_no} का डेटा सेव हो गया!")
        except Exception as e:
            flash(f"Error: {str(e)}")
        return redirect('/admin')
    return render_template('admin.html')

# View All Students - PASSWORD PROTECTED
@app.route('/admin/view')
@login_required
def view_all():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM scores ORDER BY CAST(roll_no AS INTEGER)")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_all.html', students=students)

# Delete Student - PASSWORD PROTECTED
@app.route('/admin/delete/<roll_no>')
@login_required
def delete_student(roll_no):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scores WHERE roll_no = %s", (roll_no,))
        conn.commit()
        cursor.close()
        conn.close()
        flash(f"Roll No {roll_no} Delete Ho Gaya!")
    except Exception as e:
        flash(f"Delete Error: {str(e)}")
    return redirect('/admin/view')

if __name__ == '__main__':
    app.run(debug=True)
