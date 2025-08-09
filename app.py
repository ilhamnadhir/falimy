from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, random, os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to something unique & strong
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Create uploads folder if not exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Create table if not exists
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        photo TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        photo = request.files["photo"]

        if photo:
            filename = f"{name}_{photo.filename}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(filepath)
        else:
            filename = ""

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (name, age, gender, photo) VALUES (?, ?, ?, ?)", (name, age, gender, filename))
        conn.commit()
        conn.close()
        return redirect(url_for("match", username=name))
    return render_template("index.html")

@app.route("/match/<username>")
def match(username):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Get the current user
    c.execute("SELECT * FROM users WHERE name = ?", (username,))
    current_user = c.fetchone()

    # Select possible mothers (female, not current user)
    c.execute("SELECT * FROM users WHERE gender = 'Female' AND name != ?", (username,))
    females = c.fetchall()

    # Select possible fathers (male, not current user)
    c.execute("SELECT * FROM users WHERE gender = 'Male' AND name != ?", (username,))
    males = c.fetchall()

    # All others for siblings
    c.execute("SELECT * FROM users WHERE name != ?", (username,))
    all_others = c.fetchall()

    conn.close()

    if not females or not males or len(all_others) < 3:
        return "Not enough users in the database to find a full family yet!"

    mother = random.choice(females)
    father = random.choice(males)

    # Exclude current user, mother, father from sibling candidates
    sibling_candidates = [p for p in all_others if p != mother and p != father]
    sibling = random.choice(sibling_candidates)

    sibling_role = "Brother" if sibling[3] == "Male" else "Sister"

    return render_template("match.html", username=username,
                           mother=mother, father=father,
                           sibling=sibling, sibling_role=sibling_role)

# Admin login
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "mypassword123":  # Change this to your chosen password
            session["admin_logged_in"] = True
            return redirect(url_for("all_users"))
        else:
            return "Wrong password!"
    return '''
    <form method="POST">
        <input type="password" name="password" placeholder="Enter admin password" required>
        <button type="submit">Login</button>
    </form>
    '''

# Admin page showing all users
@app.route("/all-users")
def all_users():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("all_users.html", users=users)

# Admin logout
@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
