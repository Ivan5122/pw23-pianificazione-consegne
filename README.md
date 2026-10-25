# PW 23 - Pianificazione delle consegne agroalimentari

Repository pubblica: https://github.com/Ivan5122/pw23-pianificazione-consegne

Questo progetto risolve, mediante enumerazione completa, un problema di consegna con un deposito e cinque clienti. Confronta due scenari:

- Scenario A: un veicolo refrigerato con capacità di 600 kg.
- Scenario B: due veicoli refrigerati identici con capacità di 300 kg ciascuno.

Il deposito simulato si trova a Mairano, nel comune di Noviglio. I clienti sono associati alle località confinanti di Rosate, Gaggiano, Vernate, Binasco e Zibido San Giacomo.

## Contenuto

```text
data/istanza_pw23.json       dati, percorrenze, capacità e costi
src/pianificazione.py        calcolo dei percorsi e confronto economico
src/dashboard.py             generazione della pagina HTML statica
src/main.py                  esecuzione completa
tests/                       test automatici con unittest
output/risultati_pw23.json   risultati generati
output/pw23_dashboard.html   pagina HTML generata
output/figure/               figure usate nel report
```

Il report Word/PDF è conservato separatamente dal repository pubblico perché contiene i dati identificativi dello studente.

## Requisiti

Serve Python 3.10 o successivo. Il progetto usa soltanto la libreria standard di Python e non richiede installazioni aggiuntive.

## Esecuzione

Dalla cartella principale del progetto:

```powershell
python -m unittest discover -s tests -v
python -m src.main
```

Il secondo comando rigenera:

- `output/risultati_pw23.json`;
- `output/pw23_dashboard.html`.

La pagina HTML può essere aperta direttamente nel browser e funziona senza connessione Internet.
Per consultarla dalla repository, scaricare `output/pw23_dashboard.html` e aprirlo nel browser.

## Metodo

Ogni percorso parte dal deposito e vi ritorna. Ogni cliente viene visitato una sola volta e nessuna consegna viene frazionata.

Lo Scenario A enumera tutte le `5! = 120` sequenze possibili.

Lo Scenario B considera tutte le partizioni dei clienti tra i due veicoli, eliminando le duplicazioni dovute all'identità dei mezzi, e tutti gli ordini interni ai percorsi. Per l'istanza corrente vengono esaminate 15 partizioni, 10 risultano compatibili con la capacità e producono 120 coppie di percorsi candidate.

La soluzione preferita minimizza prima la distanza totale e poi il tempo di guida. Il programma riporta anche il tempo di completamento con carico e consegne.

## Dati e tempi

Le località e gli indirizzi pubblici sono reali. I municipi e i punti civici indicati servono soltanto a definire coordinate riproducibili: impresa, clienti, domande, capacità e costi sono simulati.

Le distanze e i tempi stradali sono stati ottenuti il 25 ottobre 2026 con:

- geocodifica OpenStreetMap Nominatim;
- motore di routing OSRM sulla rete OpenStreetMap.

Il file dati conserva la matrice completa e il collegamento alla richiesta OSRM. I tempi sono statici e non rappresentano il traffico in tempo reale.

## Calcolo economico

Il costo totale comprende:

1. noleggio giornaliero dei veicoli;
2. costo chilometrico;
3. costo degli autisti, includendo guida, carico e consegne.

Nello Scenario B il costo degli autisti somma le ore dei due conducenti. Il tempo di completamento, invece, considera i due percorsi eseguiti in parallelo.

L'analisi di sensibilità varia una voce per volta:

- noleggio del veicolo grande;
- noleggio di ciascun veicolo piccolo;
- costo orario degli autisti;
- costo chilometrico, con una variazione simultanea percentuale.

I costi sono stime didattiche al netto IVA e non preventivi commerciali.

## Risultati dell'istanza corrente

| Indicatore | Scenario A | Scenario B |
|---|---:|---:|
| Percorso ottimo | D - C5 - C2 - C1 - C3 - C4 - D | D - C5 - C2 - C1 - D; D - C3 - C4 - D |
| Carico | 420 kg | 250 kg + 170 kg |
| Distanza totale | 38,49 km | 43,24 km |
| Tempo di guida totale | 54,02 min | 60,26 min |
| Tempo fino all'ultimo rientro | 144,02 min | 97,51 min |
| Costo base | 192,23 EUR | 219,08 EUR |

Con i parametri iniziali lo Scenario A costa 26,85 EUR in meno. Il pareggio si raggiunge quando il noleggio del veicolo grande arriva a circa 146,85 EUR al giorno oppure quando ciascun veicolo piccolo costa circa 56,58 EUR al giorno. Negli intervalli considerati non si osservano altri incroci per il costo orario degli autisti o per la variazione percentuale del costo chilometrico.

## Verifiche della bozza

- Test automatici eseguiti: 9 superati su 9.
- Documento Word: 7.197 parole secondo il conteggio di Microsoft Word.
- PDF di controllo: 12 pagine.
- Segnaposto del template rimossi.
- Nome, matricola e collegamento alla repository sono stati inseriti nel report finale.

## Limiti

Il modello non include finestre temporali, ordini anticipati, ritorni intermedi, pedaggi, soste, penali o variazioni del traffico. La capacità è espressa in chilogrammi; volume e catena del freddo sono assunti compatibili con i mezzi.
