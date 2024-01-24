from flask import request, abort, Blueprint
from flasgger import swag_from
from extensions import db
from models import Playlist, Song, PlaylistSong
import random

playlist_bp = Blueprint('playlist_bp', __name__)

@playlist_bp.route('/')
def index():
    return "Welcome to the Playlist Manager API!"

@playlist_bp.route('/playlists', methods=['POST'])
@swag_from('swagger_docs/create_playlist.yml')
def create_playlist():
    if not request.json or not 'name' in request.json:
        abort(400, description="Name is required.")
    
    name = request.json.get('name')
    description = request.json.get('description', '')
    
    new_playlist = Playlist(Name=name, Description=description)
    
    db.session.add(new_playlist)
    db.session.commit()
    
    return {
        'PlaylistID': new_playlist.PlaylistID,
        'Name': new_playlist.Name,
        'Description': new_playlist.Description,
        'CreationDate': new_playlist.CreationDate
    }, 201

@playlist_bp.route('/playlists', methods=['GET'])
@swag_from('swagger_docs/get_playlists.yml')
def get_playlists():
    all_playlists = Playlist.query.all()
    playlists_dict = [
        {
            'PlaylistID': playlist.PlaylistID,
            'Name': playlist.Name,
            'Description': playlist.Description,
            'CreationDate': playlist.CreationDate
        } for playlist in all_playlists
    ]
    return playlists_dict

@playlist_bp.route('/playlists/<int:playlist_id>', methods=['GET'])
@swag_from('swagger_docs/get_playlist.yml')
def get_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    playlist_songs = (PlaylistSong.query
                      .filter(PlaylistSong.PlaylistID == playlist_id)
                      .order_by(PlaylistSong.Position)
                      .all())

    songs = []
    for playlist_song in playlist_songs:
        song = Song.query.get(playlist_song.SongID)
        songs.append({
            'SongID': song.SongID,
            'Title': song.Title,
            'Artist': song.Artist
        })

    return {
        'PlaylistID': playlist.PlaylistID,
        'Name': playlist.Name,
        'Description': playlist.Description,
        'Songs': songs
    }


@playlist_bp.route('/playlists/<int:playlist_id>/shuffle', methods=['POST'])
@swag_from('swagger_docs/shuffle_playlist.yml')
def shuffle_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    playlist_songs = PlaylistSong.query.filter_by(PlaylistID=playlist_id).all()
    if not playlist_songs:
        abort(404, description="No songs found in the playlist.")

    random.shuffle(playlist_songs)

    for index, playlist_song in enumerate(playlist_songs):
        playlist_song.Position = index

    db.session.commit()

    shuffled_playlist = [Song.query.get(playlist_song.SongID) for playlist_song in playlist_songs]

    shuffled_playlist_data = [{'SongID': song.SongID, 'Title': song.Title, 'Artist': song.Artist, 'Album': song.Album, 'Length': song.Length, 'Genre': song.Genre} for song in shuffled_playlist]

    return {'result': 'Playlist shuffled', 'shuffled_playlist': shuffled_playlist_data}, 200

@playlist_bp.route('/playlists/<int:playlist_id>/shuffle', methods=['GET'])
@swag_from('swagger_docs/get_shuffled_playlist.yml')
def get_shuffled_playlist(playlist_id):
    shuffle_playlist_response = shuffle_playlist(playlist_id)

    return shuffle_playlist_response

@playlist_bp.route('/playlists/<int:playlist_id>/add_song/<int:song_id>', methods=['POST'])
@swag_from('swagger_docs/add_song_to_playlist.yml')
def add_song_to_playlist(playlist_id, song_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    song = Song.query.get_or_404(song_id)
    db.session.add(song)
    db.session.commit()

    playlist_songs = PlaylistSong.query.filter_by(PlaylistID=playlist_id).all()
        
    if playlist_songs:
        last_position = playlist_songs[-1].Position + 1
    else:
        last_position = 0 

    playlist_song = PlaylistSong(PlaylistID=playlist_id, SongID=song.SongID, Position=last_position+1)
    db.session.add(playlist_song)
    db.session.commit()

    return get_playlist(playlist_id)

@playlist_bp.route('/playlists/<int:playlist_id>/add_song/<int:song_id>', methods=['GET'])
@swag_from('swagger_docs/get_add_song_to_playlist.yml')
def get_add_song_to_playlist(playlist_id, song_id):
    add_song_to_playlist_response = add_song_to_playlist(playlist_id, song_id)

    return add_song_to_playlist_response


@playlist_bp.route('/playlists/<int:playlist_id>/remove_song/<int:song_id>', methods=['DELETE'])
@swag_from('swagger_docs/remove_song_from_playlist.yml')
def remove_song_from_playlist(playlist_id, song_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    playlist_song = PlaylistSong.query.filter_by(PlaylistID=playlist_id, SongID=song_id).first_or_404()

    db.session.delete(playlist_song)
    db.session.commit()
    
    playlist_songs = PlaylistSong.query.filter_by(PlaylistID=playlist_id).all()
    for index, playlist_song in enumerate(playlist_songs):
        playlist_song.Position = index
    db.session.commit()

    return get_playlist(playlist_id)

@playlist_bp.route('/playlists/<int:playlist_id>/remove_song/<int:song_id>', methods=['GET'])
@swag_from('swagger_docs/get_remove_song_from_playlist.yml')
def get_remove_song_from_playlist(playlist_id, song_id):
    remove_song_from_playlist_response = remove_song_from_playlist(playlist_id, song_id)

    return remove_song_from_playlist_response   

@playlist_bp.route('/songs', methods=['GET'])
@swag_from('swagger_docs/get_songs.yml')
def get_songs():
    songs = Song.query.all()
    return [{
        'SongID': song.SongID,
        'Title': song.Title,
        'Artist': song.Artist
    } for song in songs]

@playlist_bp.route('/playlists/<int:playlist_id>/delete', methods=['DELETE'])
@swag_from('swagger_docs/delete_playlist.yml')
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    PlaylistSong.query.filter_by(PlaylistID=playlist_id).delete()

    db.session.delete(playlist)
    db.session.commit()

    return {'result': 'Playlist deleted'}, 200

@playlist_bp.route ('/playlists/<int:playlist_id>/delete', methods=['GET'])
@swag_from('swagger_docs/get_delete_playlist.yml')
def get_delete_playlist(playlist_id):
    delete_playlist_response = delete_playlist(playlist_id)

    return delete_playlist_response

@playlist_bp.errorhandler(404)
@swag_from('swagger_docs/error_404.yml')
def not_found(error):
    return {'error': 'Not found'}, 404

def add_playlist_if_not_exists(name, description):
    if not Playlist.query.filter_by(Name=name).first():
        new_playlist = Playlist(Name=name, Description=description)
        db.session.add(new_playlist)
        db.session.commit()
        return new_playlist
    else:
        return Playlist.query.filter_by(Name=name).first()

def add_song_if_not_exists(title, artist, album, length, genre):
    if not Song.query.filter_by(Title=title).first():
        new_song = Song(Title=title, Artist=artist, Album=album, Length=length, Genre=genre)
        db.session.add(new_song)
        db.session.commit()
        return new_song
    else:
        return Song.query.filter_by(Title=title).first()

def add_playlist_song_if_not_exists(playlist_id, song_id, position):
    if not PlaylistSong.query.filter_by(PlaylistID=playlist_id, SongID=song_id).first():
        new_playlist_song = PlaylistSong(PlaylistID=playlist_id, SongID=song_id, Position=position)
        db.session.add(new_playlist_song)
        db.session.commit()
        return new_playlist_song
    else:
        return PlaylistSong.query.filter_by(PlaylistID=playlist_id, SongID=song_id).first()