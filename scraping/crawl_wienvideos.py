#!/usr/bin/env python3

# Script to crawl recordings and transcripts of videos of the City of Vienna.
# Requires youtube-dl and BeautifulSoup4 packages

import argparse
from pathlib import Path
import re
import time
import urllib
import urllib.request
from bs4 import BeautifulSoup
import youtube_dl
import xml.etree.ElementTree as ET


def main(args, page_start=1, page_end=218):
    sleep_sec = 1
    ua_string = r"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0"

    for page in range(page_start, page_end):
        url_fulllist = f"https://www.wien.gv.at/video/liste?page={page}"
        try:
            req_fulllist = urllib.request.Request(url_fulllist)
            req_fulllist.add_header('Referer', 'https://www.wien.gv.at/video')
            req_fulllist.add_header('User-Agent', ua_string)
            print(f"requesting fulllist URL '{url_fulllist}'")
            with urllib.request.urlopen(req_fulllist, timeout=5) as response_fulllist:
                content = response_fulllist.read()
                html = content.decode('utf-8')
                bs = BeautifulSoup(html, 'html.parser')
                for article in bs('article'):
                    url_article = article.find('a')['href']
                    if url_article.startswith('http'):
                        article_name = '_'.join(url_article.split('/')[-2:])
                        if not Path(args.output_dir).joinpath(article_name+".html").exists():
                            print(article_name)
                            try:
                                req_article = urllib.request.Request(url_article)
                                req_article.add_header('Referer', url_fulllist)
                                req_article.add_header('User-Agent', ua_string)
                                if sleep_sec is not None:
                                    time.sleep(sleep_sec)
                                print(f"requesting article URL '{url_article}'")
                                with urllib.request.urlopen(req_article, timeout=5) as response_article, \
                                    open(Path(args.output_dir) / (article_name+".html"), 'wb') as html_file:
                                    content = response_article.read()
                                    html_file.write(content)
                                    html = content.decode('utf-8')
                                    bs_article = BeautifulSoup(html, 'html.parser')
                                    script = bs_article.select_one('article > div[class="vAPOutContainer clearfix"] > script')
                                    # print(script)
                                    html_script = ' '.join(script.stripped_strings).strip()
                                    # print(html_script)
                                    match = re.search(r'vTrack:"(http.*)"', html_script)
                                    if match:
                                        url_subtitle = match.group(1)
                                        print(f"sub:{url_subtitle}")
                                        try:
                                            req_subtitle = urllib.request.Request(url_subtitle)
                                            req_subtitle.add_header('Referer', url_article)
                                            req_subtitle.add_header('User-Agent', ua_string)
                                            if sleep_sec is not None:
                                                time.sleep(sleep_sec)
                                            print(f"requesting subtitle URL '{url_subtitle}'")
                                            with urllib.request.urlopen(req_subtitle, timeout=5) as response_subtitle:
                                                content = response_subtitle.read()
                                                try:
                                                    sub = content.decode('utf-8')
                                                    ET.fromstring(sub)
                                                    ext = '.ttaf'
                                                except:
                                                    try:
                                                        sub = content.decode('cp1252')
                                                        ET.fromstring(sub)
                                                        ext = '.ttaf'
                                                    except:
                                                        ext = '.srt'
                                                with open(Path(args.output_dir) / (article_name+ext), 'w', encoding='utf-8') as html_file:
                                                    html_file.write(sub)

                                            match = re.search(r'vFile:"(http.*)",', html_script)
                                            if match:
                                                url_video = match.group(1)
                                                print(f"vFile:{url_video}")
                                                # Vimeo link, use youtube-dl
                                                ydl_opts = {
                                                    'outtmpl': str(Path(args.output_dir).joinpath(article_name + ".%(ext)s"))
                                                }
                                                if sleep_sec is not None:
                                                    time.sleep(sleep_sec)
                                                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                                    try:
                                                        ydl.download([url_video])
                                                    except:
                                                        print(f"Unable to request URL '{url_video}'.")
                                        except urllib.error.URLError as e:
                                            print(f"Unable to request URL '{url_subtitle}': {e}.")
                                    # break
                            except urllib.error.URLError as e:
                                print(f"Unable to request URL '{url_article}': {e}.")
        except urllib.error.URLError as e:
            print(f"Unable to request URL '{url_fulllist}': {e}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=str)
    args = parser.parse_args()
    # There are 217 pages, as of now, of the full list of videos
    main(args, page_start=1, page_end=218)
