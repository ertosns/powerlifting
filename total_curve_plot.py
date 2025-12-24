import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd

def make_total_curve_plot(df):
    plt.rcParams['text.color'] = 'lime'
    plt.rcParams['axes.labelcolor'] = 'lime'
    plt.rcParams['font.size'] = 16
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 16
    plt.rcParams['xtick.labelsize'] = 16
    plt.rcParams['ytick.labelsize'] = 16
    plt.grid(color='lime', linewidth=2, linestyle='--', axis='both')
    fig, ax = plt.subplots()
    fig.set_size_inches(16, 10)
    ax.set_facecolor('black')
    ax.spines['bottom'].set_color('lime')
    ax.spines['top'].set_color('lime')
    ax.spines['right'].set_color('lime')
    ax.spines['left'].set_color('lime')
    ax.xaxis.label.set_color('lime')
    ax.yaxis.label.set_color('lime')
    ax.tick_params(axis='x', colors='lime')
    ax.tick_params(axis='y', colors='lime')
    fig.set_facecolor('black')
    X = df['datetime']
    def get_total(row):
        return row['deadlift'] + row['bench'] + row['squat']
    total = df.apply(get_total, axis=1)
    ax.plot(X, total, label='Total', color='lime', linewidth=3)
    ax.set_xlabel('Date', fontsize=16, color='lime', fontweight='bold')
    ax.set_ylabel('Total (kgs)', fontsize=16, color='lime', fontweight='bold')
    #legend = ax.legend(loc="upper left")
    #plt.setp(legend.get_texts(), fontsize=5, color='lime', fontweight='bold')
    plt.xticks(rotation=45, color='lime', fontsize=16, fontweight='bold')
    plt.yticks(color='lime', fontsize=16, fontweight='bold')
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.rcParams["figure.figsize"] = (200,3)
    plt.close(fig)
    return image_base64
