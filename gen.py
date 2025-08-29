"""
Generiere Verkaufs-Website

Aufruf: this script [Optionen]
Optionen:
    -m  <pixel> generiere Bilder mit maximaler Bildausdehnung
        Default: 1000
    -M  <megapixel> generiere Bilder mit Bildgröße in Megapixel
    -q  <image quality>
        recommended: 25 .. 75
        default: 50
    -r  alte Bilder löschen
    -h  diese Hilfe
"""
from os import makedirs, chdir, remove
from os.path import dirname, isdir, exists, getmtime
import re, json
from glob import glob
from html import escape as esc
# from datetime import datetime
from PIL import Image, ExifTags
from math import sqrt

import locale
locale.setlocale(locale.LC_ALL, 'de_DE')

class Data(object):
    def __init__(self, id, title, content, para=True):
        self.id = id
        self.title = title
        self.content = self.para(content) if para else content
        self.imgs = []

    @staticmethod
    def sub(rx, repl, txt:str):
        return re.sub(rx, repl, txt, flags=re.M)    
    
    @staticmethod
    def para(txt:str):
        return Data.sub(r'^', '<p>', Data.sub(r'$', '</p>', re.sub(r'\*(\S.*?\S)\*', r'<b>\1</b>', txt.strip())))
    
    def __str__(self):
        return '\n'.join([self.id, self.title, self.content, ', '.join(self.imgs)])

class Gen(object):
    def __init__(self, imgSize=None, imgMP=None, quality=None, rm=False):
        self.dir = dirname(__file__)
        self.back()
        with open('template.html') as fh:
            self.template = fh.read()
            fh.close()
        self.statsFile = 'stats.json'
        self.imprint = 'Kein Impressum vorhanden.'
        self.imgSize = int(imgSize) if imgSize else None
        self.imgPix  = float(imgMP) if imgMP else None
        self.quality = int(quality) if quality else 50
        self.imgAuto = False
        self.imgFile = 'img.json'
        self.isDir = 'img'
        self.itDir = 'site/img'
        if not isdir(self.isDir):
            self.imgSize = None
            self.imgPix  = None
        elif not isdir(self.itDir): makedirs(self.itDir)
        if rm: self.rmImages()

        self.articles = self.tokenizeF('articles.txt')
        self.categories = self.tokenizeF('categories.txt', False)
        for d in self.categories: d.content = d.content.split()
        self.rxImg = re.compile(r'\b(' + '|'.join([d.id for d in self.articles]) + r')_\d{1,2}\.\w+')

        cont = self.tokenizeF('formal.txt')
        tMap = self.tokens2dict(self.tokenizeF('formal.txt'))
        title, txt = tMap['imprint']
        self.mkHtml('impressum', title, [txt])
        _, txt = tMap['heading']
        self.template = self.template.replace('#DESC', txt)
        self.title, self.intro = tMap['intro']

    def assignImages(self):
        iMap = { a.id : a for a in self.articles }
        for (id, img) in self.imgList('site'):
            iMap[id].imgs.append(self.img(img))
        self.articles = [d for d in self.articles if d.imgs]
        self.aMap = { a.id : a for a in self.articles }
        for c in self.categories:
            c.content = [id for id in c.content if self.aMap.get(id)]
        self.categories = [c for c in self.categories if c.content]

    def genTemplateIndex(self):
        index = [self.link('index', 'Start')]
        for c in self.categories:
            index.append(self.link(c.id, c.title))
        index.append(self.link('impressum', 'Impressum'))
        self.template = self.template.replace('#INDEX', ' '.join(index))

    @staticmethod
    def articleLink(a:Data):
        return (
            f'<a href={a.id}.html>',
            f'<h2>{a.title}</h2>',
            a.imgs[0],
            '</a>'
        )


    def genIndex(self):
        cont = [self.intro]
        for a in self.articles:
            cont.extend(self.articleLink(a))
        self.mkHtml('index', self.title, cont)

    def genCategories(self):
        for c in self.categories:
            cont = []
            for id in c.content:
                cont.extend(self.articleLink(self.aMap[id]))
            self.mkHtml(c.id, c.title, cont)

    def genArticles(self):
        for a in self.articles:
            self.mkHtml(a.id, a.title, [a.content, *a.imgs])

    def mkHtml(self, trg, ttl, content):
        with open(f'site/{trg}.html', 'w') as fh:
            fh.write(self.template.replace('#TITLE', ttl).replace('#CONTENT', '\n'.join(content)))
            fh.close()

    def back(self):
        chdir(self.dir)


    def imgList(self, dir=None):
        if dir: chdir(dir)
        res = []
        for f in glob('img/*'):
            mo = self.rxImg.search(f)
            if mo:
                res.append((mo.group(1), f))
        self.back()
        return res

    @staticmethod
    def rmImages():
        for f in glob('site/img/*'): remove(f)

    @staticmethod
    def rmHtml():
        for f in glob('site/*.html'): remove(f)

    @staticmethod
    def exifRotate(img):
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

    def genImagesSize(self):
        print('gen images -m', self.imgSize, '-q', self.quality)
        for _, src in self.imgList():
            trg = self.imgTrg(src)
            if not trg: continue
            try:
                with Image.open(src) as img:
                    img = self.exifRotate(img)
                    img.thumbnail((self.imgSize, self.imgSize))
                    img.save(trg, quality=self.quality)
                    print('->', src)
            except Exception as e:
                print(f'failed: {src} ({e})')
        self.saveImgRun('size', self.imgSize, self.quality)

    def genImagesPix(self):
        print('gen images -M', self.imgPix, '-q', self.quality)
        pix = self.imgPix * 1000000
        for _, src in self.imgList():
            trg = self.imgTrg(src)
            if not trg: continue
            try:
                with Image.open(src) as img:
                    img = self.exifRotate(img)
                    w = img.width
                    h = img.height
                    r =  sqrt(pix / (w * h))
                    nw = int(r * w + 0.5)
                    nh = int(r * h + 0.5)
                    ni = img.resize((nw, nh))
                    ni.save(trg, quality=self.quality)
                    print('->', src)
            except Exception as e:
                print(f'failed: {src} ({e})')
        self.saveImgRun('pix', self.imgPix, self.quality)

    def genImagesAuto(self):
        if exists(self.imgFile):
            with open(self.imgFile, 'r') as fh:
                data = json.load(fh)
                self.quality = data['quality']
                self.imgAuto = True
                if data['type'] == 'pix':
                    self.imgPix = data['value']
                    self.genImagesPix()
                elif data['type'] == 'size':
                    self.imgSize = data['value']
                    self.genImagesSize()

    def imgTrg(self, src):
        trg = f'site/{src}'
        if self.imgAuto and exists(trg) and getmtime(trg) > getmtime(src):
            return None
        return trg 

    def saveImgRun(self, type:str, value:int, quality:int):
        with open(self.imgFile, 'w') as fh:
            data = { 'type': type, 'value': value, 'quality': quality}
            json.dump(data, fh)
    
    @staticmethod
    def tokenize(txt:str, para=True):
        rxF = re.compile(r'^# *(\w+) *: *(.*)\n+', re.M)
        rxS = re.compile(r'^# *\w+ *: *.*\n+', re.M)
        rxC = re.compile(r'^ *| *$', re.M)
        txt = esc(rxC.sub('', txt.strip().replace("\t", ' ')))
        heads = rxF.findall(txt)
        conts = [t.strip() for t in rxS.split(txt)]
        rem = conts.pop(0)
        res = []
        for n, (id, title) in enumerate(heads):
            res.append(Data(id, title, conts[n], para=para))
        return res
    
    @staticmethod
    def tokenizeF(file, para=True):
        with open(file, 'r') as fh:
            return Gen.tokenize(fh.read(), para=para)

    @staticmethod
    def tokens2dict(tokens:list):
        return { d.id: (d.title, d.content) for d in tokens }

    @staticmethod
    def img(src):
        return f'<img src={src.replace('\\', '/')}>'
    
    @staticmethod
    def link(name, desc):
        return f'<a href={name}.html>{desc}</a>'
    
    def run(self):
        if self.imgSize: self.genImagesSize()
        elif self.imgPix: self.genImagesPix()
        else: self.genImagesAuto()
        self.rmHtml()
        self.assignImages()
        self.genTemplateIndex()
        self.genIndex()
        self.genCategories()
        self.genArticles()

if __name__ == "__main__":
    import sompy
    from docopts import docopts
    opts, args = docopts(__doc__)
    Gen(
        imgSize = opts.get('m'),
        imgMP   = opts.get('M'),
        quality = opts.get('q'),
        rm      = opts.get('r')
    ).run()
