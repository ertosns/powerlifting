from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd
import os
import secrets
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_migrate import Migrate
from models import db, app
from io import BytesIO
from total_curve_plot import make_total_curve_plot

migrate = Migrate(app, db)

from models import User, Record

with app.app_context():
        db.create_all()

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
GOOGLE_ID = ''
GOOGLE_SECRET = ''
google_bp = make_google_blueprint(client_id=GOOGLE_ID,
                                  client_secret=GOOGLE_SECRET,
				scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
                                  redirect_url="/powerlifting/google_login/callback")

app.register_blueprint(google_bp, url_prefix="/powerlifting/google_login")

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
        if user and user.password and check_password_hash(user.password, password):
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
@app.route("/powerlifting/google_login/callback", methods=["GET", "POST"])
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()
    google_id = info["id"]
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(email=info.get("email"), google_id=google_id)
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("profile"))

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

def make_download_plot(df):
    plt.grid(color='green', linewidth=1.2, linestyle='--', axis='both')
    fig, ax = plt.subplots()
    ax.set_title("https://finai.solutions/powerlifting/profile")
    ax.text(0.1, 0.9, "Squat: {}, Bench: {}, Deadlift: {}".format(df['squat'].iloc[-1], df['bench'].iloc[-1], df['deadlift'].iloc[-1]), size=15, color='black')
    fig.set_size_inches(9, 9)
    ax.set_facecolor('black')
    ax.spines['bottom'].set_color('green')
    ax.spines['top'].set_color('green')
    ax.spines['right'].set_color('green')
    ax.spines['left'].set_color('green')
    ax.tick_params(axis='x', colors='green')
    ax.tick_params(axis='y', colors='green')
    fig.set_facecolor('black')
    X = df['datetime']
    ax.plot(X, df['deadlift'], label='deadlift')
    ax.plot(X, df['squat'], label='squat')
    ax.plot(X, df['bench'], label='bench')
    ax.legend(loc="upper left")

    plt.xticks(rotation=90)
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf

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
        is_target = request.form['is_target']
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
                is_target=is_target,
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
            analysis += "Your deadlift is too low; ideal deadlift is 110%-120% of your squat, it should be {:.1f}-{:.1f}. ".format(1.1 * squat, 1.2 * squat)
    else:
        analysis = "Not enough data for analysis."
    return analysis or "Looks balanced!"

def add_days_to_date(date_str, days):
    # Convert the string to a datetime object
    date = pd.to_datetime(date_str, format='%Y-%m-%d')
    # Add the specified number of days
    new_date = date + pd.Timedelta(days=days)
    # Convert back to string in the same format
    return new_date.strftime('%Y-%m-%d')

@app.route('/powerlifting/profile')
@login_required
def profile():
    records = Record.query.filter_by(user_id=current_user.id).order_by(Record.id).all()
    if not records:
        df = pd.DataFrame(columns=['datetime','deadlift','squat','bench','weight','gender'])
    else:
        recs =[]
        for r in records:
                if r.is_target == 'target':
                        while len(recs)>1:
                                interpolate_date = add_days_to_date(recs[-1]['datetime'], 30)
                                if interpolate_date < r.datetime:
                                        recs += [{'datetime':  interpolate_date}]
                                else:
                                        break
                dict_rec = {
                        'datetime': r.datetime,
                        'deadlift': r.deadlift,
                        'squat': r.squat,
                        'bench': r.bench,
                        'weight': r.weight,
                        'gender': r.gender
                }
                recs+=[dict_rec]
        df = pd.DataFrame(recs)
        df = df.interpolate()
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
                #TODO interpolate
                if r.is_target == 'target':
                        while len(records_with_analysis)>1:
                                interpolate_date = add_days_to_date(records_with_analysis[-1]['datetime'], 30)
                                if interpolate_date < r.datetime:
                                        records_with_analysis += [{'datetime':  interpolate_date}]
                                else:
                                        break
                records_with_analysis.append(record_dict)
        table_html = df.to_html(classes="table table-striped", index=False)
        df.sort_values(by='datetime', inplace=True)
        plot_url = make_plot(df)
    else:
        table_html = ""
        plot_url = ""
    df = pd.DataFrame(records_with_analysis)
    df.sort_values(by='datetime', inplace=True)
    interpolated_records = df.interpolate().to_dict('records')
    
    # Generate share token for the user
    share_token = get_or_create_share_token(current_user)
    share_url = url_for('share_plot', token=share_token, _external=True)
    
    return render_template('profile.html', records=interpolated_records, plot_url=plot_url, analysis=analysis, user=current_user, share_url=share_url)

def get_or_create_share_token(user):
    """Generate or retrieve a unique share token for the user"""
    if not user.share_token:
        user.share_token = secrets.token_urlsafe(32)
        db.session.commit()
    return user.share_token

@app.route('/powerlifting/share/<token>')
def share_plot(token):
    """Public route to view a shared plot"""
    user = User.query.filter_by(share_token=token).first_or_404()
    records = Record.query.filter_by(user_id=user.id).order_by(Record.id).all()
    
    if not records:
        return render_template('share.html', plot_url=None, error="No records available to display.")
    
    recs = []
    for r in records:
        if r.is_target == 'target':
            while len(recs) > 1:
                interpolate_date = add_days_to_date(recs[-1]['datetime'], 30)
                if interpolate_date < r.datetime:
                    recs += [{'datetime': interpolate_date}]
                else:
                    break
        dict_rec = {
            'datetime': r.datetime,
            'deadlift': r.deadlift,
            'squat': r.squat,
            'bench': r.bench,
            'weight': r.weight,
            'gender': r.gender
        }
        recs += [dict_rec]
    
    df = pd.DataFrame(recs)
    df = df.interpolate()
    df.sort_values(by='datetime', inplace=True)
    
    # Use make_total_curve_plot which doesn't include weight or wilks
    plot_url = make_total_curve_plot(df)
    
    return render_template('share.html', plot_url=plot_url, error=None)

@app.route('/powerlifting/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    record = Record.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash('Record deleted successfully.', 'success')
    return redirect(url_for('profile'))

@app.route('/powerlifting/download')
def download_plot():
    # You may have a database call here to get records
    img_bytes = get_records_from_database()

    # If make_plot returns a BytesIO object:
    img_bytes.seek(0)
    return send_file(
        img_bytes,
        mimetype='image/png',
        as_attachment=True,
        download_name='records_plot.png'
    )

# Helper function examples
def get_records_from_database():
    # Implement your DB query here
    records = Record.query.filter_by(user_id=current_user.id).order_by(Record.id).all()
    records = records if records else []  # Return an empty list if no records found
    if not records:
        df = pd.DataFrame(columns=['datetime','deadlift','squat','bench','weight','gender'])
    else:
        recs =[]
        for r in records:
                if r.datetime > pd.Timestamp.now().strftime('%Y-%m-%d'):
                        continue
                if r.is_target == 'target':
                        while len(recs)>1:
                                interpolate_date = add_days_to_date(recs[-1]['datetime'], 30)
                                if interpolate_date < r.datetime:
                                        recs += [{'datetime':  interpolate_date}]
                                else:
                                        break
                dict_rec = {
                        'datetime': r.datetime,
                        'deadlift': r.deadlift,
                        'squat': r.squat,
                        'bench': r.bench,
                        'weight': r.weight,
                        'gender': r.gender
                }
                recs+=[dict_rec]
        df = pd.DataFrame(recs)
        df = df.interpolate()
    ##
    return make_download_plot(df)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run('0.0.0.0', port=54321)
