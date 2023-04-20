import argparse
import json
import os
import re
import requests
import sys
import tempfile
import time
from PIL import Image
from reportlab.lib.pagesizes import portrait
from reportlab.pdfgen.canvas import Canvas

VERSION = '1.0'
NAME_OF_PROGRAM = 'resumeio2pdf'
COPY = 'Copyright (c) 2023, Kabirou ALASSANE <kabirou2001@gmail.com>'
COPY_URL = 'https://github.com/BlakvGhost/resumeio2pdf/'

RESUME_PAGE = 'https://resume.io/r/{}'
RESUME_META = 'https://ssr.resume.tools/meta/ssid-{}?cache={}'
RESUME_EXT = 'png' # png, jpeg
RESUME_IMG = 'https://ssr.resume.tools/to-image/ssid-{}-{}.{}?cache={}&size={}'
RESUME_SIZE = 1800
TIMEOUT = 60

EXIT_CODE_MISUSE_ARGS = 2

RE_SID = re.compile('^[a-zA-Z0-9]+$')
RE_ID = re.compile('^\d+$')
RE_URL = re.compile('^https://resume\.io/r/([a-zA-Z0-9]+)')
RE_ID_URL = re.compile('^https://resume\.io/(?:app|api)/.*?/(\d+)')

def main():
    parser = argparse.ArgumentParser(description='Convert a resume on resume.io to a PDF file')
    parser.add_argument('-url', metavar='URL', help='Link to resume of the format: https://resume.io/r/SecureID')
    parser.add_argument('-sid', metavar='SecureID', help='SecureID of resume')
    parser.add_argument('-version', action='store_true', help='Show version')
    parser.add_argument('-verbose', action='store_true', help='Show detail information')
    parser.add_argument('-y', action='store_true', help='Overwrite PDF file')
    parser.add_argument('-pdf', metavar='PDF', help='Name of PDF file (default: SecureID + .pdf)')

    args = parser.parse_args()

    if args.version:
        print(f'{NAME_OF_PROGRAM} version {VERSION}')
        sys.exit(0)

    if not args.sid:
        parser.print_help()
        sys.exit(EXIT_CODE_MISUSE_ARGS)

    print(f'SecureID: {args.sid}')
    print(f'URL: {args.url}')
    print(f'PDF: {args.pdf}')

    meta, err = get_meta(args.sid)
    if err:
        sys.exit(err)

    images, err = get_resume_images(args.sid, len(meta['pages']))
    if err:
        sys.exit(err)

    pdf_file_name = args.pdf if args.pdf else f'{args.sid}.pdf'
    err = generate_pdf(meta, images, pdf_file_name)
    if err:
        sys.exit(err)

    cleanup(images)

    print(f'Resume stored to {pdf_file_name}')

def cleanup(images):
    for image in images:
        if os.path.exists(image):
            #os.remove(image)
            #print(f'Image {image} successfully deleted.')
            pass

def generate_pdf(info, images, pdf_file_name):
    c = Canvas(pdf_file_name, pagesize=portrait(info['pages'][0]['viewport']))
    print('Start Generate PDF')
    for i, image in enumerate(images):
        print(f'Add page #{i+1}')
        img = Image.open(image)
        c.setPageSize(portrait(info['pages'][i]['viewport']))
        c.drawImage(image, 0, 0, width=info['pages'][i]['viewport'].get('width'), height=info['pages'][i]['viewport'].get('height'))
        c.showPage()
        print(f'Page #{i+1} added')
        c.setFont('Helvetica', 10)
        c.drawString(50, 30, f'Page {i+1} of {len(images)}')
    c.save()
    return None

def get_meta(sid):
    """Get meta information about resume."""
    print('Get meta information')
    url = RESUME_META.format(sid, int(time.time()))
    r = requests.get(url, timeout=TIMEOUT)
    if r.status_code != 200:
        return None, f'Error getting meta information: {r.status_code}'
    return json.loads(r.content), None

def get_resume_images(sid, page_count):
    """Get screenshot images of each resume page."""
    print('Get resume images')
    images = []
    for i in range(1, page_count+1):
        url = RESUME_IMG.format(sid, i, RESUME_EXT, int(time.time()), RESUME_SIZE)
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, f'Error getting image {i}: {r.status_code}'
        _, temp_path = tempfile.mkstemp(suffix=f'.{RESUME_EXT}')
        with open(temp_path, 'wb') as f:
            f.write(r.content)
        images.append(temp_path)
    return images, None

if __name__ == '__main__':
    main()
