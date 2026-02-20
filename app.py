from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from textblob import TextBlob
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ================= MODELS =================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    sentiment = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= NLP =================

def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    return "Neutral"

# ================= ROUTES =================

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"])
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    feedbacks = Feedback.query.filter_by(user_id=current_user.id).all()
    sentiments = [f.sentiment for f in feedbacks]

    positive = sentiments.count("Positive")
    negative = sentiments.count("Negative")
    neutral = sentiments.count("Neutral")

    monthly_data = {}
    for f in feedbacks:
        month = f.date.strftime("%Y-%m")
        monthly_data[month] = monthly_data.get(month, 0) + 1

    return render_template("dashboard.html",
                           positive=positive,
                           negative=negative,
                           neutral=neutral,
                           total=len(feedbacks),
                           monthly_data=monthly_data)

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    text = request.json["text"]
    sentiment = analyze_sentiment(text)

    feedback = Feedback(text=text,
                        sentiment=sentiment,
                        user_id=current_user.id)

    db.session.add(feedback)
    db.session.commit()

    return jsonify({"sentiment": sentiment})

@app.route("/upload_csv", methods=["POST"])
@login_required
def upload_csv():
    file = request.files["file"]
    df = pd.read_csv(file)

    for text in df.iloc[:,0]:
        sentiment = analyze_sentiment(str(text))
        feedback = Feedback(text=text,
                            sentiment=sentiment,
                            user_id=current_user.id)
        db.session.add(feedback)

    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ================= INIT =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)