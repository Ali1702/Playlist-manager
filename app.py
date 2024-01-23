from flask import Flask, request, abort
from extensions import db
from model import Playlist, Song, PlaylistSong
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://sa:YourStrong!Passw0rd@localhost:1433/Playlists?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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
    return {
        'PlaylistID': new_playlist.PlaylistID,
        'Name': new_playlist.Name,
        'Description': new_playlist.Description,
        'CreationDate': new_playlist.CreationDate
    }, 201

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
    return playlists_dict

@app.route('/playlists/<int:playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    # Retrieve the playlist
    playlist = Playlist.query.get_or_404(playlist_id)

    # Retrieve songs in the playlist, ordered by Position
    playlist_songs = (PlaylistSong.query
                      .filter(PlaylistSong.PlaylistID == playlist_id)
                      .order_by(PlaylistSong.Position)
                      .all())

    # Fetch each song's details
    songs = []
    for playlist_song in playlist_songs:
        song = Song.query.get(playlist_song.SongID)
        songs.append({
            'SongID': song.SongID,
            'Title': song.Title,
            'Artist': song.Artist
        })

    # Return playlist details including ordered songs
    return {
        'PlaylistID': playlist.PlaylistID,
        'Name': playlist.Name,
        'Description': playlist.Description,
        'Songs': songs
    }


@app.route('/playlists/<int:playlist_id>/shuffle', methods=['POST'])
def shuffle_playlist(playlist_id):
    # Find the playlist with the given ID
    playlist = Playlist.query.get_or_404(playlist_id)

    # Get all songs from the playlist
    playlist_songs = PlaylistSong.query.filter_by(PlaylistID=playlist_id).all()
    if not playlist_songs:
        abort(404, description="No songs found in the playlist.")

    # Shuffle the songs using Python's random module
    random.shuffle(playlist_songs)

    # Update the Position field in the database for each PlaylistSong
    for index, playlist_song in enumerate(playlist_songs):
        playlist_song.Position = index

    # Commit all changes at once
    db.session.commit()

    # Retrieve the shuffled playlist as a list of Song objects
    shuffled_playlist = [Song.query.get(playlist_song.SongID) for playlist_song in playlist_songs]

    # Convert the shuffled playlist to a list of dictionaries for JSON serialization
    shuffled_playlist_data = [{'SongID': song.SongID, 'Title': song.Title, 'Artist': song.Artist, 'Album': song.Album, 'Length': song.Length, 'Genre': song.Genre} for song in shuffled_playlist]

    return {'result': 'Playlist shuffled', 'shuffled_playlist': shuffled_playlist_data}, 200

@app.route('/playlists/<int:playlist_id>/shuffle', methods=['GET'])
def get_shuffled_playlist(playlist_id):
    # Retrieve the shuffled playlist by calling the shuffle_playlist function
    shuffle_playlist_response = shuffle_playlist(playlist_id)

    # You can now return the shuffled playlist in the response
    return shuffle_playlist_response

@app.route('/playlists/<int:playlist_id>/add_song/<int:song_id>', methods=['POST'])
def add_song_to_playlist(playlist_id, song_id):
    # Find the playlist with the given ID or return 404
    playlist = Playlist.query.get_or_404(playlist_id)
    song = Song.query.get_or_404(song_id)
    db.session.add(song)
    db.session.commit()

    # Link the song with the playlist
    # Make a playlist song on the last position of the playlist
    playlist_songs = PlaylistSong.query.filter_by(PlaylistID=playlist_id).all()
        
    # Determine the position for the new song
    if playlist_songs:
        last_position = playlist_songs[-1].Position + 1
    else:
        last_position = 0  # First song in the playlist

    playlist_song = PlaylistSong(PlaylistID=playlist_id, SongID=song.SongID, Position=last_position+1)
    db.session.add(playlist_song)
    db.session.commit()

    # Return the updated playlist
    return get_playlist(playlist_id)

@app.route('/playlists/<int:playlist_id>/add_song/<int:song_id>', methods=['GET'])
def get_add_song_to_playlist(playlist_id, song_id):
    # Retrieve the shuffled playlist by calling the shuffle_playlist function
    add_song_to_playlist_response = add_song_to_playlist(playlist_id, song_id)

    # You can now return the shuffled playlist in the response
    return add_song_to_playlist_response


@app.route('/playlists/<int:playlist_id>/remove_song/<int:song_id>', methods=['DELETE'])
def remove_song_from_playlist(playlist_id, song_id):
    # Check if the playlist exists
    playlist = Playlist.query.get_or_404(playlist_id)
    # Check if the song exists in the playlist
    playlist_song = PlaylistSong.query.filter_by(PlaylistID=playlist_id, SongID=song_id).first_or_404()

    # Remove the song from the playlist
    db.session.delete(playlist_song)
    db.session.commit()
    
    # Fix the positions of the remaining songs
    playlist_songs = PlaylistSong.query.filter_by(PlaylistID=playlist_id).all()
    for index, playlist_song in enumerate(playlist_songs):
        playlist_song.Position = index
    db.session.commit()

    # Return the updated playlist
    return get_playlist(playlist_id)

@app.route('/playlists/<int:playlist_id>/remove_song/<int:song_id>', methods=['GET'])
def get_remove_song_from_playlist(playlist_id, song_id):
    # Retrieve the shuffled playlist by calling the shuffle_playlist function
    remove_song_from_playlist_response = remove_song_from_playlist(playlist_id, song_id)

    # You can now return the shuffled playlist in the response
    return remove_song_from_playlist_response   

@app.route('/songs', methods=['GET'])
def get_songs():
    songs = Song.query.all()
    return [{
        'SongID': song.SongID,
        'Title': song.Title,
        'Artist': song.Artist
    } for song in songs]

@app.route('/playlists/<int:playlist_id>/delete', methods=['DELETE'])
def delete_playlist(playlist_id):
    # Find the playlist with the given ID or return 404
    playlist = Playlist.query.get_or_404(playlist_id)

    # First, delete all associated PlaylistSong records
    PlaylistSong.query.filter_by(PlaylistID=playlist_id).delete()

    # Now, delete the playlist
    db.session.delete(playlist)
    db.session.commit()

    return {'result': 'Playlist deleted'}, 200

@app.route ('/playlists/<int:playlist_id>/delete', methods=['GET'])
def get_delete_playlist(playlist_id):
    # Retrieve the shuffled playlist by calling the shuffle_playlist function
    delete_playlist_response = delete_playlist(playlist_id)

    # You can now return the shuffled playlist in the response
    return delete_playlist_response

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404

if __name__ == '__main__':
     with app.app_context():
        db.create_all()  # Create the tables if they don't already exist

        def add_playlist_if_not_exists(name, description):
            if not Playlist.query.filter_by(Name=name).first():
                new_playlist = Playlist(Name=name, Description=description)
                db.session.add(new_playlist)
                db.session.commit()
                return new_playlist
            else:
                return Playlist.query.filter_by(Name=name).first()

        # Add playlists
        playlist1 = add_playlist_if_not_exists("Chill Vibes", "Relaxing tunes to chill out.")
        playlist2 = add_playlist_if_not_exists("Workout Mix", "High-energy hits for the gym.")
        playlist3 = add_playlist_if_not_exists("Study Playlist", "Concentration music for studying.")

        # Create some Songs
        song1 = Song(Title="Song One", Artist="Artist A")
        song2 = Song(Title="Song Two", Artist="Artist B")
        song3 = Song(Title="Song Three", Artist="Artist C")
        song4 = Song(Title="Song Four", Artist="Artist D")
        song5 = Song(Title="Song Five", Artist="Artist E")
        song6 = Song(Title="Song Six", Artist="Artist F")
        song7 = Song(Title="Song Seven", Artist="Artist G")

        db.session.add_all([song1, song2, song3, song4, song5, song6, song7])
        db.session.commit()
        
        playlist_song1 = PlaylistSong(PlaylistID=playlist1.PlaylistID, SongID=song1.SongID, Position=0)
        playlist_song2 = PlaylistSong(PlaylistID=playlist1.PlaylistID, SongID=song2.SongID, Position=1)
        playlist_song3 = PlaylistSong(PlaylistID=playlist1.PlaylistID, SongID=song3.SongID, Position=2)
        playlist_song4 = PlaylistSong(PlaylistID=playlist1.PlaylistID, SongID=song4.SongID, Position=3)
        playlist_song5 = PlaylistSong(PlaylistID=playlist2.PlaylistID, SongID=song5.SongID, Position=0)
        playlist_song6 = PlaylistSong(PlaylistID=playlist2.PlaylistID, SongID=song6.SongID, Position=1)
        playlist_song7 = PlaylistSong(PlaylistID=playlist2.PlaylistID, SongID=song7.SongID, Position=2)

        db.session.add_all([playlist_song1, playlist_song2, playlist_song3, playlist_song4, playlist_song5, playlist_song6, playlist_song7])
        db.session.commit()

        # Print all Playlists
        print("Playlists:")
        playlists = Playlist.query.all()
        for playlist in playlists:
            print(playlist)
            print(playlist.PlaylistID)

        # Print all Songs
        print("\nSongs:")
        songs = Song.query.all()
        for song in songs:
            print(song)
            
        # Start the Flask app
        app.run(debug=True)