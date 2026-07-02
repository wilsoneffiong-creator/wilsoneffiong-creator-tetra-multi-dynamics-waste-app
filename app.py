from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tetra-secret-key-v6' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tetra_v6.db'  # New DB = clean table
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========= DATABASE MODELS =========
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)
    pickup_date = db.Column(db.String(20), nullable=False)
    pickup_time = db.Column(db.String(50), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# ========= CREATE DB + DEFAULT ADMIN =========
with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(email="admin@tetra.com").first():
        admin = Admin(email="admin@tetra.com", password="admin123")
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: admin@tetra.com / admin123")

# ========= ROUTES - 3 SEPARATE PAGES =========

@app.route("/")
def home():
    # L9C RULE: Home = Welcome only. No forms.
    return render_template("home.html")

@app.route("/book", methods=["GET", "POST"])
def book():
    # L9C RULE: Book = Form only
    if request.method == "POST":
        booking = Booking(
            name=request.form["name"],
            phone=request.form["phone"],
            category=request.form["category"],
            address=request.form["address"],
            pickup_date=request.form["pickup_date"],
            pickup_time=request.form["pickup_time"]
        )
        db.session.add(booking)
        db.session.commit()
        flash("Booking submitted successfully!")
        return redirect(url_for("book"))
    
    return render_template("book.html", today=date.today().isoformat())

@app.route("/admin", methods=["GET", "POST"])
def admin():
    # L9C RULE: Admin = Login only
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        admin_user = Admin.query.filter_by(email=email).first()
        if admin_user and admin_user.password == password:
            session["admin_id"] = admin_user.id
            return redirect(url_for("dashboard"))
        flash("Invalid email or password")
    
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    # Protect this page
    if "admin_id" not in session:
        return redirect(url_for("admin"))
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template("dashboard.html", bookings=bookings)

@app.route("/logout")
def logout():
    session.pop("admin_id", None)
    flash("Logged out successfully")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)