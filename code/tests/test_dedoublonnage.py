from agent.dedoublonnage import statistiques_theme, identite

FB = {
    "A1": {"id": "A1", "email": "thomas@devnest.fr", "auteur": "Thomas", "date": "2026-10-23T09:00"},
    "A2": {"id": "A2", "email": "Thomas@DevNest.fr", "auteur": "Thomas", "date": "2026-10-28T09:00"},
    "A3": {"id": "A3", "email": "thomas@devnest.fr", "auteur": "Thomas", "date": "2026-11-13T09:00"},
    "B1": {"id": "B1", "email": "lucas@datapulse.fr", "auteur": "Lucas", "date": "2026-10-30T09:00"},
    "P1": {"id": "P1", "email": None, "auteur": "Mehdi K.", "date": "2026-11-14T09:00"},
    "P2": {"id": "P2", "email": None, "auteur": "Mehdi K.", "date": "2026-11-15T09:00"},
}
D = {
    "A1#1": {"feedback_id": "A1", "gravite": "Majeur", "enjeu_business": "Adoption"},
    "A2#1": {"feedback_id": "A2", "gravite": "Majeur", "enjeu_business": "Rétention"},
    "A3#1": {"feedback_id": "A3", "gravite": "Mineur", "enjeu_business": "Efficacité"},
    "B1#1": {"feedback_id": "B1", "gravite": "Mineur", "enjeu_business": "Adoption"},
    "P1#1": {"feedback_id": "P1", "gravite": "Bloquant", "enjeu_business": "Rétention"},
    "P2#1": {"feedback_id": "P2", "gravite": "Bloquant", "enjeu_business": "Rétention"},
}


def test_relances_de_la_meme_personne_comptent_pour_un_demandeur():
    s = statistiques_theme(["A1#1", "A2#1", "A3#1", "B1#1"], D, FB)
    assert (s["nb_messages"], s["nb_demandeurs"], s["nb_relances"]) == (4, 2, 2)


def test_gravite_et_enjeu_max_retenus_pour_le_demandeur():
    s = statistiques_theme(["A1#1", "A2#1", "A3#1"], D, FB)
    thomas = s["demandeurs"][0]
    assert (thomas["gravite"], thomas["enjeu_business"], thomas["nb_messages"]) == ("Majeur", "Rétention", 3)
    assert s["gravite_max"] == "Majeur" and s["enjeux"][0] == "Rétention"


def test_avis_sans_email_identifie_par_auteur():
    assert identite(FB["P1"]) == identite(FB["P2"])
    assert statistiques_theme(["P1#1", "P2#1"], D, FB)["nb_demandeurs"] == 1


def test_deux_demandes_du_meme_feedback_comptent_un_message():
    fb = {"X": {"id": "X", "email": "x@a.fr", "date": "2026-11-12T10:00"}}
    d = {"X#1": {"feedback_id": "X", "gravite": "Majeur", "enjeu_business": "Efficacité"},
         "X#2": {"feedback_id": "X", "gravite": "Mineur", "enjeu_business": "Efficacité"}}
    assert statistiques_theme(["X#1", "X#2"], d, fb)["nb_messages"] == 1
