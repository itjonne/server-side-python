let kilpailunData;
const JOUKKUEEN_ID = "6008099190079488";

window.onload = () => {
    asetaNavClickit();
    asetaFormSubmit();
    haeKilpailunTiedot(JOUKKUEEN_ID);

}

function asetaFormSubmit() {
    let nappula = document.getElementById('submit_button');
    nappula.addEventListener('click', (e) => {
        e.preventDefault();

        document.getElementById('joukkue_nimi_virhe').textContent = "";
        document.getElementById('joukkue_jasenet_virhe').textContent = "";
        
        let joukkue_nimi = document.getElementById('joukkue_input').value;
        let joukkue_sarja = document.getElementById('sarja_input').value;
        let joukkue_jasenet = [];

        for (let i = 0; i < 5; i++) {
            let jasen = document.getElementById('jasen-' + i.toString()).value;
            if (jasen.trim().length > 0) {
                joukkue_jasenet.push(jasen.trim());
            }
        }
        
        let check_nimi = tarkistaJoukkueenNimi(joukkue_nimi);
        let check_jasenet = tarkistaJoukkueenJasenet(joukkue_jasenet);

        if (check_nimi == true && check_jasenet == true) {
            let form = document.getElementById('form');
            document.getElementById('input_id').value = JOUKKUEEN_ID;

            const data = new URLSearchParams();
            for (const pair of new FormData(form)) {
                data.append(pair[0], pair[1]);
            }

            fetch("http://users.jyu.fi/~jovimajo/cgi-bin/tiea2080/vt5/flask.cgi/muokkaa", {
                method: 'post',
                body: data,
            })          
            .then(
                () => {
                    haeKilpailunTiedot(JOUKKUEEN_ID);
            
                    $('#joukkuelistaus').show();
                    $('#muokkaa').hide();
                    $('#logout').hide();
                }
            ).catch((err) => {
                $('#joukkuelistaus').hide();
                $('#muokkaa').show();
                $('#logout').hide();

                document.getElementById('submit_virhe').textContent = "Joukkueen tallentamisessa ongelmia";
            });

        }
    })   
}

function tarkistaJoukkueenNimi(joukkue_nimi) {
    if (joukkue_nimi.trim().length == 0) {
        document.getElementById('joukkue_nimi_virhe').textContent = "Anna joukkueelle nimi";
        return false;
    }

    for (joukkue of kilpailunData) {
        if (joukkue_nimi.toUpperCase().trim() == joukkue.joukkue_nimi.toUpperCase()) {
            if (joukkue.joukkue_id.toString() == JOUKKUEEN_ID) continue;
            document.getElementById('joukkue_nimi_virhe').textContent = "Joukkue on jo kilpailussa";
            return false;
        }
    }
    return true;
}

function tarkistaJoukkueenJasenet(joukkue_jasenet) {
    if (joukkue_jasenet.length < 2) {
        document.getElementById('joukkue_jasenet_virhe').textContent = "Liian vähän jäseniä";
        return false;
    }
    return true;
}

// id: String
function haeKilpailunTiedot(id) {
    let url = new URL("http://users.jyu.fi/~jovimajo/cgi-bin/tiea2080/vt5/flask.cgi/joukkuelistaus");
    url.searchParams.append("id", id);

    fetch(url)
    .then(function(response) {
        // muunnetaan response-objektin sisältö jsoniksi
        // https://developer.mozilla.org/en-US/docs/Web/API/Response
        return response.json();
     })
        // käsitellään varsinainen tulos
    .then(function(data) {
        kilpailunData = data;
        naytaJoukkuelistaus(data);
        asetaJoukkueForm(id, data);
     })
    .catch(error => console.log('Virhe datan näyttämisessä:', error));
}

function asetaJoukkueForm(id, data) {
    for (joukkue of data) {
        if (joukkue.joukkue_id.toString() === id) {
            try {
                document.getElementById('joukkue_nimi_virhe').textContent = "";
                document.getElementById('joukkue_jasenet_virhe').textContent = "";

                let joukkueen_nimi = document.getElementById('joukkue_input');
                let joukkueLink_nimi = document.getElementById('muokkaaLink');
                joukkueen_nimi.value = joukkue.joukkue_nimi;
                joukkueLink_nimi.textContent = joukkue.joukkue_nimi;

                document.getElementById(joukkue.sarja_nimi.split(' ').join('')).checked = true;

                // Tyhjennetään formi
                for (let i = 0; i < 5; i++) {
                    document.getElementById('jasen-' + i.toString()).value = "";
                }
                
                JSON.parse(joukkue.jasenet).forEach( (value, i) => {
                    document.getElementById('jasen-' + i.toString()).value = value;
                } )

                
            }
            catch(err) {
                console.log(err);
            }
        }
    }
}

function naytaJoukkuelistaus(data) {
    let paikka = document.getElementById('joukkuelistaus')
    while (paikka.firstChild) {
        paikka.removeChild(paikka.firstChild);
    }

    let sarjat = [];

    for (joukkue of data) {
        if (!sarjat.includes(joukkue.sarja_nimi)) {
            sarjat.push(joukkue.sarja_nimi);
        }        
    }

    let ul = document.createElement('ul');

    for (sarja of sarjat) {
        let li = document.createElement('li');
        li.textContent = sarja;
        
        let sarjan_joukkueet = []
        for (joukkue of data) {
            if (joukkue.sarja_nimi === sarja) {
                sarjan_joukkueet.push(joukkue);
            }
        }

        sarjan_joukkueet.sort( (a, b) => {
            if (a.joukkue_nimi.toUpperCase() < b.joukkue_nimi.toUpperCase()) return -1;
            if (a.joukkue_nimi.toUpperCase() > b.joukkue_nimi.toUpperCase()) return 1;
            return 0;
        });

        let ul_joukkueet = document.createElement('ul');
        for (joukkue of sarjan_joukkueet) {
            let li_joukkue = document.createElement('li');
            li_joukkue.textContent = joukkue.joukkue_nimi;

            let ul_jasenet = document.createElement('ul');

            for (jasen of JSON.parse(joukkue.jasenet)) {
                let li_jasen = document.createElement('li');
                li_jasen.textContent = jasen;
                ul_jasenet.appendChild(li_jasen);
            }
            li_joukkue.appendChild(ul_jasenet);
            ul_joukkueet.appendChild(li_joukkue);          
        }
        li.appendChild(ul_joukkueet);
        ul.appendChild(li);
        paikka.appendChild(ul);
    }
}

// Asettaa onClickit naveille, sulkee ne mitä ei ole käytössä.
function asetaNavClickit() {
    $('#muokkaaLink').click((e) => {
        e.preventDefault();

        if (kilpailunData.length > 0) {
            asetaJoukkueForm(JOUKKUEEN_ID, kilpailunData);
        }

        $('#joukkuelistaus').hide();
        $('#logout').hide();
        $('#muokkaa').show();
    });

    $('#joukkuelistausLink').click((e) => {
        e.preventDefault();

        if (kilpailunData.length > 0) {
            asetaJoukkueForm(JOUKKUEEN_ID, kilpailunData);
        }

        $('#joukkuelistaus').show();
        $('#muokkaa').hide();
        $('#logout').hide();
    });

    $('#logoutLink').click((e) => {
        e.preventDefault();

        if (kilpailunData.length > 0) {
            asetaJoukkueForm(JOUKKUEEN_ID, kilpailunData);
        }

        $('#logout').show();
        $('#muokkaa').hide();
        $('#joukkuelistaus').hide();
    });
}