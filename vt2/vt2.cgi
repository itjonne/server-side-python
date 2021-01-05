#!/usr/bin/python
# -*- coding: utf-8 -*-
import cgi
import cgitb; cgitb.enable()
import os
from jinja2 import Template, Environment, FileSystemLoader
import simplejson as json
import urllib

print """Content-type: text/html; charset=UTF-8

"""

form = cgi.FieldStorage()
koko = form.getfirst(u'koko', "-1").decode('UTF-8')
teksti = form.getfirst(u'teksti', "").decode('UTF-8')
laudan_tila = form.getfirst(u'koordinaatit', "").decode('UTF-8')
poista = form.getfirst(u'poista', "").decode('UTF-8')
virhe = ""

try:
    koko = int(koko)
except:
    koko = 0    
    
# Formissa ei ole testausta, jos koko == 0, ei ruudukkoa piirretä
# Jos koko ei ole 8-16 välillä, piirretään 8-kokoinen taulukko    
if (koko < 8 or koko > 16 or koko == ""):
    virhe = u"Anna laudan koko välillä 8-16"
    if koko == -1:
        virhe = u""

try:
    tmpl_path = os.path.join(os.path.dirname(os.environ['SCRIPT_FILENAME']), 'templates')
except:
    tmpl_path = "templates"

# alustetaan Jinja sopivilla asetuksilla
env = Environment(autoescape=True, loader=FileSystemLoader(tmpl_path), extensions=['jinja2.ext.autoescape'])

# ladataan oma template
template = env.get_template('vt2_3.html')

# Jos halutaan muokata pelilautaa tullaan tänne
if poista and laudan_tila:
    koordinaatit = json.loads(laudan_tila)
    poistettava = poista.replace("(", "")
    poistettava = poistettava.replace(")","")
    poistettava = poistettava.split(",")
    # poistettavan koordinaatit tulee muodossa "(x,y)"
    # ei järkevin tapa, mutta toimii
    x = poistettava[0]
    y = poistettava[1]

    testirivi = koordinaatit[ int(x) -1 ]
    
    for paikka in range(len(testirivi)):
        if paikka == int(y) -1:
            koordinaatit[int(x) - 1][paikka] = "o"
            
    json_koordinaatit = urllib.quote_plus(json.dumps(koordinaatit))

    print template.render(koko=koko, teksti=teksti, virhe=virhe, koordinaatit=koordinaatit, json_koordinaatit=json_koordinaatit).encode("UTF-8")  
            
elif not virhe:
    koordinaatit = [None] * koko

    for rivi in range(koko):
        for sarake in range(koko):
            if sarake == 0:
                koordinaatit[rivi] = [None] * koko
                if sarake == rivi:
                    koordinaatit[rivi][sarake] = 'x'
                else:
                    if sarake+rivi == koko-1:
                        koordinaatit[rivi][sarake] = 'y'
                    else:
                        koordinaatit[rivi][sarake] = 'o'        
            else:
                if sarake == rivi:
                    koordinaatit[rivi][sarake] = "x"
                else:
                    if sarake+rivi == koko-1:
                        koordinaatit[rivi][sarake] = 'y'
                    else:        
                        koordinaatit[rivi][sarake] = "o"   
            
    json_koordinaatit = urllib.quote_plus(json.dumps(koordinaatit))
    print template.render(koko=koko, teksti=teksti, virhe=virhe, koordinaatit=koordinaatit, json_koordinaatit=json_koordinaatit).encode("UTF-8")                    
# TODO: Luultavasti <ahref="?jsoni+poistett
else:
# Renderoidaan Jinjan template jossa tyyli-muuttujan tilalle sijoitetaan css-tiedoston osoite
# samassa yhteydessÃ¤ voidaan mÃ¤Ã¤ritellÃ¤ useampiakin muuttujia jinjalle vietÃ¤vÃ¤ksi
    print template.render(koko=koko, teksti=teksti, virhe=virhe).encode("UTF-8")