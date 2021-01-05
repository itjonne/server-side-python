#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable(format="text")
import cgi
import urllib2
import simplejson as json

print u"""Content-type: text/plain; charset=UTF-8
"""

# Ladataan tietorakenne verkosta    
sivu = urllib2.urlopen("http://appro.mit.jyu.fi/tiea2120/vt/vt1/2019/data.json")
data = json.load(sivu)
virheilmoitus = ""
# ========= APUFUNKTIOT ==========

# Funktio joukkueen lisäämiseen
def lisaaJoukkue(data, joukkue, kilpailu_nimi, sarja_nimi):
    if not joukkue:
        return

    try:
        if (len(data) > 0):
            for kilpailu in data:
                if (kilpailu["nimi"].encode("UTF-8") == kilpailu_nimi.encode("UTF-8")):
                    for sarja in kilpailu["sarjat"]:
                        if (sarja["nimi"].encode("UTF-8") == sarja_nimi.encode("UTF-8")):
                            sarja["joukkueet"].append(joukkue)
    except:
        pass


# Funktio joukkueen poistamiseen
def poistaJoukkue(data, joukkue_nimi, kilpailu_nimi, sarja_nimi):
    try:
        if (len(data) > 0):
            for kilpailu in data:
                if (kilpailu['nimi'].encode('UTF-8') == kilpailu_nimi.encode('UTF-8')):
                    for sarja in kilpailu['sarjat']:
                        if (sarja['nimi'].encode('UTF-8') == sarja_nimi.encode('UTF-8')):
                            sarja['joukkueet'] = [joukkue for joukkue in sarja['joukkueet'] if not (joukkue['nimi'].encode('UTF-8') == joukkue_nimi.encode('UTF-8'))]
    except:
        pass

def laskeJoukkueenPisteet(kilpailu_rastit, joukkue_rastit):
    pisteet = 0
    rastit = []

    # Poistetaan duplicaatit
    for rasti in joukkue_rastit:
        if str(rasti['rasti']) not in rastit:
            if rasti['rasti'] > 0:
                rastit.append(str(rasti['rasti']))

    for rasti in rastit:
        for kilpailu_rasti in kilpailu_rastit:
            try:
                if rasti == str(kilpailu_rasti['id']):              
                    if(kilpailu_rasti['koodi'][0].isdigit()):
                        pisteet += int(kilpailu_rasti['koodi'][0])
                        break
            except:
                print('meni rikki')
                break        
    return pisteet

def lisaaCGIJoukkue(nimi, jasenet, id, leimaustapa):
    if idEiKaytossa(id) and len(nimi):
        joukkue = {
            "nimi": nimi,
            "jasenet": jasenet,
            "id": id,
            "leimaustapa": leimaustapa,
            "rastit": []
        }
        return ("", joukkue)
    else:
        virheilmoitus = "Joukkuetta ei voitu lisätä! Muista antaa joukkueelle validi ID ja nimi"
        return (virheilmoitus, {})
      
def idEiKaytossa(id):
    if not id:
        return False

    for kilpailu in data:
        for sarja in kilpailu['sarjat']:
            for joukkue in sarja['joukkueet']:
                if (str(joukkue['id']) == str(id)):
                    return False
    return True

# ========== KOODI =========

# Otetaan koppi parametreista
tiedot = cgi.FieldStorage()


try:
    joukkue_nimi = tiedot.getfirst(u"nimi", "").decode("UTF-8")                    
    joukkue_id = tiedot.getfirst(u"id", "").decode("UTF-8")
    joukkue_jasenet = []            
    joukkue_leimaustapa = []        
    for jasen in tiedot.getlist(u"jasenet"):
        joukkue_jasenet.append(jasen)
    for leimaustapa in tiedot.getlist(u"leimaustapa"):
        joukkue_leimaustapa.append(leimaustapa)
except:
    joukkue_nimi = ""
    joukkue_jasenet = []
    joukkue_leimaustapa = []
    joukkue_id = ""

virheilmoitus, joukkue = lisaaCGIJoukkue(joukkue_nimi, joukkue_jasenet, joukkue_id, joukkue_leimaustapa)
# Lisättävä joukkue, nimi tulee parametreista (Oletuksena "Pällit")                        

# Lisätään tietorakenteeseen uusi joukkue
lisaaJoukkue(data, joukkue, u"Jäärogaining", u"4h")
poistaJoukkue(data, u'Vara 1', u"Jäärogaining", u"8h")
poistaJoukkue(data, u'Pelättimet', u"Jäärogaining", u"4h")
poistaJoukkue(data, u'Vapaat', u"Jäärogaining", u"4h")
#testi
poistaJoukkue(data, u'Kissakala', u"Jäärogaining", u"4h")

# Käydään tietorakenteen joukkueet läpi, sortataan ja printataan.
joukkueet = []

for kilpailu in data:
    kilpailu_rastit = kilpailu['rastit'] if kilpailu['rastit'] else [] 
    print(kilpailu["nimi"].encode("UTF-8"))
    for sarja in kilpailu["sarjat"]:
        for joukkue in sarja["joukkueet"]:
            joukkue_dict = {
                'nimi': "",
                'pisteet': 0
            }
            joukkue_dict['nimi'] = joukkue['nimi'].encode('UTF-8')
            joukkue_dict['pisteet'] = laskeJoukkueenPisteet(kilpailu_rastit, joukkue['rastit'] if joukkue['rastit'] else [])
            joukkueet.append(joukkue_dict)
            

joukkueet_sorted = sorted(joukkueet, key=lambda joukkue: joukkue['pisteet'], reverse=True)
for jouk in joukkueet_sorted:
    print("    " + jouk['nimi'] + " " + str(jouk['pisteet']))

if virheilmoitus:
    print('\n' + virheilmoitus) 