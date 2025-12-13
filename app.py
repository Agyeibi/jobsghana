from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret"  # <<-- change this for production!

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- Models ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Job Finder / Job Giver
    gender = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- Utilities ----------
def calculate_age(born: date) -> int:
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age

def valid_phone(phone: str) -> bool:
    # Accepts +233XXXXXXXXX where X are digits (9 digits after +233)
    return bool(re.fullmatch(r"\+233[0-9]{9}", phone))

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    # collect form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    region = request.form.get('region', '').strip()
    role = request.form.get('role', '').strip()
    gender = request.form.get('gender', '').strip()
    dob_str = request.form.get('dob', '').strip()
    password = request.form.get('password', '')

    # Basic validation
    if not all([name, email, phone, region, role, gender, dob_str, password]):
        flash('All fields are required.')
        return redirect(url_for('home'))

    # Validate phone
    if not valid_phone(phone):
        flash('Phone must be in Ghana format: +233XXXXXXXXX')
        return redirect(url_for('home'))

    # Parse DOB and check age >= 15
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        flash('Invalid date of birth format.')
        return redirect(url_for('home'))

    if calculate_age(dob) < 15:
        flash('You must be at least 15 years old to register.')
        return redirect(url_for('home'))

    # Check existing user
    if User.query.filter_by(email=email).first():
        flash('Email already registered. Please login.')
        return redirect(url_for('home'))

    # Create user
    hashed = generate_password_hash(password)
    new_user = User(name=name, email=email, phone=phone, region=region, role=role, gender=gender, dob=dob, password=hashed)
    db.session.add(new_user)
    db.session.commit()

    # set session
    session['user_name'] = new_user.name
    session['user_id'] = new_user.id
    session['role'] = new_user.role
    flash('Registration successful — welcome!')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        flash('Please enter email and password.')
        return redirect(url_for('home'))

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_name'] = user.name
        session['user_id'] = user.id
        session['role'] = user.role
        flash('Login successful.')
        return redirect(url_for('dashboard'))
    flash('Invalid credentials.')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_name'):
        flash('Login required to view dashboard.')
        return redirect(url_for('home'))

    if session.get('role') == 'Job Giver':
        jobs = Job.query.filter_by(posted_by=session.get('user_id')).order_by(Job.date_posted.desc()).all()
    else:
        jobs = Job.query.order_by(Job.date_posted.desc()).all()
    return render_template('dashboard.html', jobs=jobs)

@app.route('/post-job', methods=['POST'])
def post_job():
    if not session.get('user_name') or session.get('role') != 'Job Giver':
        flash('Only Job Givers can post jobs.')
        return redirect(url_for('dashboard'))

    title = request.form.get('title', '').strip()
    company = request.form.get('company', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()

    if not all([title, company, location, description]):
        flash('All job fields are required.')
        return redirect(url_for('dashboard'))

    job = Job(title=title, company=company, location=location, description=description, posted_by=session.get('user_id'))
    db.session.add(job)
    db.session.commit()
    flash('Job posted successfully.')
    return redirect(url_for('dashboard'))

@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    if not session.get('user_name'):
        # For UX: we prompt user to register via modal on client side - also flash here
        flash('Please register or login to search jobs.')
        return redirect(url_for('home'))

    if not query:
        flash('Please enter a search term.')
        return redirect(url_for('dashboard'))

    jobs = Job.query.filter(
        (Job.title.ilike(f'%{query}%')) |
        (Job.company.ilike(f'%{query}%')) |
        (Job.location.ilike(f'%{query}%'))
    ).order_by(Job.date_posted.desc()).all()

    return render_template('jobs.html', jobs=jobs, query=query)

# ---------- Init DB ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
