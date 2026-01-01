# Ascension Shell - REPL Interattivo

Una shell interattiva per testare e sperimentare con il linguaggio Ascension in tempo reale.

## Caratteristiche

- **REPL completo**: Esegui codice Ascension riga per riga e vedi i risultati immediatamente
- **Input multilinea**: Le parentesi graffe `{}` abilitano automaticamente la modalità multilinea
- **Autocompletamento**: Premi TAB per completare keyword, funzioni built-in e variabili definite
- **Storico comandi**: Naviga tra i comandi precedenti con le frecce ↑ ↓
- **Persistenza history**: Lo storico viene salvato in `~/.ascension_history`
- **Ispezione stato**: Comandi per visualizzare variabili, funzioni, struct e matrici
- **Debug mode**: Visualizza il bytecode generato per ogni istruzione
- **Carica/Salva**: Importa file `.asc` esistenti o esporta la sessione corrente

## Requisiti

- Python 3.6+
- `ascension_12_6.py` nella stessa directory

## Utilizzo

```bash
python3 ascension_shell_12_6.py
```

## Comandi Speciali

Tutti i comandi speciali iniziano con un punto `.`:

| Comando | Descrizione |
|---------|-------------|
| `.help` | Mostra l'aiuto completo |
| `.clear` | Resetta lo stato (variabili, funzioni, struct) |
| `.vars` | Mostra tutte le variabili globali definite |
| `.funcs` | Mostra le funzioni definite |
| `.structs` | Mostra le struct definite |
| `.matrices` | Mostra matrici e array con anteprima contenuto |
| `.protos` | Mostra i prototipi funzione registrati |
| `.load FILE` | Carica ed esegue un file .asc |
| `.save FILE` | Salva la sessione corrente in un file |
| `.history` | Mostra gli ultimi 20 comandi |
| `.debug` | Attiva/disattiva la visualizzazione del bytecode |
| `.quit` | Esci dalla shell (anche Ctrl+D) |

## Esempi di Sessione

### Operazioni Base

```
a§c> x = 42;
a§c> y = 8;
a§c> print(x + y);
OUTPUT > 50

a§c> .vars
Variabili globali:
────────────────────────────────────────
  x = 42
  y = 8
```

### Definizione Funzioni (Multilinea)

```
a§c> func fattoriale(n) {
...>     if (n <= 1) {
...>         return 1;
...>     }
...>     return n * fattoriale(n - 1);
...> }
a§c> print(fattoriale(5));
OUTPUT > 120

a§c> .funcs
Funzioni definite:
────────────────────────────────────────
  fattoriale(n)
```

### Stringhe (v12.6)

```
a§c> testo = "Hello World";
a§c> print(substr(testo, 0, 5));
OUTPUT > Hello

a§c> print(chr(65));
OUTPUT > A

a§c> print(to_int("A"));
OUTPUT > 65
```

### Matrici

```
a§c> m = matrix(3, 3, 0);
a§c> m[1][1] = 5;
a§c> .matrices

Matrici (2D):
──────────────────────────────────────────────────
  m: 3x3
    [0, 0, 0]
    [0, 5, 0]
    [0, 0, 0]
```

### Debug Mode

```
a§c> .debug
Modalità debug: ON

a§c> x = 10 + 5;

--- BYTECODE ---
     0: ('PUSH', '10')
     1: ('PUSH', '5')
     2: ('ADD', None)
     3: ('STORE', 'x')
----------------
```

### Caricamento File

```
a§c> .load esempi/fibonacci.asc
Caricamento esempi/fibonacci.asc...
File 'esempi/fibonacci.asc' caricato.

a§c> print(fibonacci(10));
OUTPUT > 55
```

## Peculiarità

### Input Multilinea Automatico

La shell rileva automaticamente quando il codice richiede più righe contando le parentesi graffe. Il prompt cambia da `a§c>` a `...>` finché tutte le graffe non sono chiuse:

```
a§c> if (x > 0) {
...>     print("positivo");
...> } else {
...>     print("non positivo");
...> }
```

### Stato Persistente

A differenza dell'esecuzione di un file, la shell mantiene lo stato tra le istruzioni:

```
a§c> x = 10;
a§c> x += 5;
a§c> print(x);
OUTPUT > 15
```

Variabili, funzioni e struct rimangono disponibili per tutta la sessione fino a `.clear` o `.quit`.

### Ispezione Intelligente

Il comando `.vars` mostra il tipo appropriato per ogni variabile:

```
a§c> .vars
Variabili globali:
────────────────────────────────────────
  contatore = 42
  nome = 'Mario'
  config = array[3]
  persona = struct Utente
  griglia = matrix(4x4)
  risultato = NULL
```

### Prototipi Funzione

Il comando `.protos` mostra lo stato dei prototipi (forward declarations):

```
a§c> func pari(n);
a§c> func dispari(n);
a§c> .protos

Prototipi funzione:
──────────────────────────────────────────────────
  func pari(n); ○ solo prototipo
  func dispari(n); ○ solo prototipo

a§c> func pari(n) { ... }
a§c> func dispari(n) { ... }
a§c> .protos

Prototipi funzione:
──────────────────────────────────────────────────
  func pari(n); ✓ definita
  func dispari(n); ✓ definita
```

### Interruzione Sicura

- `Ctrl+C` interrompe l'input corrente senza uscire
- `Ctrl+D` o `.quit` esce dalla shell
- Il buffer multilinea viene resettato dopo un'interruzione

## File History

Lo storico dei comandi viene salvato automaticamente in:
```
~/.ascension_history
```

Questo permette di recuperare comandi da sessioni precedenti usando le frecce ↑ ↓.

## Note

- La shell richiede che `ascension_12_6.py` sia nella stessa directory o importabile da Python
- Alcune funzionalità (HTTP, Tkinter, Curses) potrebbero richiedere librerie Python aggiuntive
- Per applicazioni GUI complete, è consigliato eseguire file `.asc` direttamente invece della shell

## Licenza

GPL v3 - Copyright (C) 2025 Ascension Lang
