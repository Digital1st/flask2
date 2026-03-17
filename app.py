import os
from flask import Flask, render_template, request, redirect
import psycopg

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/testdb")

def get_conn():
    return psycopg.connect(DATABASE_URL)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    mark INTEGER
                );
            """)
        conn.commit()

@app.route("/")
def index():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students ORDER BY id DESC")
            students = cur.fetchall()
    return render_template("index.html", students=students)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    mark = request.form["mark"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO students (name, mark) VALUES (%s, %s)", (name, mark))
        conn.commit()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":
        name = request.form["name"]
        mark = request.form["mark"]
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE students SET name=%s, mark=%s WHERE id=%s", (name, mark, id))
            conn.commit()
        return redirect("/")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students WHERE id=%s", (id,))
            student = cur.fetchone()

    return render_template("edit.html", student=student)

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE id=%s", (id,))
        conn.commit()
    return redirect("/")

init_db()

if __name__ == "__main__":
    app.run(debug=True)
