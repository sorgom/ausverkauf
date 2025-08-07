# ausverkauf
A simple Python Website builder

## source syntax
- headings like markup
- images !(image name)
- paragraphs: any text -> 
- bold: **bold** -> <b></b>
- italic _ita _ licü._.wumpel -> <i></i>


## folders
### repo
    - html template with place holders
    - #TITLE
    - #BODYCLASS
    - #CONTENT
### source
- source: content.txt
- imprint
- images
### site
- css file (to be stored)
- html files (generated)
- img: images resized


# generated HTML
## overview
must show
- title
- description
- categories
    - title
    - gain / loss since last update
- gen script must have -r release option
    - show difference from last update
        - date time last
        - date time now


## source syntax sample
```
# Alles muss raus
Wohnungsauflösung in Krefeld
Tel. 0172 399 35 36

@ elektro: Elektrogeräte
# kuehlschrank: Kühlschrank Beko
Zustand: Top

@ moebel: Möbel
# schrankwand: Schrankwandsystem 
Top Zustand
Insgesamt 10 Elemente:
- 7 X Schubladen und Türe
- 3 X Zweitürer
B/H/T 250 190 60
*VB 200,-*

# coutch_rot: Couch rot Vintage
ca. 1950
Zustand:
- Polsterung immer noch gut
- Klappsystem-Verschraubung überholungsbedürftig
*VB 50,-* 
```
## data model
```
categories = [
    ('elektro', 'Elektrogeräte')
]
items = {
    elektro : [
        ('schrankwand', 'Schrankwandsystem', )
    ]
}

```