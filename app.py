from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tetra_secret_key_change_me' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tetra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===== MODELS - MATCHES ALL YOUR TEMPLATES =====
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pickup_date = db.Column(db.String(20), nullable=False)
    pickup_time = db.Column(db.String(50), nullable=False) # <-- V5.4 field
    status = db.Column(db.String(20), default='Pending')   # <-- Dashboard field
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # <-- Dashboard field

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False) # <-- login.html uses email
    password = db.Column(db.String(200), nullable=False)

# ===== LOGIN REQUIRED =====
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Login required', 'warning')
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

# ===== ROUTES - MATCHES base.html nav =====
@app.route('/')
def home():   # <-- FIX 1: Changed from 'index' to 'home' to match base.html
    return render_template('home.html') # <-- Using home.html

@app.route('/index') # <-- Keep old link working too
def index():
    return redirect(url_for('home'))

@app.route('/book', methods=['GET', 'POST'])
def book():
    today = date.today().isoformat()
    if request.method == 'POST':
        booking = Booking(
            name=request.form['name'],
            phone=request.form['phone'],
            category=request.form['category'],
            address=request.form['address'],
            pickup_date=request.form['pickup_date'],
            pickup_time=request.form['pickup_time'] # <-- V5.4
        )
        db.session.add(booking)
        db.session.commit()
        flash('Booking received! We will call you soon.', 'success')
        return redirect(url_for('home'))
    return render_template('book.html', today=today)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        admin = Admin.query.filter_by(email=request.form['email']).first() # <-- FIX 2: email not username
        if admin and check_password_hash(admin.password, request.form['password']):
            session['admin_id'] = admin.id
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    stats = {
        'total': Booking.query.count(),
        'medical': Booking.query.filter_by(category='Medical').count(),
        'household': Booking.query.filter_by(category='Household').count(),
        'e_waste': Booking.query.filter_by(category='E-Waste').count(),
        'others': Booking.query.filter_by(category='Others').count(),
    }
    user = Admin.query.get(session['admin_id']) # <-- for {{ user.email }}
    pending = Booking.query.filter_by(status='Pending').count() # <-- for admin dashboard
    return render_template('dashboard.html', stats=stats, user=user, bookings=bookings, total=stats['total'], pending=pending)

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('home'))

# ===== FIRST RUN SETUP =====
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        admin = Admin(email='admin@tetra.com', password=generate_password_hash('admin123')) # <-- FIX 2
        db.session.add(admin)
        db.session.commit()
        print('Default admin created: admin@tetra.com / admin123')

if __name__ == '__main__':
    app.run(debug=True)