#!/usr/bin/env python3
# coding=utf-8
# Copyright 2020 Ewald Enzinger

import argparse
import os
from pathlib import Path
from xml.etree.ElementTree import XML
import zipfile


def get_docx_text(path: os.PathLike) -> list:
    """Extract raw text from docx file"""
    WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    PARA = WORD_NAMESPACE + 'p'
    TEXT = WORD_NAMESPACE + 't'
    paragraphs = []
    with zipfile.ZipFile(path) as document:
        xml_content = document.read('word/document.xml')
        tree = XML(xml_content)
        for paragraph in tree.iter(PARA):
            texts = [node.text.replace("\n", " ")
                     for node in paragraph.iter(TEXT)
                     if node.text]
            if texts:
                paragraphs.append(''.join(texts))

    return paragraphs


def main(args):
    for docx_path in Path(args.transcript_dir).glob("*.docx"):
        paragraphs = get_docx_text(docx_path)
        #with open(Path(args.output_dir) / (docx_path.stem + ".txt"), 'w', encoding='utf-8') as text_file:
        #    text_file.write("\n".join(paragraphs))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript_dir", type=str)
    parser.add_argument("output_dir", type=str)
    args = parser.parse_args()
    main(args)
