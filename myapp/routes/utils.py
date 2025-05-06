import base64
import os
import secrets
import time
import requests
from PIL import Image

from flask import current_app, session


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



def get_spotify_token():
    if 'spotify_access_token' in session and 'spotify_token_expires' in session:
        if time.time() < session['spotify_token_expires']:
            return session['spotify_access_token']

    client_id = current_app.config.get('SPOTIFY_CLIENT_ID')
    client_secret = current_app.config.get('SPOTIFY_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("Error: Spotify Client ID or Secret not configured.")
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
        print("Obtained new Spotify token.")
        return token_info['access_token']

    except requests.exceptions.RequestException as e:
        print(f"Error getting Spotify token: {e}")
        session.pop('spotify_access_token', None)
        session.pop('spotify_token_expires', None)
        return None

