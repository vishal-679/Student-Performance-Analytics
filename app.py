from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3, csv, io
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_PATH = Path(__file__).with_name("students.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                semester INTEGER NOT NULL,
                subject TEXT NOT NULL,
                marks REAL NOT NULL CHECK(marks >= 0 AND marks <= 100)
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            demo = [
                ("Aarav Sharma","CS101","CSE",3,"Python",88),
                ("Diya Patel","CS102","CSE",3,"Python",94),
                ("Rohan Kumar","EC201","ECE",3,"Python",67),
                ("Meera Nair","CS103","CSE",3,"DBMS",79),
                ("Arjun Rao","IT301","IT",5,"DBMS",56),
                ("Sara Khan","CS104","CSE",3,"DBMS",91),
                ("Kabir Das","EC202","ECE",3,"Networks",72),
                ("Ananya Iyer","IT302","IT",5,"Networks",84),
                ("Ishaan Verma","CS105","CSE",3,"Networks",43),
                ("Tara Reddy","EC203","ECE",3,"Mathematics",96),
                ("Vivaan Joshi","IT303","IT",5,"Mathematics",61),
                ("Aditi Menon","CS106","CSE",3,"Mathematics",75),
            ]
            conn.executemany("""INSERT INTO students
                (name,roll_no,department,semester,subject,marks)
                VALUES (?,?,?,?,?,?)""", demo)

@app.route("/")
def index():
    with db() as conn:
        students = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        avg = conn.execute("SELECT ROUND(AVG(marks),1) FROM students").fetchone()[0] or 0
        passed = conn.execute("SELECT COUNT(*) FROM students WHERE marks >= 40").fetchone()[0]
        pass_rate = round((passed / total) * 100, 1) if total else 0
        at_risk = conn.execute("SELECT COUNT(*) FROM students WHERE marks < 40").fetchone()[0]
        subject_rows = conn.execute("""
            SELECT subject, ROUND(AVG(marks),1) AS average
            FROM students GROUP BY subject ORDER BY subject
        """).fetchall()
        dept_rows = conn.execute("""
            SELECT department, ROUND(AVG(marks),1) AS average
            FROM students GROUP BY department ORDER BY department
        """).fetchall()
        distribution = conn.execute("""
            SELECT CASE
                WHEN marks < 40 THEN 'Below 40'
                WHEN marks < 60 THEN '40–59'
                WHEN marks < 80 THEN '60–79'
                ELSE '80–100' END AS band, COUNT(*) AS total
            FROM students GROUP BY band
        """).fetchall()
        top = conn.execute("SELECT name,roll_no,subject,marks FROM students ORDER BY marks DESC LIMIT 5").fetchall()
    return render_template("index.html", students=students, total=total, avg=avg,
        pass_rate=pass_rate, at_risk=at_risk, subject_rows=subject_rows,
        dept_rows=dept_rows, distribution=distribution, top=top)

@app.route("/add", methods=["POST"])
def add_student():
    data = [request.form.get(k, "").strip() for k in
            ("name","roll_no","department","semester","subject","marks")]
    try:
        name, roll, dept, semester, subject, marks = data
        if not all(data): raise ValueError("Please fill in every field.")
        semester = int(semester); marks = float(marks)
        if semester < 1 or semester > 12: raise ValueError("Semester must be between 1 and 12.")
        if marks < 0 or marks > 100: raise ValueError("Marks must be between 0 and 100.")
        with db() as conn:
            conn.execute("""INSERT INTO students
                (name,roll_no,department,semester,subject,marks)
                VALUES (?,?,?,?,?,?)""", (name,roll,dept.upper(),semester,subject,marks))
        flash("Student record added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("That roll number already exists. Use a unique roll number.", "error")
    except (ValueError, TypeError) as e:
        flash(str(e) or "Please enter valid values.", "error")
    return redirect(url_for("index"))

@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    with db() as conn:
        conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    flash("Student record deleted.", "success")
    return redirect(url_for("index"))

@app.route("/export")
def export_csv():
    with db() as conn:
        rows = conn.execute("""SELECT name,roll_no,department,semester,subject,marks,
            CASE WHEN marks >= 40 THEN 'Pass' ELSE 'Needs Improvement' END AS result
            FROM students ORDER BY name""").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name","Roll Number","Department","Semester","Subject","Marks","Result"])
    writer.writerows([tuple(r) for r in rows])
    return Response(output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition":"attachment; filename=student_performance.csv"})

@app.route("/reset-demo", methods=["POST"])
def reset_demo():
    with db() as conn:
        conn.execute("DELETE FROM students")
        demo = [
            ("Aarav Sharma","CS101","CSE",3,"Python",88),
            ("Diya Patel","CS102","CSE",3,"Python",94),
            ("Rohan Kumar","EC201","ECE",3,"Python",67),
            ("Meera Nair","CS103","CSE",3,"DBMS",79),
            ("Arjun Rao","IT301","IT",5,"DBMS",56),
            ("Sara Khan","CS104","CSE",3,"DBMS",91),
            ("Kabir Das","EC202","ECE",3,"Networks",72),
            ("Ananya Iyer","IT302","IT",5,"Networks",84),
            ("Ishaan Verma","CS105","CSE",3,"Networks",43),
            ("Tara Reddy","EC203","ECE",3,"Mathematics",96),
            ("Vivaan Joshi","IT303","IT",5,"Mathematics",61),
            ("Aditi Menon","CS106","CSE",3,"Mathematics",75),
        ]
        conn.executemany("""INSERT INTO students
            (name,roll_no,department,semester,subject,marks)
            VALUES (?,?,?,?,?,?)""", demo)
    flash("Demo data restored.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
