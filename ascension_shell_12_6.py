#!/usr/bin/env python3
"""
Ascension Shell - REPL Interattivo
Versione 1.3 (Substr Edition)

Una shell interattiva per testare codice Ascension in tempo reale.

Uso:
    python3 ascension_shell_12_6.py

Comandi speciali:
    .help     - Mostra aiuto
    .clear    - Pulisce variabili e stato
    .vars     - Mostra variabili definite
    .funcs    - Mostra funzioni definite
    .structs  - Mostra struct definite
    .matrices - Mostra matrici definite
    .protos   - Mostra prototipi funzione
    .load FILE- Carica ed esegue un file .asc
    .save FILE- Salva la sessione in un file
    .history  - Mostra storico comandi
    .debug    - Toggle modalità debug (mostra bytecode)
    .quit     - Esci (oppure Ctrl+D)

Novità v1.3 (Ascension 12.6):
    - substr(string, start, length): estrae sottostringa
    - chr(code): converte codice ASCII in carattere

Copyright (C) 2025 Ascension Lang - GPL v3
"""

import sys
import os
import readline
import atexit

# Importa Ascension
try:
    from ascension_12_6 import AscensionCompiler, AscensionVM, AscensionException
    ASCENSION_VERSION = "12.6 (Substr Edition)"
except ImportError:
    try:
        from ascension import AscensionCompiler, AscensionVM, AscensionException
        ASCENSION_VERSION = "unknown"
    except ImportError:
        print("Errore: impossibile importare Ascension.")
        print("Assicurati che ascension_12_6.py sia nella stessa directory.")
        sys.exit(1)


class AscensionShell:
    """Shell REPL per Ascension"""

    PROMPT = "a§c> "
    PROMPT_CONTINUE = "...> "

    def __init__(self):
        self.compiler = AscensionCompiler()
        self.vm = AscensionVM()
        self.history = []
        self.debug_mode = False
        self.session_code = []
        self.multiline_buffer = ""
        self.brace_count = 0

        # Setup history file
        self.history_file = os.path.expanduser("~/.ascension_history")
        self._setup_readline()

    def _setup_readline(self):
        """Configura readline per history e autocompletamento"""
        try:
            readline.read_history_file(self.history_file)
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass

        atexit.register(self._save_history)

        # Autocompletamento base - aggiornato v12.6
        keywords = [
            # Parole chiave
            'if', 'else', 'while', 'for', 'func', 'return', 'struct',
            'global', 'print', 'switch', 'case', 'default', 'try', 'catch', 'throw',
            'break', 'continue', 'include',
            # Built-in standard
            'new', 'len', 'keys', 'to_int', 'to_float', 'read',
            # Valori speciali
            'true', 'false', 'NULL',
            # Array multidimensionali
            'matrix', 'rows', 'cols', 'dim',
            # System commands
            'system', 'exec',
            # NUOVO v12.6: Stringhe
            'substr', 'chr',
            # File I/O
            'open', 'close', 'write', 'read_line', 'read_all',
            # HTTP
            'http_get', 'http_post', 'response_status', 'response_body',
            # Sockets
            'socket_open', 'socket_close', 'socket_bind', 'socket_listen',
            'socket_accept', 'socket_connect', 'socket_send', 'socket_recv',
            'get_ip',
            # Tkinter
            'tk_root', 'tk_widget', 'tk_pack', 'tk_grid', 'tk_mainloop',
            'tk_config', 'tk_get', 'tk_set', 'tk_msgbox', 'tk_command',
            'tk_bind', 'tk_after', 'tk_after_cancel', 'tk_update', 'tk_destroy',
            'tk_clear', 'tk_focus', 'tk_geometry', 'tk_title', 'tk_resizable',
            'tk_text_get', 'tk_text_insert', 'tk_listbox_add', 'tk_listbox_get',
            'tk_listbox_index', 'tk_filedialog_open', 'tk_filedialog_save',
            'tk_askstring', 'tk_askyesno',
            'tk_canvas_line', 'tk_canvas_rect', 'tk_canvas_oval',
            'tk_canvas_text', 'tk_canvas_clear', 'tk_canvas_delete', 'tk_canvas_move',
            # Curses
            'curses_init', 'curses_end', 'curses_clear', 'curses_move',
            'curses_write', 'curses_refresh', 'curses_read_key',
            # Comandi shell
            '.help', '.clear', '.vars', '.funcs', '.structs', '.matrices', '.protos',
            '.load', '.save', '.history', '.debug', '.quit'
        ]

        def completer(text, state):
            options = [k for k in keywords if k.startswith(text)]
            options += [v for v in self.vm.global_memory.keys() if v.startswith(text)]
            if state < len(options):
                return options[state]
            return None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

    def _save_history(self):
        """Salva history su file"""
        try:
            readline.write_history_file(self.history_file)
        except:
            pass

    def print_banner(self):
        """Stampa banner di benvenuto"""
        print()
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║           ASCENSION SHELL - REPL Interattivo              ║")
        print("║              Versione 1.3 (Substr Edition)                ║")
        print("╠═══════════════════════════════════════════════════════════╣")
        print(f"║  Ascension VM: {ASCENSION_VERSION:<43} ║")
        print("║  Digita .help per aiuto, .quit per uscire                 ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print()

    def print_help(self):
        """Stampa messaggio di aiuto"""
        print("""
Ascension Shell - Comandi disponibili:
══════════════════════════════════════

COMANDI SPECIALI (iniziano con .):
  .help       Mostra questo messaggio
  .clear      Resetta lo stato (variabili, funzioni, struct)
  .vars       Mostra variabili globali definite
  .funcs      Mostra funzioni definite
  .structs    Mostra struct definite
  .matrices   Mostra matrici/array multidimensionali definiti
  .protos     Mostra prototipi funzione registrati
  .load FILE  Carica ed esegue un file .asc
  .save FILE  Salva il codice della sessione in un file
  .history    Mostra storico comandi
  .debug      Toggle modalità debug (mostra bytecode)
  .quit       Esci dalla shell (anche Ctrl+D)

SINTASSI ASCENSION:
  x = 10;                    Assegnazione
  print("Ciao", x);          Stampa
  func nome(a, b) { ... }    Definizione funzione
  func nome(a, b);           Prototipo funzione
  if (x > 5) { ... }         Condizionale
  for (i=0; i<10; i+=1) {}   Loop for
  while (cond) { ... }       Loop while
  struct Nome { campo1; }    Definizione struct

VALORI SPECIALI:
  true, false               Valori booleani (1 e 0)
  NULL                       Valore nullo (distinto da 0)

STRINGHE (v12.6):
  substr(str, start, len)   Estrae sottostringa
  chr(code)                 Converte codice ASCII in carattere
  to_int("A")               Ottiene codice ASCII (65)

ARRAY MULTIDIMENSIONALI:
  m = matrix(3, 4, 0);       Crea matrice 3x4 inizializzata a 0
  m[0][1] = 5;               Scrittura stile C
  m[0,1] = 5;                Scrittura stile comma
  r = rows(m);               Numero righe
  c = cols(m);               Numero colonne

SYSTEM COMMANDS:
  system("comando");         Esegue comando, ritorna exit code
  exec("comando");           Esegue comando, ritorna output

MULTILINEA:
  Le parentesi graffe { } permettono input multilinea.

ESEMPI:
  a§c> x = 42;
  a§c> print(x);
  OUTPUT > 42

  a§c> func quadrato(n) {
  ...>     return n * n;
  ...> }
  a§c> print(quadrato(5));
  OUTPUT > 25

  a§c> testo = "Hello World";
  a§c> print(substr(testo, 0, 5));
  OUTPUT > Hello

  a§c> print(chr(65));
  OUTPUT > A
""")

    def cmd_clear(self):
        """Resetta lo stato della VM"""
        self.compiler = AscensionCompiler()
        self.vm = AscensionVM()
        self.session_code = []
        print("Stato resettato.")

    def cmd_vars(self):
        """Mostra variabili globali"""
        if not self.vm.global_memory:
            print("Nessuna variabile definita.")
            return

        print("\nVariabili globali:")
        print("─" * 40)
        for name, value in sorted(self.vm.global_memory.items()):
            if not name.startswith('__'):
                if isinstance(value, dict):
                    if value.get('__matrix__'):
                        type_str = f"matrix({value.get('__rows__', '?')}x{value.get('__cols__', '?')})"
                    elif value.get('__type__'):
                        type_str = f"struct {value.get('__type__')}"
                    else:
                        type_str = f"array[{len([k for k in value if not str(k).startswith('__')])}]"
                    val_repr = type_str
                elif value is None:
                    val_repr = "NULL"
                elif isinstance(value, str):
                    val_repr = repr(value)
                else:
                    val_repr = str(value)
                
                if len(val_repr) > 50:
                    val_repr = val_repr[:47] + "..."
                print(f"  {name} = {val_repr}")
        print()

    def cmd_funcs(self):
        """Mostra funzioni definite"""
        funcs = [label for label in self.vm.labels.keys()
                 if not label.startswith('L') and not label.startswith('_')
                 and not any(label.startswith(x) for x in ['skip', 'ws', 'we', 'fs', 'fe', 'if_', 'next_', 'elif_', 'es', 'nc', 'c', 'e'])]

        if not funcs:
            print("Nessuna funzione definita.")
            return

        print("\nFunzioni definite:")
        print("─" * 40)
        for func in sorted(funcs):
            # Mostra argomenti se disponibili
            if func in self.compiler.function_prototypes:
                args = self.compiler.function_prototypes[func]
                args_str = ", ".join(args) if args else ""
                print(f"  {func}({args_str})")
            else:
                print(f"  {func}()")
        print()

    def cmd_structs(self):
        """Mostra struct definite"""
        if not self.compiler.structs:
            print("Nessuna struct definita.")
            return

        print("\nStruct definite:")
        print("─" * 40)
        for name, fields in sorted(self.compiler.structs.items()):
            print(f"  struct {name} {{ {', '.join(fields)} }}")
        print()

    def cmd_matrices(self):
        """Mostra matrici definite"""
        matrices = {}
        arrays = {}
        
        for name, value in self.vm.global_memory.items():
            if name.startswith('__'):
                continue
            if isinstance(value, dict):
                if value.get('__matrix__'):
                    matrices[name] = value
                elif not value.get('__type__'):
                    arrays[name] = value
        
        if not matrices and not arrays:
            print("Nessuna matrice o array definito.")
            return

        if matrices:
            print("\nMatrici (2D):")
            print("─" * 50)
            for name, mat in sorted(matrices.items()):
                rows = mat.get('__rows__', 0)
                cols = mat.get('__cols__', 0)
                print(f"  {name}: {rows}x{cols}")
                if rows <= 4 and cols <= 6:
                    for r in range(rows):
                        row_vals = [str(mat.get(f"{r},{c}", 0)) for c in range(cols)]
                        print(f"    [{', '.join(row_vals)}]")
            print()

        if arrays:
            print("\nArray (1D):")
            print("─" * 50)
            for name, arr in sorted(arrays.items()):
                size = len([k for k in arr if not str(k).startswith('__')])
                preview = []
                for i in range(min(5, size)):
                    val = arr.get(i, '?')
                    if val is None:
                        preview.append("NULL")
                    elif isinstance(val, str):
                        preview.append(repr(val))
                    else:
                        preview.append(str(val))
                if size > 5:
                    preview.append('...')
                print(f"  {name}[{size}]: [{', '.join(preview)}]")
            print()

    def cmd_protos(self):
        """Mostra prototipi funzione registrati"""
        if not self.compiler.function_prototypes:
            print("Nessun prototipo funzione registrato.")
            return

        print("\nPrototipi funzione:")
        print("─" * 50)
        for name, args in sorted(self.compiler.function_prototypes.items()):
            args_str = ", ".join(args) if args else ""
            status = "✓ definita" if name in self.compiler.function_defined else "○ solo prototipo"
            print(f"  func {name}({args_str}); {status}")
        print()

    def cmd_load(self, filename):
        """Carica ed esegue un file .asc"""
        if not filename:
            print("Uso: .load FILENAME")
            return

        if not os.path.exists(filename):
            if os.path.exists(filename + ".asc"):
                filename = filename + ".asc"
            else:
                print(f"Errore: file '{filename}' non trovato.")
                return

        try:
            with open(filename, 'r') as f:
                code = f.read()

            print(f"Caricamento {filename}...")
            self.execute(code, from_file=True)
            self.session_code.append(f"// Caricato da: {filename}")
            self.session_code.append(code)
            print(f"File '{filename}' caricato.")

        except Exception as e:
            print(f"Errore caricamento: {e}")

    def cmd_save(self, filename):
        """Salva la sessione in un file"""
        if not filename:
            print("Uso: .save FILENAME")
            return

        if not filename.endswith('.asc'):
            filename += '.asc'

        try:
            with open(filename, 'w') as f:
                f.write("// Sessione Ascension Shell\n")
                f.write("// Versione: 1.3 (Substr Edition)\n")
                f.write("// " + "=" * 40 + "\n\n")
                f.write('\n'.join(self.session_code))
                f.write('\n')

            print(f"Sessione salvata in '{filename}'")

        except Exception as e:
            print(f"Errore salvataggio: {e}")

    def cmd_history(self):
        """Mostra storico comandi"""
        print("\nStorico comandi:")
        print("─" * 40)

        try:
            history_len = readline.get_current_history_length()
            start = max(1, history_len - 20)

            for i in range(start, history_len + 1):
                item = readline.get_history_item(i)
                if item:
                    print(f"  {i}: {item}")
        except:
            for i, cmd in enumerate(self.history[-20:], 1):
                print(f"  {i}: {cmd}")

        print()

    def count_braces(self, code):
        """Conta parentesi graffe non chiuse"""
        count = 0
        in_string = False

        for i, c in enumerate(code):
            if c == '"' and (i == 0 or code[i-1] != '\\'):
                in_string = not in_string
            if not in_string:
                if c == '{':
                    count += 1
                elif c == '}':
                    count -= 1

        return count

    def execute(self, code, from_file=False):
        """Esegue codice Ascension"""
        try:
            new_compiler = AscensionCompiler()
            new_compiler.structs = self.compiler.structs.copy()
            new_compiler.label_counter = self.compiler.label_counter
            # Preserva prototipi e definizioni già raccolte
            new_compiler.function_prototypes = self.compiler.function_prototypes.copy()
            new_compiler.function_defined = self.compiler.function_defined.copy()

            bytecode = new_compiler.compile(code)
            
            self.compiler.label_counter = new_compiler.label_counter
            # Aggiorna prototipi e definizioni
            self.compiler.function_prototypes.update(new_compiler.function_prototypes)
            self.compiler.function_defined.update(new_compiler.function_defined)

            if self.debug_mode:
                print("\n--- BYTECODE ---")
                for i, op in enumerate(bytecode):
                    print(f"  {i:4}: {op}")
                print("----------------\n")

            self.compiler.structs.update(new_compiler.structs)

            old_program_len = len(self.vm.program)

            for idx, op in enumerate(bytecode):
                if op[0] == 'LABEL':
                    self.vm.labels[op[1]] = old_program_len + idx

            self.vm.program.extend(bytecode)
            self.vm.structs.update(new_compiler.structs)

            self.vm.ip = old_program_len

            if self.vm.local_frames and self.vm.local_frames[0]:
                self.vm.global_memory.update(self.vm.local_frames[0])

            self.vm.local_frames = [self.vm.global_memory.copy()]
            self.vm.call_stack = []
            self.vm.stack = []

            self.vm.run()

            if self.vm.local_frames and self.vm.local_frames[0]:
                self.vm.global_memory.update(self.vm.local_frames[0])

            if not from_file:
                self.session_code.append(code)

        except AscensionException as e:
            print(f"Errore Ascension: {e.message}")

        except Exception as e:
            print(f"Errore: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()

    def handle_command(self, line):
        """Gestisce comandi speciali"""
        parts = line.split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == '.help':
            self.print_help()
        elif cmd == '.clear':
            self.cmd_clear()
        elif cmd == '.vars':
            self.cmd_vars()
        elif cmd == '.funcs':
            self.cmd_funcs()
        elif cmd == '.structs':
            self.cmd_structs()
        elif cmd in ('.matrices', '.matrix', '.mat'):
            self.cmd_matrices()
        elif cmd in ('.protos', '.proto', '.prototypes'):
            self.cmd_protos()
        elif cmd == '.load':
            self.cmd_load(arg.strip())
        elif cmd == '.save':
            self.cmd_save(arg.strip())
        elif cmd == '.history':
            self.cmd_history()
        elif cmd == '.debug':
            self.debug_mode = not self.debug_mode
            print(f"Modalità debug: {'ON' if self.debug_mode else 'OFF'}")
        elif cmd in ('.quit', '.exit', '.q'):
            return False
        else:
            print(f"Comando sconosciuto: {cmd}")
            print("Digita .help per la lista comandi.")

        return True

    def run(self):
        """Loop principale della shell"""
        self.print_banner()

        while True:
            try:
                if self.multiline_buffer:
                    prompt = self.PROMPT_CONTINUE
                else:
                    prompt = self.PROMPT

                line = input(prompt)

                self.history.append(line)

                if not line.strip():
                    continue

                if line.strip().startswith('.') and not self.multiline_buffer:
                    if not self.handle_command(line.strip()):
                        break
                    continue

                self.multiline_buffer += line + "\n"
                self.brace_count = self.count_braces(self.multiline_buffer)

                if self.brace_count <= 0:
                    code = self.multiline_buffer.strip()
                    self.multiline_buffer = ""
                    self.brace_count = 0

                    if code:
                        self.execute(code)

            except EOFError:
                print("\nArrivederci!")
                break

            except KeyboardInterrupt:
                print("\n(Interrotto - usa .quit per uscire)")
                self.multiline_buffer = ""
                self.brace_count = 0
                continue

        print()


def main():
    """Entry point"""
    shell = AscensionShell()
    shell.run()


if __name__ == "__main__":
    main()
