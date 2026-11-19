from agent.regroupement import controler_regroupement, THEME_NON_REGROUPE


def t(titre, demandes):
    return {"titre": titre, "demandes": demandes, "backlog_id": None, "hors_vision": False}


def test_regroupement_correct_inchange():
    themes, alertes = controler_regroupement([t("A", ["1#1", "2#1"]), t("B", ["3#1"])], ["1#1", "2#1", "3#1"])
    assert alertes == [] and [x["theme_id"] for x in themes] == ["TH-1", "TH-2"]


def test_doublon_retire_du_second_theme():
    themes, alertes = controler_regroupement([t("A", ["1#1"]), t("B", ["1#1", "2#1"])], ["1#1", "2#1"])
    assert themes[1]["demandes"] == ["2#1"] and len(alertes) == 1


def test_demande_oubliee_placee_dans_un_theme_dedie():
    themes, alertes = controler_regroupement([t("A", ["1#1"])], ["1#1", "2#1"])
    assert themes[-1]["titre"] == THEME_NON_REGROUPE and themes[-1]["demandes"] == ["2#1"]


def test_identifiant_inconnu_et_theme_vide_supprimes():
    themes, alertes = controler_regroupement([t("A", ["9#9"]), t("B", ["1#1"])], ["1#1"])
    assert [x["titre"] for x in themes] == ["B"] and themes[0]["theme_id"] == "TH-1"
