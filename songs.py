import csv
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

from fields import URL, ID, TITLE

OUT_PATH_TEMPLATE = "data/songs/{id}.txt"


def song_lyrics_from_url(url, remove_section_headers):
    """
    From https://github.com/johnwmillr/LyricsGenius
    """
    page = requests.get(url)
    if page.status_code == 404:
        return None

    html = BeautifulSoup(page.text, "html.parser")
    div = html.find("div", class_="lyrics")
    if not div:
        return None

    lyrics = div.get_text()
    if remove_section_headers:
        lyrics = re.sub('(\[.*?\])*', '', lyrics)
        lyrics = re.sub('\n{2}', '\n', lyrics)
    return lyrics.strip("\n")


def run(input_csv: str) -> None:
    with open(input_csv, mode='r') as f:
        reader = csv.DictReader(f)
        next(reader)
        for row in reader:
            fname = OUT_PATH_TEMPLATE.format(id=row[ID])
            if row[URL] and not os.path.exists(fname):
                print("Fetching {}".format(row[TITLE]))
                text = song_lyrics_from_url(row[URL], True)
                with open(fname, "w") as out_file:
                    out_file.write(text)
            else:
                print("Skipping {}".format(row[TITLE]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Input file path parameter is expected")
        sys.exit(1)
    run(sys.argv[1])
