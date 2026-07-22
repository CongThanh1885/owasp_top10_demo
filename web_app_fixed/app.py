from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3, os, html, secrets
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecret"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect("db/users.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("base.html")

# --- SQL Injection fixed ---
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session["user"] = username
            return "Login success!"
        return "Invalid credentials!"
    return render_template("login.html")

# --- XSS fixed ---
@app.route("/comment", methods=["GET","POST"])
def comment():
    if request.method == "POST":
        comment = request.form["comment"]
        safe_comment = html.escape(comment)
        return render_template("comment.html", comment=safe_comment)
    return render_template("comment.html", comment=None)

# --- CSRF fixed ---
@app.route("/change-password", methods=["GET","POST"])
def change_password():
    if request.method == "GET":
        token = secrets.token_hex(16)
        session["csrf_token"] = token
        return render_template("change_password.html", token=token)
    else:
        if request.form.get("csrf_token") != session.get("csrf_token"):
            return "CSRF detected!", 403
        # update password
        username = request.form["username"]
        newPassword = request.form["newPassword"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=? WHERE username=?", (newPassword, username))
        conn.commit()
        conn.close()
        return "Password changed!"

# --- File Upload fixed ---
@app.route("/upload", methods=["GET","POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return "File uploaded safely!"
        return "Invalid file type!", 400
    return render_template("upload.html")

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("db", exist_ok=True)
    app.run(host="0.0.0.0", port=5656)
