from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from myapp.forms import AccountUpdateForm
from myapp.models import Playlist, User, SavedPlaylist, Comment
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
    if view == "archived":
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=True).all()
    elif view == "saved":
        saved = SavedPlaylist.query.filter_by(user_id=current_user.id).all()
        playlists = [entry.playlist for entry in saved]
    else:
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=False).all()

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
    if view == "archived":
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=True).all()
    elif view == "saved":
        saved = SavedPlaylist.query.filter_by(user_id=current_user.id).all()
        playlists = [entry.playlist for entry in saved]
    else:
        playlists = Playlist.query.filter_by(user_id=current_user.id, archived=False).all()

    user_pfp = url_for('static', filename='pictures/users/' + current_user.profile_picture)
    total_duration_list = formatted_total_duration(playlists)
    return render_template('account.html', playlists=playlists, form=form, user_pfp=user_pfp, 
                           total_durations=total_duration_list, current_view=view)


@main.route('/profile/<username>')
def profile(username):
    target_user = User.query.filter_by(username=username).first_or_404()
    view = request.args.get("view", "my")
    playlists = []
    if view == "saved":
        saved = SavedPlaylist.query.filter_by(user_id=target_user.id).all()
        playlists = [entry.playlist for entry in saved]
    else:
        playlists = Playlist.query.filter_by(user_id=target_user.id, archived=False, visibility="public").all()

    user_pfp = url_for('static', filename='pictures/users/' + target_user.profile_picture)
    total_duration_list = formatted_total_duration(playlists)
    return render_template('user_profile.html', user=target_user, playlists=playlists, user_pfp=user_pfp, 
                           total_durations=total_duration_list, current_view=view)


@main.route('/search_user')
def search_user():
    username = request.args.get("q", "").strip()
    if not username:
        flash("Please enter a username to search.", "warning")
        return redirect(request.referrer or url_for("main.home"))

    user = User.query.filter_by(username=username).first()
    if user:
        return redirect(url_for('main.profile', username=username))
    else:
        flash('User not found', 'danger')
        return redirect(request.referrer or url_for("main.home"))



@main.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    playlist_id_str = request.form.get('playlist_id')
    comment_content = request.form.get('comment_content')
    referring_url = request.referrer

    if not playlist_id_str:
        flash('Playlist ID is missing.', 'danger')
        return redirect(referring_url)

    try:
        playlist_id = int(playlist_id_str)
    except ValueError:
        flash('Invalid Playlist ID format.', 'danger')
        return redirect(referring_url)

    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        flash('Playlist not found.', 'danger')
        return redirect(referring_url)

    if not comment_content or not comment_content.strip():
        flash('Comment content cannot be empty.', 'danger')
        return redirect(referring_url)

    try:
        new_comment = Comment(
            content=comment_content.strip(),
            user_id=current_user.id,
            playlist_id=playlist_id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred while adding your comment. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('An unexpected error occurred. Please try again.', 'danger')

    return redirect(referring_url)


@main.route('/delete_comment', methods=['POST'])
@login_required
def delete_comment():
    playlist_id_str = request.form.get('playlist_id')
    comment_id_str = request.form.get('comment_id')
    referring_url = request.referrer or url_for('main.home')

    if not playlist_id_str or not comment_id_str:
        flash('Missing required parameters (playlist_id or comment_id).', 'danger')
        return redirect(referring_url)
    
    try:
        comment_id = int(comment_id_str)
    except ValueError:
        flash('Invalid ID format.', 'danger')
        return redirect(referring_url)

    comment_to_delete = Comment.query.get(comment_id)
    if not comment_to_delete:
        flash('Comment not found.', 'danger')
        return redirect(referring_url)

    playlist = Playlist.query.get(comment_to_delete.playlist_id)
    if not playlist:
        flash('Associated playlist not found. Cannot verify permissions.', 'danger')
        return redirect(referring_url)


    can_delete = False
    if current_user.id == playlist.user_id:
        can_delete = True
    elif current_user.id == comment_to_delete.user_id:
        can_delete = True

    if not can_delete:
        flash('You are not authorized to delete this comment.', 'danger')
        return redirect(referring_url)

    try:
        db.session.delete(comment_to_delete)
        db.session.commit()
        flash('Comment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the comment. Please try again.', 'danger')

    return redirect(referring_url)



