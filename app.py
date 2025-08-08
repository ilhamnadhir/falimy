from flask import Flask, render_template, request, redirect, url_for
import sqlite3, random, os

app = Flask(__name__)
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
    c.execute("SELECT DISTINCT * FROM users WHERE gender = 'Female' AND name != ?", (username,))
    females = c.fetchall()

    # Select possible fathers (male, not current user)
    c.execute("SELECT DISTINCT * FROM users WHERE gender = 'Male' AND name != ?", (username,))
    males = c.fetchall()

    # All others for siblings (excluding chosen mother and father later)
    c.execute("SELECT DISTINCT * FROM users WHERE name != ?", (username,))
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

if __name__ == "__main__":
    app.run(debug=True)
