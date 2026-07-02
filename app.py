from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tetra_secret_key_change_me'  # change this later
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tetra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===== MODELS =====
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pickup_date = db.Column(db.String(20), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ===== LOGIN REQUIRED DECORATOR =====
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Login required', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===== ROUTES =====
@app.route('/')
def home():   # <-- FIXED: was 'index'. Now matches url_for('home')
    return render_template('index.html')

# V5.4: PUBLIC BOOKING WITH DATE + TIME
@app.route('/book', methods=['GET', 'POST'])
def book():
    today = date.today().isoformat() # V5.4: block past date
    if request.method == 'POST':
        booking = Booking(
            name=request.form['name'],
            phone=request.form['phone'],
            category=request.form['category'],
            address=request.form['address'],
            pickup_date=request.form['pickup_date']
        )
        db.session.add(booking)
        db.session.commit()
        flash('Booking received! We will call you soon.', 'success')
        return redirect(url_for('home')) # <-- now works
    return render_template('book.html', today=today)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        admin = Admin.query.filter_by(username=request.form['username']).first()
        if admin and check_password_hash(admin.password, request.form['password']):
            session['admin_id'] = admin.id
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template('dashboard.html', bookings=bookings)

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('home'))

# ===== FIRST RUN: CREATE ADMIN + DB =====
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        admin = Admin(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print('Default admin created: admin / admin123')

if __name__ == '__main__':
    app.run(debug=True)