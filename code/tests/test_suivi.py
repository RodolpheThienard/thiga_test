from agent.suivi import (DEPLOYE, EN_COURS, charger_suivi, cle_suivi, destinataires, enregistrer_envoi,
                         envoyer_email, etat_theme, rediger_email)


def test_etat_selon_backlog_et_suivi():
    assert etat_theme(None, None) == "À créer"
    assert etat_theme("À faire", "complète") == "Ticket créé"
    assert etat_theme("En cours", None) == "En cours (backlog)"
    assert etat_theme("Livré", "partielle") == "Livré, insuffisant"
    assert etat_theme(None, None, {"statut": EN_COURS}) == EN_COURS  # le suivi du PO prime
    assert etat_theme("À faire", None, {"statut": DEPLOYE}) == DEPLOYE


def test_cle_de_suivi_stable():
    assert cle_suivi({"backlog_id": "BL-101", "titre": "Export"}) == "BL-101"
    assert cle_suivi({"backlog_id": None, "titre": "Crash Android"}) == "Crash Android"


def test_destinataires_reels_distincts_et_demo_exclue():
    fbx = {
        "MAIL-1": {"id": "MAIL-1", "source": "Boîte Gmail", "email": "Camille@Client.fr"},
        "MAIL-2": {"id": "MAIL-2", "source": "Boîte Gmail", "email": "camille@client.fr"},  # relance
        "JIRA-SUP-1": {"id": "JIRA-SUP-1", "source": "JIRA", "email": "paul@client.fr"},
        "FB-001": {"id": "FB-001", "source": "Email support", "email": "fictif@demo.fr"},
        "FB-002": {"id": "FB-002", "source": "Avis Play Store", "email": None},
    }
    adresses, exclus = destinataires(list(fbx), fbx)
    assert adresses == ["camille@client.fr", "paul@client.fr"] and exclus == 1


def test_modeles_d_email():
    objet, corps = rediger_email(EN_COURS, "Crash Android")
    assert "en cours de traitement" in objet and "Crash Android" in corps
    objet, corps = rediger_email(DEPLOYE, "Crash Android")
    assert "Correctif déployé" in objet and "déployé" in corps


def test_envoi_en_copie_cachee():
    envois = []

    class FauxSMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def login(self, *a): envois.append(("login", a[0]))
        def send_message(self, msg, from_addr, to_addrs): envois.append((msg, to_addrs))

    envoyer_email("po@orbiteam.fr", "secret", ["a@x.fr", "b@y.fr"], "Objet", "Corps", smtp=FauxSMTP)
    msg, to_addrs = envois[1]
    assert to_addrs == ["po@orbiteam.fr", "a@x.fr", "b@y.fr"]
    assert msg["To"] == "po@orbiteam.fr" and msg["Bcc"] is None and "a@x.fr" not in msg.as_string()


def test_journal_des_envois(tmp_path):
    chemin = tmp_path / "suivi.json"
    enregistrer_envoi("BL-101", EN_COURS, 3, chemin)
    suivi = enregistrer_envoi("BL-101", DEPLOYE, 3, chemin)
    assert suivi["BL-101"]["statut"] == DEPLOYE and len(suivi["BL-101"]["historique"]) == 2
    assert charger_suivi(chemin) == suivi and "@" not in chemin.read_text()
