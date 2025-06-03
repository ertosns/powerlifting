from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///powerlifting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.String, nullable=False)
    deadlift = db.Column(db.Float, nullable=False)
    squat = db.Column(db.Float, nullable=False)
    bench = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String, nullable=False)

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

@app.route('/add_record', methods=['GET', 'POST'])
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
            gender=gender
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

@app.route('/profile')
def profile():
    records = Record.query.order_by(Record.id).all()
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
    if not df.empty:
        df['gross'] = df.apply(wilks_score, axis=1)
        df['total (kgs)'] = df.apply(get_total, axis=1)

        for r in records:
                record_dict = {
                        'id': r.id,
                        'datetime': r.datetime,
                        'deadlift': r.deadlift,
                        'squat': r.squat,
                        'bench': r.bench,
                        'weight': r.weight,
                        'gender': r.gender,
                        'analysis': compute_analysis(r)
                }
                records_with_analysis.append(record_dict)
        table_html = df.to_html(classes="table table-striped", index=False)
        plot_url = make_plot(df)
        analysis = df['gross'].iloc[-1] # or your custom analysis logic
    else:
        table_html = ""
        plot_url = ""
        analysis = ""
    return render_template('profile.html', records=records_with_analysis, plot_url=plot_url, analysis=analysis)

@app.route('/delete_record/<int:record_id>', methods=['POST'])
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
