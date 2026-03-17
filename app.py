import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Configure your Render Postgres connection string.")
    return psycopg.connect(DATABASE_URL)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    mark INTEGER NOT NULL CHECK (mark >= 0 AND mark <= 100)
                );
            """)
        conn.commit()

@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    with get_conn() as conn:
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    "SELECT id, name, mark FROM students WHERE name ILIKE %s ORDER BY id DESC",
                    (f"%{search}%",)
                )
            else:
                cur.execute("SELECT id, name, mark FROM students ORDER BY id DESC")
            students = cur.fetchall()

    return render_template("index.html", students=students, search=search)

@app.route("/add", methods=["POST"])
def add_student():
    name = request.form.get("name", "").strip()
    mark = request.form.get("mark", "").strip()

    if not name or not mark.isdigit():
        return redirect(url_for("index"))

    mark = int(mark)
    if mark < 0 or mark > 100:
        return redirect(url_for("index"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO students (name, mark) VALUES (%s, %s)",
                (name, mark)
            )
        conn.commit()

    return redirect(url_for("index"))

@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mark = request.form.get("mark", "").strip()

        if not name or not mark.isdigit():
            return redirect(url_for("edit_student", student_id=student_id))

        mark = int(mark)
        if mark < 0 or mark > 100:
            return redirect(url_for("edit_student", student_id=student_id))

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE students SET name = %s, mark = %s WHERE id = %s",
                    (name, mark, student_id)
                )
            conn.commit()

        return redirect(url_for("index"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, mark FROM students WHERE id = %s",
                (student_id,)
            )
            student = cur.fetchone()

    if not student:
        return redirect(url_for("index"))

    return render_template("edit.html", student=student)

@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()

    return redirect(url_for("index"))

# initialize once on startup
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
