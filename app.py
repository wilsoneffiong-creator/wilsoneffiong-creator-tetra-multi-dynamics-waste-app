from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tetra-secret-key-change-this' # CHANGE THIS LATER

DB_FILE = 'users.json'

# L9C RULE: Auto create DB if Render doesn't have it
def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump([], f) # Create empty user list

def load_users():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)

init_db() # Run on startup

# L9C RULE: Fix BuildError - Add missing routes for base.html
@app.route('/')
def home():
    return render_template('dashboard.html') # Or "TETRA Home"

@app.route('/book')
def book():
    return "Book Page - Coming Soon", 200

# L9C RULE: Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        
        if any(u['email'] == email for u in users):
            flash('Email already exists')
            return redirect(url_for('register'))
            
        users.append({
            'email': email, 
            'password': generate_password_hash(password)
        })
        save_users(users)
        flash('Account created. Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# L9C RULE: Login Route  
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        
        user = next((u for u in users if u['email'] == email), None)
        if user and check_password_hash(user['password'], password):
            session['user'] = email
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)