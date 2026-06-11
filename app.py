from flask import Flask, render_template, request, redirect, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_key_for_shares"

# डेटाबेस सेटअप - 5 सब्जेक्ट्स के साथ टेबल बनाना
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
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
    conn.close()

# ऐप स्टार्ट होते ही खुद-ब-खुद टेबल बनाने के लिए
with app.app_context():
    init_db()

# होम पेज (सिर्फ स्टूडेंट सर्च - एडमिन बटन हटा दिया गया है)
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

# सीक्रेट एडमिन पैनल (टीचर के लिए मार्क्स एंट्री - सिर्फ /admin लिंक से खुलेगा)
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
        
        # 5 सब्जेक्ट्स का टोटल और परसेंटेज लॉजिक
        total = math + science + english + hindi + social_science
        percentage = round((total / 500) * 100, 2)
        
        # फेल और डिवीज़न (1st, 2nd, 3rd) का लॉजिक
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
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scores (roll_no, name, math, science, english, hindi, social_science, total, percentage, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (roll_no, name, math, science, english, hindi, social_science, total, percentage, status))
            conn.commit()
            conn.close()
            flash(f"Roll No {roll_no} का डेटा सफलतापूर्वक सेव हो गया!")
        except Exception as e:
            flash(f"Error: {str(e)}")
            
        return redirect('/admin')
        
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
    
