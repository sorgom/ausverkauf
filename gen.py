"""
Generiere Verkaufs-Website

Aufruf: this script [Optionen]
Optionen:
    -a Statistic aktualisieren
    -G  <pixel> maximale Bildgröße
        Default: 1000
    -B  generiere Bilder ne

"""
from os import makedirs, chdir
from os.path import exists, dirname, basename, isdir
import json, re
from glob import glob
from html import escape as esc
from datetime import datetime
from PIL import Image, ExifTags

import locale
locale.setlocale(locale.LC_ALL, 'de_DE')

class Gen(object):
    def __init__(self, imgSize=1000, genImgs=False, genStats=False):
        chdir(dirname(__file__))
        with open('template.html') as fh:
            self.template = fh.read()
            fh.close()
        self.statsFile = 'stats.json'
        self.imprint = 'Kein Impressum vorhanden.'
        self.imgSize = imgSize
        self.genImgs = genImgs
        self.genStats = genStats

    def mkHtml(self, trg, ttl, bodyClass, content):
        with open(f'site/{trg}.html', 'w') as fh:
            fh.write(self.template.replace('#TITLE', ttl).replace('#BODYCLASS', bodyClass).replace('#CONTENT', '\n'.join(content)))
            fh.close()

    @staticmethod
    def auto_rotate(img):
        try:
            exif = img._getexif()
            if exif:
                orientation_key = next(k for k, v in ExifTags.TAGS.items() if v == 'Orientation')
                orientation = exif.get(orientation_key, None)

                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except Exception as e:
            print(f"EXIF rotation skipped: {e}")
        return img

    def genImages(self):
        sDir = 'img'
        tDir = 'site/img'
        if not isdir(sDir): return
        if not isdir(tDir): makedirs(tDir)
        for file in glob(f'{sDir}/*'):
            try:
                with Image.open(file) as img:
                    img = self.auto_rotate(img)
                    img.thumbnail((self.imgSize, self.imgSize))
                    img.save(f'site/{file}')
                    print('->', file)
            except Exception as e:
                print(f'failed: {file} ({e})')
         
    def scanImages(self):
        chdir('site')
        self.images = {}
        rx = re.compile(r'^(.*)_[^_.]*?\.')
        for file in glob('img/*'):
            mo = rx.search(basename(file))
            if not mo: continue
            self.images.setdefault(mo.group(1), []).append(self.img(file))
        chdir('..')

    @staticmethod
    def splitEx(txt, rCatch:str):
        rSplit = rCatch.replace('(', '').replace(')', '')
        heads = re.findall(rCatch, txt, flags=re.M)
        conts = [t.strip() for t in re.split(rSplit, txt, flags=re.M)]
        rem = conts.pop(0)
        return heads, conts, rem
    
    @staticmethod
    def sub(rx, repl, txt:str):
        return re.sub(rx, repl, txt, flags=re.M)    
    
    @staticmethod
    def clean(txt:str):
        return Gen.sub(r'^ *| *$', '', txt.strip().replace("\t", ' '))  

    @staticmethod
    def para(txt:str):
        return Gen.sub(r'^', '<p>', Gen.sub(r'$', '</p>', re.sub(r'\*(\S.*?\S)\*', r'<b>\1</b>', txt.strip())))

    @staticmethod
    def img(src):
        return f'<img src={src}>'
    
    @staticmethod
    def link(name, desc):
        return f'<a href={name}.html>[ {desc} ]</a>'
    
    def parseContent(self):
        with open('content.txt', 'r') as fh:
            #   separate into categories and chapters
            txt = Gen.clean(fh.read())
            rxImp = re.compile(r'^>{3,}\n(.*)', re.M | re.S)
            mo = rxImp.search(txt)
            if mo:
                self.imprint = mo.group(1)
                txt = rxImp.sub('', txt)
            self.cats, conts, head = Gen.splitEx(esc(txt), r'^[@] *(\w+) *: *(.*)\n')
            a, b, _ = Gen.splitEx(head, r'^# *(.*)')
            self.head, self.desc = (a.pop(0), Gen.para(b.pop(0)))
            fh.close()
        self.chaps = {}
        for n, cont in enumerate(conts):
            heads, descs, _ = Gen.splitEx(cont, r'^# *(\w+) *: *(.*)\n')
            items = []
            for m, [item, name] in enumerate(heads):
                if self.images.get(item):
                    items.append([item, name, Gen.para(descs[m])])
            if len(items) > 0: 
                self.chaps[self.cats[n][0]] = items
        index = [self.link('index', 'Start')]
        for cat, name in self.cats:
            if self.chaps.get(cat):
                index.append(self.link(cat, name))
        index.append(self.link('impressum', 'Impressum'))
        self.template = self.template.replace('#DESC', self.desc).replace('#INDEX', ' '.join(index))

    def genIndex(self):
        stats = {}
        if exists(self.statsFile):
            with open(self.statsFile) as fh:
                stats = json.load(fh)
            fh.close()
        cont = [f'<p>Letzte Aktualisierung: {datetime.now().strftime("%A, %d. %B %Y")}</p>', '<ul>']
        nStats = {}
        for cat, name in self.cats:
            num = len(self.chaps.get(cat, []))
            nStats[cat] = num
            cdif = ''
            last = stats.get(cat)
            if last is not None and num != last:
                cdif = f' ({num - last:+d})'
            desc = f'{name}: {num}{cdif}'
            cont.append(f'<li><a href={cat}.html>{desc}</a></li>')
        cont.append('</ul>')
        self.mkHtml('index', self.head, 'index', cont)
        if self.genStats:
            with open(self.statsFile, 'w') as fh:
                json.dump(nStats, fh)
                fh.close()

    def genChapters(self):
        for cat, ttl in self.cats:
            items = self.chaps.get(cat)
            if not items: continue
            cont = []
            for item, name, desc in items:
                imgs = self.images.get(item)
                if not imgs: continue
                cont.append(f'<a href={item}.html>')
                cont.append(f'<h2>{name}</h2>')
                cont.append(imgs[0])
                cont.append('</a>')
                self.mkHtml(item, name, 'object', [desc, *imgs])     

            self.mkHtml(cat, ttl, 'category', cont)

    def genImprint(self):
        self.mkHtml('impressum', 'Impressum', 'imprint', [self.para(self.imprint)])

    def run(self):
        if self.genImgs: self.genImages()
        self.scanImages()
        self.parseContent()
        self.genIndex()
        self.genChapters()
        self.genImprint()

if __name__ == "__main__":
    import sompy
    from docopts import docopts
    gen = Gen()
    gen.run()
    # gen.genImages()
