from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import uuid
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey_jobsghana"
DB_NAME = "jobs.db"

# ------------------------
# Database Initialization
# ------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        type TEXT
    )''')
    # Jobs table
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        category TEXT,
        location TEXT,
        poster_id TEXT,
        is_paid INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

# ------------------------
# Helper Functions
# ------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------------
# Routes
# ------------------------

# Home Page
@app.route('/')
def home():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY is_paid DESC")
    jobs = c.fetchall()
    conn.close()
    return render_template('index.html', jobs=jobs)

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['type']
        user_id = str(uuid.uuid4())

        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                      (user_id, name, email, password, user_type))
            conn.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists.")
        finally:
            conn.close()
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_type'] = user['type']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.")
    return render_template('login.html')

# User Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')

    conn = get_db_connection()
    c = conn.cursor()

    if session['user_type'] == 'employer':
        if search_query:
            c.execute("SELECT * FROM jobs WHERE poster_id=? AND title LIKE ?",
                      (session['user_id'], f"%{search_query}%"))
        else:
            c.execute("SELECT * FROM jobs WHERE poster_id=?", (session['user_id'],))
    else:
        if search_query:
            c.execute("SELECT * FROM jobs WHERE title LIKE ? OR category LIKE ? ORDER BY is_paid DESC",
                      (f"%{search_query}%", f"%{search_query}%"))
        else:
            c.execute("SELECT * FROM jobs ORDER BY is_paid DESC")

    jobs = c.fetchall()
    conn.close()
    return render_template('dashboard.html', jobs=jobs)

# Post a Job
@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['user_type'] != 'employer':
        flash("Only employers can post jobs.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        location = request.form['location']
        is_paid = 1 if 'is_paid' in request.form else 0
        job_id = str(uuid.uuid4())

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (job_id, title, description, category, location, session['user_id'], is_paid))
        conn.commit()
        conn.close()

        flash("Job posted successfully!")
        return redirect(url_for('dashboard'))

    return render_template('post_job.html')

# Payment Route (Flutterwave)
@app.route('/pay/<job_id>')
def pay(job_id):
    tx_ref = str(uuid.uuid4())
    amount = 10  # Premium job cost in GHS
    email = "customer@example.com"  # Replace with session email if available

    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": "GHS",
        "payment_type": "mobilemoneyghana",
        "redirect_url": "https://yourdomain.com/payment-success",
        "customer": {"email": email, "phonenumber": "0240000000", "name": "Customer Name"},
        "customizations": {"title": "Premium Job Post", "description": "Pay to promote job"}
    }
    headers = {
        "Authorization": "Bearer YOUR_FLW_SECRET_KEY",
        "Content-Type": "application/json"
    }

    r = requests.post("https://api.flutterwave.com/v3/payments", json=payload, headers=headers)
    response = r.json()

    if response.get('status') == 'success':
        return redirect(response['data']['link'])
    else:
        flash("Payment initiation failed. Try again.")
        return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Run App
if __name__ == '__main__':
    app.run(debug=True)
