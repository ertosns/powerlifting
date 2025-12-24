from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask import Flask

app = Flask(__name__)
app.secret_key = b'\xf6\x91\nKp\x13\xd4\xf3$!\xa2\x00\xf6\xd4\xa6\x0cB\x89B>\x1b\xf8'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///powerlifting_b7.db'
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
    share_token = db.Column(db.String(64), unique=True, nullable=True)
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
