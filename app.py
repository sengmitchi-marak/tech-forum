from flask import Flask, render_template, request, redirect, session, flash
import os
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "tech_forum_secret_key"


# DATABASE CONNECTION
def get_db_connection():
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL")
    )
    return conn

# CREATE DATABASE TABLES
def create_tables():

    conn = get_db_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    # QUESTIONS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            tag VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id)
        )
    """)

    # ANSWERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            answer TEXT NOT NULL,
            question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()



# HOME PAGE
@app.route("/")
def home():

    search = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:

        cursor.execute("""
        SELECT
            questions.id,
            questions.title,
            questions.description,
            questions.created_at,
            users.username,
            COUNT(DISTINCT likes.id),
            COUNT(DISTINCT answers.id)

        FROM questions

        JOIN users
        ON questions.user_id = users.id

        LEFT JOIN likes
        ON questions.id = likes.question_id

        LEFT JOIN answers
        ON questions.id = answers.question_id

        WHERE LOWER(questions.title)
        LIKE LOWER(%s)

        GROUP BY
        questions.id,
        users.username

        ORDER BY questions.created_at DESC
        """, ('%' + search + '%',))

    else:

        cursor.execute("""
        SELECT
            questions.id,
            questions.title,
            questions.description,
            questions.created_at,
            users.username,
            COUNT(DISTINCT likes.id),
            COUNT(DISTINCT answers.id)

        FROM questions

        JOIN users
        ON questions.user_id = users.id

        LEFT JOIN likes
        ON questions.id = likes.question_id

        LEFT JOIN answers
        ON questions.id = answers.question_id

        GROUP BY
        questions.id,
        users.username

        ORDER BY questions.created_at DESC LIMIT 5
        """)

    questions = cursor.fetchall()

    if len(questions) == 0:
        message = "No matching questions found."
    else:
        message = ""


    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        questions=questions,
        message=message
    )

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        print("POST request received")
        print(request.form)
        
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check passwords
        if password != confirm_password:

            return render_template(
                "register.html",
                error="Passwords do not match!"
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check whether email already exists
        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()
            conn.close()

            return render_template(
                "register.html",
                error="Email already registered!"
            )

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert user
        cursor.execute("""
            INSERT INTO users
            (username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, hashed_password))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()
        print("User:",user)

        cursor.close()
        conn.close()

        # Check user
        if user:

            stored_password = user[3]
            print("Password correct:",check_password_hash(stored_password,password))

            # Compare entered password with hashed password
            if check_password_hash(
                stored_password,
                password
            ):

                session["user_id"] = user[0]
                session["username"] = user[1]
                session["email"] = user[2]

                #Check for admin
                if email == "admin@gmail.com" and password == "admin123":
                    session["admin"] = True
                else:
                    session["admin"] = False

                return redirect("/")

        return render_template(
            "login.html",
            error="Invalid email or password!"
        )

    return render_template("login.html")


#Admin DASHBOARD
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Total Questions
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]

    # Total Answers
    cursor.execute("SELECT COUNT(*) FROM answers")
    total_answers = cursor.fetchone()[0]

    # Total Likes
    cursor.execute("SELECT COUNT(*) FROM likes")
    total_likes = cursor.fetchone()[0]

    # Show all users
    cursor.execute("""
        SELECT id, username, email
        FROM users
        ORDER BY id
    """)
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_questions=total_questions,
        total_answers=total_answers,
        total_likes=total_likes,
        users=users
    )


#DELETE USER ACCOUNT
@app.route("/admin/delete_user/<int:user_id>")
def admin_delete_user(user_id):

    if not session.get("admin"):
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin")


# ASK QUESTION
@app.route("/ask", methods=["GET", "POST"])
def ask_question():

    # User must be logged in
    if "user_id" not in session:
        flash("Only registered members can ask questions. Please login first.")
        return redirect("/login")

    if request.method == "POST":

        title = request.form["title"].strip()
        description = request.form["description"].strip()
        user_id = session["user_id"]

        # ✅ Check for empty fields
        if not title or not description:
            return render_template(
                "ask_question.html",
                error="⚠️ Please fill in all the fields before posting."
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO questions
            (title, description, user_id)
            VALUES (%s, %s, %s)
        """, (
            title,
            description,
            user_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/")

    return render_template("ask_question.html")

# QUESTION DETAILS
@app.route("/question/<int:id>")
def question(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get question and question author's username
    cursor.execute("""
        SELECT
            questions.id,
            questions.title,
            questions.description,
            questions.tag,
            questions.created_at,
            users.username,
            questions.user_id
        FROM questions
        JOIN users
            ON questions.user_id = users.id
        WHERE questions.id = %s
    """, (id,))

    question_data = cursor.fetchone()

    # If question doesn't exist
    if question_data is None:

        cursor.close()
        conn.close()

        return "Question not found", 404

    # Get answers and answer authors
    cursor.execute("""
        SELECT
            answers.id,
            answers.answer,
            answers.created_at,
            users.username
        FROM answers
        JOIN users
            ON answers.user_id = users.id
        WHERE answers.question_id = %s
        ORDER BY answers.created_at ASC
    """, (id,))

    answers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "question.html",
        question=question_data,
        answers=answers,
        question_id=id
    )


#EDIT QUESTION
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_question(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,title, description
        FROM questions
        WHERE id=%s AND user_id=%s
    """, (id, session["user_id"]))

    question = cursor.fetchone()

    if question is None:
        cursor.close()
        conn.close()
        return "Unauthorized", 403

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        cursor.execute("""
            UPDATE questions
            SET title=%s,
                description=%s
            WHERE id=%s
        """, (title, description, id))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(f"/question/{id}")

    cursor.close()
    conn.close()

    return render_template(
        "edit_question.html",
        question=question
    )


#DELETE QUESTION
@app.route("/delete_question/<int:id>")
def delete_question(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete answers first
    cursor.execute(
        "DELETE FROM answers WHERE question_id=%s",
        (id,)
    )

    cursor.execute("""
        DELETE FROM questions
        WHERE id=%s
        AND user_id=%s
    """, (
        id,
        session["user_id"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/")


# POST ANSWER
@app.route("/answer/<int:question_id>", methods=["POST"])
def answer(question_id):
    if "user_id" not in session:
     flash("🔒 Please login to answer questions.")
     return redirect("/login")


    #temporary
    answer_text = request.form["answer"]

    print("Answer received:", answer_text)
    print("Question ID:", question_id)
    print("User ID:", session["user_id"]) #temp

    # User must be logged in
    if "user_id" not in session:
        return redirect("/login")

    answer_text = request.form["answer"]

    # Don't allow empty answers
    if not answer_text.strip():
        return redirect(f"/question/{question_id}")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO answers
        (answer, question_id, user_id)
        VALUES (%s, %s, %s)
    """, (
        answer_text,
        question_id,
        user_id
    ))
    

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/question/{question_id}")

#PROFILE PAGE
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = session["user_id"]

    # Count questions asked
    cursor.execute(
        "SELECT COUNT(*) FROM questions WHERE user_id = %s",
        (user_id,)
    )
    total_questions = cursor.fetchone()[0]

    # Count answers given
    cursor.execute(
        "SELECT COUNT(*) FROM answers WHERE user_id = %s",
        (user_id,)
    )
    total_answers = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        username=session["username"],
        email=session["email"],
        total_questions=total_questions,
        total_answers=total_answers
    )

#Like Button 
@app.route("/like/<int:question_id>")
def like(question_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM likes
        WHERE user_id=%s AND question_id=%s
    """, (user_id, question_id))

    like = cursor.fetchone()

    if like:
        cursor.execute("""
            DELETE FROM likes
            WHERE user_id=%s AND question_id=%s
        """, (user_id, question_id))
    else:
        cursor.execute("""
            INSERT INTO likes(user_id,question_id)
            VALUES(%s,%s)
        """, (user_id, question_id))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/")


#DELETE ACCOUNT
@app.route("/delete_account")
def delete_account():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    #DELETE ALL ANSWERS BELONGING TO THE USERS QUESTIONS
    cursor.execute("""
        DELETE FROM answers
        WHERE question_id IN(
        SELECT id FROM questions
        WHERE user_id=%s)
    """,(user_id,))

    #DELETE ANSWERS WRITTEN BY USERS
    cursor.execute("DELETE FROM questions WHERE id=%s",(user_id,))

    conn.commit()
    cursor.close()
    conn.close()

    session.clear()
    return redirect("/")


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")



# RUN APPLICATION
if __name__ == "__main__":

    create_tables()

    app.run(debug=True)