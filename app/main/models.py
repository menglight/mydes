from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager # login_manager will be initialized in app/__init__.py

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    # We can add subscription status here later
    stripe_customer_id = db.Column(db.String(120), nullable=True, index=True)
    subscription_active = db.Column(db.Boolean, default=False)
    stripe_subscription_id = db.Column(db.String(120), nullable=True, index=True) # To store current subscription ID
    stripe_current_period_end = db.Column(db.DateTime, nullable=True) # To know when subscription ends/renews

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
