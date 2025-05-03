from flask import Blueprint, abort, jsonify, render_template, flash, redirect, request, url_for, current_app, session
from flask_login import login_user, current_user, logout_user, login_required

from myapp.models import Playlist, User, Track, PlaylistTrack
from myapp.forms import PlaylistCreationForm, PlaylistUpdateForm, RegistrationForm, LoginForm, AccountUpdateForm
from myapp.extensions import db, bcrypt

import os 
import secrets 
import base64
import requests 
import time
from PIL import Image


bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('main.login'))
    else:
        return render_template('register.html', form=form)
    

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


def formatted_total_duration(playlists):
    total_duration_list = []

    for playlist in playlists:
        total_seconds = playlist.total_duration
        if total_seconds <= 0:
            total_duration_list.append("N/A")
            continue

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = (total_seconds % 3600) % 60
        if hours < 1:
            total_duration_list.append(f"{minutes} min {seconds} sec")
        else: 
            total_duration_list.append(f"{hours} hr {minutes} min")

    return total_duration_list

@bp.route('/home')
@login_required
def home():
    view = request.args.get("view", "my")
    playlists = []
    if view == "my":
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=False).all()
    elif view == "archived":
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=True).all()
        
    user_pfp = url_for('static', filename='pictures/users/' + current_user.profile_picture)
    total_duration_list = formatted_total_duration(playlists)
    return render_template('home.html', playlists=playlists, user_pfp=user_pfp, 
                           total_durations=total_duration_list, current_view=view)


def save_picture(form_picture, subfolder):
    if not form_picture:
        return None
    
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    if subfolder == 'users':
        picture_path = os.path.join(current_app.root_path, 'static/pictures/users', picture_fn)
    elif subfolder == 'playlists':
        picture_path = os.path.join(current_app.root_path, 'static/pictures/playlists', picture_fn)

    output_size = (400, 400)
    image = Image.open(form_picture)
    image.thumbnail(output_size)
    image.save(picture_path)

    return picture_fn

@bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        pic_fn_to_delete = current_user.profile_picture
        new_pfp_fn = 'default_pfp.jpg' if form.restore_default_picture.data else save_picture(form.profile_picture.data, 'users')

        if new_pfp_fn:
            current_user.profile_picture = new_pfp_fn
            if pic_fn_to_delete != 'default_pfp.jpg':
                file_path = os.path.join(current_app.root_path, 'static/pictures/users', pic_fn_to_delete)
                if os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    print(f"Cover file not found, skipping delete: {file_path}")
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account'))
    
    form.username.data = current_user.username
    form.bio.data = current_user.bio
    view = request.args.get("view", "my")
    playlists = []
    if view == "my":
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=False).all()
    elif view == "archived":
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=True).all()

    user_pfp = url_for('static', filename='pictures/users/' + current_user.profile_picture)
    total_duration_list = formatted_total_duration(playlists)
    return render_template('account.html', playlists=playlists, form=form, user_pfp=user_pfp, 
                           total_durations=total_duration_list, current_view=view)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/playlist/<int:playlist_id>/toggle_archive', methods=['POST'])
@login_required
def toggle_playlist_archive(playlist_id):
    origin_view = request.form.get('origin_view', 'my')
    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.author != current_user:
        abort(403)

    try:
        playlist.archived = not playlist.archived
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error toggling archive status for playlist {playlist_id}: {e}")
    
    return redirect(url_for('main.account', view=origin_view))


@bp.route('/playlist/<int:playlist_id>/delete', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    origin_view = request.form.get('origin_view', 'my')
    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.author != current_user:
        abort(403)

    cover_fn_to_delete = playlist.cover_photo
    if cover_fn_to_delete and cover_fn_to_delete != 'default_cover.jpg':
        file_path = os.path.join(current_app.root_path, 'static/pictures/playlists', cover_fn_to_delete)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print(f"Cover file not found, skipping delete: {file_path}")

    try:
        db.session.delete(playlist)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting playlist {playlist_id}: {e}")
    
    return redirect(url_for('main.account', view=origin_view))


@bp.route('/playlist/<int:playlist_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_playlist(playlist_id):
    origin_view = request.args.get('origin_view')
    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.author != current_user:
        abort(403)

    form = PlaylistUpdateForm()
    if form.validate_on_submit():
        old_cover_fn = playlist.cover_photo
        new_cover_fn = 'default_cover.jpg' if form.restore_default_cover.data else save_picture(form.cover_photo.data, 'playlists')

        try:
            playlist.name = form.name.data
            playlist.description = form.description.data
            playlist.visibility = form.visibility.data
            if new_cover_fn:
                playlist.cover_photo = new_cover_fn
                if old_cover_fn != 'default_cover.jpg':
                    old_cover_path = os.path.join(current_app.root_path, 'static/pictures/playlists', old_cover_fn)
                    if os.path.exists(old_cover_path):
                        os.remove(old_cover_path)
            db.session.commit()
            flash(f"Playlist '{playlist.name}' edited successfully!", 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error editing playlist: {e}")
            flash('Error editing playlist.', 'danger')
            return render_template('edit_playlist.html', form=form)

        return redirect(url_for('main.account', view=origin_view))

    form.name.data = playlist.name
    form.description.data = playlist.description
    form.visibility.data = playlist.visibility
    cover = playlist.cover_photo
    return render_template('edit_playlist.html', form=form, view=origin_view, cover=cover)


@bp.route('/playlist/<int:playlist_id>/add_track', methods=['POST'])
@login_required
def add_track_to_playlist(playlist_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        track_data = data.get('track')
        
        if not track_data:
            return jsonify({"error": "Track data is required"}), 400
            
        playlist = Playlist.query.get(playlist_id)
        if not playlist or playlist.author != current_user:
            return jsonify({"error": "Playlist not found or access denied"}), 403
            
        track = Track.query.filter_by(external_id=track_data.get('spotify_id')).first()
        
        if not track:
            track = Track(
                external_id=track_data.get('spotify_id'),
                title=track_data.get('name'),
                artist=track_data.get('artists'),
                album=track_data.get('album'),
                duration=track_data.get('duration_sec')
            )
            db.session.add(track)
            db.session.flush()
            
        existing_playlist_track = PlaylistTrack.query.filter_by(
            playlist_id=playlist_id,
            track_id=track.id
        ).first()
        
        if existing_playlist_track:
            return jsonify({"message": "Track already in playlist", "success": True}), 200
            
        
        playlist_track = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track.id,
        )
        
        db.session.add(playlist_track)
        db.session.commit()
        
        return jsonify({
            "message": "Track added to playlist successfully",
            "success": True,
            "track": {
                "id": track.id,
                "title": track.title,
                "artist": track.artist,
                "album": track.album,
                "duration": track.duration
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding track to playlist: {e}")
        return jsonify({"error": "An error occurred while adding the track to the playlist"}), 500



@bp.route('/playlist/<int:playlist_id>/remove_track', methods=['POST'])
@login_required
def remove_track_from_playlist(playlist_id):
    try:
        playlist_track_id = request.form.get('playlist_track_id')
        origin_view = request.args.get('origin_view', 'my')
        if not playlist_track_id:
            flash('Track ID is required', 'danger')
            return redirect(url_for('main.account', view=origin_view))
            
        playlist = Playlist.query.get_or_404(playlist_id)
        if playlist.author != current_user:
            abort(403)
            
        playlist_track = PlaylistTrack.query.filter_by(
            id=playlist_track_id,
            playlist_id=playlist_id
        ).first_or_404()
        
        track = playlist_track.track
        
        db.session.delete(playlist_track)
        
        remaining_references = PlaylistTrack.query.filter_by(track_id=track.id).count()
        
        if remaining_references == 0:
            db.session.delete(track)
            
        db.session.commit()
        flash('Track removed successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error removing track from playlist: {e}")
        flash('Failed to remove track', 'danger')
    
    return redirect(url_for('main.account', view=origin_view))



@bp.route('/playlist/create', methods=['GET', 'POST'])
@login_required
def create_playlist():
    form = PlaylistCreationForm()

    if form.validate_on_submit():
        cover_filename = None
        if form.cover_photo.data:
            cover_filename = save_picture(form.cover_photo.data, 'playlists')
        playlist = Playlist(name=form.name.data, description=form.description.data,
                            visibility=form.visibility.data, cover_photo=cover_filename,
                            author=current_user)
        try:
            db.session.add(playlist)
            db.session.commit()
            flash(f"Playlist '{playlist.name}' created successfully!", 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error creating playlist: {e}")
            flash('Error creating playlist.', 'danger')
            return render_template('create_playlist.html', form=form)

        return redirect(url_for('main.account'))

    return render_template('create_playlist.html', form=form)


@bp.route('/search_song', methods=['GET'])
def search_song():
    url = 'https://api.spotify.com/v1/search'

    song_title = request.args.get('title')
    song_artist = request.args.get('artist')

    if not song_title or not song_artist:
        return jsonify({"error": "Specify both title and artist"}), 400

    access_token = get_spotify_token()
    if not access_token:
        return jsonify({"error": "Could not authenticate with Spotify"}), 500


    query = f'track:"{song_title}" artist:"{song_artist}"'
    headers = {'Authorization': 'Bearer ' + access_token}
    params = {
        'q': query,
        'type': 'track',
        'limit': 15
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()

        tracks_data = []
        if search_results.get('tracks') and search_results['tracks'].get('items'):
            for item in search_results['tracks']['items']:
                track_info = {
                    'spotify_id': item.get('id'),
                    'name': item.get('name'),
                    'artists': ', '.join([artist.get('name') for artist in item.get('artists', [])]),
                    'album': item.get('album', {}).get('name'),
                    'image_url': item.get('album', {}).get('images', [{}])[0].get('url') if item.get('album', {}).get('images') else None,
                    'duration_sec': item.get('duration_ms') // 1000
                }
                tracks_data.append(track_info)

        return jsonify(tracks_data)

    except requests.exceptions.RequestException as e:
        print(f"Error searching Spotify: {e}")
        if response.status_code == 401:
            session.pop('spotify_access_token', None)
            session.pop('spotify_token_expires', None)
            return jsonify({"error": "Spotify authorization failed (token might have expired). Please try again."}), 401
        return jsonify({"error": f"Error searching Spotify: {e}"}), 500
    except Exception as e:
         print(f"An unexpected error occurred during Spotify search: {e}")
         return jsonify({"error": "An internal error occurred"}), 500



def get_spotify_token():
    if 'spotify_access_token' in session and 'spotify_token_expires' in session:
        if time.time() < session['spotify_token_expires']:
            return session['spotify_access_token']

    client_id = current_app.config.get('SPOTIFY_CLIENT_ID')
    client_secret = current_app.config.get('SPOTIFY_CLIENT_SECRET')

    print(client_id)
    print(client_secret)

    if not client_id or not client_secret:
        print("Error: Spotify Client ID or Secret not configured.") # for debugging
        return None


    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic ' + auth_base64,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_info = response.json()

        session['spotify_access_token'] = token_info['access_token']
        session['spotify_token_expires'] = time.time() + token_info['expires_in'] - 60
        print("Obtained new Spotify token.") # For debugging
        return token_info['access_token']

    except requests.exceptions.RequestException as e:
        print(f"Error getting Spotify token: {e}")
        session.pop('spotify_access_token', None)
        session.pop('spotify_token_expires', None)
        return None


