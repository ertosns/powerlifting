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
    
    # Get last values for legend
    last_squat = df['squat'].iloc[-1] if len(df) > 0 else 0
    last_bench = df['bench'].iloc[-1] if len(df) > 0 else 0
    last_deadlift = df['deadlift'].iloc[-1] if len(df) > 0 else 0
    last_total = total.iloc[-1] if len(total) > 0 else 0
    
    # Plot individual lifts in different colors with last values in legend
    ax.plot(X, df['squat'], label=f'Squat ({last_squat} kg)', color='cyan', linewidth=2.5, alpha=0.8)
    ax.plot(X, df['bench'], label=f'Bench ({last_bench} kg)', color='magenta', linewidth=2.5, alpha=0.8)
    ax.plot(X, df['deadlift'], label=f'Deadlift ({last_deadlift} kg)', color='yellow', linewidth=2.5, alpha=0.8)
    ax.plot(X, total, label=f'Total ({last_total} kg)', color='lime', linewidth=3)
    
    ax.set_xlabel('Date', fontsize=16, color='lime', fontweight='bold')
    ax.set_ylabel('Weight (kgs)', fontsize=16, color='lime', fontweight='bold')
    
    # Add legend
    legend = ax.legend(loc="upper left", fontsize=14, framealpha=0.9)
    plt.setp(legend.get_texts(), color='lime', fontweight='bold')
    legend.get_frame().set_facecolor('black')
    legend.get_frame().set_edgecolor('lime')
    
    plt.xticks(rotation=45, color='lime', fontsize=16, fontweight='bold')
    plt.yticks(color='lime', fontsize=16, fontweight='bold')
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.rcParams["figure.figsize"] = (200,3)
    plt.close(fig)
    return image_base64
