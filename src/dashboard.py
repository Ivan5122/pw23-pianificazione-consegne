"""Generazione della pagina HTML statica del project work."""

from __future__ import annotations

import html
import math
from pathlib import Path
from typing import Any


COLORI_SCENARI = ("#176b87", "#c45d2c")
COLORI_COSTI = ("#2b5d8a", "#d08a2e", "#4e8b57")


def _numero(valore: float, decimali: int = 2) -> str:
    testo = f"{valore:,.{decimali}f}"
    return testo.replace(",", "X").replace(".", ",").replace("X", ".")


def _punto(x: float, y: float) -> str:
    return f"{x:.1f},{y:.1f}"


def _mappa_nodi(dati: dict[str, Any], larghezza: int, altezza: int) -> dict[str, tuple]:
    nodi = [dati["deposito"]] + dati["clienti"]
    latitudini = [float(nodo["lat"]) for nodo in nodi]
    longitudini = [float(nodo["lon"]) for nodo in nodi]
    lat_min, lat_max = min(latitudini), max(latitudini)
    lon_min, lon_max = min(longitudini), max(longitudini)
    margine_x, margine_y = 85.0, 65.0
    ampiezza = larghezza - 2 * margine_x
    altezza_utile = altezza - 2 * margine_y

    posizioni = {}
    for nodo in nodi:
        x = margine_x + (float(nodo["lon"]) - lon_min) / (lon_max - lon_min) * ampiezza
        y = margine_y + (lat_max - float(nodo["lat"])) / (
            lat_max - lat_min
        ) * altezza_utile
        posizioni[nodo["id"]] = (x, y)
    return posizioni


def _mappa_etichette(dati: dict[str, Any]) -> dict[str, tuple[float, float]]:
    offset = {
        "D": (-35, 27),
        "C1": (-70, 27),
        "C2": (12, -10),
        "C3": (-15, 37),
        "C4": (13, 24),
        "C5": (13, -13),
    }
    return {
        nodo["id"]: offset.get(nodo["id"], (12, -10))
        for nodo in [dati["deposito"]] + dati["clienti"]
    }


def _crea_grafo(
    dati: dict[str, Any],
    risultato: dict[str, Any],
    titolo: str,
) -> str:
    larghezza, altezza = 760, 470
    posizioni = _mappa_nodi(dati, larghezza, altezza)
    etichette = {
        nodo["id"]: f'{nodo["id"]} · {nodo["localita"]}'
        for nodo in [dati["deposito"]] + dati["clienti"]
    }
    offset = _mappa_etichette(dati)
    parti = [
        f'<svg class="grafo" viewBox="0 0 {larghezza} {altezza}" '
        f'role="img" aria-label="{html.escape(titolo)}">',
        f"<title>{html.escape(titolo)}</title>",
        '<rect width="760" height="470" rx="12" fill="#f6f2e9"/>',
    ]

    for indice_veicolo, veicolo in enumerate(risultato["veicoli"]):
        colore = COLORI_SCENARI[indice_veicolo % len(COLORI_SCENARI)]
        punti = " ".join(
            _punto(*posizioni[identificativo])
            for identificativo in veicolo["sequenza_nodi"]
        )
        parti.append(
            f'<polyline points="{punti}" fill="none" stroke="{colore}" '
            'stroke-width="4" stroke-linecap="round" stroke-linejoin="round" '
            'opacity="0.88"/>'
        )
        for numero_tappa, identificativo in enumerate(
            veicolo["sequenza_nodi"][1:-1], start=1
        ):
            x, y = posizioni[identificativo]
            parti.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" '
                f'fill="{colore}" stroke="#ffffff" stroke-width="3"/>'
            )
            parti.append(
                f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" '
                f'font-size="13" font-weight="700" fill="#ffffff">{numero_tappa}</text>'
            )

    for nodo in [dati["deposito"]] + dati["clienti"]:
        x, y = posizioni[nodo["id"]]
        if nodo["id"] == "D":
            parti.append(
                f'<rect x="{x - 14:.1f}" y="{y - 14:.1f}" width="28" height="28" '
                'rx="5" fill="#263238" stroke="#ffffff" stroke-width="3"/>'
            )
            parti.append(
                f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" '
                'font-size="13" font-weight="700" fill="#ffffff">D</text>'
            )
        elif nodo["id"] not in {
            identificativo
            for veicolo in risultato["veicoli"]
            for identificativo in veicolo["sequenza_nodi"][1:-1]
        }:
            parti.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" '
                'fill="#ffffff" stroke="#263238" stroke-width="2"/>'
            )

        dx, dy = offset[nodo["id"]]
        parti.append(
            f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" '
            'font-size="13" fill="#243238" font-family="Arial, sans-serif">'
            f"{html.escape(etichette[nodo['id']])}</text>"
        )

    parti.append("</svg>")
    legenda = []
    for indice_veicolo, veicolo in enumerate(risultato["veicoli"]):
        colore = COLORI_SCENARI[indice_veicolo % len(COLORI_SCENARI)]
        percorso = " → ".join(veicolo["sequenza_nodi"])
        legenda.append(
            '<span class="sequenza">'
            f'<i style="background:{colore}"></i>'
            f"Veicolo {indice_veicolo + 1}: {html.escape(percorso)}"
            "</span>"
        )
    return (
        "".join(parti)
        + '<div class="legenda-percorsi">'
        + "".join(legenda)
        + "</div>"
    )


def _crea_grafico_costi(confronto: dict[str, Any]) -> str:
    larghezza, altezza = 760, 330
    margine_sinistro, margine_superiore, margine_inferiore = 70, 35, 55
    valori = [confronto["costo_a"], confronto["costo_b"]]
    massimo = max(costo["totale"] for costo in valori)
    limite = max(50.0, math.ceil(massimo / 50.0) * 50.0)
    area_altezza = altezza - margine_superiore - margine_inferiore
    larghezza_barra = 120
    posizioni_x = (250, 500)
    parti = [
        f'<svg class="grafico" viewBox="0 0 {larghezza} {altezza}" '
        'role="img" aria-label="Confronto dei costi base">',
        '<rect width="760" height="330" rx="12" fill="#ffffff"/>',
    ]

    for indice in range(6):
        valore = limite * indice / 5
        y = margine_superiore + area_altezza - area_altezza * indice / 5
        parti.append(
            f'<line x1="{margine_sinistro}" y1="{y:.1f}" x2="720" y2="{y:.1f}" '
            'stroke="#dde3e5" stroke-width="1"/>'
        )
        parti.append(
            f'<text x="{margine_sinistro - 10}" y="{y + 4:.1f}" '
            'text-anchor="end" font-size="12" fill="#53636b">'
            f"{_numero(valore, 0)} €</text>"
        )

    for indice, (nome, costo) in enumerate(zip(("Scenario A", "Scenario B"), valori)):
        x = posizioni_x[indice]
        base_y = margine_superiore + area_altezza
        accumulato = 0.0
        voci = (
            ("Noleggio", costo["noleggio"]),
            ("Chilometri", costo["costo_km"]),
            ("Autisti", costo["costo_autisti"]),
        )
        for indice_voce, (_, valore) in enumerate(voci):
            altezza_barra = area_altezza * valore / limite
            y = base_y - area_altezza * (accumulato + valore) / limite
            accumulato += valore
            parti.append(
                f'<rect x="{x - larghezza_barra / 2:.1f}" y="{y:.1f}" '
                f'width="{larghezza_barra}" height="{altezza_barra:.1f}" '
                f'fill="{COLORI_COSTI[indice_voce]}"/>'
            )
        parti.append(
            f'<text x="{x}" y="{base_y + 25}" text-anchor="middle" '
            f'font-size="15" font-weight="700" fill="#243238">{nome}</text>'
        )
        parti.append(
            f'<text x="{x}" y="{base_y + 43}" text-anchor="middle" '
            f'font-size="13" fill="#53636b">Totale {_numero(costo["totale"])} €</text>'
        )

    for indice, (nome, colore) in enumerate(
        zip(("Noleggio", "Costo chilometrico", "Autisti"), COLORI_COSTI)
    ):
        x = 250 + indice * 155
        parti.append(f'<rect x="{x}" y="13" width="14" height="14" fill="{colore}"/>')
        parti.append(
            f'<text x="{x + 20}" y="25" font-size="12" fill="#243238">'
            f"{html.escape(nome)}</text>"
        )

    parti.append("</svg>")
    return "".join(parti)


def _crea_grafico_sensibilita(nome: str, serie: dict[str, Any]) -> str:
    larghezza, altezza = 760, 310
    sinistra, destra, alto, basso = 75, 25, 35, 55
    area_larghezza = larghezza - sinistra - destra
    area_altezza = altezza - alto - basso
    valori = serie["valori"]
    costi = serie["costo_a"] + serie["costo_b"]
    minimo_y = 0.0
    massimo_y = max(50.0, math.ceil(max(costi) / 50.0) * 50.0)
    minimo_x, massimo_x = min(valori), max(valori)

    def x_grafico(valore: float) -> float:
        if massimo_x == minimo_x:
            return sinistra + area_larghezza / 2
        return sinistra + (valore - minimo_x) / (massimo_x - minimo_x) * area_larghezza

    def y_grafico(valore: float) -> float:
        return alto + area_altezza - (valore - minimo_y) / (
            massimo_y - minimo_y
        ) * area_altezza

    parti = [
        f'<svg class="grafico" viewBox="0 0 {larghezza} {altezza}" '
        f'role="img" aria-label="Sensibilità {html.escape(nome)}">',
        '<rect width="760" height="310" rx="12" fill="#ffffff"/>',
    ]

    for indice_tick in range(6):
        valore_y = massimo_y * indice_tick / 5
        y = y_grafico(valore_y)
        parti.append(
            f'<line x1="{sinistra}" y1="{y:.1f}" x2="{larghezza - destra}" '
            f'y2="{y:.1f}" stroke="#dde3e5" stroke-width="1"/>'
        )
        parti.append(
            f'<text x="{sinistra - 10}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#53636b">{_numero(valore_y, 0)} €</text>'
        )

    for proporzione in (0.0, 0.5, 1.0):
        valore_x = minimo_x + (massimo_x - minimo_x) * proporzione
        x = x_grafico(valore_x)
        parti.append(
            f'<line x1="{x:.1f}" y1="{alto}" x2="{x:.1f}" '
            f'y2="{altezza - basso}" stroke="#eef1f2" stroke-width="1"/>'
        )
        parti.append(
            f'<text x="{x:.1f}" y="{altezza - basso + 24}" text-anchor="middle" '
            f'font-size="12" fill="#53636b">{_numero(valore_x, 1)}</text>'
        )

    for chiave, colore, nome_linea in (
        ("costo_a", COLORI_SCENARI[0], "Scenario A"),
        ("costo_b", COLORI_SCENARI[1], "Scenario B"),
    ):
        punti = " ".join(
            _punto(x_grafico(x), y_grafico(y))
            for x, y in zip(valori, serie[chiave])
        )
        parti.append(
            f'<polyline points="{punti}" fill="none" stroke="{colore}" '
            'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        parti.append(
            f'<circle cx="{x_grafico(valori[-1]) - 135 + (0 if chiave == "costo_a" else 90):.1f}" '
            f'cy="22" r="6" fill="{colore}"/>'
        )
        parti.append(
            f'<text x="{x_grafico(valori[-1]) - 122 + (0 if chiave == "costo_a" else 90):.1f}" '
            f'y="26" font-size="12" fill="#243238">{nome_linea}</text>'
        )

    pareggio = serie.get("punto_pareggio")
    if pareggio is not None:
        x = x_grafico(pareggio)
        parti.append(
            f'<line x1="{x:.1f}" y1="{alto}" x2="{x:.1f}" '
            f'y2="{altezza - basso}" stroke="#263238" stroke-width="1.5" '
            'stroke-dasharray="6 5"/>'
        )
        parti.append(
            f'<text x="{x + 7:.1f}" y="{alto + 16}" font-size="12" '
            f'fill="#263238">Pareggio {_numero(pareggio)}</text>'
        )

    parti.append(
        f'<text x="{larghezza / 2:.1f}" y="{altezza - 8}" text-anchor="middle" '
        f'font-size="12" fill="#53636b">Valore variato ({html.escape(serie["unita"])})</text>'
    )
    parti.append("</svg>")
    return "".join(parti)


def _crea_tabella_clienti(dati: dict[str, Any]) -> str:
    righe = []
    for cliente in dati["clienti"]:
        righe.append(
            "<tr>"
            f'<td>{html.escape(cliente["id"])}</td>'
            f'<td>{html.escape(cliente["localita"])}</td>'
            f'<td>{html.escape(cliente["punto_riferimento"])}</td>'
            f'<td>{html.escape(cliente["tipo_cliente"])}</td>'
            f'<td class="numero">{_numero(cliente["domanda_kg"], 0)} kg</td>'
            "</tr>"
        )
    return (
        '<table><thead><tr><th>Codice</th><th>Località</th>'
        "<th>Punto logistico</th><th>Cliente simulato</th><th>Domanda</th>"
        "</tr></thead><tbody>"
        + "".join(righe)
        + "</tbody></table>"
    )


def _crea_tabella_matrice(dati: dict[str, Any]) -> str:
    nodi = [dati["deposito"]] + dati["clienti"]
    intestazioni = "".join(
        f"<th>{html.escape(nodo['id'])}</th>" for nodo in nodi
    )
    righe = []
    for indice, nodo in enumerate(nodi):
        celle = []
        for indice_destinazione in range(len(nodi)):
            distanza = dati["matrice_distanze_km"][indice][indice_destinazione]
            tempo = dati["matrice_tempi_min"][indice][indice_destinazione]
            contenuto = (
                "0"
                if indice == indice_destinazione
                else f"{_numero(distanza, 1)} km<br>{_numero(tempo, 1)} min"
            )
            celle.append(f'<td class="numero">{contenuto}</td>')
        righe.append(
            f"<tr><th>{html.escape(nodo['id'])} · {html.escape(nodo['localita'])}</th>"
            + "".join(celle)
            + "</tr>"
        )
    return (
        '<div class="tabella-scorrevole"><table class="matrice">'
        "<thead><tr><th>Da / a</th>"
        + intestazioni
        + "</tr></thead><tbody>"
        + "".join(righe)
        + "</tbody></table></div>"
    )


def _crea_righe_percorsi(
    risultato: dict[str, Any], capacita: float
) -> str:
    righe = []
    for indice, veicolo in enumerate(risultato["veicoli"], start=1):
        sequenza = " → ".join(veicolo["sequenza_nodi"])
        righe.append(
            "<tr>"
            f"<td>Veicolo {indice}</td>"
            f"<td>{html.escape(sequenza)}</td>"
            f'<td class="numero">{_numero(veicolo["carico_kg"], 0)} / {_numero(capacita, 0)} kg</td>'
            f'<td class="numero">{_numero(veicolo["distanza_km"])} km</td>'
            f'<td class="numero">{_numero(veicolo["tempo_guida_min"], 1)} min</td>'
            f'<td class="numero">{_numero(veicolo["tempo_completamento_min"], 1)} min</td>'
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Mezzo</th><th>Percorso</th><th>Carico</th>"
        "<th>Distanza</th><th>Guida</th><th>Tempo fino al rientro</th>"
        "</tr></thead><tbody>"
        + "".join(righe)
        + "</tbody></table>"
    )


def _crea_tabella_costi(confronto: dict[str, Any]) -> str:
    return (
        "<table><thead><tr><th>Voce</th><th>Scenario A</th>"
        "<th>Scenario B</th></tr></thead><tbody>"
        f'<tr><td>Noleggio</td><td class="numero">{_numero(confronto["costo_a"]["noleggio"])} €</td>'
        f'<td class="numero">{_numero(confronto["costo_b"]["noleggio"])} €</td></tr>'
        f'<tr><td>Costo chilometrico</td><td class="numero">{_numero(confronto["costo_a"]["costo_km"])} €</td>'
        f'<td class="numero">{_numero(confronto["costo_b"]["costo_km"])} €</td></tr>'
        f'<tr><td>Autisti</td><td class="numero">{_numero(confronto["costo_a"]["costo_autisti"])} €</td>'
        f'<td class="numero">{_numero(confronto["costo_b"]["costo_autisti"])} €</td></tr>'
        f'<tr class="totale"><td>Totale</td><td class="numero">{_numero(confronto["costo_a"]["totale"])} €</td>'
        f'<td class="numero">{_numero(confronto["costo_b"]["totale"])} €</td></tr>'
        "</tbody></table>"
    )


def _crea_tabella_sensibilita(risultati: dict[str, Any]) -> str:
    righe = []
    for serie in risultati["sensibilita"].values():
        pareggio = serie["punto_pareggio"]
        valore_pareggio = (
            "Nessun incrocio nell'intervallo"
            if pareggio is None
            else f"{_numero(pareggio)} {html.escape(serie['unita'])}"
        )
        righe.append(
            "<tr>"
            f'<td>{html.escape(serie["descrizione"])}</td>'
            f"<td>{valore_pareggio}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Parametro variato</th>"
        "<th>Valore di pareggio</th></tr></thead><tbody>"
        + "".join(righe)
        + "</tbody></table>"
    )


def _link_fonte(metadati: dict[str, Any], chiave: str) -> str:
    fonte = metadati[chiave]
    return (
        f'<li><a href="{html.escape(fonte["url"], quote=True)}" '
        'target="_blank" rel="noopener">'
        f'{html.escape(fonte["nome"])}</a>{html.escape(fonte.get("nota", ""))}</li>'
    )


def genera_dashboard(
    dati: dict[str, Any], risultati: dict[str, Any], percorso: str | Path
) -> None:
    """Scrive una pagina HTML autonoma e utilizzabile senza connessione."""
    scenario_a = risultati["scenario_a"]
    scenario_b = risultati["scenario_b"]
    confronto = risultati["confronto_base"]
    scenario_conveniente = confronto["scenario_conveniente"]
    vantaggio = abs(confronto["differenza_a_meno_b"])
    meta = risultati["metadati"]

    grafici_sensibilita = "".join(
        f'<article class="pannello"><h3>{html.escape(serie["descrizione"])}</h3>'
        f'<p class="nota">Variazione del costo totale al cambiare di una sola voce.</p>'
        f"{_crea_grafico_sensibilita(nome, serie)}</article>"
        for nome, serie in risultati["sensibilita"].items()
    )

    html_pagina = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PW 23 · Pianificazione delle consegne</title>
  <style>
    :root {{
      --inchiostro: #243238;
      --testo: #394b52;
      --tenue: #66777e;
      --sfondo: #eee9df;
      --carta: #fffdf8;
      --bordo: #d9d2c5;
      --accento: #176b87;
      --secondo: #c45d2c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--sfondo);
      color: var(--testo);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.6;
    }}
    main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 38px 0 70px; }}
    header.hero {{
      padding: 42px;
      background: linear-gradient(125deg, #243238 0%, #315c68 100%);
      color: #ffffff;
      border-radius: 18px;
      box-shadow: 0 18px 40px rgba(36, 50, 56, 0.16);
    }}
    .sopratitolo {{ margin: 0 0 8px; text-transform: uppercase; letter-spacing: .12em; font-size: .78rem; }}
    h1, h2, h3 {{ font-family: Arial, Helvetica, sans-serif; line-height: 1.2; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 3.6rem); }}
    h2 {{ margin: 0 0 16px; color: var(--inchiostro); font-size: 1.55rem; }}
    h3 {{ margin: 0 0 8px; color: var(--inchiostro); font-size: 1.1rem; }}
    .hero p {{ max-width: 850px; margin: 16px 0 0; color: #e5eef0; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }}
    .chip {{ padding: 5px 11px; border: 1px solid rgba(255,255,255,.35); border-radius: 999px; font: 12px Arial, sans-serif; }}
    section {{ margin-top: 28px; }}
    .pannello {{
      padding: 25px;
      background: var(--carta);
      border: 1px solid var(--bordo);
      border-radius: 14px;
      box-shadow: 0 8px 22px rgba(61, 52, 38, 0.06);
    }}
    .griglia-due {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }}
    .indicatori {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }}
    .indicatore {{ padding: 18px; background: #ffffff; border-left: 5px solid var(--accento); border-radius: 8px; }}
    .indicatore strong {{ display: block; color: var(--inchiostro); font: 700 1.45rem Arial, sans-serif; }}
    .indicatore span {{ color: var(--tenue); font-size: .9rem; }}
    p {{ margin: 8px 0 0; }}
    .avviso {{ padding: 15px 18px; border-left: 5px solid var(--secondo); background: #fff7ef; border-radius: 8px; }}
    .nota {{ color: var(--tenue); font-size: .93rem; }}
    .grafo, .grafico {{ width: 100%; height: auto; display: block; margin-top: 14px; }}
    table {{ width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: .88rem; }}
    th, td {{ padding: 10px 11px; border-bottom: 1px solid var(--bordo); vertical-align: top; }}
    th {{ background: #f2ede4; color: var(--inchiostro); text-align: left; }}
    td.numero {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
    tr.totale td {{ font-weight: 700; background: #eef5f4; }}
    .tabella-scorrevole {{ overflow-x: auto; }}
    table.matrice {{ min-width: 880px; }}
    .legenda {{ display: flex; gap: 18px; flex-wrap: wrap; margin-top: 12px; color: var(--tenue); font: .85rem Arial, sans-serif; }}
    .legenda i {{ width: 11px; height: 11px; display: inline-block; border-radius: 50%; margin-right: 6px; }}
    .legenda-percorsi {{ display: grid; gap: 5px; margin-top: 10px; color: var(--testo); font: .84rem Arial, sans-serif; }}
    .sequenza {{ display: flex; align-items: flex-start; gap: 8px; }}
    .sequenza i {{ width: 22px; height: 4px; flex: 0 0 22px; margin-top: 8px; border-radius: 4px; }}
    .elenco-fonti {{ margin: 0; padding-left: 22px; }}
    .elenco-fonti a {{ color: var(--accento); font-weight: 700; }}
    footer {{ margin-top: 30px; padding-top: 18px; border-top: 1px solid #bdb4a5; color: var(--tenue); font: .82rem Arial, sans-serif; }}
    @media (max-width: 800px) {{
      header.hero {{ padding: 28px; }}
      .griglia-due, .indicatori {{ grid-template-columns: 1fr; }}
      .pannello {{ padding: 18px; }}
    }}
  </style>
</head>
<body>
<main>
  <header class="hero">
    <p class="sopratitolo">Project Work PW 23 · Informatica per le Aziende Digitali</p>
    <h1>Pianificazione delle consegne agroalimentari</h1>
    <p>Confronto tra un veicolo da 600 kg e due veicoli identici da 300 kg, con percorsi scelti tramite enumerazione completa e costi simulati.</p>
    <div class="chips">
      <span class="chip">Deposito: Mairano, Noviglio</span>
      <span class="chip">5 clienti</span>
      <span class="chip">Dati stradali OSRM</span>
      <span class="chip">Consultazione: {html.escape(meta["data_consultazione"])}</span>
    </div>
  </header>

  <section class="pannello">
    <h2>Contesto e regole dell'istanza</h2>
    <p><strong>{html.escape(meta["impresa_simulata"])}</strong> è un'impresa lattiero-casearia simulata. Distribuisce prodotti freschi deperibili a cinque clienti fittizi nelle località confinanti di Rosate, Gaggiano, Vernate, Binasco e Zibido San Giacomo.</p>
    <p>Ogni percorso parte dal deposito e vi ritorna. Ogni cliente riceve una sola consegna, senza frazionamenti. Il carico richiede 15 minuti per veicolo; ogni consegna richiede altri 15 minuti. I percorsi sono ottimizzati prima per distanza totale e poi per tempo di guida.</p>
    <p class="avviso">Le località, gli indirizzi pubblici e le percorrenze sono dati reali. Impresa, clienti, domande, capacità e costi sono simulati. Lo scenario non contiene finestre temporali o ordini anticipati.</p>
  </section>

  <section class="indicatori">
    <div class="indicatore"><strong>{_numero(risultati["domanda_totale_kg"], 0)} kg</strong><span>Domanda totale</span></div>
    <div class="indicatore"><strong>{_numero(scenario_a["riepilogo"]["distanza_totale_km"])} km</strong><span>Distanza Scenario A</span></div>
    <div class="indicatore"><strong>{_numero(scenario_b["riepilogo"]["distanza_totale_km"])} km</strong><span>Distanza Scenario B</span></div>
    <div class="indicatore"><strong>{html.escape(scenario_conveniente)}</strong><span>Scenario economicamente conveniente</span></div>
  </section>

  <section class="griglia-due">
    <article class="pannello">
      <h2>Soluzione ottima A</h2>
      <p>Un solo veicolo, capacità 600 kg, carico {_numero(scenario_a["riepilogo"]["carico_totale_kg"], 0)} kg.</p>
      {_crea_grafo(dati, scenario_a, "Percorso ottimo dello scenario A")}
    </article>
    <article class="pannello">
      <h2>Soluzione ottima B</h2>
      <p>Due veicoli identici, capacità 300 kg ciascuno. Entrambi sono necessari.</p>
      {_crea_grafo(dati, scenario_b, "Percorsi ottimi dello scenario B")}
    </article>
  </section>

  <section class="pannello">
    <h2>Percorsi, capacità e tempi</h2>
    <h3>Scenario A</h3>
    {_crea_righe_percorsi(scenario_a, 600)}
    <h3 style="margin-top:22px">Scenario B</h3>
    {_crea_righe_percorsi(scenario_b, 300)}
    <p class="nota">Il tempo di completamento è il tempo fino al rientro del singolo veicolo. Nello scenario B i due mezzi operano in parallelo; il costo degli autisti somma invece le ore pagate a entrambi.</p>
  </section>

  <section class="griglia-due">
    <article class="pannello">
      <h2>Confronto economico base</h2>
      {_crea_grafico_costi(confronto)}
    </article>
    <article class="pannello">
      <h2>Scomposizione dei costi</h2>
      {_crea_tabella_costi(confronto)}
      <p class="nota">Scenario {html.escape(scenario_conveniente)} più conveniente di {_numero(vantaggio)} €. Stime al netto IVA, non preventivi commerciali.</p>
    </article>
  </section>

  <section>
    <h2 style="padding: 0 4px;">Come cambia la convenienza</h2>
    <div class="griglia-due">
      {grafici_sensibilita}
    </div>
  </section>

  <section class="pannello">
    <h2>Valori di pareggio</h2>
    {_crea_tabella_sensibilita(risultati)}
    <p class="nota">Il pareggio è calcolato nell'intervallo indicato, cambiando una voce per volta e lasciando invariati gli altri parametri.</p>
  </section>

  <section class="pannello">
    <h2>Clienti e domanda</h2>
    {_crea_tabella_clienti(dati)}
  </section>

  <section class="pannello">
    <h2>Matrice delle percorrenze</h2>
    <p class="nota">Ogni cella contiene distanza stradale in chilometri al primo rigo e tempo stimato in minuti al secondo. La riga è l'origine.</p>
    {_crea_tabella_matrice(dati)}
  </section>

  <section class="pannello">
    <h2>Dati, fonti e limiti</h2>
    <ul class="elenco-fonti">
      {_link_fonte(meta, "fonte_localita")}
      {_link_fonte(meta, "fonte_geocodifica")}
      {_link_fonte(meta, "fonte_percorsi")}
    </ul>
    <p class="nota">I tempi di guida sono stime statiche e non includono il traffico in tempo reale. Il noleggio si assume comprensivo di assicurazione e manutenzione; il costo chilometrico include il consumo del veicolo. Eventuali pedaggi, soste, multe e penali non sono modellati.</p>
  </section>

  <footer>
    Istanza deterministica PW 23 · Dati consultati il {html.escape(meta["data_consultazione"])} · Pagina statica senza dipendenze esterne
  </footer>
</main>
</body>
</html>
"""

    percorso = Path(percorso)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    with percorso.open("w", encoding="utf-8", newline="\n") as file_html:
        file_html.write(html_pagina)
