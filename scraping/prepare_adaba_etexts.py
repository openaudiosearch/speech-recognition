#!/usr/bin/env python3

# This script imports Adaba "etexts" data

import xml.etree.ElementTree as ET
import struct
import wave
import audioop
import csv
from pathlib import Path
import logging


logger = logging.Logger("prepare_adaba", logging.INFO)

def main():
    # Input folder
    input_dir = r'/data/adaba/etexts/'
    # Output metadata
    metadata_path = r'/data/adaba/metadata.csv'
    # Output folder
    output_dir = r'/data/adaba/wav/'
    # Requested sampling rate
    requested_sampling_rate = 22050

    with open(metadata_path, 'a', encoding='utf-8', newline='') as metadata_file:
        tsv_writer = csv.writer(metadata_file, delimiter='\t')
        tsv_writer.writerow(['PATH', 'DURATION', 'SPEAKERID', 'TRANSCRIPT'])

        for metadata_path in Path(input_dir).rglob('*AT*.eaf'):
            wav_path = Path(metadata_path.parent).joinpath(metadata_path.stem[4:] + ".wav")
            if wav_path.exists() and not Path(output_dir).joinpath(metadata_path.stem).exists():
                # Read audio file contents
                raw, sampling_rate, num_samples, num_channels = read_wav(str(wav_path.absolute()), requested_sampling_rate)
                if len(raw) > 0:
                    print(metadata_path.name)
                    speaker_id = metadata_path.stem[4:]
                    if num_channels > 1:
                        print(f"File {wav_path.name} has more than one channel!")
                    # Separate the two channels
                    #ch_A = raw[0::num_channels]
                    # Create directory, e.g. "p012_spontan"
                    try:
                        # Read metadata file contents
                        tree = ET.parse(str(metadata_path))
                    except:
                        print(f"Metadata file for {metadata_path.name} is invalid!")
                        continue
                    Path(output_dir).joinpath(metadata_path.stem).mkdir(parents=True, exist_ok=True)
                    sampling_rate = requested_sampling_rate
                    root = tree.getroot()
                    timeslots = {}
                    for ts in root.find('TIME_ORDER').findall('TIME_SLOT'):
                        timeslots[ts.get('TIME_SLOT_ID')] = int(ts.get('TIME_VALUE'))
                    print(f"Timeslots: {len(timeslots)}")
                    for a in root.find('TIER').findall('ANNOTATION'):
                        annotation = a.find('ALIGNABLE_ANNOTATION')
                        start_time = timeslots[annotation.get('TIME_SLOT_REF1')] / 1000.0
                        end_time = timeslots[annotation.get('TIME_SLOT_REF2')] / 1000.0
                        transcript = annotation.find('ANNOTATION_VALUE').text
                        if transcript is not None:
                            transcript = transcript.replace("\n", "")
                            duration =  end_time - start_time
                            file_name = f"{int(start_time * 100):06d}-{int(end_time * 100):06d}.wav"
                            # Get start and end time as audio sample indices
                            index_start = int(start_time * sampling_rate)
                            index_end = int(end_time * sampling_rate)
                            section_audio = raw[index_start:index_end]
                            file_path = str(Path(output_dir) / metadata_path.stem / file_name)
                            with wave.open(file_path, 'w') as wav_file:
                                wav_file.setparams((1, 2, sampling_rate, num_samples, 'NONE', 'not compressed')) # pylint:no-member
                                bytes_audio = struct.pack('<%dh' % len(section_audio), *section_audio)
                                wav_file.writeframes(bytes_audio)
                            tsv_writer.writerow([file_path, f"{duration:.2f}", speaker_id, transcript])


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
        logger.warning(f"Unable to read WAV file '{filepath}'.")
        return (), 0, 0, 0


if __name__ == "__main__":
    main()
