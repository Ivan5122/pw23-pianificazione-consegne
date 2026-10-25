"""Risoluzione completa dell'istanza logistica PW 23."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Any


PERCORSO_PREDEFINITO = (
    Path(__file__).resolve().parent.parent / "data" / "istanza_pw23.json"
)


def carica_istanza(percorso: str | Path = PERCORSO_PREDEFINITO) -> dict[str, Any]:
    """Legge il file JSON che contiene l'istanza."""
    with Path(percorso).open("r", encoding="utf-8") as file_json:
        return json.load(file_json)


def valida_istanza(dati: dict[str, Any]) -> None:
    """Controlla la struttura e i vincoli principali prima del calcolo."""
    deposito = dati.get("deposito", {})
    clienti = dati.get("clienti", [])
    if deposito.get("id") != "D":
        raise ValueError("Il deposito deve avere identificativo D.")
    if len(clienti) != 5:
        raise ValueError("L'istanza deve contenere esattamente cinque clienti.")

    identificativi = [deposito["id"]] + [cliente["id"] for cliente in clienti]
    if len(identificativi) != len(set(identificativi)):
        raise ValueError("Gli identificativi dei nodi devono essere univoci.")

    numero_nodi = len(identificativi)
    for nome_matrice in ("matrice_distanze_km", "matrice_tempi_min"):
        matrice = dati.get(nome_matrice, [])
        if len(matrice) != numero_nodi or any(
            len(riga) != numero_nodi for riga in matrice
        ):
            raise ValueError(f"{nome_matrice} deve essere una matrice 6 x 6.")
        if any(valore < 0 for riga in matrice for valore in riga):
            raise ValueError(f"{nome_matrice} non può contenere valori negativi.")
        if any(matrice[i][i] != 0 for i in range(numero_nodi)):
            raise ValueError(f"La diagonale di {nome_matrice} deve essere zero.")

    domande = [float(cliente["domanda_kg"]) for cliente in clienti]
    if any(domanda <= 0 for domanda in domande):
        raise ValueError("Ogni cliente deve avere una domanda positiva.")

    scenario_a = dati["scenari"]["A"]
    scenario_b = dati["scenari"]["B"]
    domanda_totale = sum(domande)
    if domanda_totale > float(scenario_a["capacita_kg"]):
        raise ValueError("La capacità del veicolo A non copre la domanda totale.")
    if domanda_totale <= float(scenario_b["capacita_kg"]):
        raise ValueError("Lo scenario B deve richiedere necessariamente due veicoli.")
    if max(domande) > float(scenario_b["capacita_kg"]):
        raise ValueError("Un cliente supera la capacità di un veicolo dello scenario B.")

    if int(scenario_a["numero_veicoli"]) != 1:
        raise ValueError("Lo scenario A deve usare un solo veicolo.")
    if int(scenario_b["numero_veicoli"]) != 2:
        raise ValueError("Lo scenario B deve usare due veicoli.")


def _identificativo_nodo(dati: dict[str, Any], indice: int) -> str:
    if indice == 0:
        return dati["deposito"]["id"]
    return dati["clienti"][indice - 1]["id"]


def crea_metriche_percorso(
    ordine: tuple[int, ...] | list[int], dati: dict[str, Any]
) -> dict[str, Any]:
    """Calcola carico, distanza e tempi per un percorso chiuso al deposito."""
    ordine = tuple(ordine)
    numero_clienti = len(dati["clienti"])
    if not ordine or len(ordine) != len(set(ordine)):
        raise ValueError("Un percorso deve contenere clienti distinti.")
    if any(indice < 1 or indice > numero_clienti for indice in ordine):
        raise ValueError("Il percorso contiene un indice cliente non valido.")

    sequenza = (0,) + ordine + (0,)
    distanza = sum(
        dati["matrice_distanze_km"][origine][destinazione]
        for origine, destinazione in zip(sequenza, sequenza[1:])
    )
    tempo_guida = sum(
        dati["matrice_tempi_min"][origine][destinazione]
        for origine, destinazione in zip(sequenza, sequenza[1:])
    )
    carico = sum(dati["clienti"][indice - 1]["domanda_kg"] for indice in ordine)
    tempo_servizio = len(ordine) * dati["vincoli"]["servizio_min_per_cliente"]
    tempo_carico = dati["vincoli"]["carico_min_per_veicolo"]

    return {
        "sequenza_nodi": [_identificativo_nodo(dati, indice) for indice in sequenza],
        "ordine_clienti": [_identificativo_nodo(dati, indice) for indice in ordine],
        "carico_kg": round(float(carico), 4),
        "distanza_km": round(float(distanza), 4),
        "tempo_guida_min": round(float(tempo_guida), 4),
        "tempo_servizio_min": round(float(tempo_servizio), 4),
        "tempo_carico_min": round(float(tempo_carico), 4),
        "tempo_completamento_min": round(
            float(tempo_guida + tempo_servizio + tempo_carico), 4
        ),
    }


def _riepiloga_veicoli(veicoli: list[dict[str, Any]]) -> dict[str, Any]:
    tempo_autisti = sum(veicolo["tempo_completamento_min"] for veicolo in veicoli)
    return {
        "numero_veicoli_utilizzati": len(veicoli),
        "carichi_veicoli_kg": [veicolo["carico_kg"] for veicolo in veicoli],
        "carico_totale_kg": round(
            sum(veicolo["carico_kg"] for veicolo in veicoli), 4
        ),
        "distanza_totale_km": round(
            sum(veicolo["distanza_km"] for veicolo in veicoli), 4
        ),
        "tempo_guida_totale_min": round(
            sum(veicolo["tempo_guida_min"] for veicolo in veicoli), 4
        ),
        "tempo_servizio_totale_min": round(
            sum(veicolo["tempo_servizio_min"] for veicolo in veicoli), 4
        ),
        "tempo_carico_totale_min": round(
            sum(veicolo["tempo_carico_min"] for veicolo in veicoli), 4
        ),
        "tempo_autisti_totale_min": round(float(tempo_autisti), 4),
        "tempo_completamento_min": round(
            max(veicolo["tempo_completamento_min"] for veicolo in veicoli), 4
        ),
    }


def _chiave_confronto(candidato: dict[str, Any]) -> tuple[Any, ...]:
    riepilogo = candidato["riepilogo"]
    ordini = tuple(
        tuple(veicolo["ordine_clienti"]) for veicolo in candidato["veicoli"]
    )
    return (
        riepilogo["distanza_totale_km"],
        riepilogo["tempo_guida_totale_min"],
        ordini,
    )


def risolvi_scenario_a(dati: dict[str, Any]) -> dict[str, Any]:
    """Enumera tutti i 120 percorsi possibili con un solo veicolo."""
    capacita = float(dati["scenari"]["A"]["capacita_kg"])
    clienti = tuple(range(1, len(dati["clienti"]) + 1))
    migliore = None
    candidati_valutati = 0
    candidati_ammissibili = 0

    for ordine in itertools.permutations(clienti):
        candidati_valutati += 1
        veicolo = crea_metriche_percorso(ordine, dati)
        if veicolo["carico_kg"] > capacita:
            continue

        candidati_ammissibili += 1
        candidato = {
            "veicoli": [veicolo],
            "riepilogo": _riepiloga_veicoli([veicolo]),
        }
        if migliore is None or _chiave_confronto(candidato) < _chiave_confronto(
            migliore
        ):
            migliore = candidato

    if migliore is None:
        raise ValueError("Nessun percorso ammissibile nello scenario A.")

    migliore["candidati_valutati"] = candidati_valutati
    migliore["candidati_ammissibili"] = candidati_ammissibili
    return migliore


def risolvi_scenario_b(dati: dict[str, Any]) -> dict[str, Any]:
    """Enumera assegnazioni e ordini completi per due veicoli identici."""
    capacita = float(dati["scenari"]["B"]["capacita_kg"])
    clienti = tuple(range(1, len(dati["clienti"]) + 1))
    migliore = None
    partizioni_valutate = 0
    partizioni_ammissibili = 0
    candidati_valutati = 0

    for dimensione_primo_veicolo in range(1, len(clienti)):
        for primo_veicolo in itertools.combinations(
            clienti, dimensione_primo_veicolo
        ):
            # Il primo cliente identifica una sola delle due partizioni simmetriche.
            if clienti[0] not in primo_veicolo:
                continue

            partizioni_valutate += 1
            secondo_veicolo = tuple(
                cliente for cliente in clienti if cliente not in primo_veicolo
            )
            carico_primo = sum(
                dati["clienti"][indice - 1]["domanda_kg"]
                for indice in primo_veicolo
            )
            carico_secondo = sum(
                dati["clienti"][indice - 1]["domanda_kg"]
                for indice in secondo_veicolo
            )
            if carico_primo > capacita or carico_secondo > capacita:
                continue

            partizioni_ammissibili += 1
            for ordine_primo in itertools.permutations(primo_veicolo):
                veicolo_primo = crea_metriche_percorso(ordine_primo, dati)
                for ordine_secondo in itertools.permutations(secondo_veicolo):
                    candidati_valutati += 1
                    veicolo_secondo = crea_metriche_percorso(ordine_secondo, dati)
                    veicoli = [veicolo_primo, veicolo_secondo]
                    candidato = {
                        "veicoli": veicoli,
                        "riepilogo": _riepiloga_veicoli(veicoli),
                    }
                    if migliore is None or _chiave_confronto(
                        candidato
                    ) < _chiave_confronto(migliore):
                        migliore = candidato

    if migliore is None:
        raise ValueError("Nessuna soluzione ammissibile nello scenario B.")

    migliore["partizioni_valutate"] = partizioni_valutate
    migliore["partizioni_ammissibili"] = partizioni_ammissibili
    migliore["candidati_valutati"] = candidati_valutati
    return migliore


def calcola_costo(
    riepilogo: dict[str, Any], configurazione: dict[str, Any]
) -> dict[str, float]:
    """Applica le tre voci di costo concordate a un risultato stradale."""
    numero_veicoli = int(configurazione["numero_veicoli"])
    noleggio = numero_veicoli * float(configurazione["costo_noleggio_giorno"])
    costo_km = float(configurazione["costo_km"]) * riepilogo[
        "distanza_totale_km"
    ]
    costo_autisti = (
        float(configurazione["costo_autista_ora"])
        * riepilogo["tempo_autisti_totale_min"]
        / 60.0
    )
    totale = noleggio + costo_km + costo_autisti
    return {
        "noleggio": round(noleggio, 2),
        "costo_km": round(costo_km, 2),
        "costo_autisti": round(costo_autisti, 2),
        "totale": round(totale, 2),
    }


def _valori_sensibilita(parametro: dict[str, Any]) -> list[float]:
    minimo = float(parametro["minimo"])
    massimo = float(parametro["massimo"])
    passo = float(parametro["passo"])
    numero_passi = int(round((massimo - minimo) / passo))
    return [round(minimo + indice * passo, 4) for indice in range(numero_passi + 1)]


def _punto_pareggio(valori: list[float], differenze: list[float]) -> float | None:
    for indice, differenza in enumerate(differenze):
        if math.isclose(differenza, 0.0, abs_tol=0.005):
            return valori[indice]

    for indice in range(len(differenze) - 1):
        prima = differenze[indice]
        seconda = differenze[indice + 1]
        if prima * seconda < 0:
            valore = valori[indice] + (
                (0.0 - prima)
                * (valori[indice + 1] - valori[indice])
                / (seconda - prima)
            )
            return round(valore, 2)
    return None


def _crea_serie_sensibilita(
    nome: str,
    configurazione: dict[str, Any],
    risultato_a: dict[str, Any],
    risultato_b: dict[str, Any],
) -> dict[str, Any]:
    scenario_a = dict(configurazione["scenari"]["A"])
    scenario_b = dict(configurazione["scenari"]["B"])
    valori = _valori_sensibilita(configurazione["sensibilita"][nome])
    costi_a: list[float] = []
    costi_b: list[float] = []

    for valore in valori:
        if nome == "noleggio_veicolo_grande":
            scenario_a["costo_noleggio_giorno"] = valore
        elif nome == "noleggio_veicolo_piccolo":
            scenario_b["costo_noleggio_giorno"] = valore
        elif nome == "costo_autista":
            scenario_a["costo_autista_ora"] = valore
            scenario_b["costo_autista_ora"] = valore
        elif nome == "costo_km_percentuale":
            scenario_a["costo_km"] = configurazione["scenari"]["A"]["costo_km"] * (
                1 + valore / 100.0
            )
            scenario_b["costo_km"] = configurazione["scenari"]["B"]["costo_km"] * (
                1 + valore / 100.0
            )
        else:
            raise ValueError(f"Sensibilità non riconosciuta: {nome}")

        costi_a.append(calcola_costo(risultato_a["riepilogo"], scenario_a)["totale"])
        costi_b.append(calcola_costo(risultato_b["riepilogo"], scenario_b)["totale"])

    differenze = [round(a - b, 2) for a, b in zip(costi_a, costi_b)]
    return {
        "descrizione": configurazione["sensibilita"][nome]["descrizione"],
        "unita": configurazione["sensibilita"][nome]["unita"],
        "valori": valori,
        "costo_a": costi_a,
        "costo_b": costi_b,
        "differenza_a_meno_b": differenze,
        "punto_pareggio": _punto_pareggio(valori, differenze),
    }


def crea_risultati(dati: dict[str, Any]) -> dict[str, Any]:
    """Risolve i due scenari e costruisce confronto e sensibilità."""
    valida_istanza(dati)
    scenario_a = risolvi_scenario_a(dati)
    scenario_b = risolvi_scenario_b(dati)

    costo_a = calcola_costo(scenario_a["riepilogo"], dati["scenari"]["A"])
    costo_b = calcola_costo(scenario_b["riepilogo"], dati["scenari"]["B"])
    differenza = round(costo_a["totale"] - costo_b["totale"], 2)

    confronto = {
        "costo_a": costo_a,
        "costo_b": costo_b,
        "differenza_a_meno_b": differenza,
        "scenario_conveniente": "A" if differenza < 0 else "B",
    }

    nomi_sensibilita = (
        "noleggio_veicolo_grande",
        "noleggio_veicolo_piccolo",
        "costo_autista",
        "costo_km_percentuale",
    )
    sensibilita = {
        nome: _crea_serie_sensibilita(
            nome, dati, scenario_a, scenario_b
        )
        for nome in nomi_sensibilita
    }

    return {
        "metadati": dati["metadati"],
        "data_consultazione": dati["metadati"]["data_consultazione"],
        "domanda_totale_kg": round(
            sum(float(cliente["domanda_kg"]) for cliente in dati["clienti"]), 2
        ),
        "scenario_a": scenario_a,
        "scenario_b": scenario_b,
        "confronto_base": confronto,
        "sensibilita": sensibilita,
    }


def salva_json(contenuto: dict[str, Any], percorso: str | Path) -> None:
    """Scrive un file JSON leggibile e deterministico."""
    percorso = Path(percorso)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    with percorso.open("w", encoding="utf-8", newline="\n") as file_json:
        json.dump(contenuto, file_json, ensure_ascii=False, indent=2)
        file_json.write("\n")
