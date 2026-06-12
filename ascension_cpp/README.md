# Ascension C++ v12.7 (Math Edition)

Port C++ modulare dell'interprete Ascension con architettura header-only.

## Struttura

```
ascension_cpp/
├── ascension.cpp       # Main
├── value.hpp           # Tipi Value, Dict, Opcode
├── compiler.hpp        # Compilatore
├── vm.hpp              # Virtual Machine
├── modules/
│   ├── mod_fileio.hpp  # File I/O (sempre incluso)
│   ├── mod_curses.hpp  # TUI con ncurses (opzionale)
│   └── mod_network.hpp # Socket TCP/UDP (opzionale)
└── README.md
```

## Compilazione

### Base (solo File I/O)
```bash
g++ -std=c++17 -O2 ascension.cpp -o ascension
```

### Con Curses (Linux/macOS)
```bash
g++ -std=c++17 -O2 -DHAS_CURSES ascension.cpp -o ascension -lncurses
```

### Con Networking
```bash
g++ -std=c++17 -O2 -DHAS_NETWORK ascension.cpp -o ascension
```

### Full (tutto abilitato)
```bash
g++ -std=c++17 -O2 -DHAS_CURSES -DHAS_NETWORK ascension.cpp -o ascension -lncurses
```

### Windows (con MinGW)
```bash
g++ -std=c++17 -O2 -DHAS_NETWORK ascension.cpp -o ascension.exe -lws2_32
```

## Uso

```bash
./ascension script.asc             # Esegui
./ascension script.asc -debug      # Esegui con debug bytecode
./ascension script.asc -allow-exec # Abilita system() ed exec()
./ascension                        # Mostra moduli compilati
```

## Sicurezza

- `system()` ed `exec()` sono **disabilitati di default**: uno script che li usa
  termina con `SecurityError`. Abilitarli esplicitamente con `-allow-exec`,
  solo per script fidati.
- `http_get`/`http_post` supportano solo `http://`: gli URL `https://` vengono
  rifiutati con errore (non esiste supporto TLS, prima la richiesta partiva in
  chiaro sulla porta 443).
- Le richieste HTTP hanno timeout di 10s e risposta limitata a 8 MB;
  `socket_recv` è limitato a 1 MB per chiamata.

## Funzioni per Modulo

### Core (sempre disponibile)
- Variabili, operatori, controllo flusso
- Struct, array 1D/2D, matrici
- Funzioni, ricorsione
- Math: sqrt, pow, sin, cos, tan, etc.
- random(), PI, E

### File I/O (mod_fileio.hpp)
- `file_open(file, mode)` / `open(file, mode)` → handle
- `file_write(handle, content)` / `write(handle, content)`
- `file_read_line(handle)` / `read_line(handle)`
- `file_read_all(handle)` / `read_all(handle)`
- `file_close(handle)` / `close(handle)`

### Curses (mod_curses.hpp) - richiede `-DHAS_CURSES`
- `curses_init()`, `curses_end()`
- `curses_clear()`, `curses_refresh()`
- `curses_move(y, x)`, `curses_write(str)`
- `curses_read_key()`
- `curses_max_y()`, `curses_max_x()`

### Network (mod_network.hpp) - richiede `-DHAS_NETWORK`
- `http_get(url)` → response body
- `http_post(url, data)` → response body
- `socket_open(type, proto)` - type: "TCP"/"UDP"
- `socket_bind(sid, ip, port)`
- `socket_listen(sid, backlog)`
- `socket_accept(sid)`
- `socket_connect(sid, ip, port)`
- `socket_send(sid, data)`
- `socket_recv(sid, maxbytes)`
- `socket_close(sid)`
- `get_ip(hostname)`

## Esempio

```c
// hello.asc
print("Hello from Ascension C++!");

struct Point { x, y }

p = new Point();
p.x = 10;
p.y = 20;

print("Point:", p.x, p.y);

func distance(p1, p2) {
    dx = p2.x - p1.x;
    dy = p2.y - p1.y;
    return sqrt(dx*dx + dy*dy);
}

origin = new Point();
origin.x = 0;
origin.y = 0;

print("Distance from origin:", distance(origin, p));
```

## Licenza

GPL v3 - (c) 2026 EdeFede
