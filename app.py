from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tetra_secret_key_change_me') 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tetra_v6.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pickup_date = db.Column(db.String(20), nullable=False)
    pickup_time = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    today = date.today().isoformat()
    if request.method == 'POST':
        booking = Booking(
            name=request.form['name'], phone=request.form['phone'],
            category=request.form['category'], address=request.form['address'],
            pickup_date=request.form['pickup_date'], pickup_time=request.form['pickup_time']
        )
        db.session.add(booking); db.session.commit()
        flash('Booking received! We will call you soon.', 'success')
        return redirect(url_for('home'))
    return render_template('book.html', today=today)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        admin = Admin.query.filter_by(email=request.form['email']).first()
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
    user = Admin.query.get(session['admin_id'])
    pending = Booking.query.filter_by(status='Pending').count()
    return render_template('dashboard.html', stats=stats, user=user, bookings=bookings, total=stats['total'], pending=pending)

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()
    if not Admin.query.first():
        admin = Admin(email='admin@tetra.com', password=generate_password_hash('admin123'))
        db.session.add(admin); db.session.commit()
        print('Default admin created: admin@tetra.com / admin123')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)