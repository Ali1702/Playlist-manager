from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sa:YourStrong!Passw0rd@localhost/playlists'
db = SQLAlchemy(app)

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

    # Add a representation method for debugging purposes
    def __repr__(self):
        return f'<Song {self.Title}>'

class PlaylistSong(db.Model):
    __tablename__ = 'PlaylistSongs'
    PlaylistID = db.Column(db.Integer, db.ForeignKey('Playlists.PlaylistID'), primary_key=True)
    SongID = db.Column(db.Integer, db.ForeignKey('Songs.SongID'), primary_key=True)
    Position = db.Column(db.Integer, nullable=False)

    # Add a representation method for debugging purposes
    def __repr__(self):
        return f'<PlaylistSong {self.PlaylistID} {self.SongID}>'

# ... rest of the Flask app code ...
@app.route('/')
def index():
    return "Welcome to the Playlist Manager API!"

@app.route('/playlists', methods=['POST'])
def create_playlist():
    # Ensure that the request contains JSON
    if not request.json or not 'name' in request.json:
        abort(400, description="Name is required.")
    
    # Extract the playlist name and optional description from the request
    name = request.json.get('name')
    description = request.json.get('description', '')
    
    # Create a new Playlist instance
    new_playlist = Playlist(Name=name, Description=description)
    
    # Add to the database session and commit
    db.session.add(new_playlist)
    db.session.commit()
    
    # Return the new playlist as JSON with a 201 status code
    return jsonify({
        'PlaylistID': new_playlist.PlaylistID,
        'Name': new_playlist.Name,
        'Description': new_playlist.Description,
        'CreationDate': new_playlist.CreationDate
    }), 201

@app.route('/playlists', methods=['GET'])
def get_playlists():
    # Query the database for all playlists
    all_playlists = Playlist.query.all()
    # Convert the list of Playlist objects to a list of dictionaries
    playlists_dict = [
        {
            'PlaylistID': playlist.PlaylistID,
            'Name': playlist.Name,
            'Description': playlist.Description,
            'CreationDate': playlist.CreationDate
        } for playlist in all_playlists
    ]
    # Return the list of playlists as JSON
    return jsonify(playlists_dict)

@app.route('/playlists/<int:playlist_id>/shuffle', methods=['POST'])
def shuffle_playlist(playlist_id):
    # Find the playlist with the given ID
    playlist = Playlist.query.get_or_404(playlist_id)
    # Get all songs from the playlist
    playlist_songs = PlaylistSongs.query.filter_by(PlaylistID=playlist_id).all()

    # Shuffle the songs using Python's random module
    song_ids = [song.SongID for song in playlist_songs]
    random.shuffle(song_ids)

    # Now, update the PlaylistSongs entries with the new order
    # Note: This assumes you have a 'Position' column in PlaylistSongs to keep track of the order
    for index, song_id in enumerate(song_ids):
        song = PlaylistSongs.query.filter_by(PlaylistID=playlist_id, SongID=song_id).first()
        song.Position = index
        db.session.commit()

    return jsonify({'result': 'Playlist shuffled'}), 200


@app.route('/playlists/<int:playlist_id>/songs', methods=['POST'])
def add_song_to_playlist(playlist_id):
    # Find the playlist with the given ID or return 404
    playlist = Playlist.query.get_or_404(playlist_id)

    # Extract song details from the request body
    data = request.get_json()
    title = data.get('title')
    artist = data.get('artist')
    # Add more fields as necessary

    # Create the new Song instance
    new_song = Song(Title=title, Artist=artist)
    db.session.add(new_song)
    db.session.commit()

    # Link the song with the playlist
    playlist_song = PlaylistSongs(PlaylistID=playlist_id, SongID=new_song.SongID)
    db.session.add(playlist_song)
    db.session.commit()

    return jsonify(new_song), 201


@app.route('/playlists/<int:playlist_id>/songs/<int:song_id>', methods=['DELETE'])
def remove_song_from_playlist(playlist_id, song_id):
    # Check if the playlist exists
    playlist = Playlist.query.get_or_404(playlist_id)
    # Check if the song exists in the playlist
    playlist_song = PlaylistSongs.query.filter_by(PlaylistID=playlist_id, SongID=song_id).first_or_404()

    # Remove the song from the playlist
    db.session.delete(playlist_song)
    db.session.commit()

    return jsonify({'result': 'Song removed from playlist'}), 200


@app.route('/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    # Find the playlist with the given ID or return 404
    playlist = Playlist.query.get_or_404(playlist_id)

    # Delete the playlist
    db.session.delete(playlist)
    db.session.commit()

    return jsonify({'result': 'Playlist deleted'}), 200

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)