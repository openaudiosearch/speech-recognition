#!/usr/bin/env python3

# Script to crawl Austrian Nationalrat session recordings and transcripts
#
# Steps:
# 1. Crawl session main page
# 2. Get "player" link to obtain ID string to download session recording
# 3. Go through each item that has a steno protocol, download it, and save it

import argparse
import json
from pathlib import Path
import re
import sys
import time
import urllib
import urllib.request

# update_progress() : Displays or updates a console progress bar
## Accepts a float between 0 and 1. Any int will be converted to a float.
## A value under 0 represents a 'halt'.
## A value at 1 or bigger represents 100%
def update_progress(progress):
    barLength = 40 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rPercent: [{0}] {1:.2f}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()


def main(args, legislative_period="XXVII", session_start=1, session_end=120):
    sleep_sec = 1
    chunk_size = 16 * 1024
    ua_string = r"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0"

    for session in range(session_start, session_end):
        session_id = f"{session:05d}"
        # Create folder for session
        Path(args.output_dir).joinpath(session_id).mkdir(exist_ok=True, parents=True)
        url_session = f"https://www.parlament.gv.at/PAKT/VHG/{legislative_period}/NRSITZ/NRSITZ_{session:05d}/"
        try:
            req_session = urllib.request.Request(url_session)
            req_session.add_header('Referer', f'https://www.parlament.gv.at/PAKT/PLENAR/index.shtml?FBEZ=FP_007&NRBRBV=NR&GP={legislative_period}&LISTE=Anzeigen&listeId=1070')
            req_session.add_header('User-Agent', ua_string)
            print(f"requesting session URL '{url_session}'")
            with urllib.request.urlopen(req_session) as response_session, \
                open(Path(args.output_dir) / session_id / "index.html", 'wb') as html_file:
                content = response_session.read()
                html_file.write(content)
                html = content.decode('utf-8')
                if not (Path(args.output_dir) / session_id / (session_id + ".mp4")).exists():
                    # Get player page to obtain session ID of recording
                    match = re.search(r'href="(/MEDIA/play.shtml\?[^\'" >]+)"', html)
                    if match:
                        try:
                            url_player = "https://www.parlament.gv.at" + match.group(1)
                            req_player = urllib.request.Request(url_player)
                            req_player.add_header('Referer', url_session)
                            req_player.add_header('User-Agent', ua_string)
                            if sleep_sec is not None:
                                time.sleep(sleep_sec)
                            print(f"    requesting player URL '{url_player}'")
                            with urllib.request.urlopen(req_player) as response_player:
                                html_player = response_player.read().decode('utf-8')
                                #a_uuid="cd6658d4-64ea-4479-b93c-24bb09a27616"
                                match = re.search(r'a_uuid="([^\'" >]+)"', html_player)
                                if match:
                                    session_uuid = match.group(1)
                                    json_api = None
                                    try:
                                        url_api = f"https://api.ausp.cloud.insysgo.com/media/clean/{session_uuid}.mp4"
                                        req_api = urllib.request.Request(url_api)
                                        req_api.add_header('Referer', url_player)
                                        req_api.add_header('User-Agent', ua_string)
                                        if sleep_sec is not None:
                                            time.sleep(sleep_sec)
                                        print(f"    requesting API URL '{url_api}'")
                                        with urllib.request.urlopen(req_api) as response_api:
                                            json_api = json.loads(response_api.read().decode('utf-8'))
                                    except urllib.error.URLError as e:
                                        print(f"Unable to request URL '{url_player}': {e}. Retrying...")
                                        url_api = f"https://api.ausp.cloud.insysgo.com/media/dirty/{session_uuid}.mp4"
                                        req_api = urllib.request.Request(url_api)
                                        req_api.add_header('Referer', url_player)
                                        req_api.add_header('User-Agent', ua_string)
                                        if sleep_sec is not None:
                                            time.sleep(sleep_sec)
                                        print(f"    requesting API URL '{url_api}'")
                                        with urllib.request.urlopen(req_api) as response_api:
                                            json_api = json.loads(response_api.read().decode('utf-8'))
                                    if json_api is not None:
                                        url_recording = json_api.get('URL', None)
                                        if url_recording is not None:
                                            req_recording = urllib.request.Request(url_recording)
                                            req_recording.add_header('Referer', url_player)
                                            req_recording.add_header('User-Agent', ua_string)
                                            print(f"    requesting recording URL '{url_recording}'")
                                            with urllib.request.urlopen(req_recording) as response_recording, \
                                                open(Path(args.output_dir) / session_id / (session_id + ".mp4"), 'wb') as recording_file:
                                                content_length = int(response_recording.headers['content-length'])
                                                bytes_written = 0
                                                while True:
                                                    chunk = response_recording.read(chunk_size)
                                                    if not chunk:
                                                        break
                                                    bytes_written += recording_file.write(chunk)
                                                    update_progress(bytes_written / content_length)
                                                print("\nDone!")
                        except urllib.error.URLError as e:
                            print(f"Unable to request URL '{url_player}': {e}.")
                matches = re.findall(f'/PAKT/VHG/{legislative_period}/NRSITZ/NRSITZ_' + session_id + r'/(A_-_[0-9_]+\.html)"', html)
                for part in matches:
                    if not (Path(args.output_dir) / session_id / part).exists():
                        try:
                            url_part = f"https://www.parlament.gv.at/PAKT/VHG/{legislative_period}/NRSITZ/NRSITZ_{session_id}/{part}"
                            req_part = urllib.request.Request(url_part)
                            req_part.add_header('Referer', url_session)
                            req_part.add_header('User-Agent', ua_string)
                            if sleep_sec is not None:
                                time.sleep(sleep_sec)
                            print(f"    requesting part URL '{url_part}'")
                            with urllib.request.urlopen(req_part) as response_part, \
                                open(Path(args.output_dir) / session_id / part, 'wb') as part_file:
                                #content_length = response_part.headers['content-length']
                                while True:
                                    chunk = response_part.read(chunk_size)
                                    if not chunk:
                                        break
                                    part_file.write(chunk)
                        except urllib.error.URLError as e:
                            print(f"Unable to request URL '{url_part}': {e}.")
        except urllib.error.URLError as e:
            print(f"Unable to request URL '{url_session}': {e}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=str)
    args = parser.parse_args()

    # There are 89 sessions, as of now, of the XXVI Nationalrat; however, the first 81 or so don't seem to have
    #   live footage available
    # There are 120 sessions, as of 2021-08-17, of the XXVII Nationalrat
    main(args, legislative_period="XXVII", session_start=1, session_end=120)
