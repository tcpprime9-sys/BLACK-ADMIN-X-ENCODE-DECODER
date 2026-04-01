from flask import Flask, render_template, request, redirect, session, send_file
import base64, sqlite3, io, os
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = "black_admin_pro"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS history(action TEXT, filename TEXT)")
    conn.commit()
    conn.close()

init_db()

# ================= ENCODE SYSTEM =================
def multi_encode(data, times):
    for _ in range(times):
        data = base64.b64encode(data)
    return data

def auto_decode(data):
    while True:
        try:
            data = base64.b64decode(data)
        except:
            break
    return data

# ================= ENCRYPTION =================
def gen_key(p):
    return base64.urlsafe_b64encode(p.ljust(32)[:32].encode())

def encrypt(data, p):
    return Fernet(gen_key(p)).encrypt(data)

def decrypt(data, p):
    return Fernet(gen_key(p)).decrypt(data)

# ================= ROUTES =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["user"]
        p=request.form["pass"]
        conn=sqlite3.connect("database.db")
        c=conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        if c.fetchone():
            session["user"]=u
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dash():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

@app.route("/process", methods=["POST"])
def process():
    file=request.files["file"]
    action=request.form["action"]
    times=int(request.form.get("times",1))
    password=request.form.get("password","")

    data=file.read()

    if action=="encode":
        result=multi_encode(data,times)
        name="encoded.txt"

    elif action=="decode":
        result=auto_decode(data)
        name="decoded"

    elif action=="encrypt":
        result=encrypt(data,password)
        name="encrypted.bin"

    elif action=="decrypt":
        result=decrypt(data,password)
        name="decrypted"

    conn=sqlite3.connect("database.db")
    c=conn.cursor()
    c.execute("INSERT INTO history VALUES (?,?)",(action,file.filename))
    conn.commit()
    conn.close()

    return send_file(io.BytesIO(result), as_attachment=True, download_name=name)

if __name__=="__main__":
    app.run(debug=True)
