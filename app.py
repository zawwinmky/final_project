from flask import Flask, redirect, render_template, request, session, flash, url_for, jsonify # pyright: ignore[reportMissingImports]
from flask_session import Session # pyright: ignore[reportMissingImports]
from flask_sqlalchemy import SQLAlchemy # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore
from sqlalchemy.exc import IntegrityError # type: ignore
from sqlalchemy import update, or_ # type: ignore
from sqlalchemy.orm import aliased # type: ignore
from datetime import datetime
from functools import wraps

app = Flask(__name__)

app.config["SESSION_TYPE"] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

Session(app)
db = SQLAlchemy(app)

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


def login_require(f):
    @wraps(f)
    def deco_function(*args, **kwargs):
        if "user_id" not in session:
            flash("You need to log in first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return deco_function

#routes
@app.route("/")
@login_require
def index():
    return render_template("index.html")

@app.route("/send_email", methods=["POST"])
def send_email():
    sender = session["user_id"]
    receiver_email = request.form.get("receiver_email")
    subject = request.form.get("subject")
    body = request.form.get("body")
    if not receiver_email:
        return jsonify({
            'status': 'error',
            'message':"You must add receiver's email address!"
        }), 500
    if not subject:
        subject = "Default subject"
    
    no_body = {'status':'error','message':"You can't send an empty email!"}
    
    if not body:
        return jsonify(no_body), 500
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
    if 'user_id' in session:
        return redirect('/')
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
    if 'user_id' in session:
        return redirect('/')
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        if not all([email, password]):
            message = {
                'status':'error',
                'message':'You need to enter all fields'
                }
            return jsonify(message), 500
        user = Users.query.filter_by(email=email).first()
        if not user:
            message = {
                'status':'error',
                'message':"There is no user with that email"
            }
            return jsonify(message), 500
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            message = {
                'status': 'success',
                'message':'Login successful',
                'redirect_url':url_for('index')
            }
            return jsonify(message)
        else:
            message = {
                'status':'error',
                'message':"Incorrect email or password"
            }
            return jsonify(message), 401
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


@app.route('/inbox', methods=['POST', 'GET'])
def get_inbox():
    if request.method == 'POST':
        user_id = session['user_id']
        Sender = aliased(Users)
        mails = db.session.query(
        Emails,
        Sender.name.label('sender_name'),
        Sender.email.label('sender_email'),
        ).join(
        Sender, Emails.sender == Sender.id
        ).filter(
        Emails.receiver == user_id
        ).all()
        dict_mails = [{
        'id':mail.id,
        'sender_name': sender_name,
        'sender_email':sender_email,
        'receiver_name': session['user_name'],
        'receiver_email': session['user_email'],
        'subject': mail.subject,
        'body': mail.body,
        'time': mail.timestamp.isoformat(),
        } for mail, sender_name, sender_email in mails]
        return jsonify(dict_mails)
    return render_template('inbox.html')

@app.route('/get_emails', methods=['POST'])
def get_emails():
    user_id = session['user_id']
    Receiver = aliased(Users)
    Sender = aliased(Users)
    mails = db.session.query(
        Emails,
        Receiver.name.label('receiver_name'),
        Receiver.email.label('receiver_email'),
        Sender.name.label('sender_name'),
        Sender.email.label('sender_email'),
        ).join(
        Sender, Emails.sender == Sender.id
        ).join(
            Receiver, Emails.receiver == Receiver.id
        ).filter(
            or_(Emails.sender == user_id, Emails.receiver == user_id)
        ).all()
    dict_mails = [{
            'id': mail.id,
            'sender_name': sender_name,
            'sender_email': sender_email,
            'receiver_name': receiver_name,
            'receiver_email': receiver_email,
            'subject': mail.subject,
            'body': mail.body,
            'time': mail.timestamp.isoformat(),
        } for mail, sender_name, sender_email, receiver_name, receiver_email in mails]
        
    return jsonify(dict_mails)

@app.route('/sent_box', methods=['POST','GET'])
def sent_box():
    if request.method == 'POST':
        user_id = session['user_id']
        Receiver = aliased(Users)
        mails = db.session.query(
        Emails,
        Receiver.name.label('receiver_name'),
        Receiver.email.label('receiver_email'),
        ).join(
        Receiver, Emails.receiver == Receiver.id
        ).filter(
        Emails.sender == user_id
        ).all()
        dict_mails = [{
        'id':mail.id,
        'sender_name': session['user_name'],
        'sender_email':session['user_email'],
        'receiver_name': receiver_name,
        'receiver_email': receiver_email,
        'subject': mail.subject,
        'body': mail.body,
        'time': mail.timestamp.isoformat(),
        } for mail, receiver_name, receiver_email in mails]
        return jsonify(dict_mails)
    return render_template('sent_box.html')

@app.route('/get_email/<int:email_id>', methods=['POST'])
def get_email(email_id):
    user_id = session["user_id"]
    
    try:
        Sender = aliased(Users)
        Receiver = aliased(Users)
        mail_data = db.session.query(
            Emails,
            Sender.name.label('sender_name'),
            Sender.email.label('sender_email'),
            Receiver.name.label('receiver_name'),
            Receiver.email.label('receiver_email')
        ).join(
            Sender, Emails.sender == Sender.id
        ).join(
            Receiver, Emails.receiver == Receiver.id
        ).filter(
            Emails.id == email_id
        ).first()
        
        
        if not mail_data:
            return jsonify({'message': 'Email not found.'}), 404
        
        mail, sender_name, sender_email, receiver_name, receiver_email = mail_data

        if mail.sender != user_id and mail.receiver != user_id:
            return jsonify({'message': 'Unauthorized access.'}), 403

        email_info = {
            'id': mail.id,
            'sender_name': sender_name,
            'sender_email': sender_email,
            'receiver_name': receiver_name,
            'receiver_email': receiver_email, 
            'subject': mail.subject,
            'body': mail.body,
            'timestamp': mail.timestamp.isoformat()
        }
        
        return jsonify(email_info)
    except Exception as e:
        message = {
            'status':'error',
            'message':'An error occured'
        }
        return jsonify(message), 500
    
#Error handlings
@app.errorhandler(405)
def method_not_allow(error):
    return redirect('/')

@app.errorhandler(500)
def server_error(error):
    message = {
        'status':'error',
        'message':'Opps, an error occured!'
    }
    return jsonify(message), 500