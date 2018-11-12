from app import db
from datetime import datetime
from hashutils import make_pw_hash, make_salt, check_pw_hash

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    hidden = db.Column(db.Boolean)

    def __init__(self, title, body, pub_date, owner):
        self.title = title
        self.body = body
        self.pub_date = datetime.utcnow()
        self.owner_id = owner
        self.hidden = False
    
    def __repr__(self):
        return '<Blog %r>' % self.title

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, username, password):
        self.username = username
        self.email = email
        self.pw_hash = make_pw_hash(password)

    def __repr__(self):
        return '<User %r>' %self.username