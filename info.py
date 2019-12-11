import csv
import sys

import requests

from fields import ID, DATE, TITLE, ALBUM, ALBUM_ID, URL

INFO_TEMPLATE = "data/{artist}.csv"

HEADER = (ID, DATE, TITLE, ALBUM, ALBUM_ID, URL)


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
        ID: data['id'],
        URL: data.get('url', ""),
        TITLE: data.get('title', ""),
        DATE: data.get('release_date', ""),
        ALBUM_ID: album.get('id'),
        ALBUM: album.get('full_title'),
    }


def run(token: str, artist_name: str) -> None:
    resp = requests.get("http://api.genius.com/search", params={
        'q': artist_name,
        'access_token': token
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
            'access_token': token,
            'per_page': 50,
            'page': page
        })
        data = resp.json()

        songs.extend(fetch_song_ids(data, artist))
        if 'response' not in data or 'next_page' not in data['response']:
            break
        if page == data['response']['next_page']:
            break
        page = data['response']['next_page']
    num_songs = len(songs)
    songs = {x: {} for x in songs}
    idx = 1
    for song in songs.keys():
        print("Fetching song {} of {}".format(idx, num_songs))
        idx += 1
        resp = requests.get("http://api.genius.com/songs/{}".format(song), params={
            'access_token': token,
            'text_format': "plain",
        })
        data = resp.json()
        process_song(data, songs)
    if songs:
        with open(INFO_TEMPLATE.format(artist=artist_name), mode='w') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(HEADER)
            for id_, song in songs.items():
                writer.writerow([song[x] for x in HEADER])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Token and artist name parameters are expected")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])
