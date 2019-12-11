import sys

import requests
import json

TOKEN = "gikQvKax1B8rlMkRT1vVbagHpQFwa1D5Clsb2CEj1BwkBMAI6Sx8wqfLNpOJo_Ck"


def get_artist(data: dict) -> int:
    if 'result' in data and 'primary_artist' in data['result']:
        return data['result']['primary_artist'].get('id', 0)
    return 0


def fetch_song_ids(data: dict, artist: int) -> list:
    if 'response' not in data or 'songs' not in data['response']:
        return []
    ids = []
    for x in data['response']['songs']:
        if 'id' not in x:
            continue
        try:
            id = x['primary_artist']['id']
            if id == artist:
                ids.append(x['id'])
        except:
            print("Error finding primary artist for data {}".format(data))
    return ids


def process_song(data: dict, songs: dict) -> None:
    if 'response' not in data or 'song' not in data['response']:
        return
    data = data['response']['song']
    album = data.get('album', {}) or {}
    songs[data['id']] = {
        'url': data.get('url', ""),
        'title': data.get('title', ""),
        'release_date': data.get('release_date', ""),
        'album_id': album.get('id'),
        'album_title': album.get('full_title'),
    }


def run(artist: str) -> None:
    resp = requests.get("http://api.genius.com/search", params={
        'q': artist,
        'access_token': TOKEN
    })
    data = resp.json()['response']['hits']
    artists = {}
    for result in data:
        artist = get_artist(result)
        if artist > 0:
            artists[artist] = artists.get(artist, 0) + 1

    artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)
    if len(artists) < 1:
        print("Artist id not found")
        print(data)
        return
    artist = artists[0][0]
    print("Artist id: {}".format(artist))
    songs = []
    page = 1
    while page:
        print("Fetching songs page {}".format(page))
        resp = requests.get("http://api.genius.com/artists/{}/songs".format(artist), params={
            'access_token': TOKEN,
            'per_page': 50,
            'page': page
        })
        data = resp.json()
        # print(json.dumps(resp.json(), indent=4))

        songs.extend(fetch_song_ids(data, artist))
        if 'response' not in data or 'next_page' not in data['response']:
            break
        if page == data['response']['next_page']:
            break
        page = data['response']['next_page']
        break
    num_songs = len(songs)
    songs = {x: {} for x in songs}
    idx = 1
    for song in songs.keys():
        print("Fetching song {} of {}".format(idx, num_songs))
        idx += 1
        resp = requests.get("http://api.genius.com/songs/{}".format(song), params={
            'access_token': TOKEN,
            'text_format': "plain",
        })
        data = resp.json()
        # print(json.dumps(resp.json(), indent=4))
        process_song(data, songs)
    print(json.dumps(songs, indent=4))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Artist name as a parameter expected")
        sys.exit(1)
    run(sys.argv[1])
