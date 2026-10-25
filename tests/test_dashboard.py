"""Test della pagina HTML statica."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.dashboard import genera_dashboard
from src.pianificazione import PERCORSO_PREDEFINITO, carica_istanza, crea_risultati


class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dati = carica_istanza(PERCORSO_PREDEFINITO)
        cls.risultati = crea_risultati(cls.dati)

    def test_pagina_contiene_sezioni_e_dati_essenziali(self) -> None:
        with tempfile.TemporaryDirectory() as cartella:
            percorso = Path(cartella) / "dashboard.html"
            genera_dashboard(self.dati, self.risultati, percorso)
            pagina = percorso.read_text(encoding="utf-8")

            for testo in (
                "Pianificazione delle consegne agroalimentari",
                "Soluzione ottima A",
                "Soluzione ottima B",
                "Confronto economico base",
                "Come cambia la convenienza",
                "Matrice delle percorrenze",
            ):
                self.assertIn(testo, pagina)
            self.assertGreaterEqual(pagina.count("<svg"), 7)
            self.assertNotIn("<script", pagina)
            self.assertNotIn("cdn.", pagina)


if __name__ == "__main__":
    unittest.main()
