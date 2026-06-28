import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'tetra_waste_secret_key_change_me_v10'  # Change this to anything random
DATABASE = 'tetra.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            waste_type TEXT NOT NULL,
            pickup_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        waste_type = request.form['waste_type']
        pickup_date = request.form['pickup_date']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO bookings (name, phone, address, waste_type, pickup_date) VALUES (?, ?, ?)',
                     (name, phone, address, waste_type, pickup_date))
        conn.commit()
        conn.close()
        return redirect(url_for('success'))
    return render_template('book.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/admin')
def admin():
    conn = get_db_connection()
    bookings = conn.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', bookings=bookings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Default admin login. Change it later
        if username == 'admin' and password == 'tetra123':
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Username or Password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash('Registration is disabled for now. Use admin / tetra123 to login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    bookings = conn.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', bookings=bookings)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# RENDER DEPLOY FIX - DO NOT TOUCH THIS
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)