from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, TextAreaField, FileField
from wtforms.validators import ValidationError, Email, EqualTo, DataRequired, Length

from app.models import User, Events


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('SIGN IN')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('REGISTER')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email (self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

class UploadPfpForm(FlaskForm):
    pfp = FileField('Profile Picture', validators=[DataRequired()])
    submit = SubmitField('Upload')

class CreateEventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[DataRequired()])
    event_code = StringField('Event Code', validators=[DataRequired()])
    event_location = StringField('Event Location', validators=[DataRequired()])
    event_description = TextAreaField('Event Description', validators=[Length(min=0, max=140)])
    submit = SubmitField('Create Event')

    def validate_event_name(self, event_name):
        event = Events.query.filter_by(event_name=event_name.data).first()
        if event is not None:
            raise ValidationError('Please use a different event name.')

    def validate_event_code(self, event_code):
        event = Events.query.filter_by(event_code=event_code.data).first()
        if event is not None:
            raise ValidationError('Please use a different event code.')

class FavouriteSongForm(FlaskForm):
    song_name = StringField('Song Name', validators=[DataRequired()])
    artist_name = StringField('Artist Name', validators=[DataRequired()])
    track_id = StringField('Track ID', validators=[DataRequired()])
    submit = SubmitField('Favourite')


class VoteSongForm(FlaskForm):
    song_name = StringField('Song Name', validators=[DataRequired()])
    artist_name = StringField('Artist Name', validators=[DataRequired()])
    track_id = StringField('Track ID', validators=[DataRequired()])
    submit = SubmitField('Vote')


class JoinEventForm(FlaskForm):
    event_code = StringField('Event Code', validators=[DataRequired()])
    submit = SubmitField('Search')

class SongReviewForm(FlaskForm):
    review = TextAreaField('Review', validators=[Length(min=0, max=140), DataRequired()])
    user_id = StringField('User ID', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    song_id = StringField('Song ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class SearchUsersForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Search')