from flask import render_template, flash, redirect, url_for
from app import app, db
from app.forms import LoginForm, EditProfileForm, RegistrationForm, CreateEventForm, FavouriteSongForm, JoinEventForm, VoteSongForm, SongReviewForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Events, FavouriteSong, EventUsers, VotedSongs, SongReviews
from flask import request
from werkzeug.urls import url_parse
import requests


@app.context_processor # injects the current event the user is in into all templates
def inject_user_event():
    if current_user.is_authenticated:
        if current_user.in_event:
            user_id = current_user.user_id
            user_event = EventUsers.query.filter_by(user_id=user_id).first().event_id
            return dict(user_event=user_event)
        else:
            return dict(user_event=None)
    return dict(user_event=None)


@app.route('/') # displays the home page template
@app.route('/index')
@login_required
def index():
    user_id = current_user.user_id
    if current_user.in_event == 1:
        status = True
        event_id = EventUsers.query.filter_by(user_id=user_id).first().event_id
        event_name = Events.query.filter_by(event_id=event_id).first().event_name
        event_code = Events.query.filter_by(event_id=event_id).first().event_code
    else:
        status = False
        event_name = None
        event_code = None

    recent_fave = FavouriteSong.query.filter_by(user_id=user_id).order_by(FavouriteSong.song_id.desc()).first()
    fave_name = recent_fave.song_name
    fave_artist = recent_fave.artist_name
    song = search_songs(fave_name, fave_artist)

    return render_template('index.html', title='Home', user_id=user_id, status=status, event_name=event_name, event_code=event_code, recent_fave=recent_fave, fave_name=fave_name, fave_artist=fave_artist, song=song)


@app.route('/login', methods=['GET', 'POST']) # login function
def login():
    if current_user.is_authenticated: # checks if the user is already logged in, redirects to home page if yes
        return redirect(url_for('index'))
    form = LoginForm() # sets form as the LoginForm from forms.py
    if form.validate_on_submit(): # checks if the form validates when submitted
        user = User.query.filter_by (username=form.username.data).first() # checks the username against the database
        if user is None or not user.check_password (form.password.data): # if the user doesnt exist or if password doesn match
            flash('Invalid username or password')
            return redirect(url_for('login')) # restart the login
        #login_user(user, remember=form.remember_me.data)
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)


@app.route ('/logout') # logs the user out
def logout():
    logout_user() # runs the user log out function
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST']) # user registration
def register():
    if current_user.is_authenticated: # checks if user is already logged in
        return redirect (url_for('index'))
    form = RegistrationForm() # sets form as the RegistrationForm from forms.py
    if form.validate_on_submit(): # checks if the form validates when submitted
        user = User(username=form.username.data, email=form.email.data) # creates a new user from the form
        user.set_password(form.password.data) # sets the password for the new user
        db.session.add(user) # adds to database
        db.session.commit() # commits to database
        flash('Welcome to Northside DJs!!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>') # user profile page
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404() # gets the user from the database
    event_users = EventUsers.query.filter_by(user_id=user.user_id).all()
    return render_template('user.html', user=user, event_users=event_users)


@app.route('/edit_profile', methods=['GET', 'POST']) # edit profile page
@login_required
def edit_profile():
    form = EditProfileForm() # sets form as the EditProfileForm from forms.py
    if form.validate_on_submit(): # checks if the form validates when submitted
        current_user.username = form.username.data # sets the username to the form data
        current_user.about_me = form.about_me.data # sets the about me to the form data
        db.session.commit() # commits to database
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET': # if the request is a GET request
        form.username.data = current_user.username # sets the username to the current user's username
        form.about_me.data = current_user.about_me # sets the about me to the current user's about me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/create_event', methods=['GET', 'POST']) # create event page
@login_required
def create_event():

    form = CreateEventForm() # sets form as the CreateEventForm from forms.py
    user_id = current_user.user_id # gets the current user's id

    if form.validate_on_submit():
        event = Events(event_name=form.event_name.data, event_code=form.event_code.data, user_id=user_id)
        db.session.add(event)
        db.session.commit()
        flash(f'{form.event_name.data} has been created.')
        event_id = Events.query.filter_by(event_name=form.event_name.data).first().event_id
        event_user = EventUsers(event_id=event_id, user_id=user_id, is_admin=True)
        current_user.in_event = True
        db.session.add(event_user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_event.html', title='Create Event', form=form)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        song_name = request.form['song']
        artist_name = request.form['artist']
        song = search_songs(song_name, artist_name)


        song_id = song['idTrack']
        reviews = SongReviews.query.filter_by(reviewsong_id=song_id).all()
        all_reviews = []

        for item in reviews:
            username = item.username
            review = item.review
            all_reviews.append({'username': username, 'review': review})

        print(all_reviews)
        if song:
            return render_template('results.html', song=song, song_in_favourites=song_in_favourites, all_reviews=all_reviews)
        else:
            flash('Song not found')
            flash('Try double checking your spelling!')
            return render_template('search.html')
    return render_template('search.html')

def song_in_favourites(track_id):
    user_id = current_user.user_id
    return FavouriteSong.query.filter_by(user_id=user_id, track_id=track_id).first() is not None

def search_songs(song_name, artist_name): # searches for albums and gets response from api
    api = '523532'
    url = f'https://theaudiodb.com/api/v1/json/{api}/searchtrack.php?s={artist_name}&t={song_name}'
    response = requests.get(url)
    get_data = response.json()
    if 'track' in get_data and get_data['track'] is not None:
        return get_data['track'][0]

    return None


@app.route('/favourite_song', methods=['GET', 'POST'])
@login_required
def favourite_song():
    form = FavouriteSongForm()

    song_name = request.form.get('song_name')
    artist_name = request.form.get('artist_name')
    track_id = request.form.get('track_id')


    if song_name and artist_name:
        user_id = current_user.user_id
        new_song = FavouriteSong(song_name=song_name, artist_name=artist_name, track_id=track_id, user_id=user_id)

        if FavouriteSong.query.filter_by(track_id=track_id, user_id=user_id).first():
            flash('Song removed from favourites.')
            song = FavouriteSong.query.filter_by(track_id=track_id, user_id=user_id).first()
            db.session.delete(song)
            db.session.commit()
            return redirect(url_for('search'))
        else:
            db.session.add(new_song)
            db.session.commit()
            flash('Your song has been added to your favourites.')
            return redirect(url_for('search'))
    else:
        flash('Something went wrong')
        return render_template('search.html', title='Favourite Song', form=form)


@app.route('/vote_song', methods=['GET', 'POST'])
@login_required
def vote_song():
    form = VoteSongForm()
    user_id = current_user.user_id
    event_id = EventUsers.query.filter_by(user_id=user_id).first().event_id

    song_name = request.form.get('song_name')
    artist_name = request.form.get('artist_name')
    track_id = request.form.get('track_id')


    if current_user.in_event:
        if song_name and artist_name:
            if VotedSongs.query.filter_by(track_id=track_id, event_id=event_id, user_id=user_id).first() is None:
                new_song = VotedSongs(song_name=song_name, artist_name=artist_name, track_id=track_id, event_id=event_id, user_id=user_id)
                db.session.add(new_song)
                db.session.commit()
                flash(f'{song_name} has been upvoted!')
                return redirect(url_for('search'))
            else:
                flash('You have already voted for this song')
                return render_template('search.html', title='Vote Song', form=form)

        else:
            flash('Something went wrong')
            return render_template('search.html', title='Vote Song', form=form)
    else:
        flash('You are not in an event')
        return render_template('search.html', title='Vote Song', form=form)


def get_event_songs(event_id):
    user_id = current_user.user_id
    event_id = EventUsers.query.filter_by(user_id=user_id).first().event_id
    event_songs = VotedSongs.query.filter_by(event_id=event_id).all()

    unique_songs = set()

    filtered_songs = []

    for song in event_songs:
        current_song = (song.track_id, song.event_id)
        if current_song not in unique_songs:
            unique_songs.add(current_song)
            song_votes = vote_counter(song.track_id, event_id)

            song_with_votes = {
                'song_name': song.song_name,
                'artist_name': song.artist_name,
                'votes': song_votes
            }
            filtered_songs.append(song_with_votes)

    sorted_songs = sorted(filtered_songs, key=lambda k: k['votes'], reverse=True)

    return sorted_songs


def vote_counter(track_id, event_id):
    return VotedSongs.query.filter_by(track_id=track_id, event_id=event_id).count()


@app.route('/my_favourites', methods=['GET', 'POST'])
@login_required
def my_favourites():
    user_id = current_user.user_id
    songs = FavouriteSong.query.filter_by(user_id=user_id).all()
    return render_template('my_favourites.html', songs=songs)


@app.route('/my_events', methods=['GET', 'POST'])
@login_required
def my_events():
    user_id = current_user.user_id
    events = Events.query.filter_by(user_id=user_id).all()
    return render_template('my_events.html', events=events)


@app.route('/event_status/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_status(event_id):
    event = Events.query.get_or_404(event_id)
    user_id = current_user.user_id
    active_status = User.query.get(user_id).in_event
    if event:
        if event.active_status == 1:
            event.active_status = 0

            all_users = EventUsers.query.filter_by(event_id=event_id).all()

            user_ids = []
            for user in all_users:
                user_in_event = User.query.get(user.user_id) # check if this is actually necessary
                user_in_event.in_event = 0
                user_ids.append(user.user_id)
                db.session.delete(user)
                db.session.commit()

            event_songs = VotedSongs.query.filter_by(event_id=event_id).all()
            for song in event_songs:
                db.session.delete(song)
                db.session.commit()

            flash(f'{event.event_name} has been deactivated')

        else:
            if active_status == 1:
                flash('You are already in an event')
                return redirect(url_for('my_events'))
            else:
                event.active_status = 1
                current_user.in_event = 1
                user_id = current_user.user_id
                event_id = event.event_id
                event_user = EventUsers(event_id=event_id, user_id=user_id, is_admin=True)
                db.session.add(event_user)
                db.session.commit()
                flash(f'{event.event_name} has been activated')

        db.session.commit()
    return redirect(url_for('my_events'))


@app.route('/join_event', methods=['GET', 'POST'])
@login_required
def join_event():
    form = JoinEventForm()
    if current_user.in_event == 0:
        if form.validate_on_submit():
            event_code = form.event_code.data
            event = Events.query.filter_by(event_code=event_code).first()
            if event and event.active_status == 1:
                event_id = event.event_id
                user_id = current_user.user_id
                joining_user = EventUsers(event_id=event_id, user_id=user_id)
                current_user.in_event = 1
                db.session.add(joining_user)
                db.session.commit()
                event_name = Events.query.get(event_id).event_name
                flash(f'You have joined {event_name}')
                return redirect(url_for('event', event_id=event_id))
            else:
                flash('Event not found.')
                return redirect(url_for('index'))
    else:
        flash('You are already in an event. Please leave the current event to join a new one.')
        return redirect(url_for('index'))
    return render_template('join_event.html', title='Join Event', form=form)


@app.route('/leave_event', methods=['GET', 'POST'])
@login_required
def leave_event():
    admin_status = EventUsers.query.filter_by(user_id=current_user.user_id).first().is_admin
    event_id = EventUsers.query.filter_by(user_id=current_user.user_id).first().event_id
    if current_user.in_event == 1:
        current_user.in_event = 0
        EventUsers.query.filter_by(user_id=current_user.user_id).delete()
        db.session.commit()
        flash('You have left the event')
        if admin_status == 1:
            all_users = EventUsers.query.filter_by(event_id=event_id).all()
            event_status = Events.query.get_or_404(event_id).active_status
            if event_status == 1:
                Events.query.get_or_404(event_id).active_status = 0
                db.session.commit()
            user_ids = []
            for user in all_users:
                user_in_event = User.query.get(user.user_id)
                user_in_event.in_event = 0
                user_ids.append(user.user_id)
                db.session.delete(user)
                db.session.commit()
                flash('Admin has left the event. All users have been removed from the event')

            event_songs = VotedSongs.query.filter_by(event_id=event_id).all()
            for song in event_songs:
                db.session.delete(song)
                db.session.commit()
                flash('All songs have been removed from the event')


        return redirect(url_for('user', username=current_user.username))
    else:
        flash('You are not in an event')
        return redirect(url_for('user', username=current_user.username))


@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event(event_id):
    user_id = current_user.user_id
    user_event = EventUsers.query.filter_by(user_id=user_id).first().event_id
    event_name = Events.query.filter_by(event_id=user_event).first().event_name
    event_code = Events.query.filter_by(event_id=user_event).first().event_code
    users = EventUsers.query.filter_by(event_id=user_event).all()
    admin = EventUsers.query.filter_by(is_admin=1, event_id=user_event).first()
    event_songs = get_event_songs(user_event)


    if admin:
        admin_user = User.query.filter_by(user_id=admin.user_id).first()
        admin_username = admin_user.username

    users_names = []
    for user in users:
        if user.is_admin == 0:
            user_name = User.query.filter_by(user_id=user.user_id).first().username
            users_names.append(user_name)


    return render_template('event.html', event_id=user_event, user_event=user_event, event_name=event_name, event_code=event_code, users=users, users_names=users_names, admin_username=admin_username, event_songs=event_songs)



@app.route('/add_review', methods=['GET', 'POST'])
@login_required
def add_review():
    form = SongReviewForm()

    review = request.form.get('review')
    song_id = request.form.get('song_id')
    user_id = current_user.user_id
    username = current_user.username

    if review and song_id:
        new_review = SongReviews(review=review, reviewsong_id=song_id, user_id=user_id, username=username)
        db.session.add(new_review)
        db.session.commit()
        flash('Your review has been added')
        return redirect(url_for('search'))
    else:
        flash('Something went wrong')
        return redirect(url_for('search'))












