from flask import Flask, render_template, request, redirect, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_key_for_shares"

# डेटाबेस सेटअप - टेबल बनाना
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT EXISTS,
            math INTEGER,
            science INTEGER,
            english INTEGER,
            total INTEGER,
            percentage REAL
        )
    ''')
    conn.commit()
    conn.close()

# ऐप स्टार्ट होते ही खुद-ब-खुद टेबल बनाने के लिए (Gunicorn/Docker के लिए ज़रूरी)
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
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scores WHERE roll_no = ?", (roll_no,))
    student = cursor.fetchone()
    conn.close()
    
    if student:
        student_data = {
            "roll_no": student[0],
            "name": student[1],
            "math": student[2],
            "science": student[3],
            "english": student[4],
            "total": student[5],
            "percentage": student[6]
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
        
        total = math + science + english
        percentage = round((total / 300) * 100, 2)
        
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scores (roll_no, name, math, science, english, total, percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (roll_no, name, math, science, english, total, percentage))
            conn.commit()
            conn.close()
            flash(f"Roll No {roll_no} का डेटा सफलतापूर्वक सेव हो गया!")
        except Exception as e:
            flash(f"Error: {str(e)}")
            
        return redirect('/admin')
        
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
    
