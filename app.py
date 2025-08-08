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
        photo = request.files["photo"]

        if photo:
            filename = f"{name}_{photo.filename}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(filepath)
        else:
            filename = ""

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (name, age, photo) VALUES (?, ?, ?)", (name, age, filename))
        conn.commit()
        conn.close()
        return redirect(url_for("match", username=name))
    return render_template("index.html")

@app.route("/match/<username>")
def match(username):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE name != ?", (username,))
    others = c.fetchall()
    conn.close()

    if len(others) < 2:
        return "Not enough users in the database to find a family yet!"

    mother = random.choice(others)
    father = random.choice([o for o in others if o != mother])

    return render_template("match.html", username=username, mother=mother, father=father)

if __name__ == "__main__":
    app.run(debug=True)
