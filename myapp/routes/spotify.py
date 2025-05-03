from flask import Blueprint, flash, redirect, request, session, url_for
import requests

from myapp.routes.utils import get_spotify_token


spotify = Blueprint('spotify', __name__)

@spotify.route('/search_song', methods=['GET'])
def search_song():
    url = 'https://api.spotify.com/v1/search'

    song_title = request.args.get('title')
    song_artist = request.args.get('artist')

    if not song_title or not song_artist:
        flash('Please specify both title and artist', 'warning')
        return redirect(url_for('main.account'))

    access_token = get_spotify_token()
    if not access_token:
        flash('Could not authenticate with Spotify. Please try again.', 'danger')
        return redirect(url_for('main.account'))

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

        if not tracks_data:
            flash('No tracks found matching your search criteria', 'info')
            return redirect(url_for('main.account'))

        return tracks_data

    except requests.exceptions.RequestException as e:
        print(f"Error searching Spotify: {e}")
        if response.status_code == 401:
            session.pop('spotify_access_token', None)
            session.pop('spotify_token_expires', None)
            flash('Spotify authorization failed (token might have expired). Please try again.', 'danger')
            return redirect(url_for('main.account'))
        flash(f'Error searching Spotify: {str(e)}', 'danger')
        return redirect(url_for('main.account'))
    except Exception as e:
        print(f"An unexpected error occurred during Spotify search: {e}")
        flash('An internal error occurred while searching', 'danger')
        return redirect(url_for('main.account'))


