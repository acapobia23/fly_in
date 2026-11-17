# Fly-In: documentazione tecnica del progetto

## 1. Scopo del progetto

Fly-In è una simulazione di droni che attraversano una rete di hub. La rete è
descritta da file di testo: gli hub sono i vertici del grafo e le connessioni
sono gli archi. Il programma:

1. scopre automaticamente le mappe presenti nella cartella `maps/`;
2. interpreta e valida il formato testuale;
3. costruisce gli oggetti Python che rappresentano la mappa;
4. calcola tutti i percorsi semplici tra hub iniziale e hub finale;
5. muove i droni a turni, rispettando capienze e zone speciali;
6. visualizza la simulazione in una finestra Pygame.

Il punto di ingresso è [`src/__main__.py`](src/__main__.py).

## 2. Struttura delle cartelle

```text
fly_in/
├── Makefile
├── README.md
├── pyproject.toml
├── uv.lock
├── maps/
│   ├── 1_easy/
│   ├── 2_medium/
│   ├── 3_hard/
│   ├── challenger/
│   └── README.md
└── src/
    ├── __main__.py
    ├── drones.py
    ├── fly_in.py
    ├── render.py
    └── parser/
        ├── __init__.py
        ├── raw_map.py
        └── class_maps.py
```

### File di configurazione e supporto

- **`pyproject.toml`** definisce nome, versione, versione minima di Python e
  dipendenze (`pygame`, `flake8` e `mypy`).
- **`uv.lock`** blocca le versioni risolte delle dipendenze, così l'ambiente
  può essere ricreato in modo riproducibile.
- **`Makefile`** raccoglie i comandi standard per installare, avviare,
  debuggare, pulire e controllare il progetto.
- **`README.md`** contiene una panoramica generale, esempi e riferimenti.
- **`maps/README.md`** descrive le categorie delle mappe e i relativi
  obiettivi di difficoltà.
- **`run.txt`** è un esempio di output testuale prodotto dalla simulazione.

Le cartelle `.venv`, `__pycache__` e le cache di mypy/ruff sono artefatti
locali dell'ambiente e non fanno parte della logica applicativa.

## 3. Avvio dell'applicazione

Dalla radice del progetto:

```bash
make install
make run
```

Il target `install` esegue `uv sync`, mentre `run` esegue:

```bash
python3 src/__main__.py
```

È anche possibile avviare direttamente il programma:

```bash
python3 src/__main__.py
```

Il programma mostra prima l'elenco delle difficoltà e poi quello delle mappe
disponibili. Dopo la selezione apre la finestra grafica. Il comando
`make debug` avvia lo stesso programma dentro `pdb`.

## 4. Flusso completo dei dati

Il flusso principale è il seguente:

```text
file .txt della mappa
        │
        ▼
get_raw_levels()
        │  righe grezze raggruppate per cartella/file
        ▼
syntaxt_parser()
        │  dizionari tipizzati e dati validati
        ▼
get_class_maps()
        │  oggetti Map e Hub
        ▼
get_paths_drones()
        │  lista di percorsi di Hub
        ▼
fly_in()
        │  generatore di turni e movimenti
        ▼
render()
        │
        ▼
animazione Pygame
```

In [`main()`](src/__main__.py) queste fasi sono orchestrate in ordine:

1. `maps_parser()` carica e converte tutte le mappe;
2. `choose_level()` chiede all'utente difficoltà e livello;
3. `get_paths_drones()` calcola i percorsi possibili;
4. viene creato un oggetto `Drone` per ogni drone dichiarato;
5. `fly_in()` produce i turni della simulazione;
6. `render()` consuma quei turni e li anima.

`fly_in()` è un generatore: la simulazione non viene eseguita tutta prima del
rendering. Il renderer richiede un nuovo turno solo quando scade il timer
grafico.

## 5. Parser delle mappe

Il parser è diviso in due livelli:

- [`raw_map.py`](src/parser/raw_map.py) legge i file e controlla la sintassi;
- [`class_maps.py`](src/parser/class_maps.py) trasforma i dati validati in
  oggetti del dominio.

### 5.1 Scoperta dei file: `get_raw_levels()`

`get_raw_levels()` cerca la cartella `maps` partendo dalla posizione del file
parser. Per ogni sottocartella crea un gruppo di difficoltà e, per ogni file,
usa il nome senza estensione come nome del livello.

Il risultato ha una forma simile a:

```python
{
    "1_easy": {
        "01_linear_path": ["nb_drones: 2", ...],
    },
    "2_medium": {
        "01_dead_end_trap": ["nb_drones: 5", ...],
    },
}
```

Il metodo gestisce cartella mancante ed errori di lettura stampando un
messaggio e restituendo `{}`.

### 5.2 Sintassi riconosciuta

Una mappa minima contiene:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: middle 1 0 [zone=normal max_drones=2 color=blue]
end_hub: goal 2 0 [color=red]

connection: start-middle
connection: middle-goal [max_link_capacity=2]
```

Sono ammesse righe vuote e commenti che iniziano con `#`.

#### Numero di droni

```text
nb_drones: NUMERO
```

Il numero deve essere intero e non negativo secondo la regex usata dal parser.
La dichiarazione deve comparire una sola volta.

#### Hub

La sintassi è:

```text
start_hub: NOME X Y [metadati]
hub: NOME X Y [metadati]
end_hub: NOME X Y [metadati]
```

`NOME` può contenere lettere, numeri e underscore; `X` e `Y` possono essere
negativi. Esistono tre tipi strutturali di hub:

- `start_hub`: posizione iniziale dei droni;
- `end_hub`: destinazione;
- `hub`: nodo intermedio.

I metadati degli hub supportati sono:

| Metadato | Significato | Default |
|---|---|---|
| `zone` | `normal`, `priority`, `restricted` o `blocked` | `normal` |
| `color` | colore interpretato da Pygame | `none` |
| `max_drones` | numero massimo di droni dentro l'hub | `1` |

Esempio:

```text
hub: gate 4 2 [zone=restricted color=orange max_drones=3]
```

#### Connessioni

La sintassi è:

```text
connection: HUB_A-HUB_B
connection: HUB_A-HUB_B [max_link_capacity=2]
```

La capacità predefinita è `1`. `max_link_capacity` deve essere almeno `1`.
Nel modello attuale le connessioni vengono registrate nell'elenco del primo
hub, quindi la direzione descritta nel file è importante per il movimento.

### 5.3 Validazione: `syntaxt_parser()` e `check_clean_map()`

`syntaxt_parser()` usa espressioni regolari per riconoscere le tre categorie di
righe e converte i valori numerici da stringa a intero. Controlla inoltre:

- chiavi di metadati ammesse;
- valori di `zone`;
- assenza di metadati duplicati;
- presenza di `nb_drones`;
- sintassi delle connessioni;
- capacità delle connessioni.

`check_clean_map()` controlla la coerenza globale:

- non esistono due hub con lo stesso nome;
- esiste al massimo uno `start_hub`;
- esiste al massimo un `end_hub`;
- il primo hub deve essere lo `start_hub`;
- l'ultimo hub deve essere l'`end_hub`;
- non ci sono connessioni duplicate, anche se scritte in ordine inverso.

Se una mappa non è valida, `get_clean_maps()` stampa il file che ha causato
l'errore e restituisce una struttura vuota, interrompendo il caricamento
complessivo dei livelli.

## 6. Modello a oggetti

### 6.1 `Map`

[`Map`](src/parser/class_maps.py) rappresenta una mappa completa:

```python
class Map:
    nb_drones: int
    hubs: dict[str, Hub]
    start: Hub | None
    end: Hub | None
```

`add_hub()` inserisce l'hub nel dizionario e aggiorna `start` oppure `end` in
base al tipo.

Una volta costruita la mappa, la capacità dello start e dell'end viene
impostata uguale al numero totale di droni. In questo modo nessun drone viene
bloccato artificialmente nell'hub iniziale o in quello finale.

### 6.2 `Hub`

[`Hub`](src/parser/class_maps.py) rappresenta un nodo del grafo. Contiene:

- `type`, `name`, `coord`;
- `color`, `zone`, `max_drones`;
- `conn`, lista delle connessioni in uscita;
- `dr_conn`, droni attualmente impegnati sulle connessioni uscenti;
- `inside`, droni attualmente presenti nel nodo.

I metodi di capacità sono:

- `add_inside(drone)`: inserisce il drone se c'è spazio, restituendo `0` in
  caso di successo e `1` se l'hub è pieno;
- `del_inside(drone)`: rimuove il drone dall'hub;
- `add_conn(drone, next_hub)`: verifica e registra l'uso della connessione;
- `del_conn(drone)`: libera la connessione.

Il valore di ritorno `0/1` è usato dal simulatore come esito
successo/fallimento, invece di usare eccezioni per i normali casi di
congestione.

### 6.3 `Drone`

[`Drone`](src/drones.py) contiene lo stato di un singolo drone:

```python
id          # identificatore numerico
name        # ad esempio "D0"
path        # percorso principale
paths       # percorsi disponibili
current     # hub attuale
flag_conn   # stato intermedio per una zona restricted
```

`move()` aggiorna la posizione. Per un hub `restricted`, il primo passaggio
imposta `flag_conn`; il secondo passaggio lo azzera e aggiorna veramente
`current`. Per gli altri hub il movimento è immediato.

## 7. Ricerca dei percorsi

`get_paths_drones()` in [`drones.py`](src/drones.py) usa una ricerca in
profondità (DFS) ricorsiva.

Per ogni chiamata mantiene:

- `path`: il percorso parziale;
- `visited`: i nomi già presenti nel percorso.

Quando raggiunge l'end salva una copia del percorso. Un hub viene ignorato se:

- è di tipo `blocked`;
- ha zona `blocked`;
- è già in `visited`;
- non esiste nel dizionario degli hub.

Il set `visited` impedisce ai cicli delle mappe di generare ricorsioni infinite.
La ricerca produce percorsi semplici, cioè senza ripetere lo stesso hub.

Alla fine i percorsi che contengono una zona `priority` vengono ordinati prima
degli altri. L'ordine della lista è poi sfruttato dalla logica di selezione del
prossimo hub.

`get_size_paths()` calcola una capacità minima associata a ciascun percorso,
combinando capacità dei collegamenti e capacità degli hub. Il valore viene
passato a `fly_in()` come `size_paths`; nel comportamento attuale il parametro
non viene usato ulteriormente dal simulatore.

## 8. Simulazione a turni

La logica è in [`fly_in.py`](src/fly_in.py).

### 8.1 Scelta del prossimo hub

`_next_hub(drone)` esamina tutti i percorsi assegnati al drone. Per ogni
percorso che contiene l'hub corrente individua il nodo successivo e assegna una
priorità alla scelta:

1. un percorso che ha una zona `priority` rimanente;
2. a parità di priorità, il percorso più corto.

Se nessun percorso può proseguire, restituisce `None`.

### 8.2 Ciclo di `fly_in()`

Prima dell'inizio tutti i droni vengono inseriti nello start. Poi, finché
l'end non contiene tutti i droni, ogni turno esegue questi passaggi:

1. svuota `dr_conn` di tutti gli hub, perché rappresenta l'occupazione delle
   connessioni nel turno corrente;
2. considera ogni drone non ancora arrivato;
3. calcola il prossimo hub;
4. verifica la capienza del collegamento in uscita;
5. per un hub `restricted`, consuma il primo turno di attraversamento;
6. verifica la capienza dell'hub di destinazione;
7. se il movimento è possibile, libera l'hub precedente, aggiorna il drone e
   registra una stringa come `D2-gate`;
8. produce la lista dei movimenti del turno.

Se nessun drone può avanzare durante un turno, viene sollevato:

```text
RuntimeError: No Drone can move: check capacity and roads
```

Questo evita un ciclo infinito in presenza di una mappa irrisolvibile o di una
combinazione di capacità incompatibili.

### 8.3 Zone speciali

- **`normal`**: movimento standard di un turno.
- **`priority`**: movimento standard, ma il percorso viene preferito nella
  selezione.
- **`restricted`**: il primo turno registra l'ingresso e il secondo completa
  il movimento.
- **`blocked`**: il nodo non viene utilizzato nella ricerca dei percorsi.

Il simulatore stampa su terminale i movimenti riusciti, separati da spazi:

```text
D0-hub_a D1-hub_b
```

## 9. Rendering Pygame

[`render()`](src/render.py) riceve mappa, droni e generatore dei movimenti.

### Inizializzazione

- inizializza Pygame;
- crea una finestra iniziale `1200x500`;
- abilita il ridimensionamento;
- crea un font e imposta il raggio grafico degli hub.

### Conversione delle coordinate

Le coordinate degli hub sono coordinate logiche della mappa. `update_layout()`
calcola:

- estremi minimi e massimi;
- scala comune per larghezza e altezza;
- origine centrata nella finestra.

`convert(x, y)` trasforma poi le coordinate della mappa in pixel. L'asse Y
viene invertito per adattarsi al sistema di coordinate grafico.

### Disegno

Ogni frame:

1. gestisce chiusura finestra e ridimensionamento;
2. chiede al generatore il turno successivo quando il timer scade;
3. disegna lo sfondo bianco;
4. disegna le connessioni come linee;
5. disegna gli hub come cerchi colorati;
6. disegna il nome sopra ciascun hub;
7. disegna ogni drone come cerchio nero con etichetta;
8. aggiorna lo schermo;
9. limita il loop a 60 FPS.

La simulazione aspetta inizialmente 5 secondi, poi richiede un turno ogni
500 millisecondi. Quando il generatore termina, il grafo resta visibile fino
alla chiusura della finestra.

## 10. Makefile

Il [`Makefile`](Makefile) contiene questi target:

| Target | Effetto |
|---|---|
| `make install` | esegue `uv sync` e prepara l'ambiente |
| `make run` | avvia `src/__main__.py` |
| `make debug` | avvia il programma con `pdb` |
| `make clean` | rimuove cache Python, mypy e pytest |
| `make lint` | esegue Flake8 e mypy con controlli mirati |
| `make lint-strict` | esegue Flake8 e mypy in modalità `--strict` |

Le variabili `PYTHON`, `PIP`, `UV` e `SRC_DIR` possono essere sovrascritte dalla
shell, per esempio:

```bash
make run PYTHON=python3.14
```

`PIP` è definita per convenienza ma non viene usata dagli attuali target.

## 11. Tipi e stile del codice

Il progetto usa:

- annotazioni di tipo moderne (`list[str]`, `dict[str, Hub]`, `Hub | None`);
- `TypedDict` per i dati intermedi del parser;
- `TYPE_CHECKING` e import posticipati per evitare dipendenze circolari;
- Flake8 per lo stile;
- mypy per il controllo statico.

La separazione dei moduli segue responsabilità distinte:

```text
parser       lettura, sintassi e validazione
class_maps   oggetti del dominio e capacità
drones       stato dei droni e ricerca percorsi
fly_in       scheduling e avanzamento a turni
render       interfaccia grafica
__main__     orchestrazione e menu CLI
```

## 12. Cose da controllare quando si aggiunge una nuova mappa

1. Inserire il file nella sottocartella di difficoltà appropriata.
2. Mettere `nb_drones` all'inizio.
3. Dichiarare prima lo `start_hub` e per ultimo l'`end_hub`.
4. Usare nomi univoci per tutti gli hub.
5. Verificare che ogni estremità di connessione esista.
6. Evitare connessioni duplicate.
7. Usare solo le zone supportate.
8. Impostare capacità positive.
9. Assicurarsi che esista almeno un percorso non bloccato tra start ed end.
10. Avviare il programma e, se necessario, eseguire `make lint`.

## 13. Limiti e dettagli dell'implementazione attuale

Questi punti descrivono il comportamento del codice presente, non una proposta
di modifica:

- il caricamento dei livelli avviene tutto all'avvio;
- un errore di parsing in un livello fa restituire una collezione vuota
  all'intero caricamento;
- le connessioni sono costruite a partire dal campo `from`, quindi il grafo
  usato dal simulatore è orientato secondo la dichiarazione;
- `size_paths` viene calcolato e passato alla simulazione, ma non influisce
  sulle decisioni di `fly_in()`;
- la scelta del prossimo hub è locale al drone e non è un ottimizzatore
  globale del numero totale di turni;
- la funzione `render()` richiede un ambiente grafico compatibile con Pygame;
- `KeyboardInterrupt` viene gestito dal punto di ingresso con `pg.quit()`.

## 14. Controlli consigliati

Per una verifica rapida dell'ambiente:

```bash
make install
make lint
make run
```

Per il controllo più rigoroso:

```bash
make lint-strict
```

Le mappe `1_easy` sono il punto di partenza consigliato; quelle `medium`,
`hard` e `challenger` servono per verificare cicli, percorsi alternativi,
capacità ridotte, zone ristrette e carichi elevati.
