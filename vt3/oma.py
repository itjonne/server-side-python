#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template
import os
import werkzeug.exceptions
from flask_wtf import FlaskForm
from wtforms import Form, FieldList, BooleanField, PasswordField, StringField, validators, IntegerField, SelectField, widgets, SelectMultipleField, ValidationError, RadioField, SubmitField
import io
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = '\x04\xf6\xb7^\x8f\xe58\x12lw\xef\x19O](#:\x1e3o\x96K\xda\x08'

filename = "../../../data/data.json"
# Luetaan data
try:
    with io.open(filename, "r", encoding="utf-8") as file:
        data = json.loads(file.read())
except:
    data = []

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

# Kirjautumissivun handleri
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

# Samat adminille
def auth_admin(f):
    ''' Tämä decorator hoitaa kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle
    '''
    @wraps(f)
    def decorated(*args, **kwargs):
        # tässä voisi olla monimutkaisempiakin tarkistuksia mutta yleensä tämä riittää
        if not 'admin' in session:
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated

def auth_admin_kirjaudu(f):
    ''' Tämä decorator hoitaa kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle
    '''
    @wraps(f)
    def decorated(*args, **kwargs):
        # tässä voisi olla monimutkaisempiakin tarkistuksia mutta yleensä tämä riittää
        if 'admin' in session:
            return redirect(url_for('admin_kilpailut'))
        return f(*args, **kwargs)
    return decorated    

# Palauttaa, onko tuon niminen joukkue kilpailussa
def onkoJoukkueKilpailussa(kilpailu_nimi, tunnus):
        if len(data):
            joukkueet = []
            for kilpailu in data:
                if kilpailu['nimi'] == kilpailu_nimi:
                    if 'sarjat' in kilpailu:
                        for sarja in kilpailu['sarjat']:
                            if 'joukkueet' in sarja:
                                for joukkue in sarja['joukkueet']:
                                    joukkueet.append(joukkue)
            if len(joukkueet):
                for joukkue in joukkueet:
                    if joukkue['nimi'].lower() == tunnus.lower():
                        return True
        else:
            return False

# voidaan napata kiinni palvelimen virheet
@app.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_internal_server_error(e):
    return Response(u'Internal Server Error\n' + unicode(e), status=500, content_type="text/plain; charset=UTF-8")

@app.route('/kirjaudu', methods=['POST', 'GET'])
@auth_kirjaudu
def kirjaudu():
    import hashlib
    
    m = hashlib.sha512()
    avain = u"omasalainenavain"
    request_salasana = request.form.get('password', "")
    request_tunnus = request.form.get('tunnus', "").strip()
    request_kilpailu = request.form.get('kilpailu', "")
    m.update(avain.encode('UTF-8'))
    m.update(request_salasana.encode('UTF-8'))

    kilpailut = []

    if len(data):
        for kilpailu in data:
            kilpailut.append(kilpailu["nimi"])    
                
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
        password = PasswordField(u'Salasana', validators=[validators.DataRequired()])
        submit = SubmitField(u'Kirjaudu')

        # Lisävalidointia formille
        def validate(self):
            valid = FlaskForm.validate(self)
            
            if not valid:
                if not onkoJoukkueKilpailussa(request_kilpailu, request_tunnus):
                    self.tunnus.errors.append(u'Joukkuetta ei löytynyt kilpailusta')    
                    return False

                if not m.hexdigest == "156f138970bf8357ccd543af6545c86779b7e0bec9c2b92cc8e2cab6bfb80f90bcb96f4c6e597bfb939100bab302fcaa9f298eaf870d7765e686eed0de0544b1":
                    self.password.errors.append(u'Salasana väärin')
                    return False

                return False

            return True
        
    form = Joukkueet()

    salasana_oikein = m.hexdigest() == "156f138970bf8357ccd543af6545c86779b7e0bec9c2b92cc8e2cab6bfb80f90bcb96f4c6e597bfb939100bab302fcaa9f298eaf870d7765e686eed0de0544b1"
    tunnus_oikein = onkoJoukkueKilpailussa(request_kilpailu, request_tunnus)  

    if len(request_tunnus) and tunnus_oikein and salasana_oikein:
        # jos kaikki ok niin asetetaan sessioon tieto kirjautumisesta ja ohjataan laskurisivulle
        session['kirjautunut'] = "ok"
        session['kilpailu'] = request_kilpailu
        session['nimi'] = request_tunnus
        return redirect(url_for('joukkuelistaus'))
    else:
    #Jos ei ok
        if request.method == 'POST':
            if form.validate():
                return 'toimi'
            else:
                string = "virhe"
                for error in form.password.errors:
                    string += error
                return render_template('kirjaudu.html', form=form, string=string)
        else:
            return render_template('kirjaudu.html', form=form)
        
@app.route('/joukkuelistaus', methods=['POST', 'GET'])
@auth
def joukkuelistaus():
    try:
        kilpailu_nimi = session['kilpailu']
    except:
        kilpailu_nimi = ""    

    try:
        joukkue_nimi = session['nimi']
    except:
        joukkue_nimi = "Tapahtui virhe!"

    sarjat = []

    if len(data):
        for kilpailu in data:
            if kilpailu['nimi'] == kilpailu_nimi:
                if len(kilpailu['sarjat']):
                    for sarja in kilpailu['sarjat']:
                        sarjat.append(sarja)

    pituus = len(sarjat)

    return render_template('joukkuelistaus.html', joukkue_nimi=joukkue_nimi, kilpailu_nimi=kilpailu_nimi, sarjat=sarjat, pituus=pituus)

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

    # Otetaan jäsenistä koppi
    for i in range(5):
        request_jasenet.append(request.form.get('jasenet-' + str(i)))

    try:
        joukkue_nimi = session['nimi']
        kilpailu_nimi = session['kilpailu']
    except:
        joukkue_nimi = ""
        kilpailu_nimi = ""    

    sarja_lista = []
    oma_joukkue = {}
    kaikki_joukkueet = []

    # Haetaan oma joukkue kilpailusta
    if len(data):
        for kilpailu in data:
            if 'sarjat' in kilpailu:
                for sarja in kilpailu['sarjat']:
                    if sarja['nimi'] not in sarja_lista:
                        sarja_lista.append(sarja['nimi'])
                        if 'joukkueet' in sarja:
                            for joukkue in sarja['joukkueet']:
                                if joukkue['nimi'].lower() == joukkue_nimi.lower():
                                    oma_joukkue = joukkue
    # Tämän olisi voinut yhdistää edelliseen, haetaan kaikki kilpailun joukkueet
    if len(data):
        for kilpailu in data:
            if kilpailu['nimi'] == kilpailu_nimi:
                if 'sarjat' in kilpailu:
                    for sarja in kilpailu['sarjat']:
                        if 'joukkueet' in sarja:
                            for joukkue in sarja['joukkueet']:
                                kaikki_joukkueet.append(joukkue['nimi'])

    sarja_lista.sort()

    class Muokkaa(FlaskForm):
        sarjat = RadioField(u'sarjat', default=sarja_lista[0], choices=sarja_lista)
        tunnus = StringField(u'Joukkueen nimi', default=joukkue_nimi, validators=[validators.InputRequired(), validators.DataRequired()])
        #jasenet = FieldList(StringField(u'Jäsen'), min_entries=5, max_entries=5)
        submit = SubmitField(u'Muokkaa')     

    # Lisätään formiin jäsenille paikat
    lkm = 5
    for jasen in range(lkm):
        setattr(Muokkaa, u"jasenet-" + unicode(jasen), StringField(u'Jäsen ' + unicode(jasen + 1)))

    form = Muokkaa()    
    jasenet = oma_joukkue['jasenet']

    # Oma aliohjelma formin validointiin, tämä ei luultavastikaan ole oikea validointitapa, mutta toimii tässä tapauksessa
    def validateForm(data, filename):
        jasenlista = filter(None, request_jasenet)

        # Tällä filtteröidään tyhjät jäsenkirjaukset pois
        tyhjat_filtteroity_jasenlista = filter(lambda jasen: jasen.strip() != "", jasenlista)    

        if len(tyhjat_filtteroity_jasenlista) < 2:
            virhe_jasen = u"Liian vähän jäseniä"
            return render_template('muokkaa.html', virhe_jasen=virhe_jasen, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)
        elif (request_tunnus.strip().upper() in (nimi.upper() for nimi in kaikki_joukkueet)) and joukkue_nimi.strip().lower() != request_tunnus.strip().lower():
            virhe_tunnus = u"Joukkue on jo kilpailussa, valitse joku toinen"
            return render_template('muokkaa.html', virhe_tunnus=virhe_tunnus, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)
        elif (not request_tunnus.strip()):
            virhe_tunnus = u"Anna joukkueelle nimi"
            return render_template('muokkaa.html', virhe_tunnus=virhe_tunnus, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)
        # Jos ei virheitä, mennään tänne
        else:
            muokattu_joukkue = {}

            # Ensin haetaan joukkue listasta, ja poistetaan se
            if len(data):
                for kilpailu in data:
                    if kilpailu['nimi'] == kilpailu_nimi:
                        if 'sarjat' in kilpailu:
                            for sarja in kilpailu['sarjat']:
                                if 'joukkueet' in sarja:
                                    for i in range(len(sarja['joukkueet'])):
                                        if sarja['joukkueet'][i]['nimi'].upper().strip() == joukkue_nimi.upper().strip():
                                            muokattu_joukkue = sarja['joukkueet'][i]
                                            muokattu_joukkue['nimi'] = request_tunnus
                                            muokattu_joukkue['jasenet'] = tyhjat_filtteroity_jasenlista                                                                  
                                            session['nimi'] = request_tunnus
                                            joukkueen_indeksi = i
                                            del sarja['joukkueet'][i]
                                            break
                                                                    
            # Lisätään muokattu joukkue haluttuun paikkaan
            if len(data):
                for kilpailu in data:
                    if kilpailu['nimi'] == kilpailu_nimi:
                        if 'sarjat' in kilpailu:
                            for sarja in kilpailu['sarjat']:
                                if sarja['nimi'] == request_sarjat:
                                    sarja['joukkueet'].append(muokattu_joukkue)

            # päivitetään tietorakenne
            try:
                with io.open(filename, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(data, ensure_ascii=False))
            except:
                data = []
                
            return redirect(url_for('joukkuelistaus'))
   
    # Tässä oli alkuperäinne testaus POST-requestille, jälkeenpäin fiksumpi tarkistus, jätetään tämä tähän vain muistiin, että muistaa mistä lähdettiin liikkeelle
    if len(request_sarjat):
        return validateForm(data, filename)       
    else:
        return render_template('muokkaa.html', kaikki_joukkueet=kaikki_joukkueet, request_sarjat=request_sarjat, jasenet=jasenet, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi)

# ======= ADMIN ======

@app.route('/admin', methods=['POST', 'GET'])
@auth_admin_kirjaudu
def admin():
    import hashlib
    
    m = hashlib.sha512()
    avain = u"omasalainenavain"
    request_salasana = request.form.get('salasana', "")
    m.update(avain.encode('UTF-8'))
    m.update(request_salasana.encode('UTF-8'))

    form = AdminForm()

    if request.method == 'POST':
        salasana_oikein = m.hexdigest() == "37ca231b5d20e753d515ee05f267b95e8362f51e65fdb991677142c3264cb967a90c5c47e09cf645b344da55600a243de9a8c4a170dfd3c6f894d0e367157a45"
        if salasana_oikein:
            session['admin'] = 'admin'
            return redirect(url_for('admin_kilpailut'))
        else:
            virhe = u"Salasana väärin"
            return render_template('admin.html', form=form, virhe=virhe)
    return render_template('admin.html', form=form)

@app.route('/admin_kilpailut', methods=['POST', 'GET'])
@auth_admin
def admin_kilpailut():
    kilpailut = []
    for kilpailu in data:
        kilpailut.append(kilpailu)

    return render_template('admin_kilpailut.html', kilpailut=kilpailut)

@app.route('/admin_sarjat/<kilpailu_nimi>', methods=['POST', 'GET'])
@auth_admin
def admin_sarjat(kilpailu_nimi):
    kilpailu_dict = {}
    sarjat = []

    try:
        session['kilpailu'] = kilpailu_nimi
    except:
        session['kilpailu'] = ""

    for kilpailu in data:
        if 'nimi' in kilpailu:
            if kilpailu['nimi'] == kilpailu_nimi:
                kilpailu_dict = kilpailu

    if 'sarjat' in kilpailu_dict:
        for sarja in kilpailu_dict['sarjat']:
            sarjat.append(sarja)
    if sarjat:
        sorted_sarjat = sorted(sarjat, key=lambda sarja: sarja['nimi'])
    else:
        sorted_sarjat = []

    return render_template('admin_sarjat.html', sarjat=sorted_sarjat)

@app.route('/admin_joukkuelistaus/<sarja_nimi>', methods=['POST', 'GET'])
@auth_admin
def admin_joukkuelistaus(sarja_nimi):
    try:
        kilpailu_nimi = session['kilpailu']
        sarja_nimi = sarja_nimi
    except:
        kilpailu_nimi = ""
        sarja_nimi = ""

    joukkueet = []
    sarja_lista = haeSarjat(kilpailu_nimi)
    sarja_lista.sort()

    # Haetaan sarjan joukkueet
    for kilpailu in data:
        if kilpailu['nimi'] == kilpailu_nimi:
            for sarja in kilpailu['sarjat']:
                if sarja['nimi'] == sarja_nimi:
                    if 'joukkueet' in sarja:
                        for joukkue in sarja['joukkueet']:
                            joukkueet.append(joukkue)          

    kaikki_joukkueet = []

    # Haetaan kaikki kilpailun joukkueet
    if len(data):
        for kilpailu in data:
            if kilpailu['nimi'] == kilpailu_nimi:
                if 'sarjat' in kilpailu:
                    for sarja in kilpailu['sarjat']:
                        if 'joukkueet' in sarja:
                            for joukkue in sarja['joukkueet']:
                                kaikki_joukkueet.append(joukkue['nimi'])

    class AdminLisaaJoukkue(FlaskForm):
        sarjat = RadioField(u'sarjat', default=sarja_lista[0], choices=sarja_lista)
        tunnus = StringField(u'Joukkueen nimi', validators=[validators.InputRequired(), validators.DataRequired()])
        #jasenet = FieldList(StringField(u'Jäsen'), min_entries=5, max_entries=5)
        submit = SubmitField(u'Muokkaa')

    # Joukkueen jäsenille paikat
    lkm = 5
    for jasen in range(lkm):
        setattr(AdminLisaaJoukkue, u"jasenet-" + unicode(jasen), StringField(u'Jäsen ' + unicode(jasen + 1), validators=[]))

    form = AdminLisaaJoukkue()
    sorted_joukkueet = sorted(joukkueet, key=lambda joukkue: joukkue['nimi'].upper())

    # Tätä nyt olen pallotellut tässä ympäriinsä, pitäisi siistiä suuresti, tähän versioon en vielä viitsinyt
    def validateForm(data, filename):
        # Haetaan jäsenet
        request_jasenet = []

        try:
            for i in range(5):
                request_jasenet.append(request.form.get('jasenet-' + str(i)))
            request_tunnus = request.form.get('tunnus', "").strip()
            request_sarjat = request.form.get('sarjat', "")
        except:
            request_tunnus = ""
            request_sarjat = ""    
        # Filtteröidään Nonet
        jasenlista = filter(None, request_jasenet)

        # Tällä filtteröidään tyhjät jäsenkirjaukset pois
        tyhjat_filtteroity_jasenlista = filter(lambda jasen: jasen.strip() != "", jasenlista)    

        # VIRHETARKISTUKSET
        if len(tyhjat_filtteroity_jasenlista) < 2:
            virhe_jasen = u"Liian vähän jäseniä"
            return render_template('admin_joukkuelistaus.html', virhe_jasen=virhe_jasen, form=form, jasenet=request_jasenet)
        elif (request_tunnus.strip().upper() in (nimi.upper() for nimi in kaikki_joukkueet)):
            virhe_tunnus = u"Joukkue on jo kilpailussa, valitse joku toinen"
            return render_template('admin_joukkuelistaus.html', virhe_tunnus=virhe_tunnus, form=form, jasenet=request_jasenet)
        elif (not request_tunnus.strip()):
            virhe_tunnus = u"Anna joukkueelle nimi"
            return render_template('admin_joukkuelistaus.html', virhe_tunnus=virhe_tunnus, form=form, jasenet=request_jasenet)
        
        # JOS KAIKKI OK
        else:
            lisatty_joukkue = {
                'nimi': request_tunnus,
                'last': '2020-01-01 00:00:00',
                'id': uniikkiId(),
                'jasenet': tyhjat_filtteroity_jasenlista
            }
                                                    
            # Lisätään joukkue haluttuun paikkaan
            if len(data):
                for kilpailu in data:
                    if kilpailu['nimi'] == kilpailu_nimi:
                        if 'sarjat' in kilpailu:
                            for sarja in kilpailu['sarjat']:
                                if sarja['nimi'] == request_sarjat:
                                    sarja['joukkueet'].append(lisatty_joukkue)

            # päivitetään tietorakenne
            try:
                with io.open(filename, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(data, ensure_ascii=False))
            except:
                data = []
                
            return redirect(url_for('admin_joukkuelistaus', sarja_nimi=request_sarjat))

    if request.method == 'POST':
        return validateForm(data, filename)    
    # Ellei ole POST
    else:
        return render_template('admin_joukkuelistaus.html', joukkueet=sorted_joukkueet, form=form)

@app.route('/admin_muokkaa/<joukkue_nimi>', methods=['POST', 'GET'])
@auth_admin
def admin_muokkaa(joukkue_nimi):
    request_sarjat = request.form.get('sarjat', "")
    request_tunnus = request.form.get('tunnus', "").strip()
    request_jasenet = [] 

    for i in range(5):
        request_jasenet.append(request.form.get('jasenet-' + str(i)))

    try:
        joukkue_nimi = joukkue_nimi
        kilpailu_nimi = session['kilpailu']
    except:
        joukkue_nimi = ""
        kilpailu_nimi = ""    

    sarja_lista = []
    oma_joukkue = {}
    kaikki_joukkueet = []

    # Taas tehdään sama rullaus, näihin rakentaisin funktiot niin selkenee ohjelmakoodi
    if len(data):
        for kilpailu in data:
            if 'sarjat' in kilpailu:
                for sarja in kilpailu['sarjat']:
                    if sarja['nimi'] not in sarja_lista:
                        sarja_lista.append(sarja['nimi'])
                        if 'joukkueet' in sarja:
                            for joukkue in sarja['joukkueet']:
                                if joukkue['nimi'].lower() == joukkue_nimi.lower():
                                    oma_joukkue = joukkue

    if len(data):
        for kilpailu in data:
            if kilpailu['nimi'] == kilpailu_nimi:
                if 'sarjat' in kilpailu:
                    for sarja in kilpailu['sarjat']:
                        if 'joukkueet' in sarja:
                            for joukkue in sarja['joukkueet']:
                                kaikki_joukkueet.append(joukkue['nimi'])

    sarja_lista.sort()

    class Muokkaa(FlaskForm):
        sarjat = RadioField(u'sarjat', default=sarja_lista[0], choices=sarja_lista)
        tunnus = StringField(u'Joukkueen nimi', default=joukkue_nimi, validators=[validators.InputRequired(), validators.DataRequired()])
        poista = BooleanField(u'Poista joukkue')
        submit = SubmitField(u'Muokkaa')     

    lkm = 5
    for jasen in range(lkm):
        setattr(Muokkaa, u"jasenet-" + unicode(jasen), StringField(u'Jäsen ' + unicode(jasen + 1)))

    form = Muokkaa()    
    jasenet = oma_joukkue['jasenet']

    def validateForm(data, filename):
        jasenlista = filter(None, request_jasenet)

        # Tällä filtteröidään tyhjät jäsenkirjaukset pois
        tyhjat_filtteroity_jasenlista = filter(lambda jasen: jasen.strip() != "", jasenlista)    
        
        # Jos yritetään poistaa
        if request.form.get('poista', ''):
            joukkueen_rastit = []
            # Haetaan joukkueen rastit ensin
            for kilpailu in data:
                if kilpailu['nimi'] == kilpailu_nimi:
                    if 'tupa' in kilpailu:
                        for rasti in kilpailu['tupa']:
                            if str(rasti['joukkue']) == str(oma_joukkue['id']):
                                joukkueen_rastit.append(rasti)

            # Jos joukkueella on rasteja ei poisteta
            if len(joukkueen_rastit):
                virhe_rastit = u"Joukkueella on merkittynä rasteja, ei voida poistaa"
                return render_template('admin_muokkaa.html', virhe_rastit=virhe_rastit, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)
            # Muuten poistetaan joukkue tietorakenteesta
            else:
                # Ensin haetaan joukkue listasta, ja poistetaan se
                if len(data):
                    for kilpailu in data:
                        if kilpailu['nimi'] == kilpailu_nimi:
                            if 'sarjat' in kilpailu:
                                for sarja in kilpailu['sarjat']:
                                    if 'joukkueet' in sarja:
                                        for i in range(len(sarja['joukkueet'])):
                                            if sarja['joukkueet'][i]['nimi'].upper().strip() == joukkue_nimi.upper().strip():                                                         
                                                session['nimi'] = request_tunnus
                                                del sarja['joukkueet'][i]
                                                break
                # päivitetään tietorakenne
                try:
                    with io.open(filename, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(data, ensure_ascii=False))
                except:
                    data = []                                                

                return redirect(url_for('admin_joukkuelistaus', sarja_nimi=request_sarjat))    

        # VIRHETESTAUS VANHOIHIN VIRHEISIIN 
        elif len(tyhjat_filtteroity_jasenlista) < 2:
            virhe_jasen = u"Liian vähän jäseniä"
            return render_template('admin_muokkaa.html', virhe_jasen=virhe_jasen, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)
        elif (request_tunnus.strip().upper() in (nimi.upper() for nimi in kaikki_joukkueet)) and joukkue_nimi.strip().lower() != request_tunnus.strip().lower():
            virhe_tunnus = u"Joukkue on jo kilpailussa, valitse joku toinen"
            return render_template('admin_muokkaa.html', virhe_tunnus=virhe_tunnus, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)
        elif (not request_tunnus.strip()):
            virhe_tunnus = u"Anna joukkueelle nimi"
            return render_template('admin_muokkaa.html', virhe_tunnus=virhe_tunnus, request_sarjat=request_sarjat, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi, jasenet=request_jasenet)
        
        # JOS KAIKKI ON OK
        else:
            muokattu_joukkue = {}

            # Ensin haetaan joukkue listasta, ja poistetaan se
            if len(data):
                for kilpailu in data:
                    if kilpailu['nimi'] == kilpailu_nimi:
                        if 'sarjat' in kilpailu:
                            for sarja in kilpailu['sarjat']:
                                if 'joukkueet' in sarja:
                                    for i in range(len(sarja['joukkueet'])):
                                        if sarja['joukkueet'][i]['nimi'].upper().strip() == joukkue_nimi.upper().strip():
                                            muokattu_joukkue = sarja['joukkueet'][i]
                                            muokattu_joukkue['nimi'] = request_tunnus
                                            muokattu_joukkue['jasenet'] = tyhjat_filtteroity_jasenlista                                                                  
                                            session['nimi'] = request_tunnus
                                            del sarja['joukkueet'][i]
                                            break
                                                                    
            # Lisätään muokattu joukkue haluttuun paikkaan
            if len(data):
                for kilpailu in data:
                    if kilpailu['nimi'] == kilpailu_nimi:
                        if 'sarjat' in kilpailu:
                            for sarja in kilpailu['sarjat']:
                                if sarja['nimi'] == request_sarjat:
                                    sarja['joukkueet'].append(muokattu_joukkue)

            # päivitetään tietorakenne
            try:
                with io.open(filename, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(data, ensure_ascii=False))
            except:
                data = []
                
            return redirect(url_for('admin_joukkuelistaus', sarja_nimi=request_sarjat))
   
    if len(request_sarjat):
        return validateForm(data, filename)       
    else:
        return render_template('admin_muokkaa.html', kaikki_joukkueet=kaikki_joukkueet, request_sarjat=request_sarjat, jasenet=jasenet, form=form, kilpailu_nimi=kilpailu_nimi, joukkue_nimi=joukkue_nimi)

@app.route('/admin_logout', methods=['POST', 'GET'])
@auth_admin
def admin_logout():
    try:
        kilpailu_nimi = session['kilpailu']
    except:
        kilpailu_nimi = "Ei löydy"  

    kirjaudu_ulos = request.form.get('kirjaudu_ulos', "")
    if (kirjaudu_ulos):
        session.clear()
        return redirect(url_for('admin'))
    else:
        return render_template('admin_logout.html', kilpailu_nimi=kilpailu_nimi)

class AdminForm(FlaskForm):
    salasana = PasswordField(u'Salasana', validators=[validators.DataRequired()])
    submit = SubmitField(u'Kirjaudu')

# Palauttaa kilpailun sarjat
def haeSarjat(kilpailu_nimi):
    sarja_lista = []
    if len(data):
        for kilpailu in data:
            if kilpailu['nimi'] == kilpailu_nimi:
                if 'sarjat' in kilpailu:
                    for sarja in kilpailu['sarjat']:
                        if sarja['nimi'] not in sarja_lista:
                            sarja_lista.append(sarja['nimi'])

    return sarja_lista

# Palauttaa joukkueelle uniikin ID:n, nyt antaa vähän tyhmiä numeroita, pitäisi rakentaa fiksumpi, mutta toimii
def uniikkiId():
    edellisetID = []
    id = 1

    for kilpailu in data:
        if 'sarjat' in kilpailu:
            for sarja in kilpailu['sarjat']:
                if 'joukkueet' in sarja:
                    for joukkue in sarja['joukkueet']:
                        if 'id' in joukkue:
                            edellisetID.append(joukkue['id'])

    while id in edellisetID:
        id += 1

    return id

if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)        