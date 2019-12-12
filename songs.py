import csv
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

from fields import URL, ID, TITLE, TEXT

OUT_PATH_TEMPLATE = "data/songs/{id}.txt"
OUT_CSV_TEMPLATE = "{}_out.csv"


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
    with open(input_csv, "r") as f:
        out_csv_name = OUT_CSV_TEMPLATE.format(os.path.splitext(input_csv)[0])
        reader = csv.DictReader(f)
        with open(out_csv_name, "w") as outf:
            writer = csv.DictWriter(outf, reader.fieldnames + [TEXT])
            writer.writeheader()
            for row in reader:
                fname = OUT_PATH_TEMPLATE.format(id=row[ID])
                exists = os.path.exists(fname)
                if row[URL] and not exists:
                    print("Fetching {}".format(row[TITLE]))
                    text = song_lyrics_from_url(row[URL], True)
                    if text is not None:
                        with open(fname, "w") as out_file:
                            out_file.write(text)
                            exists = True
                else:
                    print("Skipping {}".format(row[TITLE]))
                if exists:
                    with open(fname, "r") as in_file:
                        text = "".join(in_file.readlines())
                        row[TEXT] = text.replace("\n\r", " ").replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
                        writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Input file path parameter is expected")
        sys.exit(1)
    run(sys.argv[1])
