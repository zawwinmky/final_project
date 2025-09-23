from flask import Flask, redirect, render_template, request, session, flash, url_for, jsonify # pyright: ignore[reportMissingImports]
from flask_session import Session # pyright: ignore[reportMissingImports]
from flask_sqlalchemy import SQLAlchemy # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore
from sqlalchemy.exc import IntegrityError # type: ignore
from sqlalchemy import update # type: ignore
from datetime import datetime

app = Flask(__name__)

app.config["SESSION_TYPE"] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
Session(app)

#database models

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    sent_emails = db.relationship('Emails', foreign_keys='Emails.sender', backref='sender_user', lazy=True)
    received_emails = db.relationship('Emails', foreign_keys='Emails.receiver', backref='receiver_user', lazy=True)

class Emails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)    

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send_email", methods=["POST"])
def send_email():
    sender = session["user_id"]
    receiver_email = request.form.get("receiver_email")
    subject = request.form.get("subject")
    body = request.form.get("body")
    receiver = Users.query.filter_by(email=receiver_email).first()
    if receiver_email == session["user_email"]:
        return jsonify({
            'status':'error',
            'message':"Can't send email to yourself!!"
            }), 500
    if not receiver:
        return jsonify({
            'status': 'error',
            'message': 'No user with that email'
        }), 404
        
    new_email = Emails(sender=sender,
    receiver=receiver.id,
    subject=subject,
    body=body,
    timestamp=datetime.now())
    try:
        db.session.add(new_email)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occured'
            }), 500
        
    return jsonify({
        'status': 'success',
        'message': 'Email successfully sent',
    }), 200
    
    
@app.route("/get_update")
def get_update():
    user_id = session["user_id"]
    sent_mails = Emails.query.filter_by(sender=user_id).all()
    return jsonify(sent_mails)

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password") 
        cpassword = request.form.get("cpassword")
        if not all([name, email, password, cpassword,]):
            flash("You need to enter all fields", "error")
            return redirect(url_for("register"))
        if password != cpassword:
            flash("Password must be same", "error")
            return redirect(url_for("register"))
        new_user = Users(name=name, email=email, password=generate_password_hash(password))
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Email already used.", "error")
            return redirect(url_for("register"))
        flash("Successfully registered", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not all([email, password]):
            flash("You need to enter all fields", "error")
            return redirect(url_for("login"))
        user = Users.query.filter_by(email=email).first()
        if not user:
            flash("There is no user with that email", "error")
            return redirect(url_for("login"))
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            flash("Login success", "success")
            return redirect(url_for("index"))
        else:
            flash("Incorrect email or password", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        id = request.form.get("id")
        name = request.form.get("name")
        email = request.form.get("email")
        if not all([id, name, email]):
            flash("You need to enter all fields.", "error")
            return redirect(url_for("profile"))
        try:
            stmt = (update(Users).where(Users.id==id).values(name=name, email=email))
            db.session.execute(stmt)
            db.session.commit()
            session["user_name"] = name
            session["user_email"] = email
            return render_template("profile.html")
        except IntegrityError:
            flash("Email already used by another user!", "error")
            db.session.rollback()
            return redirect(url_for("profile"))
    else:
        return render_template("profile.html")