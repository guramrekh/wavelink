from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from myapp.forms import AccountUpdateForm
from myapp.models import Playlist
from myapp.extensions import db
from myapp.routes.utils import formatted_total_duration, save_picture

import os


main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/home')
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


@main.route('/account', methods=['GET', 'POST'])
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

