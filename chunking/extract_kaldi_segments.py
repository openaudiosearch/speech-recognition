#!/usr/bin/env python3

# Script to extract audio chunks to separate files after chunking using Kaldi's chunking scripts

from pathlib import Path
import struct
import audioop
import struct
import wave
import logging


def read_wav(filepath, requested_sampling_rate):
    try:
        with wave.open(filepath, 'rb') as wav_file:
            num_channels, sampwidth, sampling_rate, num_samples, _, _ = wav_file.getparams()
            try:
                raw = wav_file.readframes(num_samples * num_channels)
                # Resample signal if need be
                if requested_sampling_rate is not None and requested_sampling_rate != sampling_rate:
                    raw, _ = audioop.ratecv(raw, sampwidth, num_channels, sampling_rate, requested_sampling_rate, None)
                    sampling_rate = requested_sampling_rate
                    num_samples = len(raw) // sampwidth // num_channels
                if num_channels == 2:
                    raw = audioop.tomono(raw, 2, 0.5, 0.5)
                    num_channels = 1
                raw = struct.unpack_from("%dh" % num_samples * num_channels, raw)
            except struct.error:
                # Certain programs do not set correct values in the WAVE RIFF
                # header. Therefore, we have to read all bytes in the chunk and
                # set the other fields to default values.
                raw = wav_file.readframes(-1)
                sampwidth = 2
                # Resample signal if need be
                if requested_sampling_rate is not None and requested_sampling_rate != sampling_rate:
                    raw, _ = audioop.ratecv(raw, sampwidth, num_channels, sampling_rate, requested_sampling_rate, None)
                    sampling_rate = requested_sampling_rate
                if num_channels == 2:
                    raw = audioop.tomono(raw, 2, 0.5, 0.5)
                    num_channels = 1
                num_samples = len(raw) // sampwidth // num_channels
                raw = struct.unpack_from("%dh" % num_samples * num_channels, raw)

            return (
                raw,
                sampling_rate,
                num_samples,
                num_channels
            )
    except:
        logging.warning(f"Unable to read WAV file '{filepath}'.")
        return (), 0, 0, 0



if __name__ == "__main__":
    source_dir = '/data/nationalrat27_cleaned'
    dest_dir = '/data/nationalrat27_segments'
    requested_sampling_rate = 16000

    recid_to_wav = {}
    with open(Path(source_dir).joinpath("wav.scp"), 'r', encoding="utf-8") as scp_file:
        for line in scp_file:
            line = line.rstrip("\n")
            recid, wav = line.split(maxsplit=1)
            recid_to_wav[recid] = wav

    segid_to_text = {}
    with open(Path(source_dir).joinpath("text"), 'r', encoding="utf-8") as txt_file:
        for line in txt_file:
            line = line.rstrip("\n")
            segid, text = line.split(maxsplit=1)
            segid_to_text[segid] = text

    last_recid = None
    txt_file = None
    with open(Path(source_dir).joinpath("segments"), 'r', encoding="utf-8") as seg_file, \
        open(Path(dest_dir).joinpath('metadata.csv'), 'w', encoding="utf-8") as metadata_file:
        for line in seg_file:
            line = line.rstrip("\n")
            segid, recid, start_time, end_time = line.split()
            start_time = float(start_time)
            end_time = float(end_time)
            if len(segid_to_text[segid].replace("<unk>", "").split()) < 3:
                continue
            if not last_recid == recid:
                wav_path = Path(recid_to_wav[recid])
                raw, sampling_rate, num_samples, num_channels = read_wav(str(wav_path.absolute()), requested_sampling_rate)
                last_recid = recid
            if len(raw) > 0:
                index_start = int(start_time * sampling_rate)
                index_end = int(end_time * sampling_rate)
                section_audio = raw[index_start:index_end]
                file_name = f"{int(start_time*100.0):08d}-{int(end_time*100.0):08d}.wav"
                print(f"{wav_path.stem}/{file_name}\t{segid_to_text[segid]}", file=metadata_file)
                print(f"{file_name}\t{segid_to_text[segid]}")
                Path(dest_dir).joinpath(wav_path.stem).mkdir(parents=True, exist_ok=True)
                file_path = str(Path(dest_dir) / wav_path.stem / file_name)
                with wave.open(file_path, 'w') as wav_file:
                    wav_file.setparams((1, 2, sampling_rate, num_samples, 'NONE', 'not compressed')) # pylint:no-member
                    bytes_audio = struct.pack('<%dh' % len(section_audio), *section_audio)
                    wav_file.writeframes(bytes_audio)
