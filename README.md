# Wavelink - Platform for Sharing Music Playlists

___Wavelink___ is a full-stack web application where you can create, discover, and share your music playlists. It allows users to register, personalize their accounts, and build collections of their favorite music. The platform features full Spotify integration, enabling users to search through Spotify's vast database to find and add songs to their custom playlists. Beyond just creating personal collections, users can explore playlists created by others, save public playlists to their collection, leave comments to share their thoughts, and upvote playlists they enjoy to help quality content rise to the top. 

## Prerequisites

* [Python 3.10](https://www.python.org/downloads/) or higher
* [Docker Desktop](https://docs.docker.com/desktop/)

## Installation and Running

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/guramrekh/wavelink.git
    cd wavelink
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file in the root directory and set the following environment variables:
    * `FLASK_ENV`: Specify the environment. Comment it out for development process.
        ```
        FLASK_ENV=production
        ```

    * `SECRET_KEY`: Generate a strong secret key for Flask session management.
        ```bash
        python -c "import secrets; print(secrets.token_hex(32))"
        ```
        Add the generated key to your .env file:
        ```
        SECRET_KEY=your_secret_key
        ```

    * `Postges Credentials`: specify PostgreSQL database user, password, db name, and url.
        ```
        POSTGRES_USER=your_user
        POSTGRES_PASSWORD=your_password
        POSTGRES_DB=your_db_name
        DATABASE_URL=postgresql://your_user:your_password@db:5432/your_db_name
        ``` 

    * `Spotify API Credentials`: You can get these credentials from [Spotify](https://developer.spotify.com/documentation/web-api) for free.
        ```
        SPOTIFY_CLIENT_ID=your_client_id
        SPOTIFY_CLIENT_SECRET=your_client_secret
        ```

3. **Run the app in container**:
    ```
    docker compose up --build
    ```
    The app will be accessible at http://localhost:5000
    
    ---

    ### Additional Commands

    #### Stopping the App:
    Press `Ctrl+C` and then run:

    ```bash
    docker-compose down
    ```

    This shuts down and removes the containers (but keeps volumes and images).

    ---

    #### Subsequent Runs:
    Once built, you can start the app again (without rebuilding) using:

    ```bash
    docker-compose up
    ```

    ---

    #### Run in the background (detached mode):

    ```bash
    docker-compose up -d
    ```

    ---

    #### To view logs from the running containers:

    ```bash
    docker-compose logs -f
    ```

## Running with Python + Virtualenv (Dev Setup)

1.  **Step (1) and (2) from above**

2.  **Create a virtual environment and activate:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # on Linux/Mac
    .venv\Scripts\activate     # On Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Comment out *FLASK_ENV* in .env file (Super Necessary!!!):**
    ```bash
    # FLASK_ENV=production
    ```

5. **Initialize the database (for the very first time):**
    ```bash
    python init_db.py
    flask --app myapp db init # Only if migrations folder doesn't exist
    ```

6.  **If you alter the database schema (in models.py) migrate the database:**
    ```bash
    flask --app myapp db migrate -m "Your message"
    flask --app myapp db upgrade
    ```

7. **Run the app:**
    ```bash
    flask --app myapp run  # --debug (optional)
    ```
    The app will be accessible at http://localhost:5000


## Project Structure
```
wavelink/
├── myapp/
│   ├── __init__.py         # Application factory
│   ├── config.py           # Environment configuration settings
│   ├── extensions.py       # Initializes and stores Flask extensions
│   ├── forms.py            # WTForms classes for user input
│   ├── models.py           # SQLAlchemy models
│   ├── routes/             # Application routes/endpoints
│   ├── static/
│   │   ├── css/            # Custom stylesheets
│   │   ├── js/             # JavaScript files for interactivity
│   │   └── pictures/       # Uploaded images
│   └── templates/          # Jinja2 HTML templates for rendering pages
├── migrations/             # Database migration scripts
├── Dockerfile              # Instructions to build the Docker image
├── compose.yaml            # Docker Compose configuration 
├── entrypoint.sh           # Shell script run by the container on startup
├── requirements.txt        # Python dependencies 
├── .env                    # Local environment variables
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.