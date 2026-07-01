from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
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
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# V5.4: Booking with Date + Time
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pickup_date = db.Column(db.String(20), nullable=False) # NEW V5.4
    pickup_time = db.Column(db.String(20), nullable=False) # NEW V5.4
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# V5.4: Drop + Create + Default Admin
with app.app_context():
    db.drop_all() 
    db.create_all()
    if not User.query.filter_by(email='admin@tetra.com').first():
        admin = User(email='admin@tetra.com', is_admin=True)
        admin.set_password('admin123') # CHANGE THIS AFTER GOING LIVE
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

# V5.4: PUBLIC BOOKING WITH DATE + TIME
@app.route('/book', methods=['GET', 'POST'])
def book():
    today = date.today().isoformat() # V5.4: block past dates
    if request.method == 'POST':
        booking = Booking(
            name=request.form['name'],
            phone=request.form['phone'],
            category=request.form['category'],
            address=request.form['address'],
            pickup_date=request.form['pickup_date'], # NEW
            pickup_time=request.form['pickup_time']  # NEW
        )
        db.session.add(booking)
        db.session.commit()
        flash(f"Booking received for {booking.pickup_date} {booking.pickup_time}", 'success')
        return redirect(url_for('index'))
    return render_template('book.html', today=today)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, is_admin=True).first()
        if user and user.check_password(password):
            session['admin_id'] = user.id
            return redirect(url_for('admin'))
        flash('Invalid admin credentials', 'danger')
    return render_template('login.html')

@app.route('/admin')
@admin_required
def admin():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    total_bookings = len(bookings)
    pending = Booking.query.filter_by(status='Pending').count()
    return render_template('admin.html', bookings=bookings, total=total_bookings, pending=pending)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)