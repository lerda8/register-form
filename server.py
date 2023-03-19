import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash


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
        admin INTEGER)""")

create_user_tables()

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login/form')
def login_form():
    return render_template('login.html')

@app.route("/login/form/sucess", methods=["POST", "GET"])
def login_go():
    connection = get_connection()
    cursor = connection.cursor()
    name = request.form["name"]
    password = request.form["password"]
    query_login = connection.execute('SELECT * FROM users WHERE username = ?', (name,)).fetchone()
    results=list(query_login)
    if name in results and password == results[2] and results[3] == 1:
        session.clear()
        session['user_id'] = results[1]
        if results[3] == 1:
            user_id = session.get('user_id')
            return redirect(url_for('dashboard', username=user_id))
        else:
            return "regular login"
    if len(results) <= 0: 
        return "WRONG EMAIL OR PASSWORD"
    else:
        return "WRONG EMAIL OR PASSWORD" 
    
@app.route('/dashboard/<username>')
def dashboard(username):
    return render_template("dashboard.html")



@app.route('/logout')
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
        connection.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", (name, password, "1"))
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
        connection.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", (name, password, "0"))
        connection.commit()
        return render_template("reg_user.html", name=name)
    if password != password1 and len(results) > 0: 
        return "THE PASSWORDS ARE NOT MATCHING AND AN ACCOUNT WITH THIS USERNAME ALREADY EXISTS"
    if password != password1:
        return "THE PASSWORDS ARE NOT MATCHING, TRY AGAIN"
    else:
       return "AN ACCOUNT WITH THIS USERNAME ALREADY EXISTS"
    
