"""Test del calcolo logistico ed economico."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.pianificazione import (
    PERCORSO_PREDEFINITO,
    calcola_costo,
    carica_istanza,
    crea_metriche_percorso,
    crea_risultati,
    risolvi_scenario_a,
    risolvi_scenario_b,
    salva_json,
    valida_istanza,
)


class TestPianificazione(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dati = carica_istanza(PERCORSO_PREDEFINITO)
        cls.risultati = crea_risultati(cls.dati)

    def test_istanza_valida(self) -> None:
        valida_istanza(self.dati)
        self.assertEqual(len(self.dati["clienti"]), 5)
        self.assertEqual(self.risultati["domanda_totale_kg"], 420.0)

    def test_formula_percorso_chiuso(self) -> None:
        metrica = crea_metriche_percorso((1, 2), self.dati)
        self.assertEqual(metrica["sequenza_nodi"], ["D", "C1", "C2", "D"])
        self.assertAlmostEqual(
            metrica["distanza_km"],
            self.dati["matrice_distanze_km"][0][1]
            + self.dati["matrice_distanze_km"][1][2]
            + self.dati["matrice_distanze_km"][2][0],
            places=3,
        )
        self.assertEqual(metrica["carico_kg"], 170.0)
        self.assertEqual(metrica["tempo_servizio_min"], 30.0)
        self.assertEqual(metrica["tempo_carico_min"], 15.0)

    def test_scenario_a_enumera_tutti_i_percorsi(self) -> None:
        risultato = risolvi_scenario_a(self.dati)
        self.assertEqual(risultato["candidati_valutati"], 120)
        self.assertEqual(risultato["candidati_ammissibili"], 120)
        self.assertEqual(len(risultato["veicoli"]), 1)
        self.assertEqual(
            risultato["veicoli"][0]["ordine_clienti"],
            ["C5", "C2", "C1", "C3", "C4"],
        )
        self.assertAlmostEqual(
            risultato["riepilogo"]["distanza_totale_km"], 38.4911, places=3
        )

    def test_scenario_b_usa_entrambi_i_veicoli(self) -> None:
        risultato = risolvi_scenario_b(self.dati)
        self.assertEqual(risultato["partizioni_valutate"], 15)
        self.assertEqual(risultato["partizioni_ammissibili"], 10)
        self.assertEqual(risultato["candidati_valutati"], 120)
        self.assertEqual(len(risultato["veicoli"]), 2)
        self.assertTrue(
            all(
                veicolo["carico_kg"] <= self.dati["scenari"]["B"]["capacita_kg"]
                for veicolo in risultato["veicoli"]
            )
        )
        self.assertGreater(
            sum(veicolo["carico_kg"] for veicolo in risultato["veicoli"]),
            self.dati["scenari"]["B"]["capacita_kg"],
        )
        self.assertAlmostEqual(
            risultato["riepilogo"]["distanza_totale_km"], 43.2415, places=3
        )

    def test_tutti_i_clienti_sono_visitati_una_volta(self) -> None:
        for chiave in ("scenario_a", "scenario_b"):
            visitati = [
                cliente
                for veicolo in self.risultati[chiave]["veicoli"]
                for cliente in veicolo["ordine_clienti"]
            ]
            self.assertEqual(sorted(visitati), ["C1", "C2", "C3", "C4", "C5"])

    def test_costo_base_calcolato_da_componenti_indipendenti(self) -> None:
        riepilogo_a = self.risultati["scenario_a"]["riepilogo"]
        costo_a = calcola_costo(riepilogo_a, self.dati["scenari"]["A"])
        atteso = (
            120.0
            + riepilogo_a["distanza_totale_km"] * 0.38
            + riepilogo_a["tempo_autisti_totale_min"] / 60 * 24.0
        )
        self.assertAlmostEqual(costo_a["totale"], atteso, places=2)
        self.assertEqual(
            self.risultati["confronto_base"]["scenario_conveniente"], "A"
        )

    def test_analisi_di_sensibilita_presenta_pareggi(self) -> None:
        sensibilita = self.risultati["sensibilita"]
        self.assertEqual(len(sensibilita), 4)
        self.assertIsNotNone(
            sensibilita["noleggio_veicolo_grande"]["punto_pareggio"]
        )
        self.assertIsNotNone(sensibilita["noleggio_veicolo_piccolo"]["punto_pareggio"])
        self.assertTrue(
            all(
                len(serie["valori"]) == len(serie["costo_a"]) == len(serie["costo_b"])
                for serie in sensibilita.values()
            )
        )

    def test_salvataggio_json_leggibile(self) -> None:
        with tempfile.TemporaryDirectory() as cartella:
            percorso = Path(cartella) / "risultati.json"
            salva_json(self.risultati, percorso)
            contenuto = json.loads(percorso.read_text(encoding="utf-8"))
            self.assertEqual(
                contenuto["confronto_base"]["scenario_conveniente"],
                self.risultati["confronto_base"]["scenario_conveniente"],
            )


if __name__ == "__main__":
    unittest.main()
