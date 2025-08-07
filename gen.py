from os import listdir, makedirs, chdir
from os.path import isfile, join, exists, dirname, basename
import re
from glob import glob
from html import escape as esc

class Gen(object):
    def __init__(self):
        chdir(dirname(__file__))
        with open('template.html') as fh:
            self.template = fh.read()
            fh.close()

    def mkHtml(self, trg, ttl, bodyClass, content):
        with open(f'site/{trg}.html', 'w') as fh:
            fh.write(self.template.replace('#TITLE', ttl).replace('#BODYCLASS', bodyClass).replace('#CONTENT', content))
            fh.close()

    def scanImages(self):
        chdir('site')
        self.images = {}
        rx = re.compile(r'^(.*)_[^_.]*?\.')
        for file in glob('img/*'):
            mo = rx.search(basename(file))
            if not mo: continue
            item = mo.group(1)
            self.images.setdefault(item, []).append(file)
        chdir('..')

    @staticmethod
    def splitEx(txt, rCatch, rSplit):
        heads = re.findall(rCatch, txt, flags=re.M)
        conts = [t.strip() for t in re.split(rSplit, txt, flags=re.M)]
        rem = conts.pop(0)
        return heads, conts, rem
    
    @staticmethod
    def clean(txt:str):
        return re.sub(r'^ *| *$', '', txt.strip().replace("\t", ' '), flags=re.M)  

    @staticmethod
    def para(txt:str):
        pass
        # return re.sub()


    def parseContent(self):
        self.cats = []
        with open('content.txt', 'r', encoding='utf-8') as fh:
            #   separate into categories and chapters
            cats, conts, head = Gen.splitEx(esc(Gen.clean(fh.read())), r'^[@] *(\w+) *: *(.*)\n', r'^[@].*\n')
            fh.close()
        for cont in conts:
            heads, items, _ = Gen.splitEx(cont, r'^# *(\w+) *: *(.*)\n', r'^#.*\n')
            print(heads, items, sep='\n\n')

if __name__ == "__main__":
    gen = Gen()
    gen.mkHtml('wumpel', 'Wumpel', 'test', 'hello World')
    gen.scanImages()
    gen.parseContent()
