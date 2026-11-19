from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from agent.config import FICHIER_FEEDBACKS
from agent.sources import charger_fichier, analyser_email, filtrer_par_mot_cle, fusionner


def test_lecture_du_fichier_de_sauvegarde():
    fb = charger_fichier(FICHIER_FEEDBACKS)
    assert len(fb) == 50 and {f["canal"] for f in fb} == {"email", "ticket", "commentaire"}
    assert fb[2]["id"] == "FB-003" and fb[2]["date"].startswith("2026-10-21")


def test_email_texte():
    msg = MIMEText("L'export PDF est illisible.", "plain", "utf-8")
    msg["From"] = "Jeanne Dupont <Jeanne.Dupont@Exemple.fr>"
    msg["Subject"] = "Export PDF"
    msg["Date"] = "Wed, 18 Nov 2026 09:30:00 +0100"
    f = analyser_email(msg.as_bytes(), "42")
    assert f["id"] == "MAIL-42" and f["canal"] == "email"
    assert f["email"] == "jeanne.dupont@exemple.fr" and f["auteur"] == "Jeanne Dupont"
    assert f["contenu"] == "L'export PDF est illisible." and f["date"].startswith("2026-11-18")


def test_email_html_seul():
    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText("<p>Le <b>Kanban</b> est lent</p><style>p{}</style>", "html", "utf-8"))
    msg["From"] = "a@b.fr"
    msg["Date"] = "Wed, 18 Nov 2026 09:30:00 +0100"
    assert analyser_email(msg.as_bytes(), "1")["contenu"] == "Le Kanban est lent"


def test_fusion_sans_doublon_et_triee():
    a = [{"id": "X", "date": "2026-11-02"}, {"id": "Y", "date": "2026-11-01"}]
    b = [{"id": "X", "date": "2026-11-02"}, {"id": "Z", "date": "2026-11-03"}]
    assert [f["id"] for f in fusionner(a, b)] == ["Y", "X", "Z"]


def test_filtre_par_mot_cle_sur_objet_ou_contenu_sans_casse_ni_accents():
    mails = [{"id": "MAIL-1", "objet": "Feedback Orbiteam", "contenu": "Le Gantt rame."},
             {"id": "MAIL-2", "objet": "Réunion", "contenu": "Retour sur la sécurité du SSO."},
             {"id": "MAIL-3", "objet": None, "contenu": "Newsletter du mois."}]
    assert [m["id"] for m in filtrer_par_mot_cle(mails, "orbiteam")] == ["MAIL-1"]
    assert [m["id"] for m in filtrer_par_mot_cle(mails, "  SECURITE ")] == ["MAIL-2"]
    assert filtrer_par_mot_cle(mails, "") == mails and filtrer_par_mot_cle(mails, None) == mails
    assert filtrer_par_mot_cle(mails, "facture") == []


# ---------------------------------------------------------------- JIRA
from agent.sources import analyser_ticket_jira, lire_jira  # noqa: E402

TICKET_JIRA = {
    "key": "SUP-12",
    "fields": {
        "summary": "Kanban très lent",
        "created": "2026-11-17T09:15:00.000+0100",
        "reporter": {"displayName": "Camille Martin", "emailAddress": "Camille.Martin@BTP-Rhone.fr"},
        "description": {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Le Kanban met 30 s à s'afficher."}]},
            {"type": "bulletList", "content": [{"type": "listItem", "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Projet de 400 tâches"}]}]}]},
        ]},
    },
}


def test_ticket_jira_au_format_commun():
    f = analyser_ticket_jira(TICKET_JIRA)
    assert f["id"] == "JIRA-SUP-12" and f["canal"] == "ticket" and f["source"] == "JIRA"
    assert f["email"] == "camille.martin@btp-rhone.fr" and f["entreprise"] == "btp-rhone.fr"
    assert f["auteur"] == "Camille Martin" and f["objet"] == "Kanban très lent"
    assert "30 s à s'afficher" in f["contenu"] and "400 tâches" in f["contenu"]
    assert f["date"].startswith("2026-11-17")


def test_ticket_jira_sans_description_ni_email():
    f = analyser_ticket_jira({"key": "SUP-1", "fields": {"summary": "Export PDF illisible",
                                                          "reporter": {"displayName": "Client X"}}})
    assert f["contenu"] == "Export PDF illisible" and f["email"] is None and f["auteur"] == "Client X"


def test_lecture_jira_paginee_et_authentifiee():
    appels = []

    def faux_jira(url, entetes):
        appels.append((url, entetes))
        if "nextPageToken" not in url:
            return {"issues": [TICKET_JIRA], "nextPageToken": "page2"}
        return {"issues": [{**TICKET_JIRA, "key": "SUP-13"}], "isLast": True}

    tickets = lire_jira("https://orbiteam.atlassian.net/", "po@orbiteam.fr", "jeton", "project = SUP",
                        requete=faux_jira)
    assert [t["id"] for t in tickets] == ["JIRA-SUP-12", "JIRA-SUP-13"]
    assert appels[0][0].startswith("https://orbiteam.atlassian.net/rest/api/3/search/jql?jql=project+%3D+SUP")
    assert appels[0][1]["Authorization"].startswith("Basic ") and "nextPageToken=page2" in appels[1][0]
