from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    in_event = db.Column(db.Boolean, default=False)

    events = db.relationship('Events', back_populates='user')
    songs = db.relationship('FavouriteSong', back_populates='user')
    event_users = db.relationship('EventUsers', back_populates='user')
    voted_songs = db.relationship('VotedSongs', back_populates='user')
    song_reviews = db.relationship('SongReviews', back_populates='user', foreign_keys='SongReviews.user_id')
    username_rel = db.relationship('SongReviews', back_populates='username_rel', foreign_keys='SongReviews.username')

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password (self, password):
        self.password_hash = generate_password_hash(password)

    def check_password (self, password):
        return check_password_hash(self.password_hash, password)

class Events(db.Model):
    event_id = db.Column(db.Integer, primary_key=True, unique=True)
    event_name = db.Column(db.String(64), index=True, unique=True)
    event_code = db.Column(db.Integer, unique=True)
    active_status = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', name='fk_user_id'))

    user = db.relationship('User', back_populates='events')
    event_users = db.relationship('EventUsers', back_populates='event')
    voted_songs = db.relationship('VotedSongs', back_populates='event')

    def __repr__(self):
        return '<Event {}>'.format(self.event_name)

    def get_id(self):
        return str(self.event_id)


class FavouriteSong(db.Model):
    song_id = db.Column(db.Integer, primary_key=True, unique=True)
    track_id = db.Column(db.Integer, index=True)
    song_name = db.Column(db.String(64), index=True)
    artist_name = db.Column(db.String(64), index=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', name='songs_user_id'))

    user = db.relationship('User', back_populates='songs')

    def __repr__(self):
        return '<Song {}>'.format(self.song_name)

    def get_id(self):
        return str(self.song_id)


class EventUsers(db.Model):
    event_user_id = db.Column(db.Integer, primary_key=True, unique=True)
    is_admin = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', name='event_users_user_id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id', name='event_users_event_id'))

    user = db.relationship('User', back_populates='event_users')
    event = db.relationship('Events', back_populates='event_users')

    def __repr__(self):
        return '<EventUser {}>'.format(self.event_user_id)

    def get_id(self):
        return str(self.event_user_id)

class VotedSongs(db.Model):
    vote_id = db.Column(db.Integer, primary_key=True, unique=True)
    track_id = db.Column(db.Integer, index=True)
    song_name = db.Column(db.String(64), index=True)
    artist_name = db.Column(db.String(64), index=True)

    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id', name='voted_songs_event_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', name='voted_songs_user_id'))

    event = db.relationship('Events', back_populates='voted_songs')
    user = db.relationship('User', back_populates='voted_songs')

    def __repr__(self):
        return '<VotedSongs {}>'.format(self.vote_id)

    def get_id(self):
        return str(self.vote_id)

class SongReviews(db.Model):
    review_id = db.Column(db.Integer, primary_key=True, unique=True)
    review = db.Column(db.String(140), index=True)
    reviewsong_id = db.Column(db.Integer, index=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', name='song_reviews_user_id'))
    username = db.Column(db.String(64), db.ForeignKey('user.username', name='song_reviews_username'))

    user = db.relationship('User', back_populates='song_reviews', foreign_keys=user_id)
    username_rel = db.relationship('User', back_populates='song_reviews', foreign_keys=username)

    def __repr__(self):
        return '<SongReviews {}>'.format(self.review_id)

    def get_id(self):
        return str(self.review_id)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))