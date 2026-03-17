import os
import logging
from flask import Flask, render_template, request, redirect, url_for
import psycopg

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL)

def init_db():
    app.logger.info("Initializing database...")
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
    app.logger.info("Database initialized")

@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    app.logger.info("Loading index page. search=%s", search)

    with get_conn() as conn:
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    "SELECT id, name, mark FROM students WHERE name ILIKE %s ORDER BY id DESC",
                    (f"%{search}%",)
                )
            else:
                cur.execute("SELECT id, name, mark FROM students ORDER BY id ASC")
            students = cur.fetchall()

    return render_template("index.html", students=students, search=search)

@app.route("/add", methods=["POST"])
def add_student():
    name = request.form.get("name", "").strip()
    mark_raw = request.form.get("mark", "").strip()

    if not name or not mark_raw.isdigit():
        app.logger.warning("Invalid add request: name=%r mark=%r", name, mark_raw)
        return redirect(url_for("index"))

    mark = int(mark_raw)
    if not 0 <= mark <= 100:
        app.logger.warning("Mark out of range: %s", mark)
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
        mark_raw = request.form.get("mark", "").strip()

        if not name or not mark_raw.isdigit():
            return redirect(url_for("edit_student", student_id=student_id))

        mark = int(mark_raw)
        if not 0 <= mark <= 100:
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

    if student is None:
        app.logger.warning("Student not found: %s", student_id)
        return redirect(url_for("index"))

    return render_template("edit.html", student=student)

@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()

    return redirect(url_for("index"))

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception("Unhandled exception: %s", e)
    return "Application error. Check Render logs.", 500

init_db()
