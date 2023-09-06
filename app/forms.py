from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, TextAreaField, FileField
from wtforms.validators import ValidationError, Email, EqualTo, DataRequired, Length

from app.models import User, Events


class LoginForm(FlaskForm): # Login form for existing users
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('SIGN IN')


class RegistrationForm(FlaskForm): # Registration form for new users
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('REGISTER')

    def validate_username(self, username): # Checks if username already exists in database
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email (self, email): # Checks if email already exists in database
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm): # Edit profile form for existing users
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

class UploadPfpForm(FlaskForm): # Upload profile picture form for existing users
    pfp = FileField('Profile Picture', validators=[DataRequired()])
    submit = SubmitField('Upload')

class CreateEventForm(FlaskForm): # Create event form for existing users
    event_name = StringField('Event Name', validators=[DataRequired()])
    event_code = StringField('Event Code', validators=[DataRequired()])
    event_location = StringField('Event Location', validators=[DataRequired()])
    event_description = TextAreaField('Event Description', validators=[Length(min=0, max=140)])
    dj = StringField('DJ', validators=[DataRequired()])
    submit = SubmitField('Create Event')

    def validate_event_name(self, event_name): # Checks if event name already exists in database
        event = Events.query.filter_by(event_name=event_name.data).first()
        if event is not None:
            raise ValidationError('Please use a different event name.')

    def validate_event_code(self, event_code): # Checks if event code already exists in database
        event = Events.query.filter_by(event_code=event_code.data).first()
        if event is not None:
            raise ValidationError('Please use a different event code.')

class FavouriteSongForm(FlaskForm): # Favourite song form for existing users
    song_name = StringField('Song Name', validators=[DataRequired()])
    artist_name = StringField('Artist Name', validators=[DataRequired()])
    track_id = StringField('Track ID', validators=[DataRequired()])
    submit = SubmitField('Favourite')


class VoteSongForm(FlaskForm): # Vote song form for existing users
    song_name = StringField('Song Name', validators=[DataRequired()])
    artist_name = StringField('Artist Name', validators=[DataRequired()])
    track_id = StringField('Track ID', validators=[DataRequired()])
    submit = SubmitField('Vote')


class JoinEventForm(FlaskForm): # Join event form for existing users
    event_code = StringField('Event Code', validators=[DataRequired()])
    submit = SubmitField('Search')

class SongReviewForm(FlaskForm): # Song review form for existing users
    review = TextAreaField('Review', validators=[Length(min=0, max=140), DataRequired()])
    user_id = StringField('User ID', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    song_id = StringField('Song ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class SearchUsersForm(FlaskForm): # Search users form for existing users
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Search')