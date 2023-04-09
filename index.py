import time
import os
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from google_auth_oauthlib.flow import InstalledAppFlow


client_id = 'de752de39f9b4dc1baebe7568d06d403'
client_secret = 'c487c2ddb8e5431598707f5b1b00b1e2'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))


api_service_name = 'youtube'
api_version = 'v3'
client_secrets_file = 'creds.json'
scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']

def get_authenticated_service():
    credentials = None
    if os.path.exists('token.json'):
        credentials = google.oauth2.credentials.Credentials.from_authorized_user_file('token.json', scopes)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            credentials = flow.run_local_server(port=60445)
            if not os.path.exists('token.json'):
                with open('token.json', 'w') as token_file:
                    token_file.write(credentials.to_json())
    return build(api_service_name, api_version, credentials=credentials)

youtube = get_authenticated_service()



playlist_uri = input("Enter Spotify Playlist URL: ")
results = sp.playlist_tracks(playlist_uri)
tracks = results['items']
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])



playlist_title = sp.playlist(playlist_uri)['name']
playlist_description = 'Transfer from Spotify to YouTube'
playlist_body = {
    'snippet': {
        'title': playlist_title,
        'description': playlist_description,
        'defaultLanguage': 'en'
    },
    'status': {
        'privacyStatus': 'private'
    }
}
playlist_response = youtube.playlists().insert(part='snippet,status', body=playlist_body).execute()
playlist_id = playlist_response['id']


for track in tracks:
    track_name = track['track']['name']
    artist_name = track['track']['artists'][0]['name']
    search_query = f'{track_name} {artist_name} audio'
    search_response = youtube.search().list(q=search_query, part='id', type='video', maxResults=4).execute()

    if len(search_response['items']) > 0:
        video_id = search_response['items'][0]['id']['videoId']
        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'position': 0,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()
        time.sleep(5)
    else:
        print(f'Could not find video for "{search_query}"')