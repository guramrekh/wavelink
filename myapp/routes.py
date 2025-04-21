from flask import Blueprint, abort, render_template, flash, redirect, request, url_for, current_app
from flask_login import login_user, current_user, logout_user, login_required 

from myapp.models import Playlist, User
from myapp.forms import PlaylistCreationForm, RegistrationForm, LoginForm, AccountUpdateForm
from myapp.extensions import db, bcrypt

import secrets 
import os 
from PIL import Image


bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
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
            login_user(user, remember=False)
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
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    if subfolder == 'users':
        picture_path = os.path.join(current_app.root_path, 'static/pictures/users', picture_fn)
    elif subfolder == 'playlists':
        picture_path = os.path.join(current_app.root_path, 'static/pictures/playlists', picture_fn)


    output_size = (120, 120)
    image = Image.open(form_picture)
    image.thumbnail(output_size)
    image.save(picture_path)

    return picture_fn

@bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        if form.profile_picture.data:
            current_user.profile_picture = save_picture(form.profile_picture.data, 'users')
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account'))
    elif request.method == 'GET':
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
    origin_view = request.form.get('origin_view', 'active')
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
    origin_view = request.form.get('origin_view', 'active')
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
