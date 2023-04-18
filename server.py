import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
import uuid


app = Flask(__name__)
app.secret_key = 'laksja9asd80asd09asd098asdsdkdf7763sdsds'

def get_connection():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    return conn

def create_user_tables():
    db = get_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        admin TEXT,
        plan INTEGER DEFAULT 0,
        blocked INTEGER NOT NULL DEFAULT 0)""")

create_user_tables()

def create_project_tables():
    db = get_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS projects
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)""")

create_project_tables()

def create_task_tables():
    db = get_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        due_date DATE NOT NULL,
        is_completed INTEGER NOT NULL DEFAULT 0,
        project_id TEXT,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)""")

create_task_tables()

def create_files_tables():
    db = get_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS files
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        path TEXT NOT NULL,
        task_id INTEGER NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE)""")

create_files_tables()


@app.route('/change-plan', methods=['POST'])
def change_plan():
    user_id = request.form['user_id']
    full_access = str(session['full_access'])
    if full_access == "True":
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET plan = ? WHERE username = ?', (0, user_id))
        connection.commit()
        session['full_access'] = False
        return redirect(url_for('dashboard', username=user_id, full_access=session['full_access']))
    else:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET plan = ? WHERE username = ?', (1, user_id))
        connection.commit()
        session['full_access'] = True
        return redirect(url_for('dashboard', username=user_id, full_access=session['full_access']))

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login/form')
def login_form():
    return render_template('login.html')

@app.route("/login/form/success", methods=["POST", "GET"])
def login_go():
    connection = get_connection()
    cursor = connection.cursor()
    name = request.form["name"]
    password = request.form["password"]
    query_login = connection.execute('SELECT * FROM users WHERE username = ?', (name,)).fetchone()
    if query_login is None:
        return "WRONG EMAIL OR PASSWORD"
    results = list(query_login)
    if name in results and password == results[2]:
        session.clear()
        session['user_plan'] = results[4]
        session['user_id'] = results[0]
        if results[3] == 'yes':
            if results[4] == 0:
                session['full_access'] = False
                session['is_admin'] = True
                full_access = session.get('full_access')
                user_id = results[1]
                return redirect(url_for('dashboard',username=user_id, full_access=full_access))
            else:
                session['full_access'] = True
                session['is_admin'] = True
                full_access = session.get('full_access')
                user_id = results[1]
                return redirect(url_for('dashboard',username=user_id, full_access=full_access))
        else:
            if results[4] == 0:
                session['full_access'] = False
                session['is_admin'] = False
                full_access = session.get('full_access')
                user_id = results[1]
                return redirect(url_for('dashboard',username=user_id, full_access=full_access))
            else:
                session['full_access'] = True
                session['is_admin'] = False
                full_access = session.get('full_access')
                user_id = results[1]
                return redirect(url_for('dashboard',username=user_id, full_access=full_access))
    else:
        return "ERROR"

@app.route("/my-todo/", methods=["GET", "POST"])
def todo():
    connection = get_connection()
    cursor = connection.cursor()
    user_id = session["user_id"]
    query = "SELECT * FROM tasks WHERE user_id = ?"
    cursor.execute(query, (user_id,))
    tasks = cursor.fetchall()

    # Query the files table for each task
    files = []
    for task in tasks:
        task_id = task[0]
        query = "SELECT * FROM files WHERE task_id = ?"
        cursor.execute(query, (task_id,))
        task_files = cursor.fetchall()
        files.append(task_files)

    connection.close()
    return render_template('to-do.html', tasks=tasks, files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        todo_text = request.form['todo-text']
        todo_description = request.form['todo-description']
        todo_date = request.form['todo-date']
        file = request.files['todo-file']
        filename = secure_filename(file.filename)
        user_id = session.get('user_id')
        file_id = str(uuid.uuid4())
        file_path = os.path.join('static/uploads', file_id)
        file.save(file_path)
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO tasks (name, description, due_date, user_id) VALUES (?, ?, ?, ?)",
                  (todo_text, todo_description, todo_date, user_id))
        task_id = c.lastrowid
        c.execute("INSERT INTO files (name, path, task_id) VALUES (?, ?, ?)",
                  (filename, file_path, task_id))
        conn.commit()
        conn.close()
        return redirect(url_for('todo'))
    else:
        return 'Invalid request method'




@app.route("/dashboard/<username>", methods=["GET"])
def dashboard(username):
    if 'user_id' in session:
        is_admin = session.get('is_admin')
        user_type = 'Administrator' if is_admin else 'Regular User'
        connection = get_connection()
        cursor = connection.cursor()
        query = 'SELECT * FROM users'
        users = cursor.execute(query).fetchall()
        connection.close()
        return render_template('dashboard.html', username=username, user_type=user_type, users=users)
    else:
        return redirect(url_for('login_form'))


@app.route("/delete_account", methods=["POST"])
def delete_account():
    user_id = session.get('user_id')
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
    connection.commit()
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' in session and session.get('is_admin'):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
        connection.commit()
        connection.close()
        username = session.get('user_id')
        return redirect(url_for('dashboard', username=username))
    else:
        return redirect(url_for('login_form'))

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return render_template("logout.html")

@app.route('/register/form', methods=["POST", "GET"])
def register_form():
    return render_template('register.html')

@app.route("/register/admin", methods=["POST", "GET"])
def new_account():
    connection = get_connection()
    cursor = connection.cursor()
    name = request.form["name"]
    password = request.form["password"]
    password1 = request.form["password1"]
    query = "SELECT username FROM users where username='"+name+"'"
    cursor.execute(query)
    results = cursor.fetchall()
    if password == password1 and len(results) == 0:
        connection.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", (name, password, "yes"))
        connection.commit()
        return render_template("admin_user.html", name=name)
    if password != password1 and len(results) > 0: 
        return "THE PASSWORDS ARE NOT MATCHING AND AN ACCOUNT WITH THIS USERNAME ALREADY EXISTS"
    if password != password1:
        return "THE PASSWORDS ARE NOT MATCHING, TRY AGAIN"
    else:
        return "AN ACCOUNT WITH THIS USERNAME ALREADY EXISTS"

@app.route("/register/reg_account", methods=["POST", "GET"])
def new_reg_account():
    connection = get_connection()
    cursor = connection.cursor()
    name = request.form["name"]
    password = request.form["password"]
    password1 = request.form["password1"]
    query = "SELECT username FROM users where username='"+name+"'"
    cursor.execute(query)
    results = cursor.fetchall()
    if password == password1 and len(results) == 0:
        connection.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", (name, password, "no"))
        connection.commit()
        return render_template("reg_user.html", name=name)
    if password != password1 and len(results) > 0: 
        return "THE PASSWORDS ARE NOT MATCHING AND AN ACCOUNT WITH THIS USERNAME ALREADY EXISTS"
    if password != password1:
        return "THE PASSWORDS ARE NOT MATCHING, TRY AGAIN"
    else:
       return "AN ACCOUNT WITH THIS USERNAME ALREADY EXISTS"
    
