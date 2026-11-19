from datetime import date
from agent.tendances import calculer_tendance, NOUVEAU, HAUSSE, BAISSE, STABLE

REF = date(2026, 11, 16)  # période en cours : 10/11 → 16/11 ; précédente : 03/11 → 09/11


def t(dates, **kw):
    return calculer_tendance(dates, REF, **kw)


def test_nouveau_si_aucun_message_avant_la_periode():
    assert t(["2026-11-10T08:00", "2026-11-12T09:00"])["statut"] == NOUVEAU


def test_hausse():
    r = t(["2026-11-08T10:00", "2026-11-10T10:00", "2026-11-11T10:00", "2026-11-14T10:00"])
    assert (r["statut"], r["courant"], r["precedent"]) == (HAUSSE, 3, 1)


def test_baisse_meme_sans_message_recent():
    assert t(["2026-10-20T10:00", "2026-11-04T10:00", "2026-11-05T10:00"])["statut"] == BAISSE


def test_stable_sous_le_seuil():
    assert t(["2026-11-04T10:00", "2026-11-10T10:00", "2026-11-11T10:00"])["statut"] == STABLE


def test_bornes_de_periode_incluses():
    r = t(["2026-11-09T23:59", "2026-11-10T00:00", "2026-11-16T23:59", "2026-11-17T08:00", "2026-11-03T00:00"])
    assert (r["courant"], r["precedent"]) == (2, 2)  # le 17/11 est hors période


def test_seuil_parametrable():
    dates = ["2026-11-05T10:00", "2026-11-10T10:00", "2026-11-11T10:00"]
    assert t(dates, seuil=1)["statut"] == HAUSSE
    assert t(dates, seuil=2)["statut"] == STABLE


def test_periode_parametrable():
    assert t(["2026-11-02T10:00", "2026-11-15T10:00"], periode_jours=14)["statut"] == STABLE
