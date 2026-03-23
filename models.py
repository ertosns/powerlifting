from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask import Flask
import os

app = Flask(__name__, static_url_path='/powerlifting/static')
app.secret_key = b'\xf6\x91\nKp\x13\xd4\xf3$!\xa2\x00\xf6\xd4\xa6\x0cB\x89B>\x1b\xf8'

# Configure ProxyFix for correct URL generation behind Nginx
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Ensure instance path exists
os.makedirs(app.instance_path, exist_ok=True)
# Use absolute path to instance folder for database
db_path = os.path.join(app.instance_path, 'powerlifting_b7.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
class Base(DeclarativeBase):
    pass
db = SQLAlchemy(app)
#db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(256), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=True)
    share_token = db.Column(db.String(64), nullable=True)
    # Add google_id if using OAuth
    #records = db.relationship('Record', backref='user', lazy=True)
    @property
    def is_active(self):
        #TODO
        return True
    # Flask-Login required methods and properties
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.String, nullable=False)
    deadlift = db.Column(db.Float, nullable=False)
    squat = db.Column(db.Float, nullable=False)
    bench = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String, nullable=False)
    is_target = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('records', lazy=True))


class VideoJob(db.Model):
    """Tracks video editing jobs submitted by users."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, complete, failed
    input_filename = db.Column(db.String(256), nullable=False)
    output_filename = db.Column(db.String(256), nullable=True)
    lift_type = db.Column(db.String(20), nullable=False)       # squat, bench, deadlift
    weight_kg = db.Column(db.Float, nullable=False)
    total_reps = db.Column(db.Integer, nullable=False)
    rep_timestamps_json = db.Column(db.Text, nullable=False)   # JSON: [{"start_sec": 1.0, "end_sec": 3.5}, ...]
    theme_name = db.Column(db.String(50), nullable=False)
    audio_mode = db.Column(db.String(20), nullable=False, default='original_sfx')  # original_sfx, full_replace, keep
    is_pr = db.Column(db.Boolean, nullable=False, default=False)
    record_id = db.Column(db.Integer, db.ForeignKey('record.id'), nullable=True)  # Optional link to a Record
    created_at = db.Column(db.String, nullable=False)
    completed_at = db.Column(db.String, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    celery_task_id = db.Column(db.String(256), nullable=True)

    user = db.relationship('User', backref=db.backref('video_jobs', lazy=True))
