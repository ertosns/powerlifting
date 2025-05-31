import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
from flask import render_template, Flask

MALE='male'
FEMALE='female'
DATA_PATH = os.environ.get('POWERLIFTING_DATA_PATH')
if DATA_PATH is None:
	print("powerlifting data path isn't set")
	exit()

def wilks_score(row):
    total = get_total(row)
    gender = row['gender']
    denom = 0
    x = row['weight']
    if gender == MALE:
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

def get_total(row):
    return row['deadlift'] + row['bench'] + row['squat']

def init_powerlifting(app):
    plt.rcParams['text.color'] = 'green' # All text (including titles, labels, etc.)
    plt.rcParams['axes.labelcolor'] = 'green' # Axis labels specifically
    #plt.legend(facecolor='black', fontsize="x-large")
    #legend = plt.legend(fontsize="x-large")
    #legend.get_frame().set_facecolor('red')  # Set background color

    df = pd.read_csv(DATA_PATH)
    df = df.interpolate()
    df.set_index('datetime')
    gross = []
    total = []
    for i in df.index:
        print(i)
        gross += [wilks_score(df.iloc[i])]
        total += [get_total(df.iloc[i])]
        print(gross)
        print(total)
    print(gross)
    df['gross'] = gross
    df['total (kgs)'] = total

    analysis_col = []
    for i in df.index:
        # the last row is my current
        current = df.iloc[i]
        deadlift = current['deadlift']
        squat = current['squat']
        bench = current['bench']
        # ideal for deadlift to be 130-150% of your bench press
        deadlift2bench = deadlift/bench
        analysis = ''
        if deadlift2bench >= 1.5:
            analysis += "your bench is too low, ideal bench relative to your deadlift should be {}-{} ".format(deadlift*1.5**-1, deadlift*1.3**-1)
        elif deadlift2bench <= 1.3:
            analysis += "your deadlift is too low, ideal deadlift is 130%-150% of your bench, it shoud be {}-{} ".format(1.3*bench, 1.5*bench)
        # ideal for deadlift to be 110-120% of your squat
        deadlift2squat = deadlift/squat
        if deadlift2squat >= 1.2:
            analysis += "your squat is too low, ideal squat relative to your deadlift should be {}-{} ".format(deadlift*1.2**-1, deadlift*1.1**-1)
        elif deadlift2squat <= 1.1:
            analysis += "your deadlift is too low, ideal deadlift is 110%-120% of your squat, it shoud be {}-{} ".format(1.2*squat, 1.1*squat)
        analysis_col += [analysis]
    df['analysis'] = analysis_col
    df = df.drop('gender', axis=1)
    table_html = df.to_html(classes="table table-striped", index=False)
    plt.grid(color='green', linewidth=1.2, linestyle='--', axis='both')
    fig, ax = plt.subplots()
    fig.set_size_inches(9, 9)
    ax.set_facecolor('black')
    ax.spines['bottom'].set_color('green')  # Bottom axis color
    ax.spines['top'].set_color('green')        # Top axis color
    ax.spines['right'].set_color('green')    # Right axis color
    ax.spines['left'].set_color('green')      # Left axis color
    ax.xaxis.label.set_color('yellow')
    ax.yaxis.label.set_color('blue')
    ax.tick_params(axis='x', colors='green')
    ax.tick_params(axis='y', colors='green')
    fig.set_facecolor('black')  # You can use a color name or hex code
    X = df['datetime']
    ax.plot(X, df['deadlift'], label='deadlift')
    ax.legend(facecolor='black', loc="upper left")
    ax.plot(X, df['squat'], label='squat')
    ax.legend(loc="upper left")
    ax.plot(X, df['bench'], label='bench')
    ax.legend(loc="upper left")
    ax.plot(X, df['deadlift']+df['squat']+df['bench'], label='total')
    ax.legend(loc="upper left")
    ax.plot(X, df['weight'], label='weight')
    ax.legend(loc="upper left")
    ax.plot(X, df['gross'], label='wilks score')
    ax.legend(loc="upper left")
    plt.xticks(rotation=90)
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.rcParams["figure.figsize"] = (200,3)
    plt.close(fig)

    if analysis == '':
        analysis = 'you are on the right track, deadlift/squat: {}, deadlift/bench: {}'.format(deadlift/squat, deadlift/bench)
    @app.route('/powerlifting')
    def index():
        return render_template("index.html", table_html=table_html, plot_url=image_base64, analysis=analysis)

app = Flask(__name__)
app.config.from_object(__name__)

if __name__ == '__main__':
	init_powerlifting(app)
	app.run('0.0.0.0', port=5001)

