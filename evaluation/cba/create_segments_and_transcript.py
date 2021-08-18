#!/usr/bin/env python3
# coding=utf-8

import argparse
from pathlib import Path
import re

def main(args):
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.output_dir) / 'segments', 'w', encoding='utf-8') as seg_file, \
            open(Path(args.output_dir) / 'text', 'w', encoding='utf-8') as text_file:
        for trans_path in Path(args.transcript_dir).glob("*.txt"):
            with open(trans_path, 'r', encoding='utf-8') as trans_file:
                for line in trans_file:
                    match = re.match(
                        r'^\[(?P<start>[0-9]+)\]\[(?P<end>[0-9]+)\] (?P<speaker>[A-Z]+): (?P<text>.*)$', line)
                    if match is not None:
                        start = float(match.group('start'))
                        end = float(match.group('end'))
                        if start == end or start > end:
                            print(trans_path)
                        speaker = match.group('speaker')
                        text = match.group('text')
                        utt = trans_path.stem
                        segment = f"{trans_path.stem}-{speaker}-{int(start*100):06d}-{int(end*100):06d}"

                        text = re.sub(r'(\W)hh(\W)', r'\1[noise]\2', text)
                        text = re.sub(r'^hh(\W)', r'[noise]\1', text)
                        text = re.sub(r'(\W)hh$', r'\1[noise]', text)
                        text = re.sub(r'(\W)ll(\W)', r'\1[laughter]\2', text)
                        text = re.sub(r'^ll(\W)', r'[noise]\1', text)
                        text = re.sub(r'(\W)ll$', r'\1[noise]', text)
                        text = re.sub(r'(\W?)\[\d+"?\](\W?)', r'\1 \2', text)
                        text = re.sub(r'(\W?)\[\w+\](\W?)', r'\1[noise]\2', text)
                        text = re.sub(r'(\W?)\(unv.\)(\W?)', r'\1[noise]\2', text)
                        text = re.sub(r'(\w\w)\.(\W)', r'\1 \2', text)
                        #text = re.sub(r'([^A-ZÖÜÄ])\.(\W)', r'\1 \2', text)
                        text = re.sub(r'\.\.+', r' ', text)
                        text = re.sub(r'\]\.(\s)', r']\1', text)
                        text = re.sub(r'\.\s*$', r'', text)

                        text = text.replace("-", " ")
                        text = text.replace("_", " ")
                        text = re.sub("[ ]{2,}", " ", text)
                        text = text.replace(",", "")
                        text = text.replace(";", "")
                        text = text.replace("?", "")
                        text = text.replace("!", "")
                        text = text.replace(":", "")
                        text = text.replace("\"", "")
                        text = text.strip()
                        #text = text.lower()

                        seg_file.write(
                            f"{segment} {utt} {start:.2f} {end:.2f}\n")
                        text_file.write(f"{segment} {text}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript_dir", type=str)
    parser.add_argument("output_dir", type=str)
    args = parser.parse_args()
    main(args)
