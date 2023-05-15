import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash, send_file
import os


app = Flask(__name__)
app.secret_key = 'laksja9asd80asd09asd098asdsdkdf7763sdsds'

###Database Creation

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
        file_name TEXT,
        file_path TEXT,
        project_id TEXT,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)""")

create_task_tables()


###Home

@app.route("/")
def index():
    return render_template('index.html')

###Login/Register/Logout/Login

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
        session['username'] = results[1]
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

    
###User Management

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

@app.route("/delete_account", methods=["POST"])
def delete_account():
    user_id = session.get('user_id')
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
    connection.commit()
    session.clear()
    return redirect(url_for('index'))

###TODO Page

@app.route("/tasks/", methods=["GET", "POST"])
def tasks():
    connection = get_connection()
    cursor = connection.cursor()
    user_id = session.get("user_id")
    tasks_query = "SELECT projects.name, tasks.id, tasks.name, tasks.description, tasks.due_date, tasks.is_completed, tasks.file_name, tasks.file_path FROM tasks JOIN projects ON tasks.project_id = projects.id WHERE tasks.user_id = ?;"
    cursor.execute(tasks_query,(user_id,))
    tasks = cursor.fetchall()
    projects_query = "SELECT id, name FROM projects WHERE user_id = ?;"
    cursor.execute(projects_query, (user_id,))
    projects = cursor.fetchall()
    connection.close()
    finished=[]
    unfinished=[]
    projects_finished=[]
    projects_unfinished=[]
    for task in tasks:
       if task[5]==1:
           finished.append(task)
       elif task[5]==0:
           unfinished.append(task)
    for project in projects:
        for task in unfinished:
            if task[0] == project[1]:
                projects_unfinished.append(project)
                break
            else:
                pass
        for task in finished:
            if task[0] == project[1]:
                projects_finished.append(project)
                break
        else:
            pass

    return render_template('tasks.html', projects = projects, tasks = tasks, unfinished = unfinished, finished = finished, projects_unfinished = projects_unfinished, projects_finished = projects_finished)

        


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        todo_project = request.form['todo-project']
        todo_new_project = request.form['todo-new-project']
        todo_text = request.form['todo-text']
        todo_description = request.form['todo-description']
        todo_date = request.form['todo-date']
        file = request.files.get('todo-file')
        user_id = session.get('user_id')
        full_access = session.get('full_access', False)
        conn = sqlite3.connect('users.db')
        c = conn.cursor()        
        if not full_access:
            c.execute("SELECT COUNT(*) FROM projects WHERE user_id=?", (user_id,))
            num_projects = c.fetchone()[0]
            if num_projects >= 5 and todo_new_project:
                return "You have reached the maximum number of projects. Please upgrade to full access to create more projects."
                    
            c.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (user_id,))
            num_tasks = c.fetchone()[0]
            if num_tasks >= 15:
                return "You have reached the maximum number of tasks. Please upgrade to full access to create more tasks."

        
        if not todo_project and not todo_new_project:
            return "Please choose a project or create a new project."
        if todo_project and todo_new_project:
            return "You can choose either a new project or an existing project, not both."
        
        try:
            if todo_new_project:
                c.execute("SELECT id FROM projects WHERE name=? AND user_id=?", (todo_new_project, user_id))
                project = c.fetchone()
                if not project:
                    c.execute("INSERT INTO projects (name, user_id) VALUES (?, ?)", (todo_new_project, user_id))
                    project_id = c.lastrowid
                else:
                    project_id = project[0]
            else:
                project_id = todo_project
                
            if file:
                filename = file.filename
                file_id = filename
                file_path = os.path.join('static/uploads', file_id)
                c.execute("INSERT INTO tasks (name, description, due_date, user_id, project_id, file_name, file_path) VALUES (?, ?, ?, ?, ?, ?, ?)", (todo_text, todo_description, todo_date, user_id, project_id, file_id, file_path))
                file.save(file_path)
            else:
                c.execute("INSERT INTO tasks (name, description, due_date, user_id, project_id) VALUES (?, ?, ?, ?, ?)", (todo_text, todo_description, todo_date, user_id, project_id))
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()
        return redirect(url_for('new_task'))
    else:
        return 'Invalid request method'



@app.route('/complete-task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT is_completed FROM tasks WHERE id = ?', (task_id,))
    is_completed = c.fetchone()[0]
    if is_completed == 1:
        c.execute('UPDATE tasks SET is_completed = ? WHERE id = ?', (0, task_id))
    else:
        c.execute('UPDATE tasks SET is_completed = ? WHERE id = ?', (1, task_id))
    conn.commit()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/new-task/')
def new_task():
    connection = get_connection()
    cursor = connection.cursor()
    user_id = session.get("user_id")
    project_query = "SELECT * FROM projects WHERE user_id = ?;"
    project_execute = cursor.execute(project_query,(user_id,))
    project = project_execute.fetchall()
    connection.close()
    have_projects = len(project)
    connection = get_connection()
    cursor = connection.cursor()
    all_query = "SELECT * FROM projects LEFT JOIN tasks ON projects.id = tasks.project_id WHERE projects.user_id = ?;"
    everything_execute = cursor.execute(all_query,(user_id,))
    everything = everything_execute.fetchall()
    connection.close()
    #return project
    #return redirect(url_for('session_check'))
    return render_template("new_task.html", everything=everything, project = project, have_projects = have_projects)



###Dashboards

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
    

@app.route('/open-file/<path:filename>', methods=["POST"])
def open_file(filename):    
    return send_file(filename, as_attachment=False) 
   


@app.route("/debile")
def session_check():
    session_list = []
    session_dict = {}
    session_list.append(str(session.get('user_id')))
    session_list.append(str(session.get('is_admin')))
    session_list.append(str(session.get('full_access')))
    session_list.append(str(session.get('username')))
    session_dict = {
        'user_id':session_list[0],
        'is_admin':session_list[1],
        'full_access':session_list[2],
        'username':session_list[3]
    }
    return session_dict
    return session_list



    
