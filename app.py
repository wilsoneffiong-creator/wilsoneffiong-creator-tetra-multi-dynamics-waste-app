from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# FIX V4.8: Flask 3.x safe - create tables on startup
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    stats = {'total': 0, 'medical': 0, 'household': 0, 'e_waste': 0, 'others': 0}
    return render_template('dashboard.html', user=user, stats=stats)

@app.route('/admin')
@login_required
def admin():
    users = User.query.all()
    return f"<h1>Admin</h1><p>Users in DB: {len(users)}</p><a href='/dashboard'>Back to Dashboard</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)