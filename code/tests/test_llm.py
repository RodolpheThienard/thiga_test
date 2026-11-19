import pytest
from pydantic import BaseModel
from agent.llm import ClientLLM, ErreurLLM, ErreurHorsLigne, extraire_json


class Modele(BaseModel):
    valeur: int


def client(tmp_path, reponses):
    appels = []

    def transport(systeme, messages, temperature):
        appels.append(messages)
        return reponses.pop(0)
    return ClientLLM(transport=transport, dossier_cache=tmp_path), appels


def test_extraction_json_avec_texte_ou_bloc():
    assert extraire_json('Voici :\n```json\n{"valeur": 1}\n```') == '{"valeur": 1}'
    assert extraire_json('blabla {"valeur": 2} fin') == '{"valeur": 2}'


def test_json_valide_accepte(tmp_path):
    c, appels = client(tmp_path, ['{"valeur": 3}'])
    assert c.appeler("P4_justification", "", "msg", Modele).valeur == 3 and len(appels) == 1


def test_json_invalide_une_relance_avec_l_erreur(tmp_path):
    c, appels = client(tmp_path, ['{"valeur": "x"}', '{"valeur": 4}'])
    assert c.appeler("P4_justification", "", "msg", Modele).valeur == 4
    assert len(appels) == 2 and "pas exploitable" in appels[1][-1]["content"]


def test_deux_echecs_erreur_explicite(tmp_path):
    c, _ = client(tmp_path, ["pas de json", "toujours pas"])
    with pytest.raises(ErreurLLM):
        c.appeler("P4_justification", "", "msg", Modele)


def test_cache_reutilise_sans_nouvel_appel(tmp_path):
    c, appels = client(tmp_path, ['{"valeur": 5}'])
    c.appeler("P4_justification", "", "msg", Modele)
    assert c.appeler("P4_justification", "", "msg", Modele).valeur == 5 and len(appels) == 1
    hors_ligne = ClientLLM(transport=None, dossier_cache=tmp_path)
    assert hors_ligne.appeler("P4_justification", "", "msg", Modele).valeur == 5


def test_hors_ligne_sans_cache(tmp_path):
    with pytest.raises(ErreurHorsLigne):
        ClientLLM(transport=None, dossier_cache=tmp_path).appeler("P4_justification", "", "autre", Modele)
