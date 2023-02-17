from dotenv import load_dotenv, find_dotenv
from datetime import date
import requests
import urllib.request
import base64
import json
import os
import sys

load_dotenv(find_dotenv())
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN").strip()
CLIENT_ID = os.environ.get("CLIENT_ID").strip()
CLIENT_SECRET = os.environ.get("CLIENT_SECRET").strip()
NEW_MUSIC_FRIDAY_ID = os.environ.get("NEW_MUSIC_FRIDAY_ID").strip()
USER_ID = os.environ.get("USER_ID")

today = date.today()
d1 = today.strftime("%d/%m/%Y")
d2 = today.strftime("%Y%m%d")
year = today.strftime("%Y")

OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"
def refresh_access_token():
    payload = {
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
    }
    encoded_client = base64.b64encode((CLIENT_ID + ":" + CLIENT_SECRET).encode('ascii'))
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic %s" % encoded_client.decode('ascii')
    }
    response = requests.post(OAUTH_TOKEN_URL, data=payload, headers=headers)
    return response.json()


def get_playlist(access_token,playlistid):
    url = "https://api.spotify.com/v1/playlists/%s" % playlistid
    headers = {
       "Content-Type": "application/json",
       "Authorization": "Bearer %s" % access_token
    }
    response = requests.get(url, headers=headers)
    return response.json()

def create_playlist(access_token):
    url = "https://api.spotify.com/v1/users/%s/playlists" % USER_ID
    payload = {
        "name": "New Music Friday Italia del %s" % d1,
        "description": "Ogni Venerdi, le migliori nuove uscite, copia salvata il %s" % d1
    }
    headers = {
       "Content-Type": "application/json",
       "Authorization": "Bearer %s" % access_token
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

def add_to_nmfi(access_token, nmfiplaylisttoday, tracklist):
    url = "https://api.spotify.com/v1/playlists/%s/tracks" % nmfiplaylisttoday
    payload = {
        "uris" : tracklist
    }
    headers = {
       "Content-Type": "application/json",
       "Authorization": "Bearer %s" % access_token
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

def get_spoticode(nmfiplaylisttoday):
    base_url = 'https://scannables.scdn.co/uri/plain/png/bdd74/black/640/spotify:playlist:'
    spoti_url = ''.join([base_url, nmfiplaylisttoday])
    print("Spotify Code:",spoti_url)
    return spoti_url

def get_playlistcover(access_token, nmfiplaylisttoday):
    url = "https://api.spotify.com/v1/playlists/%s/images" % nmfiplaylisttoday
    headers = {
       "Content-Type": "application/json",
       "Authorization": "Bearer %s" % access_token
    }
    response = requests.get(url, headers=headers)
    print(response.json())
    return response.json()[0]['url']

def get_officialplaylistcover(access_token, playlistid):
    url = "https://api.spotify.com/v1/playlists/%s/images" % playlistid
    headers = {
       "Content-Type": "application/json",
       "Authorization": "Bearer %s" % access_token
    }
    response = requests.get(url, headers=headers)
    print(response.json())
    return response.json()[0]['url']    

def downloadart(arturl, filename):
    response = urllib.request.urlretrieve(arturl, filename)
    return response

def check_env():
    if REFRESH_TOKEN is None or CLIENT_ID is None or CLIENT_SECRET is None or NEW_MUSIC_FRIDAY_ID is None:
        response = 1
    else:
        response = 0
    return response

def pause():
    programPause = input("Press the <ENTER> key to continue...")

if check_env() == 1:
    print("Environment variables have not been loaded, abort.")
    sys.exit(1)

access_token = refresh_access_token()['access_token']
tracks =  get_playlist(access_token,NEW_MUSIC_FRIDAY_ID)['tracks']['items']

if len(tracks) > 10:
    nmfiplaylisttoday =  create_playlist(access_token)['id']
    nmfiplaylisttoday_info =  get_playlist(access_token,nmfiplaylisttoday)
    tracklist = []

    try:
        for item in tracks:
            if item['track'] is not None: # Thanks to https://stackoverflow.com/a/60496351/2220346
                tracklist.append(item['track']['uri'])
    except:
        json_string = json.dumps(tracks)
        tracklisterror = "%s_tracklisterror.json" % d2
        with open(tracklisterror, 'w') as outfile:
            outfile.write(json_string)
        sys.exit(1) # Thanks to https://stackoverflow.com/a/69257826/2220346

    response = add_to_nmfi(access_token, nmfiplaylisttoday, tracklist)

    if "snapshot_id" in response:
        print("Playlist backup complete!")
        nmf_spoticode = get_spoticode(nmfiplaylisttoday)
        #nmf_cover = get_playlistcover(access_token, nmfiplaylisttoday)[0]['url']
        nmf_cover = get_officialplaylistcover(access_token, NEW_MUSIC_FRIDAY_ID)
        downloadart(nmf_spoticode,"nmf_spoticode.png")
        downloadart(nmf_cover,"nmf_cover.png")

        print("Adding playlist to current JSON file ...")
        print("{}: {}".format(nmfiplaylisttoday_info['name'], nmfiplaylisttoday_info['external_urls']['spotify']))
        json_nmf_add = {
        "title": nmfiplaylisttoday_info['name'],
        "cover": nmf_cover,
        "url": nmfiplaylisttoday_info['external_urls']['spotify'],
        "spoticode": nmf_spoticode
        }

        if not os.path.exists("json"):
            os.makedirs("json")
        env_file = os.getenv('GITHUB_ENV')
        with open(env_file, "a") as ghenv:
            ghenv.write("jsn="+year+".json")
        filename = os.path.join("json",year+".json") # Thanks to https://howtodoinjava.com/json/append-json-to-file/
        json_nmf = []
        with open(filename) as fp:
            json_nmf = json.load(fp)
        json_nmf.append(json_nmf_add)
        print(json_nmf)
        with open(filename, 'w') as fp_updated:
            json.dump(json_nmf, fp_updated,
            indent=4,
            separators=(',',': '))

else:
    print("Check tracklist len")
    sys.exit(1)
