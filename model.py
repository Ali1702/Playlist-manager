from extensions import db

class Playlist(db.Model):
    __tablename__ = 'Playlists'
    PlaylistID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), nullable=False)
    Description = db.Column(db.Text)
    CreationDate = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Add a representation method for debugging purposes
    def __repr__(self):
        return f'<Playlist {self.Name}>'

class Song(db.Model):
    __tablename__ = 'Songs'
    SongID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(100), nullable=False)
    Artist = db.Column(db.String(50))
    Album = db.Column(db.String(50))
    Length = db.Column(db.Integer)
    Genre = db.Column(db.String(100))

    def __repr__(self):
        return f'<Song {self.Title}>'

class PlaylistSong(db.Model):
    __tablename__ = 'PlaylistSongs'
    PlaylistID = db.Column(db.Integer, db.ForeignKey('Playlists.PlaylistID'), primary_key=True)
    SongID = db.Column(db.Integer, db.ForeignKey('Songs.SongID'), primary_key=True)
    Position = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<PlaylistSong {self.PlaylistID} {self.SongID}>'