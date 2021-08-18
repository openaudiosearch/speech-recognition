#!/usr/bin/env python3

# Script to parse crawled Austrian parlament session recordings and transcripts.

import argparse
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup
from num2words import num2words
import csv

ALPHABETISMS = [
    'COVID',
    'NEOS',
    'TOP',
    'ARBÖ',
    'APA',
    'ZIB',
    'TÜV',
    'ARGE',   # Arbeitsgemeinschaft
    'JETZT',  # Political party, now defunct
    'UNO',
    'GIS',
    'WLAN',  # Eigentlich: W LAN
    'HAK',
    'DAX',
    'BIP',
    'EIRAG',
    'EULAK',
    'OPEC',
    'AMA',
    'UNESCO',
    'EIWOG',
    'NÖN',
    'PROGE',
    'AUA',
    'DIN',  # DIN A4
    'NATO'
]

# Define digit mapping
romanNumeralMap = (('M', 1000),
                   ('CM', 900),
                   ('D', 500),
                   ('CD', 400),
                   ('C', 100),
                   ('XC', 90),
                   ('L', 50),
                   ('XL', 40),
                   ('X', 10),
                   ('IX', 9),
                   ('V', 5),
                   ('IV', 4),
                   ('I', 1))

# Define pattern to detect valid Roman numerals
romanNumeralPattern = re.compile("""
    ^                   # beginning of string
    M{0,4}              # thousands - 0 to 4 M's
    (CM|CD|D?C{0,3})    # hundreds - 900 (CM), 400 (CD), 0-300 (0 to 3 C's),
                        #            or 500-800 (D, followed by 0 to 3 C's)
    (XC|XL|L?X{0,3})    # tens - 90 (XC), 40 (XL), 0-30 (0 to 3 X's),
                        #        or 50-80 (L, followed by 0 to 3 X's)
    (IX|IV|V?I{0,3})    # ones - 9 (IX), 4 (IV), 0-3 (0 to 3 I's),
                        #        or 5-8 (V, followed by 0 to 3 I's)
    $                   # end of string
    """, re.VERBOSE)


def fromRoman(s):
    """convert Roman numeral to integer"""
    # special case
    if s == 'N':
        return 0
    if not romanNumeralPattern.search(s):
        return None
    result = 0
    index = 0
    for numeral, integer in romanNumeralMap:
        while s[index:index + len(numeral)] == numeral:
            result += integer
            index += len(numeral)
    return result


def timestamp_to_seconds(time_code: str) -> float:
    hours = float(time_code[0:2])
    minutes = float(time_code[3:5])
    seconds = float(time_code[6:8])
    return (hours*60*60)+(minutes*60)+seconds



def main(args, session_start = 1, session_end = 930):
    for session in range(session_start, session_end):
        session_id = f"{session:05d}"
        # Create folder for session
        session_dir = Path(args.input_dir).joinpath(""+session_id)
        if session_dir.joinpath(session_id + ".wav").exists():
            metadata_path = session_dir.joinpath(session_id + ".tsv")
            with open(metadata_path, 'w', encoding='utf-8', newline='') as metadata_file: #, \
                # wave.open(str(session_dir.joinpath(session_id + ".wav")), 'rb') as wav_file:
                # num_channels, sampwidth, sampling_rate, num_samples, comptype, compname = wav_file.getparams()
                frame_idx = 0
                tsv_writer = csv.writer(metadata_file, delimiter='\t')
                tsv_writer.writerow(['TIME', 'SPEAKER', 'TRANSCRIPT'])
                A_files = sorted(session_dir.glob("A*.html"))
                for proto_idx, protocol_path in enumerate(A_files):
                    with open(protocol_path, 'r', encoding='utf-8') as protocol_file:
                        start_timestamp = protocol_path.stem[4:12]
                        # print(start_timestamp)
                        protocol_content = ' '.join([line.rstrip("\n") for line in protocol_file])
                        # These '<span lang=DE>' tags are sometimes in the middle of a word!
                        # If not removed, they will cause the word to be split into parts
                        protocol_content = re.sub(r"<span .+?>", r"", protocol_content)
                        # protocol_content = protocol_content.replace('<span lang=DE>', '')
                        protocol_content = protocol_content.replace('</span>', '')
                        bs = BeautifulSoup(protocol_content, 'html.parser')
                        # By default, get the initial timestamp from the <title> element
                        # start_timestamp = bs.find('title').string[-5:].strip()
                        speaker = ''
                        seg_text = ''
                        for paragraph in bs('p'):
                            # <p class=RB> tags signal a timestamp
                            # if paragraph['class'] == ['RB']:
                                # start_timestamp = ''.join(paragraph.stripped_strings)
                            if paragraph['class'] == ['ZM']:
                                content = (' '.join(paragraph.stripped_strings)).replace('*','').strip()
                                # print(content, file=sys.stderr)
                                if content.replace('.','').isdigit():
                                    # new timestamp
                                    new_timestamp = content.replace('.', '_')
                                    # num_frames = int(timestamp_to_seconds(new_timestamp)*sampling_rate - 
                                    #     timestamp_to_seconds(start_timestamp)*sampling_rate + 5*sampling_rate)
                                    # # print(f"{start_timestamp}: {num_frames} samples ZM")
                                    # raw = wav_file.readframes(num_frames)
                                    # frame_idx = frame_idx = (len(raw)//sampwidth)
                                    # wav_file.setpos(max(frame_idx - 30*sampling_rate, 0))
                                    # frame_idx = max(frame_idx - 30*sampling_rate, 0)
                                    # with wave.open(str(Path(args.output_dir).joinpath(session_id+'_'+start_timestamp+'.wav')), 'wb') as wav_seg_file:
                                    #     wav_seg_file.setparams((num_channels, sampwidth, sampling_rate, num_frames, comptype, compname))
                                    #     wav_seg_file.writeframes(raw)
                                    # with open(Path(args.output_dir).joinpath(session_id+'_'+start_timestamp+'.txt'), 'w', encoding='utf-8') as txt_seg_file:
                                    #     txt_seg_file.write(seg_text)
                                    seg_text = ''
                                    start_timestamp = new_timestamp
                            # <p class=MsoNormal> tags signal a paragraph
                            if paragraph['class'] == ['MsoNormal']: # and paragraph.string is not None:
                                bold_tag = paragraph.find('b')
                                if bold_tag is not None:
                                    # print(bold_tag)                                
                                    link_tag = bold_tag.find('a')
                                    if link_tag is not None:
                                        speaker = ' '.join(link_tag.stripped_strings)
                                        speaker = speaker.replace("\n", " ")
                                        speaker = speaker.strip()
                                        speaker = speaker.replace('"', '')
                                        speaker = speaker.strip(',')
                                        # print(f"'{speaker}'")
                                        bold_tag.extract()
                                # Remove <i>..</i> tags (mostly not pronounced!)
                                for i_tag in paragraph.find_all('i'):
                                    # print(' '.join(i_tag.stripped_strings), file=sys.stderr)
                                    i_tag.decompose()
                                text = ' '.join(paragraph.stripped_strings).strip()
                                if len(text) > 0 and len(speaker) > 0:
                                    # Conversion BEFORE number replacement
                                    text = text.replace("\n", " ")
                                    text = text.replace("[...]", " ")
                                    text = re.sub(r"§+\s(\d+)(\w?)\s(\d+)(\w?)\s(\d+)(\w?)", r"Paragraf \1 \2 \3 \4 \5 \6", text)
                                    text = re.sub(r"§+\s(\d+)(\w?)\s(\d+)(\w?)", r"Paragraf \1 \2 \3 \4", text)
                                    text = re.sub(r"§+\s(\d+)(\w?)", r"Paragraf \1 \2", text)
                                    text = re.sub(r"Abs.\s(\d+)(\w?)\s(\d+)(\w?)\s(\d+)(\w?)", r"Absatz \1 \2 \3 \4 \5 \6", text)
                                    text = re.sub(r"Abs.\s(\d+)(\w?)\s(\d+)(\w?)", r"Absatz \1 \2 \3 \4", text)
                                    text = re.sub(r"Abs.\s(\d+)(\w?)\sund\s(\d+)(\w?)", r"Absatz \1 \2 und \3 \4", text)
                                    text = re.sub(r"Abs.\s(\d+)(\w?)", r"Absatz \1 \2", text)
                                    text = re.sub(r"(\d+)\s(\d+)\sEuro", r"\1\2 Euro", text)
                                    text = re.sub(r"\s1\sEuro", r" ein Euro", text)
                                    text = text.replace("§", "Paragraf")
                                    text = text.replace("Dr.", "Doktor")
                                    text = text.replace("Mag.", "Magister")
                                    text = text.replace("TVthek", "T. V. thek")
                                    
                                    # text = text.replace("M A ", "")
                                    text = re.sub(r"Dipl.-Ing.", r"Diplomingenieur", text)
                                    text = text.replace("Ing.", "Ingenieur")
                                    text = text.replace("%", " Prozent")
                                    text = text.replace("/", " / ")
                                    text = text.replace(", ", " , ")
                                    text = text.replace("–", " ")
                                    text = text.replace("-", " ")
                                    text = text.replace(":", "")
                                    text = text.replace(";", "")
                                    text = text.replace("!", "")
                                    text = text.replace("­", "")
                                    text = text.replace("?", "")
                                    text = text.replace("“", "")
                                    text = text.replace("„", "")

                                    # Number replacement
                                    words = text.split()
                                    text = []
                                    for word_idx, word in enumerate(words):
                                        # Is it a number of some kind?
                                        if word.replace('.','',1).isdigit():
                                            if word[-1] == ".":
                                                try:
                                                    # Check if it's a year at the end of a sentence
                                                    num = int(word[:-1])
                                                    # print(f"{word_idx}, {word}")
                                                    if num > 1920 and num < 2100:
                                                        text.append(num2words(num, to="year", lang="de"))
                                                    else:
                                                        text.append(num2words(num, ordinal=True, lang="de"))
                                                except ValueError:
                                                    print(f"ValueError: '{word}'")
                                            else:
                                                seg = word.split('.')
                                                if len(seg) > 1:
                                                    if len(seg[0]) > 2 and len(seg[1]) > 2:
                                                        # print(f"largenum: {word}")
                                                        # z.B. "500.000"
                                                        text.append(num2words(int("".join(seg)), lang="de"))
                                                    elif len(words) > word_idx+1 and words[word_idx+1] == "Uhr":
                                                        # print(f"Uhrzeit: {word}")
                                                        # z.B. "19.15 Uhr"
                                                        text.append(num2words(int(seg[0]), lang="de"))
                                                        text.append("Uhr")
                                                        text.append(num2words(int(seg[1]), lang="de"))
                                                        del words[word_idx+1]
                                                    else:
                                                        # print(f"Punkt: {word}")
                                                        # z.b. Web 2.0
                                                        text.append(num2words(int(seg[0]), lang="de"))
                                                        text.append("Punkt")
                                                        text.append(num2words(int(seg[1]), lang="de"))
                                                else:
                                                    try:
                                                        num = int(word)
                                                        # Sometimes, 10000 is written as "10&nbsp;000", which is turned into "10 0000"
                                                        # so we have to check if the next word is all digits
                                                        if len(words) > word_idx+1 and words[word_idx+1].isdigit():
                                                            # print(f"{start_timestamp} {words[word_idx+2]}")
                                                            num = num*1000 + int(words[word_idx+1])
                                                            # If we have 10 000 000:
                                                            if len(words) > word_idx+2 and words[word_idx+2].isdigit():
                                                                num = num*1000 + int(words[word_idx+2])
                                                                del words[word_idx+2]
                                                            # print(f"Grosse zahl: {num} {word} {words[word_idx+1]}")
                                                            del words[word_idx+1]
                                                            text.append(num2words(num, lang="de"))
                                                        elif num > 1920 and num < 2100:
                                                            # Likely a year
                                                            text.append(num2words(num, to="year", lang="de"))
                                                        else:
                                                            text.append(num2words(num, lang="de"))
                                                    except ValueError:
                                                        print(f"ValueError: '{word_idx}' '{word}' '{words[word_idx+1]}'")
                                        elif word.replace(',','',1).isdigit():
                                            seg = word.split(',')
                                            if len(seg) > 1:
                                                if seg[1] == "00":
                                                    # Euro amount, ignore second part, it's not pronounced
                                                    text.append(num2words(int(seg[0]), lang="de"))
                                                elif len(seg[0]) > 0 and len(seg[1]) > 0:
                                                    text.append(num2words(int(seg[0]), lang="de"))
                                                    text.append("Komma")
                                                    for letter in seg[1]:
                                                        if letter.isdigit():
                                                            text.append(num2words(int(letter), lang="de"))
                                                elif word[-1] == ',':
                                                    text.append(num2words(int(seg[0]), lang="de"))
                                                else:
                                                    print(f"{start_timestamp} {word}", file=sys.stderr)
                                        elif word.replace('.','').isdigit():
                                            # Possibly a date?
                                            seg = word.split('.')
                                            try:
                                                if len(seg) > 2:
                                                    text.append(num2words(int(seg[0]), ordinal=True, lang="de"))
                                                    text.append(num2words(int(seg[1]), ordinal=True, lang="de"))
                                                    if len(seg[2]) > 0:
                                                        text.append(num2words(int(seg[2]), to="year", lang="de"))
                                                # elif words[word_idx+1] == "Uhr":
                                                #     text.append(num2words(int(seg[0]), ordinal=True, lang="de"))
                                                #     text.append("Uhr")
                                                #     text.append(num2words(int(seg[1]), ordinal=True, lang="de"))
                                                #     del words[word_idx+1]
                                            except ValueError:
                                                print(f"ValueError: '{word}' '{words[word_idx+1]}'")
                                        elif word.upper() == word:
                                            if romanNumeralPattern.search(word):
                                                # print(f"Roman numeral: {word}")
                                                num = 0
                                                index = 0
                                                for numeral, integer in romanNumeralMap:
                                                    while word[index:index + len(numeral)] == numeral:
                                                        num += integer
                                                        index += len(numeral)
                                                text.append(num2words(num, ordinal=False, lang="de"))
                                            # Possibly an abbreviation?
                                            elif not word.upper() in ALPHABETISMS:
                                                # abbr = re.sub(r"(\w)", r"\1\\", word)
                                                # for elem in abbr.split('\\'):
                                                for letter in word:
                                                    if letter.isdigit():
                                                        try:
                                                            # Check if it's a year at the end of a sentence
                                                            num = int(letter)
                                                            if num > 1920 and num < 2100:
                                                                text.append(num2words(num, to="year", lang="de"))
                                                            else:
                                                                text.append(num2words(num, ordinal=False, lang="de"))
                                                        except ValueError:
                                                            print(f"ValueError: '{letter}'")
                                                    else:
                                                        text.append(letter+"\\ ")
                                            else:
                                                text.append(word)
                                        else:
                                            text.append(word)
                                    text = ' '.join(text)
                                    # Conversion AFTER number replacement
                                    text = re.sub(r"(\d+)/(\w+)", r"\1 \2", text)  # Law codes 
                                    text = text.replace(".", "")
                                    text = text.replace("\\", ".")
                                    text = text.replace(".", "")
                                    text = text.replace(",", "")
                                    text = text.replace("/", "")
                                    text = text.replace("\"", "")
                                    text = re.sub(r"\([^()]*\).", " [spoken-noise] ", text)
                                    text = re.sub(r"\([^()]*\)", " [spoken-noise] ", text)
                                    # text = text.replace(",.", ",")
                                    text = text.replace("‘", "")
                                    text = text.replace("‚", "")
                                    text = text.replace("à", "a")
                                    text = text.replace("é", "e")
                                    text = text.replace("ı", "i")
                                    text = text.replace("‑", " ")
                                    text = text.replace(")", "")
                                    text = re.sub(r"(\s)\s+", r"\1", text)  # Multi spaces
                                    text = text.strip()
                                    seg_text = seg_text + " " + text.lower()
                                    tsv_writer.writerow([start_timestamp, speaker, text.lower()])
                                    # print(f"{start_timestamp} '{speaker}' <<{text}>>")
                    # if len(A_files) > proto_idx+1:
                    #     next_timestamp = A_files[proto_idx+1].stem[4:12]
                    #     num_frames = int(timestamp_to_seconds(next_timestamp)*sampling_rate - \
                    #         timestamp_to_seconds(start_timestamp)*sampling_rate + 5*sampling_rate)
                    # else:
                    #     num_frames = int(num_samples - timestamp_to_seconds(start_timestamp)*sampling_rate + 5*sampling_rate)
                    # raw = wav_file.readframes(num_frames)
                    # num_frames = len(raw) // sampwidth
                    # frame_idx = frame_idx = (len(raw)//sampwidth)
                    # wav_file.setpos(max(frame_idx - 30*sampling_rate, 0))
                    # frame_idx = max(frame_idx - 30*sampling_rate, 0)
                    # # print(f"{start_timestamp}: {num_frames} samples")
                    # with wave.open(str(Path(args.output_dir).joinpath(session_id+'_'+start_timestamp+'.wav')), 'wb') as wav_seg_file:
                    #     wav_seg_file.setparams((num_channels, sampwidth, sampling_rate, num_frames, comptype, compname))
                    #     wav_seg_file.writeframes(raw)
                    # with open(Path(args.output_dir).joinpath(session_id+'_'+start_timestamp+'.txt'), 'w', encoding='utf-8') as txt_seg_file:
                    #     txt_seg_file.write(seg_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=str, default="/data/atparl/")
    #parser.add_argument("output_dir", type=str, default="/data/atparl/")
    args = parser.parse_args()
    main(args, session_start = 1, session_end = 930)
