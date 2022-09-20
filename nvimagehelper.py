#!/usr/bin/env python3.6
# 0.0 Globale Variablen, Ordner und Parameterverwaltung
# 0.1 Optional: Aktueller Artikel wird automatisch ermittelt. (recArticle)
# 1.  Datensammlung (scrapePostData)
# 2.  Laden des Beitragsbildes
# 3.  Bilder werden vorbereitet / bearbeitet
# 4.  Template wird angewendet
# 5.  Headline und Abstract wird geschrieben
# 6.  Socialtext wird ausgegeben.
# (...)
# 

import os
import argparse
import requests
from bs4 import BeautifulSoup

#Pyperclip ist notwendig um den socialText in die Zwischenablage zu kopieren. (Das spart ein Gtk-Fenster aus dem man den Text auch in den Zwischenspeicher kopieren würde.)
import pyperclip as pc


print('------------------------------------')
print('NV Image Helper v0.14')
print('------------------------------------')

# --
# Globale Ordner, Variablen usw.
# --
cwd = os.getcwd() # ermittelt das current working directory


tmpFolder = cwd+'/tmp/'
outFolder = cwd+'/fertig/'
templateFolder = cwd+'/template/'

#Check if die Ordner existieren und erstellt die Ordner, falls nicht vorhanden
file_exists = os.path.exists(tmpFolder)
if not file_exists:
	os.makedirs(tmpFolder)
file_exists = os.path.exists(outFolder)
if not file_exists:
	os.makedirs(outFolder)
file_exists = os.path.exists('template/insta-template.png')
if not file_exists:
	print('*** WARNUNG: Template nicht gefunden')

# ------------

lucysUrl = 'https://lucys-magazin.com/'







# --
# Parameterverarbeitung
# --



####################################################################################
# Aktueller Artikel wird in diesem Abschnitt ermittelt.
####################################################################################

def recArticle(x):
	global articleUrl #Die Variable bleibt dadurch auch außerhalb der Funktion (global) erhalten. 
	global isXtra
	r = requests.get(x)
	soup = BeautifulSoup(r.content, 'html.parser')

	# In Zukunft kann überprüft werden, ob "div > h3 > a" ein guter CSS-Selektor ist, oder ob es einen eindeutigeren Weg gibt, der sowohl Standard, als auch XTRA-Beiträge abgreift.
	recentArticle = soup.select_one("div > h3 > a")
	articleUrl = recentArticle.get('href')

	#print('\nDie ermittelte Artikel-URl:', articleUrl)
	#print(articleUrl)
	

	#Wenn der aktuelle Artikel ein XTRA-Artikel ist, dann wird die Überschrift (recentArticle) durch bs4 falsch abgegriffen ("div > h3 > a" ist uneindeutig). Die folgende If-Abfrage nimmt sich dem an.
	xtraUrl='https://lucys-magazin.com?s=lucys-xtra'
	if articleUrl == xtraUrl:
		print('- XTRA-Beitrag wurde erkannt')

		xtraArticle = soup.select_one("li.mh-custom-posts-large:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > h3:nth-child(1) > a:nth-child(2)")
		#print('xtraArticle-Tag:', xtraArticle)

		xtraArticleUrl = xtraArticle.get('href')
		print('\ndie ermittelte XTRA-URL:', xtraArticleUrl)

		#articleUrl wird entsprechend neu gesetzt.
		articleUrl = xtraArticleUrl
		#Bool-Variable um ggf.
		isXtra = True
	else: 
		print('- kein XTRA-Beitrag')
		print('\n- Die ermittelte Artikel-URl:', articleUrl)
		isXtra = False

recArticle(lucysUrl) 
#ruft die obige Funktion auf. lucysUrl wird als Parameter übergeben. D.h. in dieser URL wird nach dem aktuellen Artikel gesucht.

####################################################################################
# BS4 wird auf "articleUrl" angewendet
####################################################################################

# Hier kann der Artikel eingegeben werden, falls die automatische Erkennung übersprungen werden soll.
#articleUrl = "https://lucys-magazin.com/wolfgang-bauer-im-fliegenpilz-talk/"
#articleUrl = "https://lucys-magazin.com/drogenkultur-raum-und-rausch/"


def scrapePostData(x):
	r = requests.get(x)
	soup = BeautifulSoup(r.content, 'html.parser')
	global headline, bannerSource, absatz1clean, socialText, fileName, fileExtension, tagsClean

	h1 = soup.select_one('h1')	   # Sucht nach dem h1 Element
	headline = h1.get_text()	   # Die Überschrift (h1) ohne Tags
	absatz1 = soup.select_one('p')	   # Sucht nach dem ersten Absatz
	absatz1clean = absatz1.get_text()  # Der Absatz ohne Tags
	

	print('\n- Zeichen des Absatzes:', len(absatz1clean))
	if len(absatz1clean) < 400:
		print('Absatz zu kurz')
		absatz2clean = soup.find('p').findNext('p').get_text()
		#print('Zweiter Absatz:', absatz2clean)

	else:
		print('Absatz passt.')


	tags = soup.select("article > div > ul > li > a")
	tagsClean = ''
	for a in tags:
		tagsClean += str("#"+a.text+"")
	tagsClean = tagsClean.replace("-", "") # Minus wird entfernt
	tagsClean = tagsClean.replace(" ", "") # Alle Leerzeichen werden entfernt
	tagsClean = tagsClean.replace("#", " #") # Dem Rautesymbol wird eine Leerzeile vorangestellt 
	tagsClean = tagsClean.replace(" ", "",1) # Erste Leerzeile im String wird entfernt

	#socialText = '**' + headline + '**' + '\n\n' + absatz1clean + '\n\n' + articleUrl + '\n\n' + tagsClean

	# Je nachdem ob es sich um ein Youtube-Beitrag handelt, muss das Beitragsbild anders geladen werden. :)
	checkIfYoutube = soup.find("div", {"class": "mh-youtube-video"})
	if(checkIfYoutube is None):
		print("- kein Youtube-Beitrag\n\n")
		banner = soup.select_one("figure > a > img")	# Sucht nach der Adresse zum Beitragsbild
		bannerSource = banner.get('src')		# Adresse des Beitragsbildes ohne Tags
	else:
		print("- Es handelt sich um einen Youtube-Beitrag\n\n")
		banner = soup.find("div", {"class": "mh-youtube-video"})
		bannerSourceTags = banner.get('style')
		bannerSource = bannerSourceTags.replace("background-image: url('//", "")
		bannerSource = bannerSource.replace("');", "")
		bannerSource = "https://"+bannerSource
	# Folgende Variablen (global) werden für loadBanner() aber auch für den Output-Namen benötigt.
	fileName = bannerSource.split("/")[-1] # Splittet am /. Der Teil ganz rechts bleibt übrig (-1)
	fileExtension = bannerSource.split(".")[-1] # Splittet am Punkt. der Teil ganz rechts bleibt wieder übrig = Dateiendung


	

scrapePostData(articleUrl)





####################################################################################
# Beitragsbild wird geladen:
####################################################################################

def loadBanner():
	#print("\nBilddownload ab hier")
	#print("Filename:", fileName, "\n")
	flart = requests.get(bannerSource)
	with open(f'{tmpFolder}bilddownload.{fileExtension}','wb') as outFile:   
	#"f'tmp/bilddownload.{fileExtension}'" -> das f macht formatierung möglich, sodass statt ".jpg" "{fileExtension}" stehen kann.
	  outFile.write(flart.content)

loadBanner()

# __________________________________________________________________________________
#################################################################################### --- --- --- --- ---
# Bilderstellung mit Imagemagick (vormals ImageMagick.py)
#################################################################################### --- --- --- --- ---

from wand.image import Image, COMPOSITE_OPERATORS
from wand.drawing import Drawing
from wand.display import display
 
bildDownload = Image(filename =f'tmp/bilddownload.{fileExtension}')
 
print(bildDownload.height, bildDownload.width)
print(bildDownload)


#Das Beitragsbild vorne:
with Image(filename=f'{tmpFolder}bilddownload.jpg') as img:
    img.transform(resize='1080x') #Bildbreite auf 1080 pixel bringen
    img.save(filename =f"{tmpFolder}imgScaled1080H.png")

#Bild wird auf eine Mindesthöhe von 1080px gebracht. (Davon ausgehend, dass die Bilder immer horizontal sind, ist die breite immer >1080 wenn die höhe mindestens 1080 ist)
with Image(filename=f'{tmpFolder}bilddownload.jpg') as img3:
    img3.transform(resize='x1080') #Bildhöhe auf 1080 pixel bringen
    img3.save(filename =f"{tmpFolder}imgScaled1080V.png")


#Bild wird auf 1080x1080
with Image(filename=f'{tmpFolder}imgScaled1080V.png') as img3:
    #img3.transform(resize='x1080') #Bildhöhe auf 1080 pixel bringen
    img3.crop(0, 0, width=1080, height=1080, gravity='center')
    img3.save(filename =f"{tmpFolder}imgFrontScaled.png")
    #display(img3)

#Bild wird auf 1080x1080
with Image(filename=f'{tmpFolder}imgScaled1080V.png') as img3:
    #img3.transform(resize='x1080') #Bildhöhe auf 1080 pixel bringen
    img3.crop(0, 0, width=1080, height=1080, gravity='center')
    img3.gaussian_blur(sigma=6)
    img3.brightness_contrast(-50.0, 0.0)
    img3.save(filename =f"{tmpFolder}imgBackBlurred.png")
    #display(img3)



#Front und Back Zusammengesetzt (horizontales Bild auf verschwommenem Bild):

imgFront = Image(filename =f'{tmpFolder}imgScaled1080H.png')
imgBack = Image(filename =f'{tmpFolder}imgBackBlurred.png')

imgFrontClone = imgFront.clone()
imgBackClone = imgBack.clone()


imageCenterFront = imgFrontClone.height / 2 # Bildmitte des Frontbildes
posFrontImg = 540 - imageCenterFront # Halbe Bildmitte des Fertigen Bildes (1080/2=540) minus Bildmitte des Frontbildes ergibt den Versatz bei der Zusammensetzung (composite; top=posFrontImg)


with Drawing() as draw2:

    draw2.composite(operator = 'over', left = 0, top = posFrontImg,
                   width = imgFrontClone.width, height = imgFrontClone.height, image = imgFrontClone)
    draw2(imgBackClone)
    imgBackClone.save(filename =f"{tmpFolder}frontAndBack.png")
    #display(imgBackClone)




# ---------------------------------------------------------------------------------------
# Template wird auf das Bild gesetzt: (sollte zu funktion umgebaut werden)
# ---------------------------------------------------------------------------------------

def useTemplate(x,y):
	featuredImage = Image(filename = x)
	template = Image(filename =f'{templateFolder}insta-template.png')
	  
	featuredImageClone = featuredImage.clone()
	TemplateClone = template.clone()
	with Drawing() as draw:
	    draw.composite(operator = 'overlay', left = 0, top = 0,
		           width = featuredImageClone.width, height = featuredImageClone.height, image = featuredImageClone)
	    draw(TemplateClone)
	    TemplateClone.save(filename =tmpFolder+y)

useTemplate('tmp/frontAndBack.png', 'frontWithTemplate.png') # horizontal auf Blur
useTemplate('tmp/imgFrontScaled.png', 'frontWithTemplate2.png') # skaliertes Bild ohne Blur-Hintergrund
useTemplate('tmp/imgBackBlurred.png', 'backWithTemplate.png') # Rückseite & Template


# ---------------------------------------------------------------------------------------
# Funktion zum Textumbruch (notwendig für Beschriftung auf den Bildern)
# ---------------------------------------------------------------------------------------

from textwrap import wrap
from wand.color import Color


def word_wrap(image, ctx, text, roi_width, roi_height):
    """Break long text to multiple lines, and reduce point size
    until all text fits within a bounding box."""
    mutable_message = text
    iteration_attempts = 100

    def eval_metrics(txt):
        """Quick helper function to calculate width/height of text."""
        metrics = ctx.get_font_metrics(image, txt, True)
        return (metrics.text_width, metrics.text_height)

    while ctx.font_size > 0 and iteration_attempts:
        iteration_attempts -= 1
        width, height = eval_metrics(mutable_message)
        if height > roi_height:
            ctx.font_size -= 0.75  # Reduce pointsize
            mutable_message = text  # Restore original text
        elif width > roi_width:
            columns = len(mutable_message)
            while columns > 0:
                columns -= 1
                mutable_message = '\n'.join(wrap(mutable_message, columns))
                wrapped_width, _ = eval_metrics(mutable_message)
                if wrapped_width <= roi_width:
                    break
            if columns < 1:
                ctx.font_size -= 0.75  # Reduce pointsize
                mutable_message = text  # Restore original text
        else:
            break
    if iteration_attempts < 1:
        raise RuntimeError("Unable to calculate word_wrap for " + text)
    return mutable_message


# ---------------------------------------------------------------------------------------
# Seite 1 wird verarbeitet.
# ---------------------------------------------------------------------------------------
#Headline zum Debuging
#headline = 'Dies ist eine Überschrift und sie ist sehr lang'







def writeHeadline(input, caption, prefix):
  print('- Bild 1: Überschrift wird auf Bild:', prefix, 'geschrieben.')
  saveName = headline.replace(" ", "")
  
  captionColor = '#fff'
  shadowColor = '#000'
  geoHeadlineX = 80
  geoHeadlineY = 100
  widthBlock = 640
  #Schatten wird automatisch den oberen Werten angeglichen:
  geoShadowX = geoHeadlineX + 3
  geoShadowY = geoHeadlineY + 3
  saveName = caption.replace(" ", "")
  with Image(filename=input) as img:
      with Drawing() as ctx:
          ctx.font = 'FreeSans-Fett'
          ctx.fill_color = shadowColor
  
          ctx.font_size = 50
          mutable_message = word_wrap(img,
                                      ctx,
                                      caption,
                                      widthBlock,
                                      widthBlock)
          ctx.text(geoShadowX, geoShadowY, mutable_message)
          ctx.fill_color = captionColor
          ctx.text(geoHeadlineX, geoHeadlineY, mutable_message)
          ctx.draw(img)
          img.save(filename=f'{outFolder}{prefix}_{saveName}.png')
	  #Zeigt das erstellte Bild direkt an:
          #display(img)	

writeHeadline('tmp/frontWithTemplate.png', headline, 'p1a')
writeHeadline('tmp/frontWithTemplate2.png', headline, 'p2a')



# ---------------------------------------------------------------------------------------
# Seite 2
# ---------------------------------------------------------------------------------------
# Paragraph zum Debuging
#paragraph = "»TEST 123«"






def writeAbstract(input, caption):
  print('- Bild 2 wird erzeugt')
  saveName = headline.replace(" ", "")
  
  geoTextboxX = 540 ## (=1080 / 2)
  geoTextboxY = 100
  xBlock = 950
  yBlock = 900
  with Image(filename=input) as img:
      with Drawing() as ctx:
          captionColor = '#fff'
          ctx.font = 'FreeSans-Fett'
          ctx.text_alignment = 'center'
          #ctx.fill_color = shadowColor

          ctx.font_size = 45
          mutable_message = word_wrap(img,
                                      ctx,
                                      caption,
                                      xBlock,
                                      yBlock)
          #ctx.text(geoShadowX, geoShadowY, mutable_message)
          ctx.fill_color = captionColor
          ctx.text(geoTextboxX, geoTextboxY, mutable_message)
          ctx.draw(img)
          img.save(filename=f'{outFolder}p2_{saveName}.png')
	  #Zeigt das erstellte Bild direkt an:
          display(img)


paragraph = absatz1clean

abstract = "«" + paragraph + " \n\n\n(...)» "

writeAbstract('tmp/backWithTemplate.png', abstract)



# ---------------------------------------------------------------------------------------
# Social-Text
# ---------------------------------------------------------------------------------------

def showSocialText():

   socialText = '**' + headline + '**' + '\n\n' + absatz1clean + '\n\n' + articleUrl + '\n\n' + tagsClean
   print('##############################################################################')
   print('\nDer folgende Text wurde in die Zwischenablage kopiert:\n\n', socialText)
   a1 = socialText
   pc.copy(a1)

showSocialText()




#####################################################################################################################
