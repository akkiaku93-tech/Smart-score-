from flask import Flask, render_template, request, redirect, flash
import os
import psycopg2

app = Flask(__name__)
app.secret_key = "super_secret_key_for_shares"

# रेलवे के PostgreSQL से कनेक्ट करने का फंक्शन
def get_db_connection():
    # रेलवे ऑटोमैटिकली DATABASE_URL एनवायरनमेंट वेरिएबल देता है
    # अगर लोकल चला रहे हैं तो बैकअप के लिए पुराना SQLite लिंक (Testing के लिए)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Postgres Connection
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        # अगर कभी लोकल रन करें तो एरर न आए (सिर्फ सेफ्टी के लिए)
        import sqlite3
        return sqlite3.connect("database.db")

# डेटाबेस सेटअप - Postgres सिंटैक्स के साथ टेबल बनाना
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Postgres में SERIAL PRIMARY KEY का यूज होता है ऑटो-इन्क्रीमेंट के लिए
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            roll_no TEXT PRIMARY KEY,
            name TEXT,
            math INTEGER,
            science INTEGER,
            english INTEGER,
            hindi INTEGER,
            social_science INTEGER,
            total INTEGER,
            percentage REAL,
            status TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# ऐप स्टार्ट होते ही टेबल चेक करना/बनाना
with app.app_context():
    init_db()

# होम पेज (स्टूडेंट सर्च)
@app.route('/')
def index():
    return render_template('index.html')

# रिजल्ट देखने का लॉजिक
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
            "roll_no": student[0],
            "name": student[1],
            "math": student[2],
            "science": student[3],
            "english": student[4],
            "hindi": student[5],
            "social_science": student[6],
            "total": student[7],
            "percentage": student[8],
            "status": student[9]
        }
        return render_template('result.html', student=student_data)
    else:
        flash("Roll Number नहीं मिला! कृपया सही रोल नंबर डालें।")
        return redirect('/')

# एडमिन पैनल (टीचर के लिए मार्क्स एंट्री)
@app.route('/admin', methods=['GET', 'POST'])
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
        elif percentage >= 60:
            status = "1st DIVISION"
        elif percentage >= 45:
            status = "2nd DIVISION"
        elif percentage >= 33:
            status = "3rd DIVISION"
        else:
            status = "FAILED"
            
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Postgres में INSERT OR REPLACE की जगह ON CONFLICT का यूज होता है
            cursor.execute('''
                INSERT INTO scores (roll_no, name, math, science, english, hindi, social_science, total, percentage, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (roll_no) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    math = EXCLUDED.math,
                    science = EXCLUDED.science,
                    english = EXCLUDED.english,
                    hindi = EXCLUDED.hindi,
                    social_science = EXCLUDED.social_science,
                    total = EXCLUDED.total,
                    percentage = EXCLUDED.percentage,
                    status = EXCLUDED.status
            ''', (roll_no, name, math, science, english, hindi, social_science, total, percentage, status))
            
            conn.commit()
            cursor.close()
            conn.close()
            flash(f"Roll No {roll_no} का डेटा सफलतापूर्वक परमानेंटली सेव हो गया!")
        except Exception as e:
            flash(f"Error: {str(e)}")
            
        return redirect('/admin')
        
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
    
