#!/usr/bin/env python3

# Script to parse crawled recordings and transcripts of videos of the City of Vienna

import argparse
from pathlib import Path
import re
import sys
from num2words import num2words
import srt

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
    'NATO',
    'EURO',
    'FARE',
    'SORA',
    'LED',
    'CLUB',
    'WIEN',
    'ART',
    'FEM',
    'HOTEL',
    'HOERBIGER',
    'LIFE',
    'LIFE+',
    'RELAX',
    'MAG',
    'IIASA',
    'IST',
    'DAS',
    'AUDIO',
    'MUSA',
    'NEU',
    'IBIS',
    'VIDEO',
    'CON',
    'ULF',
    'MUT',
    'AIDS',
    'IVECO',
    'ALEELA',
    'ALEEL',
    'SOKO',
    'MENA',
    'DIESE',
    'NGOS',
    'EUROKEY',
    'TEST',
    'ON',
    'OFF',
    'PISA',
    'DER',
    'MAG',
    'ELF',
    'MANNER',
    'SIMS',
    'ZOOM',
    'ELEMU',
    'DO', 'RE', 'MI', 'FA', 'SOL', 'LA', 'TI'
]

expand_words = {
    'km': 'k m',
    'kg': 'k g',
    'kw': 'k w',
    'ca': 'circa',
    'va': 'vor allem',
    'nb': 'n b',
    'st': 'sankt',
    'm2': 'quadratmeter'
}

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


def main(args):
    with open(Path(args.output_dir).joinpath("segments"), 'w', encoding='utf-8', newline='') as seg_file, \
        open(Path(args.output_dir).joinpath("text"), 'w', encoding='utf-8', newline='') as text_file, \
        open(Path(args.output_dir).joinpath("wav.scp"), 'w', encoding='utf-8', newline='') as scp_file:
        for srt_path in Path(args.srt_dir).glob("*.srt"):
            # Get numerical identifer at the beginning of the file name
            session_id = int(srt_path.stem.split('_', maxsplit=1)[0])
            # Check if associated *.m4a file exists
            if Path(args.m4a_dir).joinpath(srt_path.stem + ".m4a").exists():
                with open(srt_path, 'r', encoding='utf-8') as srt_file:
                    scp_file.write(f"wienbot-{session_id:07d} ffmpeg -i {str(Path(args.m4a_dir).joinpath(srt_path.stem + '.m4a').absolute())} -vn -ar 16000 -ac 1 -f wav - |\n")
                    # wave.open(str(session_dir.joinpath(session_id + ".wav")), 'rb') as wav_file:
                    # num_channels, sampwidth, sampling_rate, num_samples, comptype, compname = wav_file.getparams()
                    print(srt_path.stem)
                    subs = srt.parse(srt_file, ignore_errors=True)
                    for sub in subs:
                        text = sub.content.strip()
                        if len(text) > 0:
                            # Conversion BEFORE number replacement
                            text = text.replace("\n", " ")
                            text = text.replace("...", " . ")
                            text = text.replace("..", " . ")
                            text = re.sub(r"(\s?\d+)\.(\d\d\d\s?)", r"\1\2", text)
                            text = re.sub(r"(\d+)\.(\w+)", r"\1. \2", text)
                            text = re.sub(r"\s?(\d+)([^\d]+)\s?", r" \1 \2 ", text)
                            text = re.sub(r"\s?([^\d]+)(\d+)\s?", r" \1 \2 ", text)
                            # text = text.replace(".", " . ")
                            text = text.replace("…", "")
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
                            text = text.replace("z.B.", "zum beispiel")
                            text = text.replace("d.h.", "das heißt")

                            # text = text.replace("M A ", "")
                            text = re.sub(r"Dipl.-Ing.", r"Diplomingenieur", text)
                            text = text.replace("Ing.", "Ingenieur")
                            text = text.replace("%", " Prozent")
                            text = text.replace("/", " ")
                            text = text.replace(",--", "")
                            text = text.replace(", ", " , ")
                            text = re.sub(r",$", r"", text)
                            text = text.replace("–", " ")
                            text = text.replace("-", " ")
                            text = text.replace("@", " ")
                            text = text.replace(":", "")
                            text = text.replace(";", "")
                            text = text.replace("!", "")
                            text = text.replace("­", "")
                            text = text.replace("?", "")
                            text = text.replace("“", "")
                            text = text.replace("„", "")
                            text = text.replace("[", "")
                            text = text.replace("]", "")

                            # Number replacement
                            words = text.split()
                            text = []
                            for word_idx, word in enumerate(words):
                                word = word.strip(r"'’\"")
                                if len(word) > 0:
                                    # Is it a number of some kind?
                                    if word.strip('.').replace('.','', 1).isdigit():
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
                                                if len(seg[0]) >= 1 and len(seg[1]) > 2:
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
                                                elif len(seg[0]) > 0 and len(seg[1]) == 2:
                                                    text.append(num2words(int(seg[0]), lang="de"))
                                                    text.append("Uhr")
                                                    text.append(num2words(int(seg[1]), lang="de"))
                                                elif len(seg[0]) > 0:
                                                    print(f"Punkt: {word}")
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
                                                print(f"{sub.start.total_seconds()} {word}", file=sys.stderr)
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
                                            if word_idx+1 < len(words):
                                                print(f"ValueError: '{word}' '{words[word_idx+1]}'")
                                            else:
                                                print(f"ValueError: '{word}' is last word")
                                    elif word.replace('.','').replace('er','').isdigit():
                                        # 48er, 44er etc.
                                        word = word.replace('.','')
                                        num = int(word.replace('er', ''))
                                        if num > 1920 and num < 2100:
                                            text.append(f"{num2words(int(word[0:2]), lang='de')} {num2words(int(word[2:4]), lang='de')}er")
                                        else:
                                            text.append(f"{num2words(num, lang='de')}er")
                                    elif word.replace('.','').replace('ern','').isdigit():
                                        # 48ern, 44ern etc.
                                        word = word.replace('.','')
                                        num = int(word.replace('ern', ''))
                                        if num > 1920 and num < 2100:
                                            text.append(f"{num2words(int(word[0:2]), lang='de')} {num2words(int(word[2:4]), lang='de')}ern")
                                        else:
                                            text.append(f"{num2words(num, lang='de')}ern")
                                    elif word.split('.')[0].lower() == "www" and len(word.split('.')) >= 3:
                                        end_idx = -1
                                        if len(word.split('.')[end_idx]) == 0:
                                            end_idx -= 1
                                        parts = word.split('.')[1:end_idx]
                                        text.append("w w w")
                                        for part in parts:
                                            text.append("punkt")
                                            text.append(part)
                                        text.append("punkt")
                                        tld = str(word.split('.')[end_idx])
                                        if tld == 'com' or tld == 'org' or tld == 'net':
                                            text.append(tld)
                                        else:
                                            text.append(' '.join([letter for letter in tld]))
                                    elif len(word.replace('.', '')) > 0 and word.replace('.', '')[-1] == '€':
                                        print(word)
                                        word = word.replace('.', '').replace(',','')[:-1]
                                        if len(word) > 0:
                                            text.append(num2words(int(word), lang="de"))
                                            text.append('euro')
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
                                        elif not word.upper() in ALPHABETISMS and len(word) < 7:
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
                                            text.append(word.lower())
                                    else:
                                        if word in expand_words:
                                            word = expand_words[word]
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
                            text = re.sub(r"\*[^*]*\*", " [noise] ", text)
                            text = re.sub(r"^# .*", "[noise]", text)
                            # text = text.replace(",.", ",")
                            text = text.replace("‘", "")
                            text = text.replace("‚", "")
                            text = text.replace("à", "a")
                            text = text.replace("é", "e")
                            text = text.replace("ı", "i")
                            text = text.replace("‑", " ")
                            text = text.replace(")", "")
                            text = text.replace("(", "")
                            text = text.replace("+", " plus")
                            # text = text.replace("gibt's", "gibt 's")
                            # text = text.replace("wenn's", "wenn 's")
                            # text = text.replace("wann's", "wann 's")
                            # text = text.replace("sich's", "sich 's")
                            # text = text.replace("braucht's", "braucht 's")
                            # text = text.replace("stell's", "stell 's")
                            text = text.replace("'s", " 's")
                            text = text.replace("ç", "c")
                            text = text.replace("è", "è")
                            text = text.replace("&", " und ")
                            text = text.replace("8erln", "achterln")
                            text = text.replace("90ern", "neunzigern")
                            text = text.replace("29er", "neun und zwanziger")
                            text = text.replace("48er", "acht und vierziger")
                            text = text.replace("’s", " 's")
                            text = text.replace("tschhhh", "[spoken-noise]")
                            text = text.replace("mmmmmhhh", "mh")
                            text = text.replace(" i i i ", " drei ")
                            text = text.replace(" i i ", " zwei ")
                            text = text.replace("=", "")
                            text = text.replace("_", " ")
                            text = re.sub(r"(\s)\s+", r"\1", text)  # Multi spaces
                            text = text.strip()
                            if len(text) > 0:
                                seg = f"wienbot-{session_id:07d}-{int(sub.start.total_seconds()*100):06d}-{int(sub.end.total_seconds()*100):06d}"
                                seg_file.write(f"{seg} wienbot-{session_id:07d} {sub.start.total_seconds():.2f} {sub.end.total_seconds():.2f}\n")
                                text_file.write(f"{seg} {text.lower()}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("srt_dir", type=str, default="/data/wienvideo/trans/srt/")
    parser.add_argument("m4a_dir", type=str, default="/data/wienvideo/m4a/")
    parser.add_argument("output_dir", type=str, default="/data/wienvideo/kaldi_data")
    args = parser.parse_args()
    main(args)
