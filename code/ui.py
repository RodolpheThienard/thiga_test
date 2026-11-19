"""Habillage visuel de l'interface : feuille de style et composants HTML (cartes, bandeau, étiquettes).

Purement présentationnel : aucune règle de calcul ici.
"""
from __future__ import annotations

from html import escape

import streamlit as st

# Icônes au trait (style Lucide, licence ISC), 24 × 24.
ICONES = {
    "boussole": '<circle cx="12" cy="12" r="10"/><path d="m16.24 7.76-2.12 6.36-6.36 2.12 2.12-6.36 6.36-2.12z"/>',
    "boite": '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6'
             'l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    "calques": '<path d="m12 2 10 5-10 5L2 7l10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "cible": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "bouclier": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1'
                'c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
                '<path d="m9 12 2 2 4-4"/>',
}

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="st-"]:not([data-testid="stIconMaterial"]), .stMarkdown, button, input, textarea, select {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
:root {
  --c-texte: #1B2333; --c-doux: #6B7689; --c-trait: #E3E8F0; --c-carte: #FFFFFF;
  --c-bleu: #2F6FDE; --c-bleu-pale: #E8F0FD; --ombre: 0 1px 2px rgba(16,24,40,.04), 0 4px 16px rgba(16,24,40,.04);
}

/* ---- Page */
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }
h1, h2, h3 { letter-spacing: -0.01em; color: var(--c-texte); }
h3 { font-size: 1.15rem !important; font-weight: 600 !important; }

/* ---- Barre latérale */
[data-testid="stSidebar"] { border-right: 1px solid var(--c-trait); }
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarUserContent"] { padding-top: 1.2rem; }
.cp-marque { display: flex; align-items: center; gap: .6rem; margin: 0 0 .2rem 0; }
.cp-marque .logo { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center;
  background: linear-gradient(135deg, #2F6FDE, #1AA6A0); color: #fff; }
.cp-marque .nom { font-weight: 700; font-size: 1.05rem; color: var(--c-texte); line-height: 1.1; }
.cp-marque .sous { font-size: .72rem; color: var(--c-doux); }
.cp-pastille { display: inline-block; font-size: .7rem; font-weight: 600; padding: .15rem .55rem;
  border-radius: 999px; margin-top: .5rem; }
.cp-pastille.horsligne { background: #FDECEC; color: #B4232F; }
.cp-pastille.connecte { background: #E3F6EC; color: #1E7B4D; }
.cp-section { font-size: .68rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
  color: #8A94A6; margin: 1.1rem 0 .35rem 0; }
.cp-carte-sombre { margin-top: 1.2rem; padding: .9rem 1rem; border-radius: 14px; color: #fff;
  background: linear-gradient(135deg, #12306B, #2F6FDE); }
.cp-carte-sombre .lib { font-size: .65rem; letter-spacing: .08em; text-transform: uppercase; opacity: .8; }
.cp-carte-sombre .val { font-weight: 700; font-size: 1rem; margin: .15rem 0 .4rem 0; }
.cp-carte-sombre .badge { display: inline-block; font-size: .68rem; font-weight: 600; padding: .1rem .5rem;
  border-radius: 999px; background: #E3F6EC; color: #1E7B4D; }

/* ---- Bandeau d'accueil */
.cp-bandeau { position: relative; overflow: hidden; border-radius: 18px; padding: 1.6rem 1.8rem; color: #fff;
  background: linear-gradient(115deg, #17A589 0%, #2378C9 55%, #1C4FA8 100%); margin-bottom: 1rem; }
.cp-bandeau::after { content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
  border-radius: 50%; background: rgba(255,255,255,.08); }
.cp-bandeau .surtitre { font-size: .72rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; opacity: .9; }
.cp-bandeau .titre { font-size: 1.9rem; font-weight: 600; line-height: 1.2; margin: .35rem 0 .45rem 0; }
.cp-bandeau .texte { font-size: .9rem; opacity: .92; max-width: 640px; }
.cp-bandeau .pilule { display: inline-block; margin-top: .9rem; padding: .45rem 1rem; border-radius: 999px;
  background: #0F1B33; color: #fff; font-size: .82rem; font-weight: 600; }
.cp-bandeau .pilule.alerte { background: #FFF4E5; color: #9A5B00; }

/* ---- Cartes indicateurs */
.cp-kpi { background: var(--c-carte); border-radius: 16px; padding: .9rem 1rem; display: flex; gap: .8rem;
  align-items: center; box-shadow: var(--ombre); min-height: 86px; }
.cp-kpi .rond { flex: none; width: 42px; height: 42px; border-radius: 50%; display: grid; place-items: center; }
.cp-kpi .lib { font-size: .78rem; color: var(--c-doux); line-height: 1.25; }
.cp-kpi .val { font-size: 1.25rem; white-space: nowrap; font-weight: 600; color: var(--c-texte); margin-top: .1rem; }

/* ---- Onglets en pilules (Streamlit ≥ 1.67 : onglets react-aria) */
[data-testid="stTabs"] [role="tablist"] { gap: .25rem; border-bottom: none !important; background: #E9EDF4;
  padding: .3rem; border-radius: 12px; width: fit-content; box-shadow: none; }
[data-testid="stTab"] { border-radius: 9px; padding: .45rem 1.05rem !important; margin: 0 !important; }
[data-testid="stTab"] p { font-weight: 500; color: var(--c-doux); font-size: .88rem; }
[data-testid="stTab"][aria-selected="true"] { background: #fff; box-shadow: var(--ombre); }
[data-testid="stTab"][aria-selected="true"] p { color: var(--c-texte); font-weight: 600; }
[data-testid="stTab"] .react-aria-SelectionIndicator { display: none; }
[data-testid="stTabPanel"] { padding-top: 1.2rem; }

/* ---- Cartes blanches : conteneurs à bordure, dépliants, tableaux */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) ,
div[data-testid="stExpander"] details {
  background: var(--c-carte); border: none !important; border-radius: 16px; box-shadow: var(--ombre);
}
div[data-testid="stExpander"] { margin-bottom: .55rem; }
div[data-testid="stExpander"] summary { padding: .85rem 1rem; }
div[data-testid="stExpander"] summary p { font-weight: 500; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { background: #fff; border-radius: 14px;
  box-shadow: var(--ombre); padding: .25rem; }
[data-testid="stAlert"] { border-radius: 14px; border: none; }

/* ---- Boutons */
.stButton > button, .stDownloadButton > button { border-radius: 999px; font-weight: 600; padding: .45rem 1.1rem; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] { box-shadow: 0 4px 12px rgba(47,111,222,.25); }

/* ---- Barre de progression du sprint */
[data-testid="stProgress"] > div > div { height: 8px !important; border-radius: 999px; }
</style>
"""


def injecter_style() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)


def icone(nom: str, couleur: str = "currentColor", taille: int = 20) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{taille}" height="{taille}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{couleur}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONES[nom]}</svg>')


def marque(mode_connecte: bool) -> None:
    pastille = ('<span class="cp-pastille connecte">connecté</span>' if mode_connecte
                else '<span class="cp-pastille horsligne">hors ligne</span>')
    st.markdown(f'<div class="cp-marque"><div class="logo">{icone("boussole", "#fff", 20)}</div>'
                f'<div><div class="nom">Copilote PO</div><div class="sous">Orbiteam</div></div></div>{pastille}',
                unsafe_allow_html=True)


def section(titre: str) -> None:
    st.markdown(f'<div class="cp-section">{escape(titre)}</div>', unsafe_allow_html=True)


def carte_sombre(libelle: str, valeur: str, badge: str) -> None:
    st.markdown(f'<div class="cp-carte-sombre"><div class="lib">{escape(libelle)}</div>'
                f'<div class="val">{escape(valeur)}</div><span class="badge">{escape(badge)}</span></div>',
                unsafe_allow_html=True)


def bandeau(surtitre: str, titre: str, texte: str, pilule: str | None = None, alerte: bool = False) -> None:
    html_pilule = f'<span class="pilule{" alerte" if alerte else ""}">{escape(pilule)}</span>' if pilule else ""
    st.markdown(f'<div class="cp-bandeau"><div class="surtitre">{escape(surtitre)}</div>'
                f'<div class="titre">{escape(titre)}</div><div class="texte">{escape(texte)}</div>'
                f'{html_pilule}</div>', unsafe_allow_html=True)


def carte_kpi(nom_icone: str, couleur: str, fond: str, libelle: str, valeur: str) -> str:
    return (f'<div class="cp-kpi"><div class="rond" style="background:{fond}">{icone(nom_icone, couleur)}</div>'
            f'<div><div class="lib">{escape(libelle)}</div><div class="val">{escape(valeur)}</div></div></div>')
