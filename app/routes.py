from flask import render_template, flash, redirect, url_for
from app import app, db
from app.forms import LoginForm, EditProfileForm, RegistrationForm, CreateEventForm
from app.forms import FavouriteSongForm, JoinEventForm, VoteSongForm, SongReviewForm, UploadPfpForm, SearchUsersForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Events, FavouriteSong, EventUsers, VotedSongs, SongReviews
from flask import request
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import requests
import os
import datetime


@app.context_processor # injects the current event the user is in into all templates
def inject_user_event():
    if current_user.is_authenticated: # checks if the user is logged in
        if current_user.in_event: # checks if the user is in an event
            user_id = current_user.user_id
            user_event = EventUsers.query.filter_by(user_id=user_id).first().event_id
            return dict(user_event=user_event) # returns the event that the user is in
        else:
            return dict(user_event=None) # returns the user event as none if the user is not in an event
    return dict(user_event=None) # returns the user event as none if the user is not logged in


@app.route('/') # displays the home page template
@app.route('/index')
@login_required
def index():
    user_id = current_user.user_id # gets the user id of the current user
    if current_user.in_event == 1: # checks if the current user is in an event
        status = True

        # gets information about the event the user is in
        event_id = EventUsers.query.filter_by(user_id=user_id).first().event_id
        event_name = Events.query.filter_by(event_id=event_id).first().event_name
        event_code = Events.query.filter_by(event_id=event_id).first().event_code
    else:
        status = False

        #sets event information to none as user is not in an event
        event_name = None
        event_code = None

    #gets the most recent addition to the users favourites
    recent_fave = FavouriteSong.query.filter_by(user_id=user_id).order_by(FavouriteSong.song_id.desc()).first()

    #gets the song information for the most recent addition to the users favourites
    if recent_fave:
        fave_name = recent_fave.song_name
        fave_artist = recent_fave.artist_name
        song = search_songs(fave_name, fave_artist)
    else: # handles the scenario of the user having no favourites
        fave_name = None
        fave_artist = None
        song = None

    #returns the website template with the relevant variables injected into it
    return render_template('index.html', title='Home', user_id=user_id, status=status, event_name=event_name, event_code=event_code, recent_fave=recent_fave, fave_name=fave_name, fave_artist=fave_artist, song=song)


### LOGIN AND USER REGISTRATION HANDLING ###
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
        login_user(user, remember=form.remember_me.data) # logs the user in
        next_page = request.args.get('next') # gets the next page from the url
        if not next_page or url_parse(next_page).netloc != '': # checks if the next page is valid
            next_page = url_for('index') # sets the next page to the home page
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)


@app.route ('/logout') # logs the user out
def logout():
    logout_user() # runs the user log out function provided by flask_login
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


### USER PROFILE HANDLING ###
@app.route('/user/<username>') # user profile page
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404() # gets the user from the database
    event_users = EventUsers.query.filter_by(user_id=user.user_id).all() # gets the events the user is in
    if user == current_user: # checks if the user is the current user
        favourites = my_favourites() # gets the current users favourites
    else: # if the user is not the current user
        favourites = user_favourites(user.user_id) # gets the users favourites
    return render_template('user.html', user=user, event_users=event_users, favourites=favourites)


@app.route('/edit_profile', methods=['GET', 'POST']) # edit profile page
@login_required
def edit_profile(): # edit profile function
    form = EditProfileForm() # sets form as the EditProfileForm from forms.py
    if form.validate_on_submit(): # checks if the form validates when submitted
        current_user.username = form.username.data # sets the username to the form data
        current_user.about_me = form.about_me.data # sets the about me to the form data
        db.session.commit() # commits to database
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username)) # redirects to the users profile page

    else:
        form.username.data = current_user.username # sets the username to the current users username
        form.about_me.data = current_user.about_me # sets the about me to the current users about me
        flash('Your changes have not been saved.')


    return render_template('edit_profile.html', title='Edit Profile',
                           form=form) # renders the edit profile page

@app.route('/upload_pfp', methods=['GET', 'POST']) # upload profile picture page
@login_required
def upload_pfp():
    form = UploadPfpForm() # sets form as the UploadPfpForm from forms.py

    if form.validate_on_submit(): # checks if the form validates when submitted
        if current_user.pfp:
            os.remove('app/static/uploads/' + current_user.pfp) # removes the old profile picture from the program files
        file_name = secure_filename(form.pfp.data.filename) # sets the file name to the secure filename
        form.pfp.data.save('app/static/uploads/' + file_name) # saves the file to the program files
        current_user.pfp = file_name # adds the name of the file to the user database entry
        db.session.commit() # commits to database
        flash('Your profile picture has been updated.')
        return redirect(url_for('user', username=current_user.username))


    return render_template('upload_pfp.html', title='Upload Profile Picture',
                           form=form)


@app.route('/search_users', methods=['GET', 'POST']) # search users page
@login_required
def search_users():
    form = SearchUsersForm() # sets form as the SearchUsersForm from forms.py
    user = form.username.data # sets user as the username searched in the form
    if user:
        found_user = User.query.filter_by(username=user).first() # gets the user from the database
        if found_user: # checks if the username exists
            username = found_user.username # sets username as the found users username
            return redirect(url_for('user', username=username))
        else: # if the username doesnt exist
            flash('User not found')
            return redirect(url_for('search_users'))

    return render_template('search_users.html', title='Search Users', form=form)


### EVENT HANDLING ###

@app.route('/create_event', methods=['GET', 'POST']) # create event page
@login_required
def create_event():

    form = CreateEventForm() # sets form as the CreateEventForm from forms.py
    user_id = current_user.user_id # gets the current user's id

    if form.validate_on_submit():
        # creates a new event from the form data
        dj = form.dj.data
        print(dj)
        search_dj = User.query.filter_by(username=dj).first()
        if search_dj:
            if search_dj.user_id == user_id:
                flash('You cannot add yourself as a DJ')
                return redirect(url_for('create_event'))
            else:
                dj_id = search_dj.user_id
                print(dj_id)
        else:
            flash('DJ not found')
            return redirect(url_for('create_event'))

        event = Events(event_name=form.event_name.data, event_code=form.event_code.data,
                       user_id=user_id, event_location=form.event_location.data,
                       event_description=form.event_description.data, dj_id=dj_id)
        db.session.add(event) # adds new event to database
        db.session.commit() # commits to database
        flash(f'{form.event_name.data} has been created. Activate your event at "my events" to begin.')
        return redirect(url_for('index'))
    return render_template('create_event.html', title='Create Event', form=form)

def get_event_songs(event_id): # gets the songs in an event
    user_id = current_user.user_id # gets the current user's id
    event_id = EventUsers.query.filter_by(user_id=user_id).first().event_id # gets the event user is in
    event_songs = VotedSongs.query.filter_by(event_id=event_id).all()  # gets songs in the users event

    unique_songs = set() # creates a set to store unique songs

    filtered_songs = [] # creates a list to store the songs

    for song in event_songs: # loops through all songs found from the database
        current_song = (song.track_id, song.event_id) # sets track id and event id of the current song
        if current_song not in unique_songs: # checks if the song is in the set of unique songs
            unique_songs.add(current_song) # adds the song to the set of unique songs
            song_votes = vote_counter(song.track_id, event_id) # gets song votes using the vote_counter function

            song_with_votes = { # creates a dictionary with the song name, artist name and votes
                'song_name': song.song_name,
                'artist_name': song.artist_name,
                'votes': song_votes
            }
            filtered_songs.append(song_with_votes) # adds the song_with_votes entry to filter_songs

    sorted_songs = sorted(filtered_songs, key=lambda k: k['votes'], reverse=True) # sorts the songs by votes in descending order

    return sorted_songs # returns the sorted songs


def vote_counter(track_id, event_id): # counts the votes for a song
    # counts the number of times a song entry appears in a single event
    return VotedSongs.query.filter_by(track_id=track_id, event_id=event_id).count()


@app.route('/my_events', methods=['GET', 'POST']) # gets the events a user has created
@login_required
def my_events():
    user_id = current_user.user_id # gets the current user's id
    events = Events.query.filter_by(user_id=user_id).all() # gets all events the user has created
    return render_template('my_events.html', events=events)


@app.route('/event_status/<int:event_id>', methods=['GET', 'POST']) # activates or deactivates an event
@login_required
def event_status(event_id):
    event = Events.query.get_or_404(event_id) # gets the event from the database
    user_id = current_user.user_id # gets the current user's id
    user_active = User.query.get(user_id).in_event # gets whether the user is in an event
    if event: # checks if the event exists

        if event.active_status == 1: # checks if the event is active

            f = open('app/static/history/' + event.event_name + '.txt', 'a')  # opens a file to store the event history
            f.write('Event History for ' + event.event_name + '\n \n') # writes the event name to the file
            f.write('Date: ' + str(datetime.datetime.now()) + '\n \n') # writes the date to the file
            f.write('All Users' + '\n' + '---' + '\n') # writes all songs to the file

            event.active_status = 0 # sets the event to inactive

            all_users = EventUsers.query.filter_by(event_id=event_id).all() # gets all users in the event

            user_ids = [] # creates a list to store the user ids
            for user in all_users: # loops through all users in the event

                username = User.query.get(user.user_id).username # gets the username of the user
                f.write(username + '\n') # writes the username to the file

                user_in_event = User.query.get(user.user_id) # check if this is actually necessary
                user_in_event.in_event = 0 # sets the user to not in an event
                user_ids.append(user.user_id) # adds the user id to the list of user ids
                db.session.delete(user) # removes user from the event database
                db.session.commit() # commits to database

            f.write('\nAll Songs' + '\n'+ '---' + '\n') # writes all songs to the file

            event_songs = VotedSongs.query.filter_by(event_id=event_id).all() # gets all voted songs in the event
            for song in event_songs: # loops through all songs in the event
                f.write(song.song_name + ' by ' + song.artist_name + '\n') # writes the song name and artist name to the file

                db.session.delete(song) # removes song from the event database
                db.session.commit() # commits to database

            f.write('\n \n')
            f.close() # closes the file

            flash(f'{event.event_name} has been deactivated')

        else:
            if user_active == 1: # checks if the user is in an event
                flash('You are already in an event') # flashes a message to the user
                return redirect(url_for('my_events'))
            else:
                event.active_status = 1 # sets the event to active
                current_user.in_event = 1 # sets the user to in an event
                user_id = current_user.user_id # gets the current user's id
                event_id = event.event_id # gets the event id
                event_user = EventUsers(event_id=event_id, user_id=user_id, is_admin=True) # adds the user to the event
                db.session.add(event_user) # adds the user to the event database
                db.session.commit() # commits to database
                flash(f'{event.event_name} has been activated')

        db.session.commit()
    return redirect(url_for('my_events'))


@app.route('/join_event', methods=['GET', 'POST']) # allows a user to join an event
@login_required
def join_event():
    form = JoinEventForm() # creates a form to join an event
    if current_user.in_event == 0: # checks if the user is in an event
        if form.validate_on_submit():
            event_code = form.event_code.data # gets the event code from the form
            event = Events.query.filter_by(event_code=event_code).first() # gets the event from the database using code entered by user
            if event and event.active_status == 1: # if the event exists and the event is active
                event_id = event.event_id # gets the event id
                user_id = current_user.user_id # gets the current user's id

                if user_id == event.dj_id: # checks if the user is the dj
                    joining_user = EventUsers(event_id=event_id, user_id=user_id, is_dj=True) # adds the user to the event as a dj
                else:
                    joining_user = EventUsers(event_id=event_id, user_id=user_id) # adds the user to the event

                current_user.in_event = 1 # sets the user to in an event
                db.session.add(joining_user)
                db.session.commit()

                # flashes a message to the user
                event_name = Events.query.get(event_id).event_name
                flash(f'You have joined {event_name}')
                return redirect(url_for('event', event_id=event_id))
            else: # if the event doesn't exist OR if the event is not active
                flash('Event not found.')
                return redirect(url_for('join_event'))
    else: # if the user is already in an event
        flash('You are already in an event. Please leave the current event to join a new one.')
        return redirect(url_for('index'))
    return render_template('join_event.html', title='Join Event', form=form)


@app.route('/leave_event', methods=['GET', 'POST']) # allows a user to leave an event
@login_required
def leave_event():
    admin_status = EventUsers.query.filter_by(user_id=current_user.user_id).first().is_admin # checks if the user is th event admin
    event_id = EventUsers.query.filter_by(user_id=current_user.user_id).first().event_id # gets the event id
    if current_user.in_event == 1: # checks if the user is in an event
        current_user.in_event = 0 # sets the user to not in an event
        EventUsers.query.filter_by(user_id=current_user.user_id).delete() # removes the user from the event database
        db.session.commit()
        flash('You have left the event')

        # ensures that when the admin leaves the event is ended and all uers and songs are removed
        if admin_status == 1: # checks if the user is the event admin
            all_users = EventUsers.query.filter_by(event_id=event_id).all() # gets all users in the event
            event_status = Events.query.get_or_404(event_id).active_status # gets the event status
            if event_status == 1: # checks if the event is active
                Events.query.get_or_404(event_id).active_status = 0 # sets the event to inactive
                db.session.commit()
            user_ids = [] # creates a list to store the user ids
            for user in all_users: # loops through all users in the event
                user_in_event = User.query.get(user.user_id)
                user_in_event.in_event = 0
                user_ids.append(user.user_id)
                db.session.delete(user) # removes user from the event database
                db.session.commit()
                flash('Admin has left the event. All users have been removed from the event')

            event_songs = VotedSongs.query.filter_by(event_id=event_id).all() # gets all voted songs in the event
            for song in event_songs: # loops through all songs in the event
                db.session.delete(song) # removes song from the event database
                db.session.commit()
                flash('All songs have been removed from the event')


        return redirect(url_for('user', username=current_user.username))
    else: # handles if the user somehow accesses the leave event button while not being in an event
        flash('You are not in an event')
        return redirect(url_for('user', username=current_user.username))


@app.route('/event/<int:event_id>', methods=['GET', 'POST']) # allows a user to view an event
@login_required
def event(event_id):

    # gets all necessary information about the current user, the event, and the songs in the event
    user_id = current_user.user_id
    if EventUsers.query.filter_by(user_id=user_id).first(): # checks if the user is in an event
        user_event = EventUsers.query.filter_by(user_id=user_id).first().event_id
        event_name = Events.query.filter_by(event_id=user_event).first().event_name
        event_code = Events.query.filter_by(event_id=user_event).first().event_code
        event_description = Events.query.filter_by(event_id=user_event).first().event_description
        event_location = Events.query.filter_by(event_id=user_event).first().event_location
        users = EventUsers.query.filter_by(event_id=user_event).all()
        admin = EventUsers.query.filter_by(is_admin=1, event_id=user_event).first()
        dj = EventUsers.query.filter_by(is_dj=1, event_id=user_event).first()
        print(dj)
        event_songs = get_event_songs(user_event)

        # gets the admin username
        if admin:
            admin_user = User.query.filter_by(user_id=admin.user_id).first()
            admin_username = admin_user.username

        if dj:
            dj_user = User.query.filter_by(user_id=dj.user_id).first()
            dj_username = dj_user.username
            print(dj_username)
        else:
            dj_username = None

        # gets the usernames of all users in the event
        users_names = []
        for user in users:
            if user.is_admin == 0:
                user_name = User.query.filter_by(user_id=user.user_id).first().username
                users_names.append(user_name)
    else: # handles if the user is not in an event
        user_event = None
        event_name = None
        event_code = None
        event_description = None
        event_location = None
        users = None
        admin_username = None
        dj_username = None
        event_songs = None
        users_names = None
        flash('You are not in an event')
        return redirect(url_for('index'))

    # injects all necessary information into the template
    return render_template('event.html', event_id=user_event, user_event=user_event, event_name=event_name, event_code=event_code, users=users, users_names=users_names, admin_username=admin_username, dj_username=dj_username, event_songs=event_songs, event_location=event_location, event_description=event_description)


@app.route('/delete_event/<int:event_id>', methods=['GET', 'POST']) # allows the admin to delete an event
@login_required
def delete_event(event_id):

    all_users = EventUsers.query.filter_by(event_id=event_id).all() # gets all users in the event
    event_status = Events.query.get_or_404(event_id).active_status  # gets the event status
    if event_status == 1:  # checks if the event is active
        Events.query.get_or_404(event_id).active_status = 0  # sets the event to inactive
        db.session.commit()
    user_ids = []  # creates a list to store the user ids
    for user in all_users:  # loops through all users in the event
        user_in_event = User.query.get(user.user_id)
        user_in_event.in_event = 0
        user_ids.append(user.user_id)
        db.session.delete(user)  # removes user from the event database
        db.session.commit()
        flash('Admin has left the event. All users have been removed from the event')

    event_songs = VotedSongs.query.filter_by(event_id=event_id).all()  # gets all voted songs in the event
    for song in event_songs:  # loops through all songs in the event
        db.session.delete(song)  # removes song from the event database
        db.session.commit()
        flash('All songs have been removed from the event')

    delete = Events.query.get_or_404(event_id)  # gets the event to be deleted
    db.session.delete(delete)  # deletes the event
    db.session.commit()
    flash('Event has been deleted')




    return redirect(url_for('my_events'))



### SONG SEARCHING AND SAVING ###

@app.route('/search', methods=['GET', 'POST']) # allows a user to search for a song
@login_required
def search():
    user_id = current_user.user_id # gets the current user id

    # handles if the user is the event dj
    if EventUsers.query.filter_by(user_id=user_id).first(): # checks if the user is in an event
        is_dj = EventUsers.query.filter_by(user_id=user_id).first().is_dj # checks if the user is a dj
        print(is_dj)
        if is_dj == True:
            dj_status = 1
        else:
            dj_status = 0
    else:
        dj_status = 0

    if request.method == 'POST': # checks if the user has submitted a search
        song_name = request.form['song'] # gets the song name from the form
        artist_name = request.form['artist'] # gets the artist name from the form
        song = search_songs(song_name, artist_name) # runs search song function using the song and artist names

        if song is not None: # checks if the song exists
            song_id = song['idTrack'] # gets the song id

            reviews = SongReviews.query.filter_by(reviewsong_id=song_id).all() # gets all reviews for the song
            all_reviews = [] # creates a list to store all reviews

            for item in reviews: # loops through all reviews
                username = item.username # gets the username of the reviewer
                review = item.review # gets the review
                id = item.review_id # gets the review id

                all_reviews.append({'username': username, 'review': review, 'id': id}) # adds the review to the list


        if song: # checks if the song exists
            return render_template('results.html', song=song, song_in_favourites=song_in_favourites, all_reviews=all_reviews, dj_status=dj_status)

        else: # if the song does not exist
            flash('Song not found')
            flash('Try double checking your spelling!')
            return render_template('search.html')
    return render_template('search.html')

def song_in_favourites(track_id):
    user_id = current_user.user_id # gets the user id
    # checks if the song is in the database linked to the user id
    return FavouriteSong.query.filter_by(user_id=user_id, track_id=track_id).first() is not None # checks if the song is in the users favourites

def search_songs(song_name, artist_name): # searches for albums and gets response from api
    api = '523532' # api key
    url = f'https://theaudiodb.com/api/v1/json/{api}/searchtrack.php?s={artist_name}&t={song_name}' # url for api
    response = requests.get(url) # gets response from api
    get_data = response.json() # converts response to json
    if 'track' in get_data and get_data['track'] is not None: # checks if the song exists
        return get_data['track'][0] # returns the song

    return None # returns none if the song does not exist


@app.route('/favourite_song', methods=['GET', 'POST']) # allows a user to favourite a song
@login_required
def favourite_song():
    form = FavouriteSongForm() # creates a form

    #gets all necessary song informaiton
    song_name = request.form.get('song_name')
    artist_name = request.form.get('artist_name')
    track_id = request.form.get('track_id')

    # makes sure the song has an artist and song name
    if song_name and artist_name:
        # gets the current user and adds the songs linked to their user id
        user_id = current_user.user_id
        new_song = FavouriteSong(song_name=song_name, artist_name=artist_name, track_id=track_id, user_id=user_id)

        # if the song is in the favourites , remove the song from user favourites
        if FavouriteSong.query.filter_by(track_id=track_id, user_id=user_id).first():
            flash('Song removed from favourites.')
            song = FavouriteSong.query.filter_by(track_id=track_id, user_id=user_id).first()
            db.session.delete(song)
            db.session.commit()
            return redirect(url_for('search'))
        else: # if the song is not in the favourites, add the song to the users favourites
            db.session.add(new_song)
            db.session.commit()
            flash('Your song has been added to your favourites.')
            return redirect(url_for('search'))
    else: # error handling
        flash('Something went wrong')
        return render_template('search.html', title='Favourite Song', form=form)


@app.route('/vote_song', methods=['GET', 'POST']) # allows a user to vote for a song
@login_required
def vote_song():

    # gets relevant information about the user and event the user is in
    form = VoteSongForm()
    user_id = current_user.user_id
    event_id = EventUsers.query.filter_by(user_id=user_id).first().event_id

    # gets relevant information about the song
    song_name = request.form.get('song_name')
    artist_name = request.form.get('artist_name')
    track_id = request.form.get('track_id')

    # checks if the user is actually in an event
    if current_user.in_event:
        # checks if the song has a name and artist
        if song_name and artist_name:
            # checks if the song has already been voted for, adds song if n ot
            if VotedSongs.query.filter_by(track_id=track_id, event_id=event_id, user_id=user_id).first() is None:
                new_song = VotedSongs(song_name=song_name, artist_name=artist_name, track_id=track_id, event_id=event_id, user_id=user_id)
                db.session.add(new_song)
                db.session.commit()
                flash(f'{song_name} has been upvoted!')
                return redirect(url_for('search'))
            else: # if the song has already been voted for
                flash('You have already voted for this song')
                return render_template('search.html', title='Vote Song', form=form)

        else: # error handling
            flash('Something went wrong')
            return render_template('search.html', title='Vote Song', form=form)
    else: # if the user somehow accesses the vote button when not in an event
        flash('You are not in an event')
        return render_template('search.html', title='Vote Song', form=form)


@app.route('/my_favourites', methods=['GET', 'POST']) # allows a user to view their favourites
@login_required
def my_favourites():
    # gets the current user and all favourited songs linked to the current user
    user_id = current_user.user_id
    songs = FavouriteSong.query.filter_by(user_id=user_id).all()
    return render_template('my_favourites.html', songs=songs)
def user_favourites(user_id):
    # gets the user whose profile is being viewed and all their favourites
    favourites = FavouriteSong.query.filter_by(user_id=user_id)

    ### DEBUGG START ###
    print(favourites)

    for song in favourites:
        print(song.song_name)
        print(song.artist_name)

    ### DEBUG END ###
    return favourites # returns the users favourites


@app.route('/add_review', methods=['GET', 'POST']) # allows a user to add a review to a song
@login_required
def add_review():
    form = SongReviewForm() # creates a form

    # gets all relevant information about the song and user
    review = request.form.get('review')
    song_id = request.form.get('song_id')
    user_id = current_user.user_id
    username = current_user.username

    if review and song_id: # checks if the review is provided and a song id is provided
        # adds new review to the review database connected to the song and user
        new_review = SongReviews(review=review, reviewsong_id=song_id, user_id=user_id, username=username)
        db.session.add(new_review)
        db.session.commit()
        flash('Your review has been added')
        return redirect(url_for('search'))
    else: # error handling
        flash('Something went wrong')
        return redirect(url_for('search'))

@app.route('/delete_review/<int:review_id>', methods=['GET', 'POST']) # allows a user to delete a review
@login_required
def delete_review(review_id): # gets the review id
    ### NOTE : Handling whether the user is the one who posted the review is done in the html ###

    # gets the review to delete
    delete = SongReviews.query.get_or_404(review_id)
    db.session.delete(delete) # deletes the review
    db.session.commit()
    flash('Review has been deleted')
    return redirect(url_for('search'))









