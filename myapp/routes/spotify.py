from flask import Blueprint, jsonify, request, session
import requests

from myapp.routes.utils import get_spotify_token


spotify = Blueprint('spotify', __name__)

@spotify.route('/search_song', methods=['GET'])
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


