import os
import pandas as pd
import base64
from total_curve_plot import make_total_curve_plot
from sqlalchemy import create_engine

def generate_total_curve_image():
    # Load real data from SQLite DB
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'powerlifting.db')
    engine = create_engine(f'sqlite:///{db_path}')
    df = pd.read_sql('SELECT id, datetime, deadlift, squat, bench FROM Record', engine)
    # Parse date and sort strictly ascending
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.sort_values(['datetime', 'id'], ascending=[True, True]).reset_index(drop=True)
    # Print sorted dates for debugging
    print(df[['id', 'datetime']].to_string())
    # Calculate total using the same logic as powerlifting.py
    def get_total(row):
        return row['deadlift'] + row['bench'] + row['squat']
    df['total'] = df.apply(get_total, axis=1)
    image_base64 = make_total_curve_plot(df)
    # Save image to static folder
    static_img_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'img')
    os.makedirs(static_img_dir, exist_ok=True)
    static_path = os.path.join(static_img_dir, 'powerlifting_total_curve.png')
    with open(static_path, 'wb') as f:
        f.write(base64.b64decode(image_base64))
    return static_path

generate_total_curve_image()