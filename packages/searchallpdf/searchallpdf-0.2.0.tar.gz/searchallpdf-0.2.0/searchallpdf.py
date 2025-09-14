#!/usr/bin/env python3
# -*coding: utf-8 -*

# Gery Casiez
# 2021 - 2025

import re
import argparse
import os
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def cleantext(text):
    return text.replace("´e", "é").replace("`e", "è").replace("ˆe", "ê").\
            replace("`a", "à").replace("ˆı", "î").replace("-\n", "").\
            replace("\n", " ").replace("¨e", "ë")

def searchInFile(file, searchterms):
    pdf_document = fitz.open(file)

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text = page.get_text()

        # OCR
        if not(text.strip()):
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)

        found = False
        for word in searchterms:
            text = cleantext(text)
            ResSearch = re.search(word.lower(), text.lower())
            found = found or bool(ResSearch)
        if found:
            print("Page %s"%(page_num + 1))
            s = text
            for word in searchterms:
                parts = re.split(word, s, flags=re.IGNORECASE)
                s2 = "\033[45;30m%s\033[m"%word
                s = s2.join(parts)
            print(s)
            print() 

def main():
    parser = argparse.ArgumentParser(description='searchallpdf')
    parser.add_argument('-f', help = 'pdf file. Search in all pdf in current and subfolders if option not defined.')
    parser.add_argument('terms', help='list of search terms', nargs='*')
    args = parser.parse_args()

    if args.f == None:
        for path, _, files in os.walk('.'):
            for name in files:
                f = os.path.join(path, name)
                if f[-4:] == '.pdf':
                    print("> %s"%f)
                    searchInFile(f, args.terms)
    else:
        if args.f[-4:] == '.pdf':
            searchInFile(args.f, args.terms)


if __name__ == "__main__":
    main()