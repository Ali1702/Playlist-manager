from flask import Flask
from flasgger import Swagger
from extensions import db
from routes import *

app = Flask(__name__)
Swagger(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:sasa@localhost:1433/playlists'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SWAGGER'] = {
    "swagger": "2.0",
    "info": {
        "title": "Playlist Manager API",
        "description": "API for managing music playlists",
        "version": "1.0.0"
    },
    "basePath": "/", 
    "specs_route": "/apidocs/"  
}

db.init_app(app)

app.register_blueprint(playlist_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        playlist1 = add_playlist_if_not_exists("Chill Vibes", "Relaxing tunes to chill out.")
        playlist2 = add_playlist_if_not_exists("Workout Mix", "High-energy hits for the gym.")
        playlist3 = add_playlist_if_not_exists("Study Playlist", "Concentration music for studying.")

        song1 = add_song_if_not_exists("Song 1", "Artist 1", "Album 1", 180, "Pop")
        song2 = add_song_if_not_exists("Song 2", "Artist 2", "Album 2", 210, "Rock")
        song3 = add_song_if_not_exists("Song 3", "Artist 3", "Album 3", 320, "Jazz")
        song4 = add_song_if_not_exists("Song 4", "Artist 4", "Album 4", 120, "Pop")
        song5 = add_song_if_not_exists("Song 5", "Artist 5", "Album 5", 280, "Rock")
        song6 = add_song_if_not_exists("Song 6", "Artist 6", "Album 6", 360, "Metal")
        song7 = add_song_if_not_exists("Song 7", "Artist 7", "Album 7", 180, "Pop")
        
        playlist_song1 = add_playlist_song_if_not_exists(playlist1.PlaylistID, song1.SongID, 0)
        playlist_song2 = add_playlist_song_if_not_exists(playlist1.PlaylistID, song2.SongID, 1)
        playlist_song3 = add_playlist_song_if_not_exists(playlist1.PlaylistID, song3.SongID, 2)
        playlist_song4 = add_playlist_song_if_not_exists(playlist1.PlaylistID, song4.SongID, 3)
        playlist_song5 = add_playlist_song_if_not_exists(playlist2.PlaylistID, song5.SongID, 0)
        playlist_song6 = add_playlist_song_if_not_exists(playlist2.PlaylistID, song6.SongID, 1)
        playlist_song7 = add_playlist_song_if_not_exists(playlist2.PlaylistID, song7.SongID, 2)
                
    app.run(debug=True)