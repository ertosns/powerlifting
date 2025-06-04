from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd
import os
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = ''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///powerlifting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#db.init_app(app)

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
GOOGLE_ID = ''
GOOGLE_SECRET = ''
google_bp = make_google_blueprint(client_id=GOOGLE_ID,
                                  client_secret=GOOGLE_SECRET,
                                  redirect_url="/google_login/callback")

app.register_blueprint(google_bp, url_prefix="/powerlifting/google_login")

from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    # Add google_id if using OAuth
    # records = db.relationship('Record', backref='user', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/powerlifting/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("signup"))
        user = User(email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("profile"))
    return render_template("signup.html")

@app.route("/powerlifting/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("profile"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/powerlifting/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Google OAuth Login
@app.route("/powerlifting/google")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()
    google_id = info["id"]
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(email=info["email"], google_id=google_id)
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("profile"))


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.String, nullable=False)
    deadlift = db.Column(db.Float, nullable=False)
    squat = db.Column(db.Float, nullable=False)
    bench = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('records', lazy=True))

def get_total(row):
    return row['deadlift'] + row['bench'] + row['squat']

def wilks_score(row):
    total = get_total(row)
    gender = row['gender']
    x = row['weight']
    if gender == 'male':
        a = -216.0475144
        b = 16.2606339
        c = -0.002388645
        d = -0.00113732
        e = 7.01863*10**-6
        f = -1.291*10**-8
    else:
        a = 594.31747775582
        b = -27.23842536447
        c = 0.82112226871
        d = -0.00930733913
        e = 4.731582*10**-5
        f = -9.054*10**-8
    return total*500/(a+b*x+c*x**2+d*x**3+e*x**4+f*x**5)

def get_previous_value(records, field, default=0.0):
    if not records:
        return default
    val = getattr(records[-1], field)
    return val if val is not None else default

def make_plot(df):
    plt.rcParams['text.color'] = 'green'
    plt.rcParams['axes.labelcolor'] = 'green'
    plt.grid(color='green', linewidth=1.2, linestyle='--', axis='both')
    fig, ax = plt.subplots()
    fig.set_size_inches(9, 9)
    ax.set_facecolor('black')
    ax.spines['bottom'].set_color('green')
    ax.spines['top'].set_color('green')
    ax.spines['right'].set_color('green')
    ax.spines['left'].set_color('green')
    ax.xaxis.label.set_color('yellow')
    ax.yaxis.label.set_color('blue')
    ax.tick_params(axis='x', colors='green')
    ax.tick_params(axis='y', colors='green')
    fig.set_facecolor('black')
    X = df['datetime']
    ax.plot(X, df['deadlift'], label='deadlift')
    ax.plot(X, df['squat'], label='squat')
    ax.plot(X, df['bench'], label='bench')
    ax.plot(X, df['deadlift'] + df['squat'] + df['bench'], label='total')
    ax.plot(X, df['weight'], label='weight')
    ax.plot(X, df['gross'], label='wilks score')
    ax.legend(loc="upper left")
    plt.xticks(rotation=90)
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.rcParams["figure.figsize"] = (200,3)
    plt.close(fig)
    return image_base64

@app.route('/powerlifting/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    if request.method == 'POST':
        records = Record.query.order_by(Record.id).all()
        date = request.form['date']
        gender = request.form['gender']
        weight = float(request.form['weight'])
        squat = request.form.get('squat')
        bench = request.form.get('bench')
        deadlift = request.form.get('deadlift')

        squat = float(squat) if squat else get_previous_value(records, 'squat', 0)
        bench = float(bench) if bench else get_previous_value(records, 'bench', 0)
        deadlift = float(deadlift) if deadlift else get_previous_value(records, 'deadlift', 0)

        rec = Record(
            datetime=date,
            deadlift=deadlift,
            squat=squat,
            bench=bench,
            weight=weight,
            gender=gender,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(rec)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('add_record.html')

def compute_analysis(record):
    deadlift = record.deadlift
    squat = record.squat
    bench = record.bench
    analysis = ''
    # Avoid division by zero
    if bench and squat:
        deadlift2bench = deadlift / bench
        if deadlift2bench >= 1.5:
            analysis += "Your bench is too low; ideal bench relative to your deadlift should be {:.1f}-{:.1f}. ".format(deadlift / 1.5, deadlift / 1.3)
        elif deadlift2bench <= 1.3:
            analysis += "Your deadlift is too low; ideal deadlift is 130%-150% of your bench, it should be {:.1f}-{:.1f}. ".format(1.3 * bench, 1.5 * bench)

        deadlift2squat = deadlift / squat
        if deadlift2squat >= 1.2:
            analysis += "Your squat is too low; ideal squat relative to your deadlift should be {:.1f}-{:.1f}. ".format(deadlift / 1.2, deadlift / 1.1)
        elif deadlift2squat <= 1.1:
            analysis += "Your deadlift is too low; ideal deadlift is 110%-120% of your squat, it should be {:.1f}-{:.1f}. ".format(1.2 * squat, 1.1 * squat)
    else:
        analysis = "Not enough data for analysis."
    return analysis or "Looks balanced!"

@app.route('/powerlifting/profile')
@login_required
def profile():
    records = Record.query.filter_by(user_id=current_user.id).order_by(Record.id).all()
    print('records: {}'.format(records))
    if not records:
        df = pd.DataFrame(columns=['datetime','deadlift','squat','bench','weight','gender'])
    else:
        df = pd.DataFrame([{
            'datetime': r.datetime,
            'deadlift': r.deadlift,
            'squat': r.squat,
            'bench': r.bench,
            'weight': r.weight,
            'gender': r.gender
        } for r in records])
    records_with_analysis = []
    analysis = None
    if not df.empty:
        df['gross'] = df.apply(wilks_score, axis=1)
        df['total (kgs)'] = df.apply(get_total, axis=1)

        for r in records:
                analysis = compute_analysis(r)
                record_dict = {
                         'id': r.id,
                        'datetime': r.datetime,
                        'deadlift': r.deadlift,
                        'squat': r.squat,
                        'bench': r.bench,
                        'weight': r.weight,
                        'gender': r.gender,
                        'analysis': analysis
                }
                records_with_analysis.append(record_dict)
        table_html = df.to_html(classes="table table-striped", index=False)
        plot_url = make_plot(df)
    else:
        table_html = ""
        plot_url = ""
    #lifts = Lift.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', records=records_with_analysis, plot_url=plot_url, analysis=analysis, user=current_user)

@app.route('/powerlifting/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    record = Record.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash('Record deleted successfully.', 'success')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run('0.0.0.0', port=54321)
