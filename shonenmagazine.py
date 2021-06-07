# Original script by drdaxxy
# https://gist.github.com/drdaxxy/1e43b3aee3e08a5898f61a45b96e4cb4

import sys
import os
import requests
import errno
from PIL import Image
from googletrans import Translator
import re

translator = Translator(service_urls=['translate.googleapis.com'])
if len(sys.argv) != 3:
    print("usage: shonenripperjson.py <url> <destination folder>")
    sys.exit(1)


destination = sys.argv[2]
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}

def make_destination(destination):
    if not os.path.exists(destination):
        try:
            os.makedirs(destination)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

def dlImage(url, outFilename, drm):
    r = requests.get(url, stream=True, headers=headers)
    if not r.ok:
        print(r)
        return

    content_type = r.headers.get('content-type')
    if content_type == "image/jpeg":
        outFilename = outFilename + ".jpg"
    elif content_type == "image/png":
        outFilename = outFilename + ".png"
    else:
        print("content type not recognized!")
        print(r)
        return

    with open(outFilename, 'wb') as file:
        for block in r.iter_content(1024):
            if not block:
                break
            file.write(block)

    if drm == True:
        source = Image.open(outFilename)
        dest = Image.new(source.mode, source.size)

        def draw_subimage(sx, sy, sWidth, sHeight, dx, dy):
            rect = source.crop((sx, sy, sx+sWidth, sy+sHeight))
            dest.paste(rect, (dx, dy, dx+sWidth, dy+sHeight))

        DIVIDE_NUM = 4
        MULTIPLE = 8
        cell_width = (source.width // (DIVIDE_NUM * MULTIPLE)) * MULTIPLE
        cell_height = (source.height // (DIVIDE_NUM * MULTIPLE)) * MULTIPLE
        for e in range(0, DIVIDE_NUM * DIVIDE_NUM):
            t = e // DIVIDE_NUM * cell_height
            n = e % DIVIDE_NUM * cell_width
            r = e // DIVIDE_NUM
            i_ = e % DIVIDE_NUM
            u = i_ * DIVIDE_NUM + r
            s = u % DIVIDE_NUM * cell_width
            c = (u // DIVIDE_NUM) * cell_height
            draw_subimage(n, t, cell_width, cell_height, s, c)

        dest.save(outFilename)

url = sys.argv[1]

def downloader():
    global url
    global destination
    if not url.endswith('.json'):
        url = url + ".json"

    print("Getting from url: "+url)
    r = requests.get(url=url, headers=headers)

    data = r.json()
    title = data['readableProduct']['title']
    title = fr"{translator.translate(title, dest='en', src='ja').text} - {title}"
    title = title.replace(r'"', r'⸤')
    title = title.replace("/", "")
    title = re.sub('|\|\/|:|\*|\?|"|<|>|\|', '', title)
    print(title)
    # input()
    parent = os.path.abspath(os.path.join(destination, os.pardir))
    destination = os.path.join(parent, title)
    make_destination(destination)

    def download_next():
        global destination
        global url
        # new_dir_name = input("New dir: ")
        url = nextReadableProductUri
        # make_destination(destination)
        downloader()

    if 'readableProduct' in data:
        readableProduct = data['readableProduct']
        nextReadableProductUri = None

        if 'nextReadableProductUri' in readableProduct:
            nextReadableProductUri = readableProduct['nextReadableProductUri']

        if 'pageStructure' in readableProduct:
            pageStructure = readableProduct['pageStructure']

            if pageStructure == None:
                print('Could not download pages. Most likely this volume is not public.')
                if nextReadableProductUri is not None:
                    download_next()
                else:
                    print(url, "was the last to be downloaded")
                    return
            choJuGiga = pageStructure['choJuGiga'] if 'choJuGiga' in pageStructure else ''

            print('choJuGiga: ', choJuGiga)

            drm = choJuGiga != "usagi"

            pages = pageStructure['pages'] if 'pages' in pageStructure else []

            if len(pages) == 0:
                print("No pages found")
                sys.exit(1)

            pageIndex = 0

            for page in pages:
                if 'src' in page:
                    src = page['src']
                    print(src)
                    pageIndex += 1
                    outFile = os.path.join(destination, f"{pageIndex:04d}")
                    dlImage(src, outFile, drm)

        else:
            print('could not find pageStructure from json response')
            sys.exit(1)

        if nextReadableProductUri != None:
            print("Next URI: ", nextReadableProductUri)
            download_next()
    else:
        print('could not find readableProduct from json response')

downloader()