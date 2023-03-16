import sqlite3
from flask import Flask, render_template, request


app = Flask(__name__)

def get_connection():
    conn = sqlite3.connect('users.db')
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

@app.route('/register/form', methods=["POST", "GET"])
def register_form():
    return render_template('register.html')

@app.route("/register/admin", methods=["POST", "GET"])
def new_account():
    db = get_connection()
    name = request.form["name"]
    password = request.form["password"]
    password1 = request.form["password1"]
    if password == password1:
        db.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", (name, password, "1"))
        db.commit()
        return render_template("admin_user.html", name=name)
    else:
        return "THE PASSWORDS ARE NOT MATCHING, TRY AGAIN"
    
@app.route("/register/reg_account", methods=["POST", "GET"])
def new_reg_account():
    db = get_connection()
    name = request.form["name"]
    password = request.form["password"]
    password1 = request.form["password1"]
    if password == password1:
        db.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", (name, password, "0"))
        db.commit()
        return render_template("reg_user.html", name=name)
    else:
        return "THE PASSWORDS ARE NOT MATCHING, TRY AGAIN"
    

    


