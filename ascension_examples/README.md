# Ascension Examples

Questa cartella contiene esempi dimostrativi per il linguaggio di programmazione **Ascension v12.5**.

## Come eseguire gli esempi

```bash
python3 ascension_12_5.py examples/01_hello_world.asc
```

Per il debug con output del bytecode:
```bash
python3 ascension_12_5.py examples/01_hello_world.asc -debug
```

## Lista Esempi

### Core Language
| File | Descrizione |
|------|-------------|
| `01_hello_world.asc` | Il classico primo programma |
| `02_variables.asc` | Variabili, tipi, operazioni |
| `03_control_flow.asc` | if/else, while, for, switch |
| `04_functions.asc` | Funzioni, ricorsione, prototipi |
| `05_arrays_matrices.asc` | Array 1D e matrici 2D |
| `06_structs.asc` | Strutture dati custom |

### I/O e Sistema
| File | Descrizione |
|------|-------------|
| `07_file_io.asc` | Lettura e scrittura file |
| `14_system_commands.asc` | Esecuzione comandi di sistema |
| `18_try_catch.asc` | Gestione errori con try/catch |

### Networking
| File | Descrizione |
|------|-------------|
| `08_http_networking.asc` | Richieste HTTP GET e POST |
| `09_web_scraper.asc` | Web scraper completo |
| `10_tcp_sockets.asc` | Client TCP e socket |

### GUI e TUI
| File | Descrizione |
|------|-------------|
| `11_gui_tkinter.asc` | Interfaccia grafica con Tkinter |
| `12_canvas_graphics.asc` | Disegno e animazioni su canvas |
| `13_curses_tui.asc` | Interfaccia testuale (terminale) |

### Utility e Algoritmi
| File | Descrizione |
|------|-------------|
| `15_algorithms.asc` | Algoritmi classici (sort, fibonacci, etc.) |
| `16_string_library.asc` | Libreria funzioni stringa |
| `17_calculator.asc` | Calcolatrice interattiva |

## Requisiti

- **Python 3.6+**
- **requests** (opzionale, per HTTP)
- **tkinter** (opzionale, per GUI)

## Note

- Gli esempi GUI (`11_`, `12_`) richiedono un ambiente grafico
- L'esempio curses (`13_`) richiede un terminale compatibile
- Gli esempi di rete (`08_`, `09_`, `10_`) richiedono connessione internet

## Licenza

GPL v3 - Vedi il file LICENSE nella root del progetto.
