from datetime import datetime
from myapp.extensions import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(20), nullable=False, default='default_pfp.jpg')

    playlists = db.relationship("Playlist", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="user", lazy=True)
    likes = db.relationship("Like", backref="user", lazy=True)

    def __repr__(self):
        return f"<User: '{self.username}', '{self.email}', '{self.profile_picture}'>"


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    cover_photo = db.Column(db.String(20), nullable=False, default='default_cover.jpg')
    description = db.Column(db.Text)
    visibility = db.Column(db.String(10), default="private")
    archived = db.Column(db.Boolean, default=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    comments = db.relationship("Comment", backref="playlist", lazy=True)
    likes = db.relationship("Like", backref="playlist", lazy=True)
    tracks = db.relationship('PlaylistTrack', backref='playlist', lazy='dynamic', cascade="all, delete-orphan")

    @property
    def total_duration(self):
        return sum(pt.track.duration or 0 for pt in self.tracks.all())

    def __repr__(self):
        return f"<Playlist: name='{self.name}', author_id={self.user_id}, visibility='{self.visibility}', created='{self.creation_date}'>"


class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(128), unique=True, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    artist = db.Column(db.String(128), nullable=False)
    album = db.Column(db.String(128)) 
    duration = db.Column(db.Integer)

    def __repr__(self):
        return f"<Track: title='{self.title}', artist='{self.artist}', external_id='{self.external_id}'>"


class PlaylistTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    order = db.Column(db.Integer)

    track = db.relationship('Track', backref='playlist_links')

    __table_args__ = (
        db.UniqueConstraint('playlist_id', 'track_id', name='unique_playlist_track'),
    )

    def __repr__(self):
        return f"<PlaylistTrack: playlist_id={self.playlist_id}, track_id={self.track_id}, order={self.order}>"


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "playlist_id", name="unique_like"),
    )

    def __repr__(self):
        return f"<Like: user_id={self.user_id}, playlist_id={self.playlist_id}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    publication_date = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.id"), nullable=False)

    def __repr__(self):
        return f"<Comment: user_id={self.user_id}, playlist_id={self.playlist_id}, published={self.publication_date}>"

