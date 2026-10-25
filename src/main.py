"""Esecuzione completa del project work PW 23."""

from __future__ import annotations

from pathlib import Path

from src.dashboard import genera_dashboard
from src.pianificazione import (
    PERCORSO_PREDEFINITO,
    carica_istanza,
    crea_risultati,
    salva_json,
)


RADICE_PROGETTO = Path(__file__).resolve().parent.parent


def esegui() -> None:
    """Calcola i risultati e rigenera tutti gli artefatti della pagina web."""
    dati = carica_istanza(PERCORSO_PREDEFINITO)
    risultati = crea_risultati(dati)
    cartella_output = RADICE_PROGETTO / "output"
    percorso_json = cartella_output / "risultati_pw23.json"
    percorso_html = cartella_output / "pw23_dashboard.html"

    salva_json(risultati, percorso_json)
    genera_dashboard(dati, risultati, percorso_html)

    scenario_a = risultati["scenario_a"]["riepilogo"]
    scenario_b = risultati["scenario_b"]["riepilogo"]
    confronto = risultati["confronto_base"]
    print(f"Scenario A: {scenario_a['distanza_totale_km']:.2f} km, "
          f"costo {confronto['costo_a']['totale']:.2f} EUR")
    print(f"Scenario B: {scenario_b['distanza_totale_km']:.2f} km, "
          f"costo {confronto['costo_b']['totale']:.2f} EUR")
    print(f"Scenario conveniente: {confronto['scenario_conveniente']}")
    print(f"Risultati: {percorso_json}")
    print(f"Dashboard: {percorso_html}")


if __name__ == "__main__":
    esegui()
