import os
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from myapp.forms import PlaylistCreationForm, PlaylistUpdateForm
from myapp.models import Playlist, PlaylistTrack, Track, SavedPlaylist, Like, Comment
from myapp.extensions import db
from myapp.routes.utils import save_picture


playlist = Blueprint('playlist', __name__, url_prefix='/playlist')

@playlist.route('/create', methods=['GET', 'POST'])
@login_required
def create_playlist():
    form = PlaylistCreationForm()

    if form.validate_on_submit():
        if Playlist.query.filter_by(name=form.name.data).first():
            flash('Playlist with that name already exists', 'danger')
            return redirect(url_for('playlist.create_playlist'))

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


@playlist.route('/<int:playlist_id>/delete', methods=['POST'])
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

    try:
        db.session.delete(playlist)
        db.session.commit()
        flash(f"Playlist '{playlist.name}' deleted successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting playlist {playlist_id}: {e}")
        flash('Error deleting playlist.', 'danger')
    
    return redirect(url_for('main.account', view=origin_view))


@playlist.route('/<int:playlist_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_playlist(playlist_id):
    origin_view = request.args.get('origin_view')
    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.author != current_user:
        abort(403)

    form = PlaylistUpdateForm()
    if form.validate_on_submit():
        if Playlist.query.filter(
                Playlist.name == form.name.data,
                Playlist.id != playlist_id
            ).first():
            flash('Playlist with that name already exists', 'danger')
            return redirect(url_for('playlist.edit_playlist', playlist_id=playlist_id))

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


@playlist.route('/<int:playlist_id>/toggle_archive', methods=['POST'])
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


@playlist.route('/<int:playlist_id>/add_track', methods=['POST'])
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
            return jsonify({
                "message": "Track already in playlist",
                "success": True
            }), 200 

        playlist_track = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track.id,
        )
        
        db.session.add(playlist_track)
        db.session.commit()
        
        return jsonify({
            "message": "Track added successfully",
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


@playlist.route('/<int:playlist_id>/remove_track', methods=['POST'])
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


@playlist.route('/<int:playlist_id>/save', methods=['POST'])
@login_required
def save_playlist(playlist_id):
    origin_view = request.form.get('origin_view', 'my')
    viewed_username = request.form.get('username')

    if not Playlist.query.get(playlist_id):
        flash('Playlist not found', 'danger')
        return redirect(url_for('main.account', view=origin_view))

    if viewed_username == current_user.username:
        flash('You cannot save your own playlist', 'danger')
        return redirect(url_for('main.profile', username=viewed_username, view=origin_view))

    existing_saved_playlist = SavedPlaylist.query.filter_by(
        user_id=current_user.id,
        playlist_id=playlist_id
    ).first()

    if existing_saved_playlist:
        flash('Playlist already saved', 'danger')
        return redirect(url_for('main.profile', username=viewed_username, view=origin_view))

    saved_playlist = SavedPlaylist(
        user_id=current_user.id,
        playlist_id=playlist_id
    )
    try:
        db.session.add(saved_playlist)
        db.session.commit()
        flash('Playlist saved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error saving playlist: {e}")
        flash('Failed to save playlist', 'danger')
    
    return redirect(url_for('main.profile', username=viewed_username, view=origin_view))


@playlist.route('/<int:playlist_id>/unsave', methods=['POST'])
@login_required
def unsave_playlist(playlist_id):
    origin_view = 'saved'

    if not Playlist.query.get(playlist_id):
        flash('Playlist not found', 'danger')
        return redirect(url_for('main.account', view=origin_view))

    saved_playlist = SavedPlaylist.query.filter_by(
        user_id=current_user.id,
        playlist_id=playlist_id
    ).first()

    if not saved_playlist:
        flash('Playlist not saved', 'danger')
        return redirect(url_for('main.account', view=origin_view))

    try:
        db.session.delete(saved_playlist)
        db.session.commit()
        flash('Playlist unsaved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error unsaving playlist: {e}")
        flash('Failed to unsave playlist', 'danger')

    return redirect(url_for('main.account', view=origin_view))


@playlist.route('/<int:playlist_id>/toggle_like', methods=['POST'])
@login_required
def toggle_like(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, playlist_id=playlist.id).first()
    referring_url = request.referrer or url_for('main.home')

    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
    else:
        new_like = Like(user_id=current_user.id, playlist_id=playlist.id)
        db.session.add(new_like)
        db.session.commit()
    
    return redirect(referring_url)


@playlist.route('/add_comment', methods=['POST'])
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
    except Exception as e:
        db.session.rollback()
        flash('An unexpected error occurred. Please try again.', 'danger')

    return redirect(referring_url)


@playlist.route('/delete_comment', methods=['POST'])
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



