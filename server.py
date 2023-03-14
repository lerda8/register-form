from flask import Flask, render_template, request


app = Flask(__name__)


@app. route("/")
def index():
    return render_template('index.html')


@app. route( '/login')
def login():
    return render_template('login.html')


@app. route('/register')
def register():
    return render_template('register.html')

@app.route("/dashboard/<username>")
def dashboard(username=None):
    return render_template("dashboard.html", username=username)

@app.route("/admin_dashboard/<username>")
def accoadmin_dashboard(username=None):
    return render_template("admin_dashboard.html", username=username)