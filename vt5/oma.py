#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template, make_response
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
        con = sqlite3.connect(os.path.abspath("../../../data/vt5"))
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
    except:
        #virheenkäsittely...
        logging.debug("tietokantayhteys ei aukea")
        for err in sys.exc_info():
            logging.debug(err)
        return None
    return con
       
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
    try:
        return kilpailu_id['id']
    except:
        return -1

def joukkueListaus(con, kilpailu_nimi):
    kilpailu_id = haeKilpailunId(con, kilpailu_nimi)

    sql = """
        select sarjat.nimi as sarja_nimi, joukkueet.id as joukkue_id, joukkueet.nimi as joukkue_nimi, joukkueet.jasenet
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

    """
        select sarjat.nimi, joukkueet.nimi, joukkueet.jasenet
        from joukkueet
        join sarjat
        on sarjat.id = joukkueet.sarja
        join kilpailut
        on sarjat.kilpailu = kilpailut.id
        and kilpailut.id = '5172934059196499'
        order by sarjat.nimi collate nocase asc, joukkueet.nimi collate nocase asc;
    """   

    return kilpailu

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

    data = cur.fetchone()

    try:
        return data['id']
    except:
        return "Ei toimi"

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

def haeKilpailuJossaJoukkue(con, joukkue_id):
    sql = """
        select kilpailut.nimi
        from kilpailut
        join sarjat
        on sarjat.kilpailu = kilpailut.id
        join joukkueet
        on (joukkueet.sarja = sarjat.id
        and joukkueet.id = :joukkue_id);
    """

    cur = con.cursor()

    try:
        cur.execute(sql, {"joukkue_id": joukkue_id})
    except:
        logging.debug('kysely ei toimi')
        for err in sys.exc_info():
            logging.debug(err)

    kilpailu_nimi = cur.fetchone()
    try:
        return kilpailu_nimi['nimi']
    except:
        return ""

def haejoukkueenTiedot(con, joukkue_id):
    sql = """
    select * 
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

    try:
        data = cur.fetchone()
        # muunnetaan kyselyn tulos json-muotoon. Tarvitaan oma konversiofunktio row_to_json
        json_data = json.dumps(data, default=row_to_json)
        # tehdään flaskin edellyttämä response json-datasta. HTTP-koodina käytetään 200 eli OK
        resp = make_response(json_data, 200)
        # määritetään responsessa käytetty merkistö ja mediatyyppi
        resp.charset = "UTF-8"
        resp.mimetype = "application/json"
    except:
        make_response("", 200)
        resp.charset = "UTF-8"
        resp.mimetype = "application/json"    
    return resp

# muuntaa sqlite3 row -tyyppisen objektin tavalliseksi dictiksi
def row_to_json(row):
    d = dict()
    for key in row.keys():
        d[key] = row[key]
    return d

app = Flask(__name__)
app.secret_key = '\x04\xf6\xb7^\x8f\xe58\x12lw\xef\x19O](#:\x1e3o\x96K\xda\x08'

# voidaan napata kiinni palvelimen virheet
@app.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_internal_server_error(e):
    return Response(u'Internal Server Error\n' + unicode(e), status=500, content_type="text/plain; charset=UTF-8")   

# REITITYS ALKAA TÄSTÄ ===========================

@app.route('/kirjaudu', methods=['GET'])
def kirjaudu():   
    con = avaaTietokanta()
    # Tällä haetaan kotiloiden tiedot
    if 'id' in request.args:
        id = u"6008099190079488"
        #id = request.args.get("id")
    else:    
        id = u"6008099190079488"
    joukkue = haejoukkueenTiedot(con, id)
    con.close()
    return joukkue
        
@app.route('/joukkuelistaus', methods=['GET'])
def joukkuelistaus():
    con = avaaTietokanta()
    # Nyt tiedetään että kotilot on Jäärogainingissa, muuten pitäis vähän säätää
    if 'id' in request.args:
        id = u"6008099190079488"
        #id = request.args.get("id")
    else:    
        id = u"6008099190079488"

    kilpailu = haeKilpailuJossaJoukkue(con, id)
    joukkuelistaus = joukkueListaus(con, kilpailu)
    json_data = json.dumps(joukkuelistaus, default=row_to_json)
    resp = make_response(json_data, 200)
    resp.charset = "UTF-8"
    resp.mimetype = "application/json"
    con.close()
    return resp

@app.route('/logout', methods=['POST', 'GET'])
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

@app.route('/muokkaa', methods=['POST'])
def muokkaa():
    con = avaaTietokanta()
    jasenet = []

    try:
        joukkue_nimi = request.form['joukkue_nimi']
        joukkue_sarja = request.form['sarja']
        joukkue_id = request.form['id']
    except:
        joukkue_nimi = ""    
        joukkue_sarja = ""
        joukkue_id = 0

    if len(request.form['jasen-0']):
        jasenet.append(request.form['jasen-0'].strip())

    if len(request.form['jasen-1']):
        jasenet.append(request.form['jasen-1'].strip())

    if len(request.form['jasen-2']):
        jasenet.append(request.form['jasen-2'].strip())

    if len(request.form['jasen-3']):
        jasenet.append(request.form['jasen-3'].strip())

    if len(request.form['jasen-4']):
        jasenet.append(request.form['jasen-4'].strip())                

    tyhjat_filtteroity_jasenlista = filter(lambda jasen: jasen.strip() != "", jasenet)

    sarja_id = haeSarjanId(con, u"Jäärogaining", joukkue_sarja)
    virheet = updateJoukkue(con, joukkue_id, joukkue_nimi, tyhjat_filtteroity_jasenlista, sarja_id)

    con.close()

    return json.dumps(virheet)

if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)        