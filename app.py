from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ----------------------------------
# APP CONFIG
# ----------------------------------

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "jobs.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ----------------------------------
# DATABASE MODELS
# ----------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    is_employer = db.Column(db.Boolean, default=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------------------
# HOME / INDEX
# ----------------------------------

@app.route("/")
def home():
    jobs = Job.query.order_by(Job.date_posted.desc()).limit(10).all()
    return render_template("home.html", jobs=jobs)

# ----------------------------------
# ALL JOBS
# ----------------------------------

@app.route("/jobs")
def jobs():
    jobs = Job.query.order_by(Job.date_posted.desc()).all()
    return render_template("jobs.html", jobs=jobs)

# ----------------------------------
# JOB DETAILS (IMPORTANT FIX)
# ----------------------------------

@app.route("/job/<int:job_id>")
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("job_details.html", job=job)

# ---------------------------------
# REGISTER
# ---------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form.get("role")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password,
            is_employer=True if role == "employer" else False
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ----------------------------------
# LOGIN
# ----------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password", "error")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["is_employer"] = user.is_employer
        session["user_name"] = user.name

        flash("Logged in successfully", "success")
        return redirect(url_for("home"))

    return render_template("login.html")

# ----------------------------------
# LOGOUT
# ----------------------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("home"))

# ----------------------------------
# POST JOB (EMPLOYER ONLY)
# ----------------------------------

@app.route("/post-job", methods=["GET", "POST"])
def post_job():
    if "user_id" not in session or not session.get("is_employer"):
        flash("Employers only. Please login.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        description = request.form["description"]
        requirements = request.form["requirements"]

        job = Job(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements
        )

        db.session.add(job)
        db.session.commit()

        flash("Job posted successfully", "success")
        return redirect(url_for("jobs"))

    return render_template("post_job.html")

# ----------------------------------
# DASHBOARD
# ----------------------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    jobs = Job.query.order_by(Job.date_posted.desc()).all()
    return render_template("dashboard.html", jobs=jobs)

# ----------------------------------
# RUN APP
# ----------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

