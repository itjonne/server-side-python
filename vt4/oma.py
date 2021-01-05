#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template
import os
import werkzeug.exceptions
from flask_wtf import FlaskForm
from wtforms import Form, FieldList, BooleanField, PasswordField, StringField, validators, IntegerField, SelectField, widgets, SelectMultipleField, ValidationError, RadioField
import json
from functools import wraps
import sqlite3
import logging
logging.basicConfig(filename='../../../data/flask.log',level=logging.DEBUG)
from contextlib import closing
import sys
import hashlib

def avaaTietokanta():
    try:
        con = sqlite3.connect(os.path.abspath("../../../data/tietokanta"))
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
    except:
        #virheenkäsittely...
        logging.debug("tietokantayhteys ei aukea")
        for err in sys.exc_info():
            logging.debug(err)
        return None
    return con

# Auth-handleri
def auth(f):
    ''' Tämä decorator hoitaa kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle
    '''
    @wraps(f)
    def decorated(*args, **kwargs):
        # tässä voisi olla monimutkaisempiakin tarkistuksia mutta yleensä tämä riittää
        if not 'kirjautunut' in session:
            return redirect(url_for('kirjaudu'))
        return f(*args, **kwargs)
    return decorated

def auth_kirjaudu(f):
    ''' Tämä decorator hoitaa kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle
    '''
    @wraps(f)
    def decorated(*args, **kwargs):
        # tässä voisi olla monimutkaisempiakin tarkistuksia mutta yleensä tämä riittää
        if 'kirjautunut' in session:
            return redirect(url_for('joukkuelistaus'))
        return f(*args, **kwargs)
    return decorated     

def haeKilpailut(con):
    kilpailut = []

    sql_kilpailut = """
    SELECT nimi
    FROM kilpailut
    """

    cur = con.cursor()
    try:
        cur.execute(sql_kilpailut)
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    haku = cur.fetchall()

    for kilpailu in haku:
        kilpailut.append(kilpailu['nimi'])

    return kilpailut    

def haeKilpailunId(con, kilpailu_nimi):
    sql_kilpailu = """
        select id
        from kilpailut
        where nimi = :kilpailu_nimi;
    """

    cur = con.cursor()

    try:
        cur.execute( sql_kilpailu, {"kilpailu_nimi": kilpailu_nimi})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    kilpailu_id = cur.fetchone()
    return kilpailu_id['id']

def joukkueListaus(con, kilpailu_nimi):
    kilpailu_id = haeKilpailunId(con, kilpailu_nimi)

    sql = """
        select sarjat.nimi as sarja_nimi, joukkueet.nimi as joukkue, joukkueet.jasenet
        from joukkueet
        join sarjat
        on sarjat.id = joukkueet.sarja
        join kilpailut
        on sarjat.kilpailu = kilpailut.id
        and kilpailut.id = :kilpailu
        order by sarjat.nimi collate nocase asc, joukkueet.nimi collate nocase asc;
    """
    
    cur = con.cursor()

    try:
        cur.execute(sql, {"kilpailu": kilpailu_id})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    kilpailu = cur.fetchall()
    return kilpailu

def kilpailunJoukkueet(con, kilpailu):
    sql = """
    select joukkueet.nimi 
    from joukkueet 
    join sarjat 
    on sarjat.id = joukkueet.sarja 
    join kilpailut 
    on sarjat.kilpailu = kilpailut.id 
    and kilpailut.nimi = :kilpailu;
    """

    cur = con.cursor()

    try:
        cur.execute( sql, {"kilpailu": kilpailu})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    joukkueet = cur.fetchall()
    palautettavat_joukkueet = []

    for joukkue in joukkueet:
        palautettavat_joukkueet.append(joukkue['nimi'])

    return palautettavat_joukkueet

def haeKilpailunSarjat(con, kilpailu):
    sql = """
        select * 
        from sarjat 
        join kilpailut 
        on sarjat.kilpailu = kilpailut.id 
        and kilpailut.nimi = :kilpailu;
    """

    cur = con.cursor()

    try:
        cur.execute( sql, {"kilpailu": kilpailu})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    sarjat = cur.fetchall()
    palautettavat_sarjat = []

    if len(sarjat):
        for sarja in sarjat:
            palautettavat_sarjat.append(sarja['nimi'])
    
    return palautettavat_sarjat

def haeSarjanId(con, kilpailu_nimi, sarja_nimi):
    sql = """
    select sarjat.id 
    from sarjat 
    join kilpailut
    on sarjat.kilpailu = kilpailut.id 
    and kilpailut.nimi = :kilpailu 
    and sarjat.nimi = :sarja;
    """

    cur = con.cursor()

    try:
        cur.execute( sql, {"kilpailu": kilpailu_nimi,
                           "sarja": sarja_nimi})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    id = cur.fetchone()

    try:
        return id['id']
    except:
        return ""

# Palauttaa -1 jos ei löydy
def haeJoukkueenId(con, tunnus):
    sql = """
    select joukkueet.id 
    from joukkueet 
    where lower(nimi) = :tunnus;
    """

    cur = con.cursor()

    try:
        cur.execute( sql, {"tunnus": tunnus.lower().strip()})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    joukkue = cur.fetchone()

    if joukkue != None:
        return joukkue['id']
    else:
        return -1    

def updateJoukkue(con, joukkue_id, request_tunnus, request_jasenet, sarja_id):
    sql = """
        UPDATE joukkueet
        SET nimi = :nimi,
            jasenet = :jasenet, 
            sarja = :sarja
        WHERE id = :id;    
    """

    cur = con.cursor()
    virheet = 0
    error = []

    [x.encode("UTF-8") for x in request_jasenet]

    try:
        cur.execute(sql, {"nimi": request_tunnus,
                          "jasenet": json.dumps(request_jasenet).decode('utf-8'),
                          "sarja": sarja_id,
                          "id": joukkue_id})
    except:
        virheet += 1
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)
            error.append(err)

    if virheet:
        con.rollback()
    else:
        con.commit()

    return error        

def varmistaSalasana(con, tunnus):
    sql = """
    select joukkueet.salasana 
    from joukkueet 
    where lower(nimi) = :tunnus;
    """

    cur = con.cursor()

    try:
        cur.execute( sql, {"tunnus": tunnus.lower().strip()})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    salasana = cur.fetchone()
    if salasana != None:
        return salasana['salasana']
    else:
        return "väärä"

def tarkistaSalasana(con, tunnus, salasana):   
    m = hashlib.sha512()
    joukkue_id = haeJoukkueenId(con, tunnus)
    if joukkue_id < 0:
        return False
    else:    
        m.update( str(joukkue_id) )
        m.update( salasana )
        if m.hexdigest() == varmistaSalasana(con, tunnus): 
            return True
        else:
            return False   

# Näin olisi voinut tehdä jo aiemmin, tehdään oikea tietorakenne sql-lausekkeesta.
# Palauttaa listan joukkueen jäsenistä
def haeJoukueenJasenet(con, joukkue_id):
    sql = """
    select jasenet 
    from joukkueet 
    where id = :joukkue_id;
    """

    cur = con.cursor()

    try:
        cur.execute( sql, {"joukkue_id": joukkue_id})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    jasenet = cur.fetchone()
    try:
        palautettavat_jasenet = json.loads(jasenet['jasenet'])
    except:
        palautettavat_jasenet = []
    return palautettavat_jasenet

# palauttaa joukkueen id:n + jäsenet dict-muodossa
def haeJoukkueenIdjaJasenet(con, joukkue_id):
    id = joukkue_id
    jasenet = haeJoukueenJasenet(con, id)

    joukkue = {
        "id": id,
        "jasenet": jasenet
    }
    return joukkue

app = Flask(__name__)
app.secret_key = '\x04\xf6\xb7^\x8f\xe58\x12lw\xef\x19O](#:\x1e3o\x96K\xda\x08'

# voidaan napata kiinni palvelimen virheet
@app.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_internal_server_error(e):
    return Response(u'Internal Server Error\n' + unicode(e), status=500, content_type="text/plain; charset=UTF-8")   

# REITITYS ALKAA TÄSTÄ ===========================

@app.route('/kirjaudu', methods=['POST', 'GET'])
@auth_kirjaudu
def kirjaudu():
    con = avaaTietokanta()    

    request_salasana = request.form.get('password', "")
    request_tunnus = request.form.get('tunnus', "").strip()
    request_kilpailu = request.form.get('kilpailu', "")
   
    kilpailut = haeKilpailut(con)  
    joukkueet = []
    salasana_oikein = False
    tunnus_oikein = False  

    class PasswordField(StringField):
        """
        Original source: https://github.com/wtforms/wtforms/blob/2.0.2/wtforms/fields/simple.py#L35-L42

        A StringField, except renders an ``<input type="password">``.
        Also, whatever value is accepted by this field is not rendered back
        to the browser like normal fields.
        """

        widget = widgets.PasswordInput(hide_value=False)
    # Form kuntoon
    class Joukkueet(FlaskForm):
        kilpailu = SelectField(u'Kilpailu', choices=kilpailut)
        tunnus = StringField(u'Joukkueen nimi', validators=[validators.InputRequired()])
        password = PasswordField(u'Salasana', [
            validators.DataRequired()
        ])
        
    form = Joukkueet()

    # Tarkistetaan löytyykö joukkue kilpailusta
    if len(request_kilpailu):
        joukkueet = kilpailunJoukkueet(con, request_kilpailu)
        tunnus_oikein = request_tunnus.lower() in (joukkue.lower() for joukkue in joukkueet)

    # Tarkistetaan salasana
    if len(request_tunnus):   
        salasana_oikein = tarkistaSalasana(con, request_tunnus, request_salasana)

    if len(request_tunnus) and salasana_oikein:
        # jos kaikki ok niin asetetaan sessioon tieto kirjautumisesta ja ohjataan laskurisivulle
        session['kirjautunut'] = "ok"
        session['kilpailu'] = request_kilpailu
        session['id'] = haeJoukkueenId(con, request_tunnus)
        session['nimi'] = request_tunnus
        con.close()

        return redirect(url_for('joukkuelistaus'))
    else:
    #Jos ei ok
        if (request_tunnus == None) or (request_tunnus == ""):
            tunnus_oikein = True
        if (request_salasana == None) or (request_salasana == ""):
            salasana_oikein = True

        con.close()
        return render_template('kirjaudu.html', tunnus_oikein=tunnus_oikein, joukkueet=joukkueet, form=form, salasana_oikein=salasana_oikein)
        
@app.route('/joukkuelistaus', methods=['POST', 'GET'])
@auth
def joukkuelistaus():
    try:
        kilpailu_nimi = session['kilpailu']
        session_id = session['id']
    except:
        kilpailu_nimi = ""    
        session_id = -1

    try:
        joukkue_nimi = session['nimi']
    except:
        joukkue_nimi = "Tapahtui virhe!"

    con = avaaTietokanta() 

    kilpailu = joukkueListaus(con, kilpailu_nimi)
    sarjat = []
    joukkueet = []

    # Joukkueen tiedot kuntoon
    try:
        for rivi in kilpailu:
            joukkue = {}
            joukkue['nimi'] = rivi['joukkue']
            joukkue['jasenet'] = json.loads(rivi['jasenet'])
            joukkue['jasenet'].sort()
            joukkue['sarja'] = rivi['sarja_nimi']
            joukkueet.append(joukkue)
            if rivi['sarja_nimi'] not in sarjat:
                sarjat.append(rivi['sarja_nimi'])
    except:
        sarjat = []

    con.close()
    return render_template('joukkuelistaus.html', session_id=session_id, sarjat=sarjat, kilpailu=joukkueet, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi) 

@app.route('/logout', methods=['POST', 'GET'])
@auth
def logout():
    try:
        kilpailu_nimi = session['kilpailu']
        joukkue_nimi = session['nimi']
    except:
        kilpailu_nimi = "Ei löydy"
        joukkue_nimi = "Ei löydy"    

    kirjaudu_ulos = request.form.get('kirjaudu_ulos', "")
    if (kirjaudu_ulos):
        session.clear()
        return redirect(url_for('kirjaudu'))
    else:
        return render_template('logout.html', joukkue_nimi=joukkue_nimi, kilpailu_nimi=kilpailu_nimi)

@app.route('/muokkaa', methods=['POST', 'GET'])
@auth
def muokkaa():
    request_sarjat = request.form.get('sarjat', "")
    request_tunnus = request.form.get('tunnus', "").strip()
    request_jasenet = [] 
    error = 0

    for i in range(5):
        try:
            request_jasenet.append(request.form.get('jasenet-' + str(i)))
        except:
            error += 1 

    try:
        joukkue_nimi = session['nimi']
        kilpailu_nimi = session['kilpailu']
        session_id = session['id']
    except:
        joukkue_nimi = ""
        kilpailu_nimi = ""
        session_id = -1    

    con = avaaTietokanta()

    oma_joukkue = haeJoukkueenIdjaJasenet(con, session_id)
    kilpailun_sarjat = haeKilpailunSarjat(con, kilpailu_nimi)
    kilpailun_sarjat.sort()
    kilpailun_joukkueet = kilpailunJoukkueet(con, kilpailu_nimi)

    class Muokkaa(FlaskForm):
        sarjat = RadioField(u'Sarja', default=kilpailun_sarjat[0], choices=kilpailun_sarjat)
        tunnus = StringField(u'Joukkueen nimi', default=joukkue_nimi, validators=[validators.DataRequired()])
        jasenet = FieldList(StringField(u'Jäsen'), min_entries=5, max_entries=5)

        # apuna käytetty: https://stackoverflow.com/questions/30519572/how-can-you-populate-a-wtforms-fieldlist-after-the-validate-on-submit-block
        def asetaJasenet(self, jasenet):
            i = 0
            for jasen in jasenet:
                self.jasenet[i].data = jasen
                i += 1
                        
    form = Muokkaa()
    
    # Samankaltainen validointi kuin vt3
    def validateForm():
        jasenlista = filter(None, request_jasenet)
        tyhjat_filtteroity_jasenlista = filter(lambda jasen: jasen.strip() != "", jasenlista)
        if len(tyhjat_filtteroity_jasenlista) < 2:
            virhe_jasen = u"Liian vähän jäseniä"
            form.asetaJasenet(request_jasenet)
            con.close()
            return render_template('muokkaa.html', virhe_jasen=virhe_jasen, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi)
        elif (request_tunnus.strip().upper() in (nimi.upper() for nimi in kilpailun_joukkueet)) and joukkue_nimi.strip().lower() != request_tunnus.strip().lower():
            virhe_tunnus = u"Joukkue on jo kilpailussa, valitse joku toinen"
            con.close()
            return render_template('muokkaa.html', virhe_tunnus=virhe_tunnus, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi)
        elif (not request_tunnus.strip()):
            virhe_tunnus = u"Anna joukkueelle nimi"
            con.close()
            return render_template('muokkaa.html', virhe_tunnus=virhe_tunnus, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)       
        else:
            sarja_id = haeSarjanId(con, kilpailu_nimi, request_sarjat)
            try:
                joukkue_id = oma_joukkue['id']
            except:
                joukkue_id = -1    

            # Virheet voisi tallettaa halutessaan johonkin, nyt käytettiin vaan testaukseen
            virheet = updateJoukkue(con, joukkue_id, request_tunnus, tyhjat_filtteroity_jasenlista, sarja_id)
            try:
                session['nimi'] = request_tunnus
            except:
                session['nimi'] = u'JOTAIN MENI RIKKI!'   

            con.close()
            return redirect(url_for('joukkuelistaus'))

    # Käytännössä ajaa saman asian kuin, request.method == 'POST, jostain syystä en tätä tällöin tajunnut tehdä.
    if len(request_sarjat):
        return validateForm()       
    else:
        if len(oma_joukkue['jasenet']):    
            form.asetaJasenet(oma_joukkue['jasenet'])
        con.close()
        return render_template('muokkaa.html', kilpailun_joukkueet=kilpailun_joukkueet, request_sarjat=request_sarjat, request_jasenet=request_jasenet, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi)

if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)        