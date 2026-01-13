#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ASCENSION - Linguaggio di Programmazione                   ║
║                         Virtual Machine e Compilatore                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Versione: 12.7 (Math Edition)                                               ║
║  Data: 13/01/2026                                                            ║
║  Autore: EdeFede                                                             ║
║  Licenza: GPL v3                                                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Caratteristiche:                                                            ║
║  - VM stack-based con bytecode                                               ║
║  - Supporto strutture dati (struct)                                          ║
║  - Controllo di flusso: if/else if/else, for, while, switch                  ║
║  - Funzioni con scope locale                                                 ║
║  - I/O file, networking (HTTP/Socket), GUI (Tkinter), TUI (Curses)           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Novità v12.7 - Math Edition:                                                ║
║  - random(): float casuale tra 0.0 e 1.0                                     ║
║  - random(max): intero casuale tra 0 e max-1                                 ║
║  - random(min, max): intero casuale tra min e max-1                          ║
║  - sqrt(x): radice quadrata                                                  ║
║  - pow(base, exp): potenza                                                   ║
║  - exp(x): e^x (esponenziale)                                                ║
║  - log(x): logaritmo naturale                                                ║
║  - abs(x): valore assoluto                                                   ║
║  - floor(x): arrotonda per difetto                                           ║
║  - ceil(x): arrotonda per eccesso                                            ║
║  - sin(x), cos(x), tan(x): funzioni trigonometriche                          ║
║  - asin(x), acos(x), atan(x): funzioni trigonometriche inverse               ║
║  - atan2(y, x): arcotangente a due argomenti                                 ║
║  - PI, E: costanti matematiche                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Novità v12.5 - Substr e Chr:                                                ║
║  - substr(string, start, length): estrae sottostringa                        ║
║  - chr(code): converte codice ASCII in carattere                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Novità v12.4 - Prototipi Funzione (Forward Declarations):                   ║
║  - Sintassi: func nome(args);  (prototipo senza corpo)                       ║
║  - Permette ricorsione mutua tra funzioni                                    ║
║  - Compilazione two-pass per risolvere forward references                    ║
║  - Verifica coerenza argomenti tra prototipo e definizione                   ║
║  - System commands: system(cmd) ritorna exit code, exec(cmd) ritorna output  ║
║  - Valori booleani: true (1), false (0)                                      ║
║  - NULL: valore speciale per indicare assenza/errore (diverso da 0)          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Novità v12.3 - Array Multidimensionali:                                     ║
║  - Sintassi C-style: arr[i][j] e comma: arr[i,j]                             ║
║  - Funzioni: matrix(r,c,v), rows(m), cols(m), dim(m)                         ║
║  - Supporto accesso/scrittura con entrambe le sintassi                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Bug Fix versioni precedenti:                                                ║
║  - Fix #1: Loop for/while annidati ora funzionano correttamente              ║
║  - Fix #2: If dentro for non causa più loop infiniti                         ║
║  - Fix #3: For loop funzionano dopo molti statement                          ║
║  - Fix #4: Accesso membri struct con punto (.) funziona correttamente        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# =============================================================================
#                              IMPORT STANDARD
# =============================================================================

import sys
import re
import os
import curses
import socket
import subprocess
import math
import random as py_random

# =============================================================================
#                              IMPORT OPZIONALI
# =============================================================================
# Questi moduli abilitano funzionalità extra ma non sono obbligatori
try:
    import requests
except ImportError:
    print("Warning: 'requests' library not found. Network (HTTP) functionality disabled.")
    requests = None

try:
    import tkinter as tk
    from tkinter import messagebox, filedialog, simpledialog
except ImportError:
    print("Warning: 'tkinter' library not found. GUI functionality disabled.")
    tk = None
    filedialog = None
    simpledialog = None

# ==========================================
#  ASCENSION VM v12
# ==========================================

# =============================================================================
#                              ECCEZIONI CUSTOM
# =============================================================================

class AscensionException(Exception):
    def __init__(self, message, error_type="Error"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)


# =============================================================================
#                              VIRTUAL MACHINE
# =============================================================================

class AscensionVM:
    """
    Macchina Virtuale stack-based per l'esecuzione del bytecode Ascension.

    La VM utilizza uno stack per le operazioni e supporta:
    - Variabili globali e locali (con scope)
    - Strutture dati (struct)
    - Chiamate a funzione con stack di chiamata
    - Gestione eccezioni (try/catch)
    - I/O su file, GUI (Tkinter), TUI (Curses), Networking (HTTP/Socket)
    """
    def __init__(self):
        """Inizializza la VM con tutti i suoi componenti."""

        # Stack principale per operazioni aritmetiche e logiche
        self.stack = []
        self.global_memory = {}
        self.local_frames = [{}]
        self.structs = {}
        self.call_stack = []
        self.try_stack = []
        self.ip = 0
        self.program = []
        self.labels = {}
        self.return_value = None
        self.file_handles = {}
        self.current_screen = None

        # ----- TKINTER (GUI) -----
        self.tk_root = None
        self.tk_refs = {}
        self.tk_ref_counter = 0

        # --- SOCKETS STATE (v11.0) ---
        self.socket_handles = {}
        self.socket_id_counter = 0

        # --- TKINTER EXTENDED STATE (v11.2) ---
        self.tk_callbacks = {}
        self.tk_after_ids = {}
        self.tk_after_counter = 0

    @property
    def memory(self):
        return self.local_frames[-1]

    def get_var(self, name):
        """
        Recupera il valore di una variabile.
        Cerca prima nel frame locale, poi in quello globale.
        Ritorna 0 se non trovata.
        """
        if name in self.local_frames[-1]:
            return self.local_frames[-1][name]
        return self.global_memory.get(name, 0)

    def set_var(self, name, value, force_global=False):
        """
        Imposta il valore di una variabile.
        Gestisce lo scoping locale/globale automaticamente.
        """
        if force_global or len(self.local_frames) == 1:
            self.global_memory[name] = value
        else:
            if name in self.global_memory and name not in self.local_frames[-1]:
                self.global_memory[name] = value
            else:
                self.local_frames[-1][name] = value

    def load_program(self, program_code, struct_defs):
        """
        Carica un programma compilato nella VM.
        Costruisce la mappa delle label per salti veloci.
        """
        self.program = program_code
        self.structs = struct_defs
        for idx, op in enumerate(self.program):
            if op[0] == 'LABEL':
                self.labels[op[1]] = idx

    def run(self):
        """
        Esegue il programma caricato.
        Loop principale che processa ogni opcode fino alla fine.
        """
        while self.ip < len(self.program):
            opcode = self.program[self.ip]
            op = opcode[0]

            try:
                # ----- OPERAZIONI SULLO STACK -----
                if op == 'PUSH':
                    val = opcode[1]
                    if isinstance(val, str):
                        if val.startswith('"'):
                            val = val[1:-1]
                            # Processa escape sequences
                            val = val.replace('\\n', '\n')
                            val = val.replace('\\t', '\t')
                            val = val.replace('\\r', '\r')
                            val = val.replace('\\"', '"')
                            val = val.replace('\\\\', '\\')
                        elif val.replace('.','',1).lstrip('-').isdigit():
                            val = float(val) if '.' in val else int(val)
                    self.stack.append(val)

                elif op == 'POP':
                    if self.stack: self.stack.pop()

                elif op == 'DUP':
                    if self.stack: self.stack.append(self.stack[-1])

                elif op == 'PUSH_DICT':
                    self.stack.append({})

                elif op == 'PUSH_NULL':
                    # NULL come valore speciale per indicare assenza/errore
                    self.stack.append(None)

                elif op == 'DICT_SET':
                    key = self.stack.pop()
                    val = self.stack.pop()
                    d = self.stack[-1]
                    if isinstance(key, str) and key.startswith('"') and key.endswith('"'):
                        key = key[1:-1]
                    if isinstance(d, dict):
                        d[key] = val

                # ----- OPERAZIONI SU VARIABILI -----
                elif op == 'LOAD':
                    var_name = opcode[1]
                    self.stack.append(self.get_var(var_name))

                elif op == 'STORE':
                    var_name = opcode[1]
                    self.set_var(var_name, self.stack.pop())

                elif op == 'STORE_GLOBAL':
                    var_name = opcode[1]
                    self.set_var(var_name, self.stack.pop(), force_global=True)

                elif op == 'LOAD_GLOBAL':
                    var_name = opcode[1]
                    self.stack.append(self.global_memory.get(var_name, 0))

                # ----- OPERAZIONI SU STRUCT -----
                elif op == 'NEW_STRUCT':
                    name = opcode[1]
                    inst = {'__type__': name}
                    for f in self.structs.get(name, []): inst[f] = 0
                    self.stack.append(inst)

                elif op == 'GET_ATTR':
                    field = opcode[1]; obj = self.stack.pop()
                    self.stack.append(obj.get(field, 0) if isinstance(obj, dict) else 0)

                elif op == 'SET_ATTR':
                    field = opcode[1]; obj = self.stack.pop(); val = self.stack.pop()
                    if isinstance(obj, dict): obj[field] = val

                # ----- OPERAZIONI SU ARRAY -----
                elif op == 'STORE_IDX':
                    idx = self.stack.pop(); name = opcode[1]; val = self.stack.pop()
                    arr_ref = None
                    # Prima cerca nel frame locale corrente
                    if name in self.local_frames[-1]:
                        arr_ref = self.local_frames[-1]
                    # Poi cerca in global_memory
                    elif name in self.global_memory:
                        arr_ref = self.global_memory
                    else:
                        # Se siamo nel main (un solo frame), crea in global_memory
                        # Altrimenti crea nel frame locale
                        if len(self.local_frames) == 1:
                            arr_ref = self.global_memory
                        else:
                            arr_ref = self.local_frames[-1]
                        arr_ref[name] = {}

                    arr = arr_ref.get(name)
                    if not isinstance(arr, dict):
                        arr_ref[name] = {}
                        arr = arr_ref[name]
                    arr[idx] = val

                elif op == 'LOAD_IDX':
                    idx = self.stack.pop(); name = opcode[1]
                    arr = self.get_var(name)
                    if isinstance(arr, str):
                        try:
                            idx = int(idx)
                            if 0 <= idx < len(arr): self.stack.append(arr[idx])
                            else: self.stack.append("")
                        except: self.stack.append("")
                    elif isinstance(arr, dict):
                        self.stack.append(arr.get(idx, 0))
                    else:
                        self.stack.append(0)

                # ----- OPERAZIONI SU ARRAY MULTIDIMENSIONALI (v12.3) -----
                elif op == 'LOAD_IDX_2D':
                    # Stack: [col, row] -> pop col, pop row
                    col = self.stack.pop()
                    row = self.stack.pop()
                    name = opcode[1]
                    arr = self.get_var(name)
                    if isinstance(arr, dict):
                        # Array 2D memorizzato come dict con chiavi "row,col"
                        key = f"{int(row)},{int(col)}"
                        self.stack.append(arr.get(key, 0))
                    else:
                        self.stack.append(0)

                elif op == 'STORE_IDX_2D':
                    # Stack: [value, col, row] -> pop col, pop row, pop value
                    col = self.stack.pop()
                    row = self.stack.pop()
                    val = self.stack.pop()
                    name = opcode[1]
                    # Trova o crea l'array
                    arr_ref = None
                    if name in self.local_frames[-1]:
                        arr_ref = self.local_frames[-1]
                    elif name in self.global_memory:
                        arr_ref = self.global_memory
                    else:
                        if len(self.local_frames) == 1:
                            arr_ref = self.global_memory
                        else:
                            arr_ref = self.local_frames[-1]
                        arr_ref[name] = {'__matrix__': True, '__rows__': 0, '__cols__': 0}
                    
                    arr = arr_ref.get(name)
                    if not isinstance(arr, dict):
                        arr_ref[name] = {'__matrix__': True, '__rows__': 0, '__cols__': 0}
                        arr = arr_ref[name]
                    
                    key = f"{int(row)},{int(col)}"
                    arr[key] = val
                    # Aggiorna dimensioni se necessario
                    r, c = int(row), int(col)
                    if arr.get('__rows__', 0) <= r:
                        arr['__rows__'] = r + 1
                    if arr.get('__cols__', 0) <= c:
                        arr['__cols__'] = c + 1

                elif op == 'CREATE_MATRIX':
                    # Crea una matrice rows x cols inizializzata con un valore
                    init_val = self.stack.pop()
                    cols = int(self.stack.pop())
                    rows = int(self.stack.pop())
                    matrix = {'__matrix__': True, '__rows__': rows, '__cols__': cols}
                    for r in range(rows):
                        for c in range(cols):
                            matrix[f"{r},{c}"] = init_val
                    self.stack.append(matrix)

                elif op == 'MATRIX_ROWS':
                    # Ritorna il numero di righe della matrice
                    arr = self.stack.pop()
                    if isinstance(arr, dict) and arr.get('__matrix__'):
                        self.stack.append(arr.get('__rows__', 0))
                    else:
                        # Per array 1D, ritorna il numero di elementi
                        self.stack.append(len([k for k in arr if not str(k).startswith('__')]) if isinstance(arr, dict) else 0)

                elif op == 'MATRIX_COLS':
                    # Ritorna il numero di colonne della matrice
                    arr = self.stack.pop()
                    if isinstance(arr, dict) and arr.get('__matrix__'):
                        self.stack.append(arr.get('__cols__', 0))
                    else:
                        # Per array 1D, ritorna 1
                        self.stack.append(1 if isinstance(arr, dict) else 0)

                elif op == 'MATRIX_DIM':
                    # Ritorna la dimensionalità (1 o 2)
                    arr = self.stack.pop()
                    if isinstance(arr, dict):
                        if arr.get('__matrix__'):
                            self.stack.append(2)
                        else:
                            self.stack.append(1)
                    else:
                        self.stack.append(0)

                # ----- CHIAMATE A FUNZIONE -----
                elif op == 'CALL':
                    if opcode[1] not in self.labels:
                        raise AscensionException(f"Funzione non definita: '{opcode[1]}'", "LinkerError")
                    self.call_stack.append((self.ip + 1, len(self.local_frames)))
                    self.local_frames.append({})
                    self.ip = self.labels[opcode[1]]
                    continue

                elif op == 'RET':
                    if self.call_stack:
                        ret_ip, _ = self.call_stack.pop()
                        self.local_frames.pop()
                        self.ip = ret_ip
                        continue
                    else: break

                elif op == 'RET_VAL':
                    ret_val = self.stack.pop() if self.stack else 0
                    if self.call_stack:
                        ret_ip, _ = self.call_stack.pop()
                        self.local_frames.pop()
                        self.stack.append(ret_val)
                        self.ip = ret_ip
                        continue
                    else:
                        self.return_value = ret_val
                        break

                # ----- INPUT/OUTPUT E FUNZIONI BUILT-IN -----
                elif op == 'READ':
                    try: self.stack.append(input("INPUT > "))
                    except EOFError: self.stack.append("")

                elif op == 'LEN':
                    target = self.stack.pop()
                    length = 0
                    if isinstance(target, str): length = len(target)
                    elif isinstance(target, dict): length = len([k for k in target if k != '__type__'])
                    self.stack.append(length)

                elif op == 'KEYS':
                    container = self.stack.pop()
                    if not isinstance(container, dict): self.stack.append({})
                    else:
                        keys_list = [k for k in container if k != '__type__']
                        try: keys_list.sort()
                        except: keys_list.sort(key=str)
                        result_array = {i: key for i, key in enumerate(keys_list)}
                        self.stack.append(result_array)

                elif op == 'TO_INT':
                    val = self.stack.pop()
                    try:
                        if isinstance(val, str):
                            if val.lstrip('-').replace('.','',1).isdigit(): self.stack.append(int(float(val)))
                            elif len(val) == 1: self.stack.append(ord(val))
                            else: raise ValueError
                        else: self.stack.append(int(float(val)))
                    except: raise AscensionException(f"Impossibile convertire '{val}' in intero.", "ConversionError")

                elif op == 'TO_FLOAT':
                    val = self.stack.pop()
                    try: self.stack.append(float(val))
                    except: raise AscensionException(f"Impossibile convertire '{val}' in float.", "ConversionError")

                elif op == 'SUBSTR':
                    # substr(string, start, length) - estrae sottostringa
                    length = int(self.stack.pop())
                    start = int(self.stack.pop())
                    string = self.stack.pop()
                    if isinstance(string, str):
                        if start < 0: start = 0
                        if start >= len(string):
                            self.stack.append("")
                        else:
                            end = start + length
                            if end > len(string): end = len(string)
                            self.stack.append(string[start:end])
                    else:
                        self.stack.append("")

                elif op == 'CHR':
                    # chr(code) - converte codice ASCII in carattere
                    code = int(self.stack.pop())
                    try:
                        if 0 <= code <= 127:
                            self.stack.append(chr(code))
                        else:
                            self.stack.append("")
                    except:
                        self.stack.append("")

                # ----- SYSTEM COMMANDS (v12.4) -----
                elif op == 'SYSTEM':
                    # Esegue comando shell, ritorna exit code
                    cmd = self.stack.pop()
                    if isinstance(cmd, str) and cmd.startswith('"') and cmd.endswith('"'):
                        cmd = cmd[1:-1]
                    try:
                        result = subprocess.run(cmd, shell=True)
                        self.stack.append(result.returncode)
                    except Exception as e:
                        self.stack.append(-1)

                elif op == 'EXEC':
                    # Esegue comando shell, ritorna output come stringa
                    cmd = self.stack.pop()
                    if isinstance(cmd, str) and cmd.startswith('"') and cmd.endswith('"'):
                        cmd = cmd[1:-1]
                    try:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        self.stack.append(result.stdout)
                    except Exception as e:
                        self.stack.append("")

                # ----- FILE I/O -----
                elif op == 'FILE_OPEN':
                    mode = self.stack.pop(); filename = self.stack.pop()
                    try:
                        f = open(filename, mode); hid = id(f); self.file_handles[hid] = f; self.stack.append(hid)
                    except: self.stack.append(None)  # NULL se fallisce

                elif op == 'FILE_WRITE':
                    content = self.stack.pop(); hid = self.stack.pop()
                    if hid is not None and hid in self.file_handles:
                        try: self.file_handles[hid].write(str(content)); self.file_handles[hid].flush(); self.stack.append(1)
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'FILE_READLINE':
                    hid = self.stack.pop()
                    if hid is not None and hid in self.file_handles:
                        try: self.stack.append(self.file_handles[hid].readline())
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'FILE_READALL':
                    hid = self.stack.pop()
                    if hid is not None and hid in self.file_handles:
                        try: self.stack.append(self.file_handles[hid].read())
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'FILE_CLOSE':
                    hid = self.stack.pop()
                    if hid is not None and hid in self.file_handles:
                        try: self.file_handles.pop(hid).close(); self.stack.append(1)
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                # ----- CURSES (TUI) -----
                elif op == 'CURSES_INIT':
                    try:
                        if curses is None: raise ImportError
                        self.current_screen = curses.initscr()
                        curses.noecho(); curses.cbreak(); self.current_screen.keypad(True); self.stack.append(1)
                    except: self.stack.append(0)
                elif op == 'CURSES_END':
                    if self.current_screen:
                        try: curses.nocbreak(); curses.echo(); curses.endwin(); self.current_screen = None; self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)
                elif op == 'CURSES_CLEAR':
                    if self.current_screen: self.current_screen.clear(); self.stack.append(1)
                    else: self.stack.append(0)
                elif op == 'CURSES_REFRESH':
                    if self.current_screen: self.current_screen.refresh(); self.stack.append(1)
                    else: self.stack.append(0)
                elif op == 'CURSES_MOVE':
                    x = int(self.stack.pop()); y = int(self.stack.pop())
                    if self.current_screen: self.current_screen.move(y, x); self.stack.append(1)
                    else: self.stack.append(0)
                elif op == 'CURSES_WRITE':
                    s = str(self.stack.pop())
                    if self.current_screen: self.current_screen.addstr(s); self.stack.append(1)
                    else: self.stack.append(0)
                elif op == 'CURSES_READ_KEY':
                    if self.current_screen:
                        try: self.stack.append(self.current_screen.getch())
                        except: self.stack.append(-1)
                    else: self.stack.append(-1)

                # --- NETWORK (HTTP) ---
                elif op == 'HTTP_GET':
                    url = str(self.stack.pop())
                    if requests:
                        try:
                            r = requests.get(url, timeout=10)
                            self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': r.status_code, 'body': r.text})
                        except Exception as e: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': str(e)})
                    else: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': "No requests lib"})

                elif op == 'HTTP_POST':
                    data = self.stack.pop(); url = str(self.stack.pop())
                    payload = {k:v for k,v in data.items() if k!='__type__'} if isinstance(data, dict) else str(data)
                    if requests:
                        try:
                            r = requests.post(url, data=payload, timeout=10)
                            self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': r.status_code, 'body': r.text})
                        except Exception as e: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': str(e)})
                    else: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': "No requests lib"})

                elif op == 'RESP_STATUS':
                    r = self.stack.pop(); self.stack.append(r.get('status', 0) if isinstance(r, dict) else 0)
                elif op == 'RESP_BODY':
                    r = self.stack.pop(); self.stack.append(r.get('body', "") if isinstance(r, dict) else "")

                # --- TKINTER GUI (v11.0) ---
                elif op == 'TK_ROOT':
                    if tk is None: raise AscensionException("Tkinter missing")
                    title = self.stack.pop()
                    if not self.tk_root:
                        self.tk_root = tk.Tk(); self.tk_root.title(str(title))
                        self.tk_ref_counter += 1; self.tk_refs[self.tk_ref_counter] = self.tk_root
                        self.stack.append(self.tk_ref_counter)
                    else: self.stack.append(1)

                elif op == 'TK_WIDGET':
                    config = self.stack.pop(); w_type = self.stack.pop(); parent_id = self.stack.pop()
                    if not isinstance(config, dict): config = {}
                    clean_conf = {k:v for k,v in config.items() if k!='__type__'}
                    if 'command' in clean_conf: del clean_conf['command']
                    # Converti parent_id a int se è float
                    if isinstance(parent_id, float):
                        parent_id = int(parent_id)
                    if parent_id in self.tk_refs:
                        try:
                            cls = getattr(tk, str(w_type))
                            w = cls(self.tk_refs[parent_id], **clean_conf)
                            self.tk_ref_counter += 1; self.tk_refs[self.tk_ref_counter] = w
                            self.stack.append(self.tk_ref_counter)
                        except Exception as e:
                            self.stack.append(0)
                    else:
                        self.stack.append(0)

                elif op == 'TK_PACK':
                    config = self.stack.pop(); wid = self.stack.pop()
                    clean_conf = {k:v for k,v in config.items() if k!='__type__'} if isinstance(config, dict) else {}
                    if wid in self.tk_refs: self.tk_refs[wid].pack(**clean_conf); self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_GRID':
                    config = self.stack.pop(); wid = self.stack.pop()
                    clean_conf = {k:v for k,v in config.items() if k!='__type__'} if isinstance(config, dict) else {}
                    if wid in self.tk_refs: self.tk_refs[wid].grid(**clean_conf); self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_CONFIG':
                    config = self.stack.pop(); wid = self.stack.pop()
                    clean_conf = {k:v for k,v in config.items() if k!='__type__'} if isinstance(config, dict) else {}
                    if wid in self.tk_refs: self.tk_refs[wid].config(**clean_conf); self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_GET':
                    wid = self.stack.pop()
                    if wid in self.tk_refs:
                        try: self.stack.append(self.tk_refs[wid].get())
                        except: self.stack.append("")
                    else: self.stack.append("")

                elif op == 'TK_MSGBOX':
                    msg = self.stack.pop(); title = self.stack.pop()
                    if tk: messagebox.showinfo(str(title), str(msg)); self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_MAINLOOP':
                    if self.tk_root:
                        try: self.tk_root.mainloop(); self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                # --- TKINTER EXTENDED (v11.2) ---
                elif op == 'TK_COMMAND':
                    func_name = str(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        callback = self._make_tk_callback(func_name)
                        self.tk_refs[wid].config(command=callback)
                        self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_BIND':
                    func_name = str(self.stack.pop())
                    event = str(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        callback = self._make_tk_event_callback(func_name)
                        self.tk_refs[wid].bind(event, callback)
                        self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_AFTER':
                    func_name = str(self.stack.pop())
                    ms = int(self.stack.pop())
                    if self.tk_root:
                        callback = self._make_tk_callback(func_name)
                        after_id = self.tk_root.after(ms, callback)
                        self.tk_after_counter += 1
                        self.tk_after_ids[self.tk_after_counter] = after_id
                        self.stack.append(self.tk_after_counter)
                    else: self.stack.append(0)

                elif op == 'TK_AFTER_CANCEL':
                    aid = int(self.stack.pop())
                    if aid in self.tk_after_ids and self.tk_root:
                        self.tk_root.after_cancel(self.tk_after_ids[aid])
                        del self.tk_after_ids[aid]
                        self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_UPDATE':
                    if self.tk_root:
                        self.tk_root.update()
                        self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_DESTROY':
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try:
                            self.tk_refs[wid].destroy()
                            del self.tk_refs[wid]
                            self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_SET':
                    value = str(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        w = self.tk_refs[wid]
                        try:
                            if isinstance(w, tk.Entry):
                                w.delete(0, tk.END); w.insert(0, value)
                            elif isinstance(w, tk.Text):
                                w.delete('1.0', tk.END); w.insert('1.0', value)
                            self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_CLEAR':
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        w = self.tk_refs[wid]
                        try:
                            if isinstance(w, tk.Entry): w.delete(0, tk.END)
                            elif isinstance(w, tk.Text): w.delete('1.0', tk.END)
                            elif isinstance(w, tk.Listbox): w.delete(0, tk.END)
                            self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_FOCUS':
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        self.tk_refs[wid].focus_set()
                        self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_GEOMETRY':
                    geom = str(self.stack.pop())
                    if self.tk_root:
                        self.tk_root.geometry(geom); self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_TITLE':
                    title = str(self.stack.pop())
                    if self.tk_root:
                        self.tk_root.title(title); self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_RESIZABLE':
                    h = int(self.stack.pop()); w = int(self.stack.pop())
                    if self.tk_root:
                        self.tk_root.resizable(w, h); self.stack.append(1)
                    else: self.stack.append(0)

                elif op == 'TK_TEXT_GET':
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.stack.append(self.tk_refs[wid].get('1.0', tk.END).rstrip('\n'))
                        except: self.stack.append("")
                    else: self.stack.append("")

                elif op == 'TK_TEXT_INSERT':
                    text = str(self.stack.pop())
                    pos = str(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.tk_refs[wid].insert(pos, text); self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_LISTBOX_ADD':
                    item = str(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.tk_refs[wid].insert(tk.END, item); self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_LISTBOX_GET':
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try:
                            sel = self.tk_refs[wid].curselection()
                            self.stack.append(self.tk_refs[wid].get(sel[0]) if sel else "")
                        except: self.stack.append("")
                    else: self.stack.append("")

                elif op == 'TK_LISTBOX_INDEX':
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try:
                            sel = self.tk_refs[wid].curselection()
                            self.stack.append(sel[0] if sel else -1)
                        except: self.stack.append(-1)
                    else: self.stack.append(-1)

                elif op == 'TK_FILEDIALOG_OPEN':
                    title = str(self.stack.pop())
                    if filedialog:
                        path = filedialog.askopenfilename(title=title)
                        self.stack.append(path if path else "")
                    else: self.stack.append("")

                elif op == 'TK_FILEDIALOG_SAVE':
                    title = str(self.stack.pop())
                    if filedialog:
                        path = filedialog.asksaveasfilename(title=title)
                        self.stack.append(path if path else "")
                    else: self.stack.append("")

                elif op == 'TK_ASKSTRING':
                    prompt = str(self.stack.pop())
                    title = str(self.stack.pop())
                    if simpledialog:
                        result = simpledialog.askstring(title, prompt)
                        self.stack.append(result if result else "")
                    else: self.stack.append("")

                elif op == 'TK_ASKYESNO':
                    msg = str(self.stack.pop())
                    title = str(self.stack.pop())
                    if messagebox:
                        result = messagebox.askyesno(title, msg)
                        self.stack.append(1 if result else 0)
                    else: self.stack.append(0)

                # --- CANVAS (v11.2) ---
                elif op == 'TK_CANVAS_LINE':
                    color = str(self.stack.pop())
                    y2 = int(self.stack.pop()); x2 = int(self.stack.pop())
                    y1 = int(self.stack.pop()); x1 = int(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.stack.append(self.tk_refs[wid].create_line(x1,y1,x2,y2,fill=color))
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_CANVAS_RECT':
                    color = str(self.stack.pop())
                    y2 = int(self.stack.pop()); x2 = int(self.stack.pop())
                    y1 = int(self.stack.pop()); x1 = int(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.stack.append(self.tk_refs[wid].create_rectangle(x1,y1,x2,y2,fill=color))
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_CANVAS_OVAL':
                    color = str(self.stack.pop())
                    y2 = int(self.stack.pop()); x2 = int(self.stack.pop())
                    y1 = int(self.stack.pop()); x1 = int(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.stack.append(self.tk_refs[wid].create_oval(x1,y1,x2,y2,fill=color))
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_CANVAS_TEXT':
                    color = str(self.stack.pop())
                    text = str(self.stack.pop())
                    y = int(self.stack.pop()); x = int(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.stack.append(self.tk_refs[wid].create_text(x,y,text=text,fill=color))
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_CANVAS_CLEAR':
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.tk_refs[wid].delete("all"); self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_CANVAS_DELETE':
                    item_id = int(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.tk_refs[wid].delete(item_id); self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                elif op == 'TK_CANVAS_MOVE':
                    dy = int(self.stack.pop()); dx = int(self.stack.pop())
                    item_id = int(self.stack.pop())
                    wid = int(self.stack.pop())
                    if wid in self.tk_refs:
                        try: self.tk_refs[wid].move(item_id, dx, dy); self.stack.append(1)
                        except: self.stack.append(0)
                    else: self.stack.append(0)

                # --- NEW: DNS Resolution (GET_IP) v11.1 ---
                elif op == 'GET_IP':
                    hostname = str(self.stack.pop())
                    try:
                        ip_addr = socket.gethostbyname(hostname)
                        self.stack.append(ip_addr)
                    except:
                        # Restituisce stringa vuota in caso di errore di risoluzione
                        self.stack.append("")

                # --- SOCKETS (TCP/IP) v11.0 ---
                elif op == 'SOCKET_OPEN':
                    proto = str(self.stack.pop()); sock_type = str(self.stack.pop())
                    try:
                        family = socket.AF_INET
                        type_map = {"TCP": socket.SOCK_STREAM, "UDP": socket.SOCK_DGRAM}
                        if sock_type not in type_map: raise ValueError("Invalid socket type")

                        s = socket.socket(family, type_map[sock_type])
                        self.socket_id_counter += 1
                        hid = self.socket_id_counter
                        self.socket_handles[hid] = s
                        self.stack.append(hid)
                    except Exception as e:
                        self.stack.append(None)  # NULL se fallisce

                elif op == 'SOCKET_BIND':
                    port = int(self.stack.pop()); ip = str(self.stack.pop()); sid = self.stack.pop()
                    if sid is not None and sid in self.socket_handles:
                        try:
                            self.socket_handles[sid].bind((ip, port))
                            self.stack.append(1)
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'SOCKET_LISTEN':
                    backlog = int(self.stack.pop()); sid = self.stack.pop()
                    if sid is not None and sid in self.socket_handles:
                        try:
                            self.socket_handles[sid].listen(backlog)
                            self.stack.append(1)
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'SOCKET_ACCEPT':
                    sid = self.stack.pop()
                    if sid is not None and sid in self.socket_handles:
                        try:
                            conn, addr = self.socket_handles[int(sid)].accept()
                            self.socket_id_counter += 1
                            new_sid = self.socket_id_counter
                            self.socket_handles[new_sid] = conn
                            self.stack.append(new_sid)
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'SOCKET_CONNECT':
                    port = int(self.stack.pop()); ip = str(self.stack.pop()); sid = self.stack.pop()
                    if sid is not None and sid in self.socket_handles:
                        try:
                            # Aggiungiamo un timeout per evitare che socket_connect blocchi il VM indefinitamente
                            self.socket_handles[int(sid)].settimeout(5)
                            self.socket_handles[int(sid)].connect((ip, port))
                            self.stack.append(1)
                        except:
                            self.stack.append(None)
                        finally:
                             # Resetta il timeout per il socket
                             if sid in self.socket_handles: self.socket_handles[int(sid)].settimeout(None)
                    else: self.stack.append(None)

                elif op == 'SOCKET_SEND':
                    data = str(self.stack.pop()); sid = self.stack.pop()
                    if sid is not None and sid in self.socket_handles:
                        try:
                            sent = self.socket_handles[int(sid)].send(data.encode('utf-8'))
                            self.stack.append(sent)
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'SOCKET_RECV':
                    max_b = int(self.stack.pop()); sid = self.stack.pop()
                    if sid is not None and sid in self.socket_handles:
                        try:
                            data = self.socket_handles[int(sid)].recv(max_b)
                            self.stack.append(data.decode('utf-8'))
                        except: self.stack.append(None)
                    else: self.stack.append(None)

                elif op == 'SOCKET_CLOSE':
                    sid = self.stack.pop()
                    if sid is not None and sid in self.socket_handles:
                        try:
                            self.socket_handles.pop(int(sid)).close()
                            self.stack.append(1)
                        except: self.stack.append(None)
                    else: self.stack.append(None)


                # --- TRY / CATCH ---
                elif op == 'TRY_START':
                    catch_label = opcode[1]
                    self.try_stack.append((catch_label, len(self.local_frames), len(self.call_stack)))
                elif op == 'TRY_END':
                    if self.try_stack: self.try_stack.pop()
                    end_label = opcode[1]; self.ip = self.labels[end_label]; continue
                elif op == 'THROW':
                    msg = self.stack.pop() if self.stack else "Unknown error"
                    raise AscensionException(str(msg))
                elif op == 'CATCH_START': pass
                elif op == 'CATCH_END': pass

                # --- MATH ---
                elif op in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'GT', 'LT', 'EQ', 'NEQ', 'GTE', 'LTE', 'AND', 'OR']:
                    b = self.stack.pop(); a = self.stack.pop()
                    # Gestione NULL nei confronti
                    if op == 'EQ': 
                        self.stack.append(1 if a == b else 0)
                    elif op == 'NEQ': 
                        self.stack.append(1 if a != b else 0)
                    elif op == 'AND': 
                        # NULL è considerato falsy
                        self.stack.append(1 if a and b else 0)
                    elif op == 'OR': 
                        self.stack.append(1 if a or b else 0)
                    elif a is None or b is None:
                        # Operazioni matematiche con NULL danno NULL
                        self.stack.append(None)
                    elif op == 'ADD' and (isinstance(a, str) or isinstance(b, str)): 
                        self.stack.append(str(a) + str(b))
                    else:
                        try: a = float(a); b = float(b)
                        except: raise AscensionException(f"Op illegale: {a} {op} {b}", "TypeError")
                        if op == 'ADD': r = a + b
                        elif op == 'SUB': r = a - b
                        elif op == 'MUL': r = a * b
                        elif op == 'DIV':
                            if b==0: raise AscensionException("DivZero")
                            r = a / b
                        elif op == 'MOD': r = a % b
                        elif op == 'GT': r = 1 if a > b else 0
                        elif op == 'LT': r = 1 if a < b else 0
                        elif op == 'GTE': r = 1 if a >= b else 0
                        elif op == 'LTE': r = 1 if a <= b else 0
                        if isinstance(r, float) and r.is_integer(): r = int(r)
                        self.stack.append(r)

                elif op == 'NOT': 
                    val = self.stack.pop()
                    # NULL è considerato falsy, quindi !NULL = 1
                    self.stack.append(1 if not val else 0)

                # ----- FUNZIONI MATEMATICHE (v12.7) -----
                elif op == 'RANDOM':
                    # Nessun argomento: float tra 0.0 e 1.0
                    self.stack.append(py_random.random())
                
                elif op == 'RANDOM_MAX':
                    # Un argomento: int tra 0 e max-1
                    max_val = int(self.stack.pop())
                    self.stack.append(py_random.randint(0, max_val - 1))
                
                elif op == 'RANDOM_RANGE':
                    # Due argomenti: int tra min e max-1
                    max_val = int(self.stack.pop())
                    min_val = int(self.stack.pop())
                    self.stack.append(py_random.randint(min_val, max_val - 1))
                
                elif op == 'SQRT':
                    val = float(self.stack.pop())
                    if val < 0:
                        raise AscensionException("sqrt di numero negativo", "MathError")
                    self.stack.append(math.sqrt(val))
                
                elif op == 'POW':
                    exp = float(self.stack.pop())
                    base = float(self.stack.pop())
                    self.stack.append(math.pow(base, exp))
                
                elif op == 'EXP':
                    val = float(self.stack.pop())
                    self.stack.append(math.exp(val))
                
                elif op == 'LOG':
                    val = float(self.stack.pop())
                    if val <= 0:
                        raise AscensionException("log di numero non positivo", "MathError")
                    self.stack.append(math.log(val))
                
                elif op == 'ABS':
                    val = self.stack.pop()
                    if isinstance(val, (int, float)):
                        self.stack.append(abs(val))
                    else:
                        self.stack.append(abs(float(val)))
                
                elif op == 'FLOOR':
                    val = float(self.stack.pop())
                    self.stack.append(int(math.floor(val)))
                
                elif op == 'CEIL':
                    val = float(self.stack.pop())
                    self.stack.append(int(math.ceil(val)))
                
                elif op == 'SIN':
                    val = float(self.stack.pop())
                    self.stack.append(math.sin(val))
                
                elif op == 'COS':
                    val = float(self.stack.pop())
                    self.stack.append(math.cos(val))
                
                elif op == 'TAN':
                    val = float(self.stack.pop())
                    self.stack.append(math.tan(val))
                
                elif op == 'ASIN':
                    val = float(self.stack.pop())
                    if val < -1 or val > 1:
                        raise AscensionException("asin fuori range [-1, 1]", "MathError")
                    self.stack.append(math.asin(val))
                
                elif op == 'ACOS':
                    val = float(self.stack.pop())
                    if val < -1 or val > 1:
                        raise AscensionException("acos fuori range [-1, 1]", "MathError")
                    self.stack.append(math.acos(val))
                
                elif op == 'ATAN':
                    val = float(self.stack.pop())
                    self.stack.append(math.atan(val))
                
                elif op == 'ATAN2':
                    x = float(self.stack.pop())
                    y = float(self.stack.pop())
                    self.stack.append(math.atan2(y, x))

                # ----- CONTROLLO DI FLUSSO -----
                elif op == 'JMP': self.ip = self.labels[opcode[1]]; continue
                elif op == 'JZ':
                    val = self.stack.pop()
                    # NULL è considerato come 0 (falsy) per i salti condizionali
                    if val == 0 or val is None: self.ip = self.labels[opcode[1]]; continue
                elif op == 'JNZ':
                    val = self.stack.pop()
                    if val != 0 and val is not None: self.ip = self.labels[opcode[1]]; continue
                elif op == 'PRINT':
                    count = opcode[1]; args = []
                    for _ in range(count):
                        val = self.stack.pop()
                        if val is None:
                            args.append("NULL")
                        elif isinstance(val, float) and val.is_integer(): 
                            args.append(str(int(val)))
                        else:
                            args.append(str(val))
                    print("OUTPUT > " + " ".join(reversed(args)))
                elif op == 'LABEL': pass

                self.ip += 1

            except AscensionException as e:
                handled = False
                while self.try_stack:
                    catch_label, frame_depth, call_depth = self.try_stack.pop()
                    while len(self.local_frames) > frame_depth: self.local_frames.pop()
                    while len(self.call_stack) > call_depth: self.call_stack.pop()
                    self.stack.append(e.message)
                    self.ip = self.labels[catch_label]
                    handled = True; break
                if not handled:
                    print(f"Uncaught Ex @ IP {self.ip}: {e.message}")
                    if self.current_screen: curses.nocbreak(); curses.echo(); curses.endwin()
                    break

            except Exception as e:
                print(f"Runtime Error @ IP {self.ip}: {e}")
                if self.current_screen: curses.nocbreak(); curses.echo(); curses.endwin()
                break

    # --- CALLBACK HELPERS (v11.2) ---
    def _make_tk_callback(self, func_name):
        """Crea closure per callback senza argomenti (bottoni, after)"""
        vm = self
        def callback():
            vm._call_ascension_func(func_name, [])
        return callback

    def _make_tk_event_callback(self, func_name):
        """Crea closure per callback con evento (bind)"""
        vm = self
        def callback(event):
            event_dict = {
                '__type__': 'EVENT',
                'x': getattr(event, 'x', 0),
                'y': getattr(event, 'y', 0),
                'key': getattr(event, 'keysym', ''),
                'keycode': getattr(event, 'keycode', 0),
                'char': getattr(event, 'char', ''),
                'button': getattr(event, 'num', 0),
            }
            vm._call_ascension_func(func_name, [event_dict])
        return callback

    def _call_ascension_func(self, func_name, args):
        """Chiama una funzione Ascension dal codice Python (callback)"""
        if func_name not in self.labels:
            print(f"Warning: Callback function '{func_name}' not defined")
            return

        # Pusha argomenti in ordine inverso
        for arg in reversed(args):
            self.stack.append(arg)

        # Setup call frame - usiamo un IP fittizio alto per indicare "ritorna a mainloop"
        self.call_stack.append((-999, len(self.local_frames)))
        self.local_frames.append({})
        self.ip = self.labels[func_name]

        # Esegui la funzione usando la stessa logica di run()
        try:
            while self.ip < len(self.program):
                opcode = self.program[self.ip]
                op = opcode[0]

                # Gestiamo manualmente RET per uscire dal callback
                if op == 'RET':
                    if self.call_stack:
                        ret_ip, _ = self.call_stack.pop()
                        self.local_frames.pop()
                        if ret_ip == -999:  # Era un callback, esci
                            break
                        self.ip = ret_ip
                        continue
                    else:
                        break

                if op == 'RET_VAL':
                    ret_val = self.stack.pop() if self.stack else 0
                    if self.call_stack:
                        ret_ip, _ = self.call_stack.pop()
                        self.local_frames.pop()
                        if ret_ip == -999:  # Era un callback, esci
                            break
                        self.stack.append(ret_val)
                        self.ip = ret_ip
                        continue
                    else:
                        break

                # Esegui l'istruzione
                self._exec_opcode(opcode)
                self.ip += 1

        except Exception as e:
            print(f"Error in callback '{func_name}': {e}")
            import traceback
            traceback.print_exc()

    def _exec_opcode(self, opcode):
        """Esegue un singolo opcode - estratto da run() per riuso nei callback"""
        op = opcode[0]

        # --- STACK OPS ---
        if op == 'PUSH':
            val = opcode[1]
            if isinstance(val, str):
                if val.startswith('"'):
                    val = val[1:-1]
                    # Processa escape sequences
                    val = val.replace('\\n', '\n')
                    val = val.replace('\\t', '\t')
                    val = val.replace('\\r', '\r')
                    val = val.replace('\\"', '"')
                    val = val.replace('\\\\', '\\')
                elif val.replace('.','',1).lstrip('-').isdigit():
                    val = float(val) if '.' in val else int(val)
            self.stack.append(val)

        elif op == 'POP':
            if self.stack: self.stack.pop()

        elif op == 'DUP':
            if self.stack: self.stack.append(self.stack[-1])

        elif op == 'PUSH_DICT':
            self.stack.append({})

        elif op == 'DICT_SET':
            key = self.stack.pop()
            val = self.stack.pop()
            d = self.stack[-1]
            if isinstance(key, str) and key.startswith('"') and key.endswith('"'):
                key = key[1:-1]
            if isinstance(d, dict):
                d[key] = val

        # --- MEMORIA ---
        elif op == 'LOAD':
            var_name = opcode[1]
            self.stack.append(self.get_var(var_name))

        elif op == 'STORE':
            var_name = opcode[1]
            self.set_var(var_name, self.stack.pop())

        elif op == 'STORE_GLOBAL':
            var_name = opcode[1]
            self.set_var(var_name, self.stack.pop(), force_global=True)

        elif op == 'LOAD_GLOBAL':
            var_name = opcode[1]
            self.stack.append(self.global_memory.get(var_name, 0))

        # --- STRUCT ---
        elif op == 'NEW_STRUCT':
            name = opcode[1]
            inst = {'__type__': name}
            for f in self.structs.get(name, []): inst[f] = 0
            self.stack.append(inst)

        elif op == 'GET_ATTR':
            field = opcode[1]; obj = self.stack.pop()
            self.stack.append(obj.get(field, 0) if isinstance(obj, dict) else 0)

        elif op == 'SET_ATTR':
            field = opcode[1]; obj = self.stack.pop(); val = self.stack.pop()
            if isinstance(obj, dict): obj[field] = val

        # --- ARRAY ---
        elif op == 'STORE_IDX':
            idx = self.stack.pop(); name = opcode[1]; val = self.stack.pop()
            arr_ref = None
            # Prima cerca nel frame locale corrente
            if name in self.local_frames[-1]:
                arr_ref = self.local_frames[-1]
            # Poi cerca in global_memory
            elif name in self.global_memory:
                arr_ref = self.global_memory
            else:
                # Se siamo nel main (un solo frame), crea in global_memory
                # Altrimenti crea nel frame locale
                if len(self.local_frames) == 1:
                    arr_ref = self.global_memory
                else:
                    arr_ref = self.local_frames[-1]
                arr_ref[name] = {}

            arr = arr_ref.get(name)
            if not isinstance(arr, dict):
                arr_ref[name] = {}
                arr = arr_ref[name]
            arr[idx] = val

        elif op == 'LOAD_IDX':
            idx = self.stack.pop(); name = opcode[1]
            arr = self.get_var(name)
            if isinstance(arr, str):
                try:
                    idx = int(idx)
                    if 0 <= idx < len(arr): self.stack.append(arr[idx])
                    else: self.stack.append("")
                except: self.stack.append("")
            elif isinstance(arr, dict):
                self.stack.append(arr.get(idx, 0))
            else:
                self.stack.append(0)

        # --- FUNZIONI ---
        elif op == 'CALL':
            if opcode[1] not in self.labels:
                raise AscensionException(f"Funzione non definita: '{opcode[1]}'", "LinkerError")
            self.call_stack.append((self.ip + 1, len(self.local_frames)))
            self.local_frames.append({})
            self.ip = self.labels[opcode[1]] - 1  # -1 perché incrementiamo dopo

        elif op == 'LABEL':
            pass  # No-op

        # --- I/O & Built-in ---
        elif op == 'READ':
            try: self.stack.append(input("INPUT > "))
            except EOFError: self.stack.append("")

        elif op == 'LEN':
            target = self.stack.pop()
            length = 0
            if isinstance(target, str): length = len(target)
            elif isinstance(target, dict): length = len([k for k in target if k != '__type__'])
            self.stack.append(length)

        elif op == 'KEYS':
            container = self.stack.pop()
            if not isinstance(container, dict): self.stack.append({})
            else:
                keys_list = [k for k in container if k != '__type__']
                try: keys_list.sort()
                except: keys_list.sort(key=str)
                result_array = {i: key for i, key in enumerate(keys_list)}
                self.stack.append(result_array)

        elif op == 'TO_INT':
            val = self.stack.pop()
            try:
                if isinstance(val, str):
                    if val.lstrip('-').replace('.','',1).isdigit(): self.stack.append(int(float(val)))
                    elif len(val) == 1: self.stack.append(ord(val))
                    else: raise ValueError
                else: self.stack.append(int(float(val)))
            except: raise AscensionException(f"Impossibile convertire '{val}' in intero.", "ConversionError")

        elif op == 'TO_FLOAT':
            val = self.stack.pop()
            try: self.stack.append(float(val))
            except: raise AscensionException(f"Impossibile convertire '{val}' in float.", "ConversionError")

        # --- PRINT ---
        elif op == 'PRINT':
            count = opcode[1]; args = []
            for _ in range(count):
                val = self.stack.pop()
                if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                args.append(val)
            print(*reversed(args))

        # --- MATH ---
        elif op in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'GT', 'LT', 'EQ', 'NEQ', 'GTE', 'LTE', 'AND', 'OR']:
            b = self.stack.pop(); a = self.stack.pop()
            if op == 'ADD' and (isinstance(a, str) or isinstance(b, str)): self.stack.append(str(a) + str(b))
            elif op == 'EQ': self.stack.append(1 if a == b else 0)
            elif op == 'NEQ': self.stack.append(1 if a != b else 0)
            elif op == 'AND': self.stack.append(1 if a and b else 0)
            elif op == 'OR': self.stack.append(1 if a or b else 0)
            else:
                try: a = float(a); b = float(b)
                except: raise AscensionException(f"Op illegale: {a} {op} {b}", "TypeError")
                if op == 'ADD': r = a + b
                elif op == 'SUB': r = a - b
                elif op == 'MUL': r = a * b
                elif op == 'DIV':
                    if b==0: raise AscensionException("DivZero")
                    r = a / b
                elif op == 'MOD': r = a % b
                elif op == 'GT': r = 1 if a > b else 0
                elif op == 'LT': r = 1 if a < b else 0
                elif op == 'GTE': r = 1 if a >= b else 0
                elif op == 'LTE': r = 1 if a <= b else 0
                if isinstance(r, float) and r.is_integer(): r = int(r)
                self.stack.append(r)

        elif op == 'NOT': self.stack.append(1 if not self.stack.pop() else 0)

        # --- FLUSSO ---
        elif op == 'JMP': self.ip = self.labels[opcode[1]] - 1
        elif op == 'JZ':
            if self.stack.pop() == 0: self.ip = self.labels[opcode[1]] - 1
        elif op == 'JNZ':
            if self.stack.pop() != 0: self.ip = self.labels[opcode[1]] - 1

        # --- TKINTER BASE ---
        elif op == 'TK_ROOT':
            if tk is None: raise AscensionException("Tkinter missing")
            title = self.stack.pop()
            if not self.tk_root:
                self.tk_root = tk.Tk(); self.tk_root.title(str(title))
                self.tk_ref_counter += 1; self.tk_refs[self.tk_ref_counter] = self.tk_root
                self.stack.append(self.tk_ref_counter)
            else: self.stack.append(1)

        elif op == 'TK_WIDGET':
            config = self.stack.pop(); w_type = self.stack.pop(); parent_id = self.stack.pop()
            if not isinstance(config, dict): config = {}
            clean_conf = {k:v for k,v in config.items() if k!='__type__'}
            if 'command' in clean_conf: del clean_conf['command']
            if parent_id in self.tk_refs:
                try:
                    cls = getattr(tk, str(w_type))
                    w = cls(self.tk_refs[parent_id], **clean_conf)
                    self.tk_ref_counter += 1; self.tk_refs[self.tk_ref_counter] = w
                    self.stack.append(self.tk_ref_counter)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_PACK':
            config = self.stack.pop(); wid = self.stack.pop()
            clean_conf = {k:v for k,v in config.items() if k!='__type__'} if isinstance(config, dict) else {}
            if wid in self.tk_refs: self.tk_refs[wid].pack(**clean_conf); self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_GRID':
            config = self.stack.pop(); wid = self.stack.pop()
            clean_conf = {k:v for k,v in config.items() if k!='__type__'} if isinstance(config, dict) else {}
            if wid in self.tk_refs: self.tk_refs[wid].grid(**clean_conf); self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_CONFIG':
            config = self.stack.pop(); wid = self.stack.pop()
            clean_conf = {k:v for k,v in config.items() if k!='__type__'} if isinstance(config, dict) else {}
            if wid in self.tk_refs: self.tk_refs[wid].config(**clean_conf); self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_GET':
            wid = self.stack.pop()
            if wid in self.tk_refs:
                try: self.stack.append(self.tk_refs[wid].get())
                except: self.stack.append("")
            else: self.stack.append("")

        elif op == 'TK_MSGBOX':
            msg = self.stack.pop(); title = self.stack.pop()
            if tk: messagebox.showinfo(str(title), str(msg)); self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_MAINLOOP':
            if self.tk_root:
                try: self.tk_root.mainloop(); self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        # --- TKINTER EXTENDED (v11.2) ---
        elif op == 'TK_COMMAND':
            func_name = str(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                callback = self._make_tk_callback(func_name)
                self.tk_refs[wid].config(command=callback)
                self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_BIND':
            func_name = str(self.stack.pop())
            event = str(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                callback = self._make_tk_event_callback(func_name)
                self.tk_refs[wid].bind(event, callback)
                self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_AFTER':
            func_name = str(self.stack.pop())
            ms = int(self.stack.pop())
            if self.tk_root:
                callback = self._make_tk_callback(func_name)
                after_id = self.tk_root.after(ms, callback)
                self.tk_after_counter += 1
                self.tk_after_ids[self.tk_after_counter] = after_id
                self.stack.append(self.tk_after_counter)
            else: self.stack.append(0)

        elif op == 'TK_AFTER_CANCEL':
            aid = int(self.stack.pop())
            if aid in self.tk_after_ids and self.tk_root:
                self.tk_root.after_cancel(self.tk_after_ids[aid])
                del self.tk_after_ids[aid]
                self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_UPDATE':
            if self.tk_root:
                self.tk_root.update()
                self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_DESTROY':
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try:
                    self.tk_refs[wid].destroy()
                    del self.tk_refs[wid]
                    self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_SET':
            value = str(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                w = self.tk_refs[wid]
                try:
                    if isinstance(w, tk.Entry):
                        w.delete(0, tk.END); w.insert(0, value)
                    elif isinstance(w, tk.Text):
                        w.delete('1.0', tk.END); w.insert('1.0', value)
                    self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_CLEAR':
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                w = self.tk_refs[wid]
                try:
                    if isinstance(w, tk.Entry): w.delete(0, tk.END)
                    elif isinstance(w, tk.Text): w.delete('1.0', tk.END)
                    elif isinstance(w, tk.Listbox): w.delete(0, tk.END)
                    self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_FOCUS':
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                self.tk_refs[wid].focus_set()
                self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_GEOMETRY':
            geom = str(self.stack.pop())
            if self.tk_root:
                self.tk_root.geometry(geom); self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_TITLE':
            title = str(self.stack.pop())
            if self.tk_root:
                self.tk_root.title(title); self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_RESIZABLE':
            h = int(self.stack.pop()); w = int(self.stack.pop())
            if self.tk_root:
                self.tk_root.resizable(w, h); self.stack.append(1)
            else: self.stack.append(0)

        elif op == 'TK_TEXT_GET':
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.stack.append(self.tk_refs[wid].get('1.0', tk.END).rstrip('\n'))
                except: self.stack.append("")
            else: self.stack.append("")

        elif op == 'TK_TEXT_INSERT':
            text = str(self.stack.pop())
            pos = str(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.tk_refs[wid].insert(pos, text); self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_LISTBOX_ADD':
            item = str(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.tk_refs[wid].insert(tk.END, item); self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_LISTBOX_GET':
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try:
                    sel = self.tk_refs[wid].curselection()
                    self.stack.append(self.tk_refs[wid].get(sel[0]) if sel else "")
                except: self.stack.append("")
            else: self.stack.append("")

        elif op == 'TK_LISTBOX_INDEX':
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try:
                    sel = self.tk_refs[wid].curselection()
                    self.stack.append(sel[0] if sel else -1)
                except: self.stack.append(-1)
            else: self.stack.append(-1)

        elif op == 'TK_FILEDIALOG_OPEN':
            title = str(self.stack.pop())
            if filedialog:
                path = filedialog.askopenfilename(title=title)
                self.stack.append(path if path else "")
            else: self.stack.append("")

        elif op == 'TK_FILEDIALOG_SAVE':
            title = str(self.stack.pop())
            if filedialog:
                path = filedialog.asksaveasfilename(title=title)
                self.stack.append(path if path else "")
            else: self.stack.append("")

        elif op == 'TK_ASKSTRING':
            prompt = str(self.stack.pop())
            title = str(self.stack.pop())
            if simpledialog:
                result = simpledialog.askstring(title, prompt)
                self.stack.append(result if result else "")
            else: self.stack.append("")

        elif op == 'TK_ASKYESNO':
            msg = str(self.stack.pop())
            title = str(self.stack.pop())
            if messagebox:
                result = messagebox.askyesno(title, msg)
                self.stack.append(1 if result else 0)
            else: self.stack.append(0)

        # --- CANVAS (v11.2) ---
        elif op == 'TK_CANVAS_LINE':
            color = str(self.stack.pop())
            y2 = int(self.stack.pop()); x2 = int(self.stack.pop())
            y1 = int(self.stack.pop()); x1 = int(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.stack.append(self.tk_refs[wid].create_line(x1,y1,x2,y2,fill=color))
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_CANVAS_RECT':
            color = str(self.stack.pop())
            y2 = int(self.stack.pop()); x2 = int(self.stack.pop())
            y1 = int(self.stack.pop()); x1 = int(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.stack.append(self.tk_refs[wid].create_rectangle(x1,y1,x2,y2,fill=color))
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_CANVAS_OVAL':
            color = str(self.stack.pop())
            y2 = int(self.stack.pop()); x2 = int(self.stack.pop())
            y1 = int(self.stack.pop()); x1 = int(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.stack.append(self.tk_refs[wid].create_oval(x1,y1,x2,y2,fill=color))
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_CANVAS_TEXT':
            color = str(self.stack.pop())
            text = str(self.stack.pop())
            y = int(self.stack.pop()); x = int(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.stack.append(self.tk_refs[wid].create_text(x,y,text=text,fill=color))
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_CANVAS_CLEAR':
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.tk_refs[wid].delete("all"); self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_CANVAS_DELETE':
            item_id = int(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.tk_refs[wid].delete(item_id); self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        elif op == 'TK_CANVAS_MOVE':
            dy = int(self.stack.pop()); dx = int(self.stack.pop())
            item_id = int(self.stack.pop())
            wid = int(self.stack.pop())
            if wid in self.tk_refs:
                try: self.tk_refs[wid].move(item_id, dx, dy); self.stack.append(1)
                except: self.stack.append(0)
            else: self.stack.append(0)

        # ----- HTTP (NETWORKING) -----
        elif op == 'HTTP_GET':
            url = str(self.stack.pop())
            if requests:
                try:
                    r = requests.get(url, timeout=10)
                    self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': r.status_code, 'body': r.text})
                except Exception as e: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': str(e)})
            else: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': "No requests lib"})

        elif op == 'HTTP_POST':
            data = self.stack.pop(); url = str(self.stack.pop())
            payload = {k:v for k,v in data.items() if k!='__type__'} if isinstance(data, dict) else str(data)
            if requests:
                try:
                    r = requests.post(url, data=payload, timeout=10)
                    self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': r.status_code, 'body': r.text})
                except Exception as e: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': str(e)})
            else: self.stack.append({'__type__': 'HTTP_RESPONSE', 'status': 0, 'body': "No requests lib"})

        elif op == 'RESP_STATUS':
            r = self.stack.pop(); self.stack.append(r.get('status', 0) if isinstance(r, dict) else 0)
        elif op == 'RESP_BODY':
            r = self.stack.pop(); self.stack.append(r.get('body', "") if isinstance(r, dict) else "")

        # Default: opcode non gestito in _exec_opcode
        else:
            pass  # Alcuni opcode sono gestiti solo in run()


# ==========================================
#  COMPILER v11.2 (Extended Tkinter)
# ==========================================

# =============================================================================
#                              COMPILATORE
# =============================================================================

class AscensionCompiler:
    """
    Compilatore che trasforma codice sorgente Ascension in bytecode.

    Il compilatore:
    - Pulisce il sorgente (rimuove commenti, normalizza spazi)
    - Parsa le definizioni di struct e funzioni
    - Genera bytecode per ogni istruzione
    """
    def extract_balanced_arg(self, expr, func_name):
        prefix = func_name + '('
        if not expr.startswith(prefix): return None
        paren_depth = 0
        brace_depth = 0
        in_string = False
        start = len(prefix)
        for i, c in enumerate(expr[start:], start):
            if c == '"' and (i == 0 or expr[i-1] != '\\'):
                in_string = not in_string
            if not in_string:
                if c == '(': paren_depth += 1
                elif c == ')':
                    if paren_depth == 0 and brace_depth == 0:
                        if i == len(expr) - 1:
                            return expr[start:i]
                        else:
                            return None
                    paren_depth -= 1
                elif c == '{': brace_depth += 1
                elif c == '}': brace_depth -= 1
        return None

    def extract_braced_block(self, text, start_pos):
        """
        Estrae un blocco tra graffe bilanciate.
        Gestisce graffe annidate e stringhe.
        Ritorna (contenuto, posizione_dopo) o (None, -1).
        """
        if start_pos >= len(text) or text[start_pos] != '{': return None, -1
        depth = 0; in_string = False
        for i in range(start_pos, len(text)):
            c = text[i]
            if c == '"' and (i == 0 or text[i-1] != '\\'): in_string = not in_string
            if not in_string:
                if c == '{': depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0: return text[start_pos+1:i], i + 1
        return None, -1

    def __init__(self):
        self.ops = []
        self.structs = {}
        self.label_counter = 0
        self.in_function = False
        self.loop_stack = []
        self.base_dir = "."
        # NEW v12.4: Prototipi funzione (forward declarations)
        self.function_prototypes = {}  # nome -> lista parametri
        self.function_defined = set()  # funzioni con corpo definito
        self.builtin_keywords = [
            'if', 'while', 'for', 'print', 'switch', 'try', 'throw', 'return',
            'read', 'len', 'keys', 'to_int', 'to_float',
            # NEW: DNS
            'get_ip',
            # NEW v12.4: System commands
            'system', 'exec',
            # NEW v12.7: Math functions
            'random', 'sqrt', 'pow', 'exp', 'log', 'abs', 'floor', 'ceil',
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2',
            # File I/O
            'open', 'write', 'close', 'read_line', 'read_all',
            # Curses
            'curses_init', 'curses_end', 'curses_clear', 'curses_refresh',
            'curses_move', 'curses_write', 'curses_read_key',
            # HTTP
            'http_get', 'http_post', 'response_status', 'response_body',
            # Tkinter Keywords (v11.0)
            'tk_root', 'tk_widget', 'tk_pack', 'tk_grid', 'tk_config', 'tk_mainloop', 'tk_msgbox', 'tk_get',
            # Tkinter Extended (v11.2)
            'tk_command', 'tk_bind', 'tk_after', 'tk_after_cancel', 'tk_update', 'tk_destroy',
            'tk_set', 'tk_clear', 'tk_focus', 'tk_geometry', 'tk_title', 'tk_resizable',
            'tk_text_get', 'tk_text_insert', 'tk_listbox_add', 'tk_listbox_get', 'tk_listbox_index',
            'tk_filedialog_open', 'tk_filedialog_save', 'tk_askstring', 'tk_askyesno',
            'tk_canvas_line', 'tk_canvas_rect', 'tk_canvas_oval', 'tk_canvas_text',
            'tk_canvas_clear', 'tk_canvas_delete', 'tk_canvas_move',
            # Sockets Keywords (v11.0)
            'socket_open', 'socket_bind', 'socket_listen', 'socket_accept',
            'socket_connect', 'socket_send', 'socket_recv', 'socket_close'
        ]

    def get_label(self, s=""):
        """Genera una label unica per salti e loop."""
        self.label_counter += 1
        return f"L{self.label_counter}_{s}"

    def collect_prototypes(self, source):
        """
        Prima passata: raccoglie tutti i prototipi e definizioni di funzione.
        Supporta sia prototipi (func nome(args);) che definizioni complete.
        Gestisce anche file inclusi ricorsivamente.
        """
        cleaned = self.clean_source(source)
        statements = self.smart_split(cleaned)
        
        for line in statements:
            line = line.strip()
            if not line:
                continue
            
            # Gestisci include ricorsivamente
            if line.startswith('include '):
                m = re.search(r'include\s+"([^"]+)"', line)
                if m:
                    filepath = os.path.join(self.base_dir, m.group(1))
                    if os.path.exists(filepath):
                        with open(filepath, 'r') as f:
                            self.collect_prototypes(f.read())
                continue
            
            # Prototipo: func nome(args);  (senza corpo)
            proto_match = re.match(r'func\s+(\w+)\s*\((.*?)\)\s*;?\s*$', line)
            if proto_match and '{' not in line:
                func_name = proto_match.group(1)
                args_str = proto_match.group(2)
                args = [x.strip() for x in args_str.split(',') if x.strip()]
                if func_name not in self.function_prototypes:
                    self.function_prototypes[func_name] = args
                continue
            
            # Definizione completa: func nome(args) { ... }
            func_match = re.search(r'func\s+(\w+)\s*\((.*?)\)\s*\{', line)
            if func_match:
                func_name = func_match.group(1)
                args_str = func_match.group(2)
                args = [x.strip() for x in args_str.split(',') if x.strip()]
                
                # Verifica coerenza con prototipo esistente
                if func_name in self.function_prototypes and func_name not in self.function_defined:
                    proto_args = self.function_prototypes[func_name]
                    if len(proto_args) != len(args):
                        raise AscensionException(
                            f"Funzione '{func_name}': definizione ha {len(args)} argomenti, "
                            f"ma prototipo ne dichiara {len(proto_args)}", 
                            "PrototypeError"
                        )
                
                self.function_prototypes[func_name] = args
                self.function_defined.add(func_name)

    def clean_source(self, source):
        """
        Pulisce il codice sorgente.
        Rimuove commenti (// e /* */) e normalizza gli spazi.
        """
        # Logica avanzata v10.2 per pulizia commenti
        lines = source.split('\n'); cleaned = []; in_multiline_comment = False
        for line in lines:
            while '/*' in line or in_multiline_comment:
                if in_multiline_comment:
                    if '*/' in line: line = line[line.index('*/') + 2:]; in_multiline_comment = False
                    else: line = ''; break
                elif '/*' in line:
                    start = line.index('/*')
                    if '*/' in line[start:]:
                        end = line.index('*/', start) + 2; line = line[:start] + line[end:]
                    else: line = line[:start]; in_multiline_comment = True
            if not in_multiline_comment and '//' in line:
                split_index = -1; in_quote = False
                for i in range(len(line)):
                    c = line[i]
                    if c == '"' and (i == 0 or line[i-1] != '\\'): in_quote = not in_quote
                    if not in_quote and i + 1 < len(line) and c == '/' and line[i+1] == '/': split_index = i; break
                if split_index != -1: line = line[:split_index]
            line = line.strip()
            if line: cleaned.append(line)
        return " ".join(cleaned)

    def smart_split(self, source):
        statements = []; current = ""; brace = 0; paren = 0; quote = False; i = 0
        while i < len(source):
            char = source[i]
            if char == '"': quote = not quote
            if not quote:
                if char == '{': brace += 1
                elif char == '}':
                    brace -= 1; current += char
                    # Solo splitta se NON siamo dentro parentesi
                    if brace == 0 and paren == 0:
                        rest = source[i+1:].lstrip()
                        if rest and not rest.startswith('else') and not rest.startswith('catch'):
                            if current.strip(): statements.append(current.strip())
                            current = ""
                    i += 1; continue
                elif char == '(': paren += 1
                elif char == ')': paren -= 1
            if char == ';' and brace == 0 and paren == 0 and not quote:
                if current.strip(): statements.append(current.strip())
                current = ""
            else: current += char
            i += 1
        if current.strip(): statements.append(current.strip())
        return statements

    def split_args(self, args_str):
        args = []; current = ""; paren = 0; brace = 0; bracket = 0; quote = False
        for c in args_str:
            if c == '"': quote = not quote
            if not quote:
                if c == '(': paren += 1
                elif c == ')': paren -= 1
                elif c == '{': brace += 1
                elif c == '}': brace -= 1
                elif c == '[': bracket += 1
                elif c == ']': bracket -= 1
            if c == ',' and paren == 0 and brace == 0 and bracket == 0 and not quote:
                if current.strip(): args.append(current.strip())
                current = ""
            else: current += c
        if current.strip(): args.append(current.strip())
        return args

    def _split_dict_pairs(self, content):
        """Splitta il contenuto di un dict in coppie (key, value)"""
        pairs = []
        current = ""
        paren = 0; brace = 0; quote = False

        for c in content:
            if c == '"': quote = not quote
            if not quote:
                if c == '(': paren += 1
                elif c == ')': paren -= 1
                elif c == '{': brace += 1
                elif c == '}': brace -= 1
            if c == ',' and paren == 0 and brace == 0 and not quote:
                if current.strip():
                    pair = current.strip()
                    if ':' in pair:
                        # Trova il primo : fuori da stringhe
                        colon_idx = self._find_colon(pair)
                        if colon_idx > 0:
                            key = pair[:colon_idx].strip()
                            val = pair[colon_idx+1:].strip()
                            pairs.append((key, val))
                current = ""
            else:
                current += c

        # Ultimo elemento
        if current.strip():
            pair = current.strip()
            if ':' in pair:
                colon_idx = self._find_colon(pair)
                if colon_idx > 0:
                    key = pair[:colon_idx].strip()
                    val = pair[colon_idx+1:].strip()
                    pairs.append((key, val))

        return pairs

    def _find_colon(self, s):
        """Trova il primo : fuori da stringhe"""
        quote = False
        for i, c in enumerate(s):
            if c == '"': quote = not quote
            if c == ':' and not quote:
                return i
        return -1

    def parse_expression(self, expr):
        """
        Parsa un'espressione e genera bytecode.
        Gestisce operatori, chiamate, accessi a struct/array.
        """
        expr = expr.strip()
        if not expr: return
        # Controlla se è una stringa semplice (una sola stringa, non "a" + "b")
        if expr.startswith('"') and expr.endswith('"'):
            # Verifica che ci sia una sola stringa contando le virgolette non escaped
            quote_count = 0
            i = 0
            while i < len(expr):
                if expr[i] == '"' and (i == 0 or expr[i-1] != '\\'):
                    quote_count += 1
                i += 1
            # Se ci sono esattamente 2 virgolette, è una stringa semplice
            if quote_count == 2:
                self.ops.append(('PUSH', expr))
                return

        # --- NEW: DNS Binding (v11.1) ---
        arg = self.extract_balanced_arg(expr, 'get_ip');
        if arg: self.parse_expression(arg); self.ops.append(('GET_IP', None)); return

        # --- TKINTER BINDINGS (v11.0) ---
        arg = self.extract_balanced_arg(expr, 'tk_root');
        if arg is not None: self.parse_expression(arg); self.ops.append(('TK_ROOT', None)); return

        if re.match(r'^tk_mainloop\s*\(\s*\)$', expr): self.ops.append(('TK_MAINLOOP', None)); return

        arg_str = self.extract_balanced_arg(expr, 'tk_widget');
        if arg_str is not None:
            args = self.split_args(arg_str)
            if len(args) == 3:
                self.parse_expression(args[0]); self.parse_expression(args[1]); self.parse_expression(args[2])
                self.ops.append(('TK_WIDGET', None)); return

        arg_str = self.extract_balanced_arg(expr, 'tk_pack');
        if arg_str is not None:
            args = self.split_args(arg_str)
            if len(args) == 2:
                self.parse_expression(args[0]); self.parse_expression(args[1])
                self.ops.append(('TK_PACK', None)); return

        arg_str = self.extract_balanced_arg(expr, 'tk_grid');
        if arg_str is not None:
            args = self.split_args(arg_str)
            if len(args) == 2:
                self.parse_expression(args[0]); self.parse_expression(args[1])
                self.ops.append(('TK_GRID', None)); return

        arg_str = self.extract_balanced_arg(expr, 'tk_config');
        if arg_str is not None:
            args = self.split_args(arg_str)
            if len(args) == 2:
                self.parse_expression(args[0]); self.parse_expression(args[1])
                self.ops.append(('TK_CONFIG', None)); return

        arg_str = self.extract_balanced_arg(expr, 'tk_msgbox');
        if arg_str is not None:
            args = self.split_args(arg_str)
            if len(args) == 2:
                self.parse_expression(args[0]); self.parse_expression(args[1])
                self.ops.append(('TK_MSGBOX', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_get');
        if arg is not None: self.parse_expression(arg); self.ops.append(('TK_GET', None)); return

        # --- TKINTER EXTENDED BINDINGS (v11.2) ---
        arg = self.extract_balanced_arg(expr, 'tk_command');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_COMMAND', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_bind');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.parse_expression(a[2]); self.ops.append(('TK_BIND', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_after');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_AFTER', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_after_cancel');
        if arg: self.parse_expression(arg); self.ops.append(('TK_AFTER_CANCEL', None)); return

        if re.match(r'^tk_update\s*\(\s*\)$', expr): self.ops.append(('TK_UPDATE', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_destroy');
        if arg: self.parse_expression(arg); self.ops.append(('TK_DESTROY', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_set');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_SET', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_clear');
        if arg: self.parse_expression(arg); self.ops.append(('TK_CLEAR', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_focus');
        if arg: self.parse_expression(arg); self.ops.append(('TK_FOCUS', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_geometry');
        if arg: self.parse_expression(arg); self.ops.append(('TK_GEOMETRY', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_title');
        if arg: self.parse_expression(arg); self.ops.append(('TK_TITLE', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_resizable');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_RESIZABLE', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_text_get');
        if arg: self.parse_expression(arg); self.ops.append(('TK_TEXT_GET', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_text_insert');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.parse_expression(a[2]); self.ops.append(('TK_TEXT_INSERT', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_listbox_add');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_LISTBOX_ADD', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_listbox_get');
        if arg: self.parse_expression(arg); self.ops.append(('TK_LISTBOX_GET', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_listbox_index');
        if arg: self.parse_expression(arg); self.ops.append(('TK_LISTBOX_INDEX', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_filedialog_open');
        if arg: self.parse_expression(arg); self.ops.append(('TK_FILEDIALOG_OPEN', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_filedialog_save');
        if arg: self.parse_expression(arg); self.ops.append(('TK_FILEDIALOG_SAVE', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_askstring');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_ASKSTRING', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_askyesno');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_ASKYESNO', None)); return

        # Canvas
        arg = self.extract_balanced_arg(expr, 'tk_canvas_line');
        if arg: a=self.split_args(arg); [self.parse_expression(x) for x in a]; self.ops.append(('TK_CANVAS_LINE', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_canvas_rect');
        if arg: a=self.split_args(arg); [self.parse_expression(x) for x in a]; self.ops.append(('TK_CANVAS_RECT', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_canvas_oval');
        if arg: a=self.split_args(arg); [self.parse_expression(x) for x in a]; self.ops.append(('TK_CANVAS_OVAL', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_canvas_text');
        if arg: a=self.split_args(arg); [self.parse_expression(x) for x in a]; self.ops.append(('TK_CANVAS_TEXT', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_canvas_clear');
        if arg: self.parse_expression(arg); self.ops.append(('TK_CANVAS_CLEAR', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_canvas_delete');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('TK_CANVAS_DELETE', None)); return

        arg = self.extract_balanced_arg(expr, 'tk_canvas_move');
        if arg: a=self.split_args(arg); [self.parse_expression(x) for x in a]; self.ops.append(('TK_CANVAS_MOVE', None)); return

        # --- SOCKETS BINDINGS (v11.0) ---
        arg = self.extract_balanced_arg(expr, 'socket_open');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('SOCKET_OPEN', None)); return

        arg = self.extract_balanced_arg(expr, 'socket_bind');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.parse_expression(a[2]); self.ops.append(('SOCKET_BIND', None)); return

        arg = self.extract_balanced_arg(expr, 'socket_listen');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('SOCKET_LISTEN', None)); return

        arg = self.extract_balanced_arg(expr, 'socket_accept');
        if arg: self.parse_expression(arg); self.ops.append(('SOCKET_ACCEPT', None)); return

        arg = self.extract_balanced_arg(expr, 'socket_connect');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.parse_expression(a[2]); self.ops.append(('SOCKET_CONNECT', None)); return

        arg = self.extract_balanced_arg(expr, 'socket_send');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('SOCKET_SEND', None)); return

        arg = self.extract_balanced_arg(expr, 'socket_recv');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('SOCKET_RECV', None)); return

        arg = self.extract_balanced_arg(expr, 'socket_close');
        if arg: self.parse_expression(arg); self.ops.append(('SOCKET_CLOSE', None)); return


        # --- BUILT-IN STANDARD (v10.2) ---
        if re.match(r'^read\s*\(\s*\)$', expr): self.ops.append(('READ', None)); return
        arg = self.extract_balanced_arg(expr, 'len');
        if arg: self.parse_expression(arg); self.ops.append(('LEN', None)); return
        arg = self.extract_balanced_arg(expr, 'keys');
        if arg: self.parse_expression(arg); self.ops.append(('KEYS', None)); return
        arg = self.extract_balanced_arg(expr, 'to_int');
        if arg: self.parse_expression(arg); self.ops.append(('TO_INT', None)); return
        arg = self.extract_balanced_arg(expr, 'to_float');
        if arg: self.parse_expression(arg); self.ops.append(('TO_FLOAT', None)); return

        # --- SUBSTR (v12.5) ---
        arg = self.extract_balanced_arg(expr, 'substr');
        if arg:
            a = self.split_args(arg)
            self.parse_expression(a[0])  # string
            self.parse_expression(a[1])  # start
            self.parse_expression(a[2])  # length
            self.ops.append(('SUBSTR', None))
            return

        # --- CHR (v12.5) ---
        arg = self.extract_balanced_arg(expr, 'chr');
        if arg:
            self.parse_expression(arg)  # code
            self.ops.append(('CHR', None))
            return

        # --- MATRIX BUILT-IN (v12.3) ---
        # matrix(rows, cols, init_value) - crea matrice inizializzata
        arg = self.extract_balanced_arg(expr, 'matrix');
        if arg:
            a = self.split_args(arg)
            if len(a) >= 2:
                self.parse_expression(a[0])  # rows
                self.parse_expression(a[1])  # cols
                if len(a) >= 3:
                    self.parse_expression(a[2])  # init value
                else:
                    self.ops.append(('PUSH', 0))  # default init = 0
                self.ops.append(('CREATE_MATRIX', None))
                return
        
        # rows(matrix) - ritorna numero righe
        arg = self.extract_balanced_arg(expr, 'rows');
        if arg: self.parse_expression(arg); self.ops.append(('MATRIX_ROWS', None)); return
        
        # cols(matrix) - ritorna numero colonne
        arg = self.extract_balanced_arg(expr, 'cols');
        if arg: self.parse_expression(arg); self.ops.append(('MATRIX_COLS', None)); return
        
        # dim(array) - ritorna dimensionalità (1 o 2)
        arg = self.extract_balanced_arg(expr, 'dim');
        if arg: self.parse_expression(arg); self.ops.append(('MATRIX_DIM', None)); return

        # --- MATH FUNCTIONS (v12.7) ---
        # random() - float tra 0.0 e 1.0
        # random(max) - int tra 0 e max-1
        # random(min, max) - int tra min e max-1
        if re.match(r'^random\s*\(\s*\)$', expr):
            self.ops.append(('RANDOM', None)); return
        arg = self.extract_balanced_arg(expr, 'random');
        if arg:
            a = self.split_args(arg)
            if len(a) == 1:
                self.parse_expression(a[0])
                self.ops.append(('RANDOM_MAX', None))
            elif len(a) == 2:
                self.parse_expression(a[0])
                self.parse_expression(a[1])
                self.ops.append(('RANDOM_RANGE', None))
            return
        
        # sqrt(x) - radice quadrata
        arg = self.extract_balanced_arg(expr, 'sqrt');
        if arg: self.parse_expression(arg); self.ops.append(('SQRT', None)); return
        
        # pow(base, exp) - potenza
        arg = self.extract_balanced_arg(expr, 'pow');
        if arg:
            a = self.split_args(arg)
            self.parse_expression(a[0])
            self.parse_expression(a[1])
            self.ops.append(('POW', None))
            return
        
        # exp(x) - e^x
        arg = self.extract_balanced_arg(expr, 'exp');
        if arg: self.parse_expression(arg); self.ops.append(('EXP', None)); return
        
        # log(x) - logaritmo naturale
        arg = self.extract_balanced_arg(expr, 'log');
        if arg: self.parse_expression(arg); self.ops.append(('LOG', None)); return
        
        # abs(x) - valore assoluto
        arg = self.extract_balanced_arg(expr, 'abs');
        if arg: self.parse_expression(arg); self.ops.append(('ABS', None)); return
        
        # floor(x) - arrotonda per difetto
        arg = self.extract_balanced_arg(expr, 'floor');
        if arg: self.parse_expression(arg); self.ops.append(('FLOOR', None)); return
        
        # ceil(x) - arrotonda per eccesso
        arg = self.extract_balanced_arg(expr, 'ceil');
        if arg: self.parse_expression(arg); self.ops.append(('CEIL', None)); return
        
        # sin(x), cos(x), tan(x) - trigonometriche
        arg = self.extract_balanced_arg(expr, 'sin');
        if arg: self.parse_expression(arg); self.ops.append(('SIN', None)); return
        arg = self.extract_balanced_arg(expr, 'cos');
        if arg: self.parse_expression(arg); self.ops.append(('COS', None)); return
        arg = self.extract_balanced_arg(expr, 'tan');
        if arg: self.parse_expression(arg); self.ops.append(('TAN', None)); return
        
        # asin(x), acos(x), atan(x) - trigonometriche inverse
        arg = self.extract_balanced_arg(expr, 'asin');
        if arg: self.parse_expression(arg); self.ops.append(('ASIN', None)); return
        arg = self.extract_balanced_arg(expr, 'acos');
        if arg: self.parse_expression(arg); self.ops.append(('ACOS', None)); return
        arg = self.extract_balanced_arg(expr, 'atan');
        if arg: self.parse_expression(arg); self.ops.append(('ATAN', None)); return
        
        # atan2(y, x) - arcotangente a due argomenti
        arg = self.extract_balanced_arg(expr, 'atan2');
        if arg:
            a = self.split_args(arg)
            self.parse_expression(a[0])
            self.parse_expression(a[1])
            self.ops.append(('ATAN2', None))
            return
        
        # PI e E come costanti
        if expr == 'PI': self.ops.append(('PUSH', math.pi)); return
        if expr == 'E': self.ops.append(('PUSH', math.e)); return

        # --- SYSTEM COMMANDS (v12.4) ---
        arg = self.extract_balanced_arg(expr, 'system');
        if arg: self.parse_expression(arg); self.ops.append(('SYSTEM', None)); return
        arg = self.extract_balanced_arg(expr, 'exec');
        if arg: self.parse_expression(arg); self.ops.append(('EXEC', None)); return

        # --- FILE I/O ---
        arg = self.extract_balanced_arg(expr, 'open');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('FILE_OPEN', None)); return
        arg = self.extract_balanced_arg(expr, 'write');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('FILE_WRITE', None)); return
        arg = self.extract_balanced_arg(expr, 'read_line');
        if arg: self.parse_expression(arg); self.ops.append(('FILE_READLINE', None)); return
        arg = self.extract_balanced_arg(expr, 'read_all');
        if arg: self.parse_expression(arg); self.ops.append(('FILE_READALL', None)); return
        arg = self.extract_balanced_arg(expr, 'close');
        if arg: self.parse_expression(arg); self.ops.append(('FILE_CLOSE', None)); return

        # --- CURSES ---
        if re.match(r'^curses_init\(\)$', expr): self.ops.append(('CURSES_INIT', None)); return
        if re.match(r'^curses_end\(\)$', expr): self.ops.append(('CURSES_END', None)); return
        if re.match(r'^curses_clear\(\)$', expr): self.ops.append(('CURSES_CLEAR', None)); return
        if re.match(r'^curses_refresh\(\)$', expr): self.ops.append(('CURSES_REFRESH', None)); return
        arg = self.extract_balanced_arg(expr, 'curses_move');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('CURSES_MOVE', None)); return
        arg = self.extract_balanced_arg(expr, 'curses_write');
        if arg: self.parse_expression(arg); self.ops.append(('CURSES_WRITE', None)); return
        if re.match(r'^curses_read_key\(\)$', expr): self.ops.append(('CURSES_READ_KEY', None)); return

        # --- NETWORKING (HTTP) ---
        arg = self.extract_balanced_arg(expr, 'http_get');
        if arg: self.parse_expression(arg); self.ops.append(('HTTP_GET', None)); return
        arg = self.extract_balanced_arg(expr, 'http_post');
        if arg: a=self.split_args(arg); self.parse_expression(a[0]); self.parse_expression(a[1]); self.ops.append(('HTTP_POST', None)); return
        arg = self.extract_balanced_arg(expr, 'response_status');
        if arg: self.parse_expression(arg); self.ops.append(('RESP_STATUS', None)); return
        arg = self.extract_balanced_arg(expr, 'response_body');
        if arg: self.parse_expression(arg); self.ops.append(('RESP_BODY', None)); return

        if expr.startswith('new '): self.ops.append(('NEW_STRUCT', expr.split()[1].split('(')[0])); return

        # --- LOGIC/MATH/PRECEDENCE (v10.2 Logic) ---
        # IMPORTANTE: Questo deve venire PRIMA del check delle chiamate a funzione
        # per gestire correttamente espressioni come: func(a) + func(b)
        if ' && ' in expr: p=expr.split(' && ', 1); self.parse_expression(p[0]); self.parse_expression(p[1]); self.ops.append(('AND', None)); return
        if ' || ' in expr: p=expr.split(' || ', 1); self.parse_expression(p[0]); self.parse_expression(p[1]); self.ops.append(('OR', None)); return
        if expr.startswith('!') and not expr.startswith('!='): self.parse_expression(expr[1:]); self.ops.append(('NOT', None)); return

        op_precedence = [('==','EQ'),('!=','NEQ'),('>=','GTE'),('<=','LTE'),('>','GT'),('<','LT'),('+', 'ADD'),('-','SUB'),('*','MUL'),('/','DIV'),('%','MOD')]
        paren_depth = 0; bracket_depth = 0
        for op_str, op_name in op_precedence:

            paren_depth = 0; bracket_depth = 0; in_string = False; i = len(expr) - 1
            while i >= 0:
                c = expr[i]
                if c == '"' and (i==0 or expr[i-1]!='\\'): in_string = not in_string
                if not in_string:
                    if c == ')': paren_depth += 1
                    elif c == '(': paren_depth -= 1
                    elif c == ']': bracket_depth += 1
                    elif c == '[': bracket_depth -= 1
                    if paren_depth == 0 and bracket_depth == 0 and i >= len(op_str) - 1:
                        if expr[i-len(op_str)+1:i+1] == op_str:
                            if op_str in ['>','<'] and i+1<len(expr) and expr[i+1]=='=': i-=1; continue
                            if op_str == '-' and i==0: i-=1; continue
                            left = expr[:i-len(op_str)+1].strip(); right = expr[i+1:].strip()
                            if left and right: self.parse_expression(left); self.parse_expression(right); self.ops.append((op_name, None)); return
                i -= 1

        # --- FUNCTION CALL ---
        # Ora viene DOPO il check degli operatori binari
        func_match = re.match(r'^([a-zA-Z_]\w*)\s*\((.*)\)$', expr)
        if func_match:
            func_name = func_match.group(1)
            if func_name not in self.builtin_keywords:
                args = self.split_args(func_match.group(2))
                for arg in args: self.parse_expression(arg)
                self.ops.append(('CALL', func_name))
                return

        if expr.startswith('(') and expr.endswith(')'):
            d=0; b=True
            for i,c in enumerate(expr):
                if c=='(': d+=1
                elif c==')': d-=1
                if d==0 and i<len(expr)-1: b=False; break
            if b: self.parse_expression(expr[1:-1]); return

        # --- VARS / LITERALS / IDX ---
        # NULL, true, false come valori nativi (v12.4)
        if expr == 'NULL': self.ops.append(('PUSH_NULL', None)); return
        if expr == 'true': self.ops.append(('PUSH', 1)); return
        if expr == 'false': self.ops.append(('PUSH', 0)); return
        
        if expr.startswith('"'): self.ops.append(('PUSH', expr))
        elif expr == '{}': self.ops.append(('PUSH_DICT', None))
        # Dict con contenuto: {"key": value, ...}
        elif expr.startswith('{') and expr.endswith('}'):
            self.ops.append(('PUSH_DICT', None))
            content = expr[1:-1].strip()
            if content:
                # Parse key:value pairs
                pairs = self._split_dict_pairs(content)
                for key, val in pairs:
                    # Push value
                    self.parse_expression(val)
                    # Push key (rimuovi quotes se presenti)
                    clean_key = key.strip()
                    if clean_key.startswith('"') and clean_key.endswith('"'):
                        clean_key = clean_key[1:-1]
                    self.ops.append(('PUSH', f'"{clean_key}"'))
                    # Set attribute
                    self.ops.append(('DICT_SET', None))
        elif expr.replace('.','',1).lstrip('-').isdigit(): self.ops.append(('PUSH', expr))
        elif '[' in expr:
            bracket_start = expr.index('[')
            arr_name = expr[:bracket_start]
            
            # Trova la fine della prima parentesi quadra
            depth = 0; bracket_end = -1
            for i in range(bracket_start, len(expr)):
                if expr[i] == '[': depth += 1
                elif expr[i] == ']':
                    depth -= 1
                    if depth == 0: bracket_end = i; break
            
            idx_content = expr[bracket_start+1:bracket_end]
            rem = expr[bracket_end+1:]
            
            # Check per sintassi comma: arr[i,j]
            if ',' in idx_content and not idx_content.startswith('"'):
                # Sintassi arr[row, col]
                parts = idx_content.split(',', 1)
                row_idx = parts[0].strip()
                col_idx = parts[1].strip()
                # Push row index
                if row_idx.lstrip('-').isdigit():
                    self.ops.append(('PUSH', int(row_idx)))
                else:
                    self.parse_expression(row_idx)
                # Push col index
                if col_idx.lstrip('-').isdigit():
                    self.ops.append(('PUSH', int(col_idx)))
                else:
                    self.parse_expression(col_idx)
                self.ops.append(('LOAD_IDX_2D', arr_name))
            # Check per sintassi C-style: arr[i][j]
            elif rem.startswith('['):
                # Trova la fine della seconda parentesi quadra
                depth2 = 0; bracket_end2 = -1
                for i in range(len(rem)):
                    if rem[i] == '[': depth2 += 1
                    elif rem[i] == ']':
                        depth2 -= 1
                        if depth2 == 0: bracket_end2 = i; break
                
                col_idx = rem[1:bracket_end2]
                # Push row index (primo indice)
                if idx_content.lstrip('-').isdigit():
                    self.ops.append(('PUSH', int(idx_content)))
                else:
                    self.parse_expression(idx_content)
                # Push col index (secondo indice)
                if col_idx.lstrip('-').isdigit():
                    self.ops.append(('PUSH', int(col_idx)))
                else:
                    self.parse_expression(col_idx)
                self.ops.append(('LOAD_IDX_2D', arr_name))
                rem = rem[bracket_end2+1:]  # Aggiorna remainder
            else:
                # Array 1D normale
                if idx_content.lstrip('-').isdigit():
                    self.ops.append(('PUSH', int(idx_content)))
                else:
                    self.parse_expression(idx_content)
                self.ops.append(('LOAD_IDX', arr_name))
            
            # Gestisci accesso a campo dopo array (es: arr[i].campo)
            if rem.startswith('.'):
                field = rem[1:].split('[')[0].split('.')[0]  # Prendi solo il nome del campo
                self.ops.append(('GET_ATTR', field))
        elif '.' in expr and not expr.replace('.','',1).isdigit():
            p = expr.split('.'); self.ops.append(('LOAD', p[0])); self.ops.append(('GET_ATTR', p[1]))
        else: self.ops.append(('LOAD', expr))


    def load_and_compile_file(self, filename):
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath): raise FileNotFoundError(f"Errore include: '{filepath}'")
        with open(filepath, 'r') as f: source = f.read()
        self._compile_internal(source)

    def _compile_internal(self, source):
        """
        Compila il codice sorgente in bytecode.
        Metodo principale di compilazione ricorsivo.
        """
        statements = self.smart_split(self.clean_source(source))
        for line in statements:
            line = line.strip()
            if not line: continue

            if line.startswith('include '):
                m = re.search(r'include\s+"([^"]+)"', line)
                if m: self.load_and_compile_file(m.group(1)); continue
            if line == 'break': self.ops.append(('JMP', self.loop_stack[-1][1])); continue
            if line == 'continue': self.ops.append(('JMP', self.loop_stack[-1][0])); continue
            if line.startswith('struct '):
                m = re.search(r'struct\s+(\w+)\s*\{(.*?)\}', line)
                if m: self.structs[m.group(1)] = [x.strip() for x in m.group(2).split(',') if x.strip()]; continue
            if line.startswith('func '):
                # Prototipo senza corpo: func nome(args); - già raccolto, skip
                proto_match = re.match(r'func\s+(\w+)\s*\((.*?)\)\s*;?\s*$', line)
                if proto_match and '{' not in line:
                    continue  # Prototipo puro, già registrato in collect_prototypes
                
                # Definizione completa: func nome(args) { ... }
                m = re.search(r'func\s+(\w+)\s*\((.*?)\)\s*\{(.*)\}', line)
                if m:
                    func_name = m.group(1)
                    # Verifica coerenza con prototipo se esiste
                    if func_name in self.function_prototypes:
                        proto_args = self.function_prototypes[func_name]
                        def_args = [x.strip() for x in m.group(2).split(',') if x.strip()]
                        if len(proto_args) != len(def_args):
                            raise AscensionException(
                                f"Funzione '{func_name}': numero argomenti ({len(def_args)}) "
                                f"non corrisponde al prototipo ({len(proto_args)})", 
                                "PrototypeError"
                            )
                    
                    lbl_skip = self.get_label("skip"); self.ops.append(('JMP', lbl_skip)); self.ops.append(('LABEL', func_name))
                    old_in = self.in_function; self.in_function = True
                    args = [x.strip() for x in m.group(2).split(',') if x.strip()]
                    for a in reversed(args): self.ops.append(('STORE', a))
                    self._compile_internal(m.group(3)); self.ops.append(('RET', None)); self.ops.append(('LABEL', lbl_skip))
                    self.in_function = old_in; continue
            if line.startswith('return'):
                e = line[6:].strip(); self.parse_expression(e) if e else None; self.ops.append(('RET_VAL' if e else 'RET', None)); continue
            if line.startswith('throw '): self.parse_expression(line[6:].strip()); self.ops.append(('THROW', None)); continue

            # --- TRY / CATCH ---
            if line.startswith('try'):
                # Try con catch che ha parametro: catch (e) { }
                m = re.search(r'try\s*\{(.*?)\}\s*catch\s*\((\w+)\)\s*\{(.*?)\}', line)
                if m:
                    lc=self.get_label("c"); le=self.get_label("e"); tb=m.group(1); ev=m.group(2); cb=m.group(3)
                    self.ops.append(('TRY_START', lc)); self._compile_internal(tb); self.ops.append(('TRY_END', le))
                    self.ops.append(('LABEL', lc)); self.ops.append(('CATCH_START', None)); self.ops.append(('STORE', ev))
                    self._compile_internal(cb); self.ops.append(('CATCH_END', None)); self.ops.append(('LABEL', le)); continue
                # Try con catch senza parametro: catch { }
                m = re.search(r'try\s*\{(.*?)\}\s*catch\s*\{(.*?)\}', line)
                if m:
                    lc=self.get_label("c"); le=self.get_label("e"); tb=m.group(1); cb=m.group(2)
                    self.ops.append(('TRY_START', lc)); self._compile_internal(tb); self.ops.append(('TRY_END', le))
                    self.ops.append(('LABEL', lc)); self.ops.append(('CATCH_START', None)); self.ops.append(('POP', None))
                    self._compile_internal(cb); self.ops.append(('CATCH_END', None)); self.ops.append(('LABEL', le)); continue

            if line.startswith('global '):
                m = re.match(r'global\s+(\w+)\s*=\s*(.+)', line)
                if m: self.parse_expression(m.group(2)); self.ops.append(('STORE_GLOBAL', m.group(1))); continue

            if line.startswith('print('):
                arg_s = re.search(r'print\((.*)\)', line).group(1)
                args = self.split_args(arg_s)
                for a in args: self.parse_expression(a)
                self.ops.append(('PRINT', len(args))); continue

            # ----- COMPILAZIONE SWITCH -----
            if line.startswith('switch'):
                m = re.search(r'switch\s*\((.*?)\)\s*\{(.*)\}', line)
                if m:
                    sv=m.group(1); bd=m.group(2); les=self.get_label("es")
                    self.parse_expression(sv); cases=re.findall(r'case\s+(.*?):\s*\{(.*?)\};', bd); df=re.search(r'default:\s*\{(.*?)\};', bd)
                    self.loop_stack.append((None, les))
                    for cv, cb in cases:
                        lnc=self.get_label("nc"); self.ops.append(('DUP', None)); self.parse_expression(cv); self.ops.append(('EQ', None)); self.ops.append(('JZ', lnc))
                        self._compile_internal(cb); self.ops.append(('JMP', les)); self.ops.append(('LABEL', lnc))
                    if df: self._compile_internal(df.group(1))
                    self.ops.append(('LABEL', les)); self.ops.append(('POP', None)); self.loop_stack.pop(); continue

            # ----- COMPILAZIONE LOOP (FOR/WHILE) -----
            if line.startswith('for'):
                # Usa extract_braced_block per gestire loop annidati correttamente
                m_header = re.match(r'for\s*\((.*?)\)\s*\{', line)
                if m_header:
                    h = m_header.group(1)
                    brace_start = m_header.end() - 1
                    b, after_body = self.extract_braced_block(line, brace_start)
                    if b is not None:
                        p = h.split(';')
                        if len(p) == 3:
                            ls = self.get_label("fs"); le = self.get_label("fe")
                            self.loop_stack.append((ls, le))
                            self._compile_internal(p[0].strip() + ";")
                            self.ops.append(('LABEL', ls))
                            self.parse_expression(p[1].strip())
                            self.ops.append(('JZ', le))
                            self._compile_internal(b)
                            self._compile_internal(p[2].strip() + ";")
                            self.ops.append(('JMP', ls))
                            self.ops.append(('LABEL', le))
                            self.loop_stack.pop()
                            continue
            if line.startswith('while'):
                # Usa extract_braced_block per gestire loop annidati correttamente
                m_cond = re.match(r'while\s*\((.*?)\)\s*\{', line)
                if m_cond:
                    cond = m_cond.group(1)
                    brace_start = m_cond.end() - 1
                    b, after_body = self.extract_braced_block(line, brace_start)
                    if b is not None:
                        ls = self.get_label("ws"); le = self.get_label("we")
                        self.loop_stack.append((ls, le))
                        self.ops.append(('LABEL', ls))
                        self.parse_expression(cond)
                        self.ops.append(('JZ', le))
                        self._compile_internal(b)
                        self.ops.append(('JMP', ls))
                        self.ops.append(('LABEL', le))
                        self.loop_stack.pop()
                        continue

            # ----- COMPILAZIONE IF/ELSE IF/ELSE -----
            if line.startswith('if'):
                m_cond = re.match(r'if\s*\((.*?)\)\s*\{', line)
                if m_cond:
                    cond = m_cond.group(1)
                    brace_start = m_cond.end() - 1
                    body, after_body = self.extract_braced_block(line, brace_start)

                    if body is not None:
                        lbl_end_chain = self.get_label("if_end")
                        lbl_next_check = self.get_label("next_check")

                        # 1. Compile Main IF
                        self.parse_expression(cond)
                        self.ops.append(('JZ', lbl_next_check))
                        self._compile_internal(body)
                        self.ops.append(('JMP', lbl_end_chain))
                        self.ops.append(('LABEL', lbl_next_check))

                        # 2. Check Chain (else if / else)
                        rem = line[after_body:].strip()

                        while True:
                            # Handle "else if"
                            if rem.startswith('else if'):
                                m_elif = re.match(r'else\s+if\s*\((.*?)\)\s*\{', rem)
                                if m_elif:
                                    cond_elif = m_elif.group(1)
                                    bs_elif = m_elif.end() - 1
                                    body_elif, ab_elif = self.extract_braced_block(rem, bs_elif)

                                    lbl_next_elif = self.get_label("elif_next")

                                    self.parse_expression(cond_elif)
                                    self.ops.append(('JZ', lbl_next_elif))
                                    self._compile_internal(body_elif)
                                    self.ops.append(('JMP', lbl_end_chain))
                                    self.ops.append(('LABEL', lbl_next_elif))

                                    rem = rem[ab_elif:].strip()
                                    continue

                            # Handle "else"
                            elif rem.startswith('else'):
                                m_else = re.match(r'else\s*\{', rem)
                                if m_else:
                                    bs_else = m_else.end() - 1
                                    body_else, ab_else = self.extract_braced_block(rem, bs_else)
                                    self._compile_internal(body_else)
                                    # Else is terminal
                                break

                            # Nothing follows
                            break

                        self.ops.append(('LABEL', lbl_end_chain))
                        continue

            # ----- ASSEGNAZIONI SHORTHAND (+=, -= ecc.) -----
            shorthand_ops = {'+=': 'ADD', '-=': 'SUB', '*=': 'MUL', '/=': 'DIV', '%=': 'MOD'}; sm = False
            for op_str, op_code in shorthand_ops.items():
                if op_str in line and not any(line.startswith(x) for x in ['if','while','for','global','print']):
                    p = line.split(op_str, 1);
                    if len(p) == 2:
                        tgt = p[0].strip(); exp = p[1].strip()
                        if not tgt or '=' in tgt: continue
                        if '.' in tgt and '[' not in tgt:
                            o, f = tgt.split('.'); self.ops.append(('LOAD', o)); self.ops.append(('GET_ATTR', f));
                            self.parse_expression(exp); self.ops.append((op_code, None));
                            self.ops.append(('LOAD', o)); self.ops.append(('SET_ATTR', f));
                        elif '[' in tgt:
                            # Trova il nome dell'array e gli indici
                            bracket_start = tgt.index('[')
                            arr_name = tgt[:bracket_start]
                            depth = 0; bracket_end = -1
                            for i in range(bracket_start, len(tgt)):
                                if tgt[i] == '[': depth += 1
                                elif tgt[i] == ']':
                                    depth -= 1
                                    if depth == 0: bracket_end = i; break
                            idx_content = tgt[bracket_start+1:bracket_end]
                            rem = tgt[bracket_end+1:]
                            
                            # Check per sintassi 2D (comma o C-style)
                            if ',' in idx_content and not idx_content.startswith('"'):
                                # Sintassi arr[i,j] += val
                                parts = idx_content.split(',', 1)
                                row_idx = parts[0].strip()
                                col_idx = parts[1].strip()
                                # Load current value
                                if row_idx.lstrip('-').isdigit(): self.ops.append(('PUSH', int(row_idx)))
                                else: self.parse_expression(row_idx)
                                if col_idx.lstrip('-').isdigit(): self.ops.append(('PUSH', int(col_idx)))
                                else: self.parse_expression(col_idx)
                                self.ops.append(('LOAD_IDX_2D', arr_name))
                                # Apply operation
                                self.parse_expression(exp); self.ops.append((op_code, None))
                                # Store back
                                if row_idx.lstrip('-').isdigit(): self.ops.append(('PUSH', int(row_idx)))
                                else: self.parse_expression(row_idx)
                                if col_idx.lstrip('-').isdigit(): self.ops.append(('PUSH', int(col_idx)))
                                else: self.parse_expression(col_idx)
                                self.ops.append(('STORE_IDX_2D', arr_name))
                            elif rem.startswith('['):
                                # Sintassi arr[i][j] += val
                                depth2 = 0; bracket_end2 = -1
                                for i in range(len(rem)):
                                    if rem[i] == '[': depth2 += 1
                                    elif rem[i] == ']':
                                        depth2 -= 1
                                        if depth2 == 0: bracket_end2 = i; break
                                col_idx = rem[1:bracket_end2]
                                # Load current value
                                if idx_content.lstrip('-').isdigit(): self.ops.append(('PUSH', int(idx_content)))
                                else: self.parse_expression(idx_content)
                                if col_idx.lstrip('-').isdigit(): self.ops.append(('PUSH', int(col_idx)))
                                else: self.parse_expression(col_idx)
                                self.ops.append(('LOAD_IDX_2D', arr_name))
                                # Apply operation
                                self.parse_expression(exp); self.ops.append((op_code, None))
                                # Store back
                                if idx_content.lstrip('-').isdigit(): self.ops.append(('PUSH', int(idx_content)))
                                else: self.parse_expression(idx_content)
                                if col_idx.lstrip('-').isdigit(): self.ops.append(('PUSH', int(col_idx)))
                                else: self.parse_expression(col_idx)
                                self.ops.append(('STORE_IDX_2D', arr_name))
                            else:
                                # Array 1D normale
                                self.parse_expression(idx_content); self.ops.append(('LOAD_IDX', arr_name))
                                self.parse_expression(exp); self.ops.append((op_code, None))
                                self.parse_expression(idx_content) if not idx_content.lstrip('-').isdigit() else self.ops.append(('PUSH', int(idx_content)))
                                self.ops.append(('STORE_IDX', arr_name))
                        else:
                            self.ops.append(('LOAD', tgt)); self.parse_expression(exp);
                            self.ops.append((op_code, None)); self.ops.append(('STORE', tgt));
                        sm = True; break
            if sm: continue

            # ----- ASSEGNAZIONI E CHIAMATE -----
            if '=' in line and not any(line.startswith(x) for x in ['if','while','for','global','print']):
                p = line.split('=', 1); tgt=p[0].strip(); exp=p[1].strip()
                if '.' in tgt and '[' not in tgt:
                    o,f = tgt.split('.')
                    self.parse_expression(exp)  # Prima il valore sullo stack
                    self.ops.append(('LOAD', o))  # Poi l'oggetto
                    self.ops.append(('SET_ATTR', f))  # SET_ATTR: pop obj, pop val
                elif '[' in tgt:
                    # Trova il nome dell'array e gli indici
                    bracket_start = tgt.index('[')
                    arr_name = tgt[:bracket_start]
                    
                    # Trova la fine della prima parentesi
                    depth = 0; bracket_end = -1
                    for i in range(bracket_start, len(tgt)):
                        if tgt[i] == '[': depth += 1
                        elif tgt[i] == ']':
                            depth -= 1
                            if depth == 0: bracket_end = i; break
                    
                    idx_content = tgt[bracket_start+1:bracket_end]
                    rem = tgt[bracket_end+1:]
                    
                    # Check per sintassi comma: arr[i,j] = val
                    if ',' in idx_content and not idx_content.startswith('"'):
                        parts = idx_content.split(',', 1)
                        row_idx = parts[0].strip()
                        col_idx = parts[1].strip()
                        self.parse_expression(exp)  # valore
                        # Push row index
                        if row_idx.lstrip('-').isdigit():
                            self.ops.append(('PUSH', int(row_idx)))
                        else:
                            self.parse_expression(row_idx)
                        # Push col index
                        if col_idx.lstrip('-').isdigit():
                            self.ops.append(('PUSH', int(col_idx)))
                        else:
                            self.parse_expression(col_idx)
                        self.ops.append(('STORE_IDX_2D', arr_name))
                    # Check per sintassi C-style: arr[i][j] = val
                    elif rem.startswith('['):
                        # Trova la seconda parentesi
                        depth2 = 0; bracket_end2 = -1
                        for i in range(len(rem)):
                            if rem[i] == '[': depth2 += 1
                            elif rem[i] == ']':
                                depth2 -= 1
                                if depth2 == 0: bracket_end2 = i; break
                        col_idx = rem[1:bracket_end2]
                        self.parse_expression(exp)  # valore
                        # Push row index
                        if idx_content.lstrip('-').isdigit():
                            self.ops.append(('PUSH', int(idx_content)))
                        else:
                            self.parse_expression(idx_content)
                        # Push col index
                        if col_idx.lstrip('-').isdigit():
                            self.ops.append(('PUSH', int(col_idx)))
                        else:
                            self.parse_expression(col_idx)
                        self.ops.append(('STORE_IDX_2D', arr_name))
                    else:
                        # Array 1D normale
                        self.parse_expression(exp)
                        if idx_content.lstrip('-').isdigit():
                            self.ops.append(('PUSH', int(idx_content)))
                        else:
                            self.parse_expression(idx_content)
                        self.ops.append(('STORE_IDX', arr_name))
                else: self.parse_expression(exp); self.ops.append(('STORE', tgt))
                continue

            # Supporto per Tkinter/Socket commands usati come statement (es. tk_pack(...))
            if line.startswith('tk_') or line.startswith('socket_'):
                self.parse_expression(line)
                # Se è una funzione che ritorna ma usata come void, puliamo lo stack (opzionale ma pulito)
                if any(line.startswith(x) for x in ['tk_pack','tk_grid','tk_config','tk_msgbox', 'socket_bind', 'socket_listen', 'socket_connect', 'socket_send', 'socket_close', 'get_ip']):
                    self.ops.append(('POP', None))
                continue

            if re.match(r'^[a-zA-Z_]\w*\s*\(.*\)$', line):
                self.parse_expression(line); self.ops.append(('POP', None))

        return self.ops

    def compile(self, source, base_dir=None):
        if base_dir: self.base_dir = base_dir
        
        # PASS 1: Raccoglie tutti i prototipi e definizioni di funzione
        self.collect_prototypes(source)
        
        # PASS 2: Compilazione effettiva
        result = self._compile_internal(source)
        
        # PASS 3: Verifica che tutte le funzioni dichiarate siano definite
        undefined = set(self.function_prototypes.keys()) - self.function_defined
        if undefined:
            raise AscensionException(
                f"Funzioni dichiarate ma mai definite: {', '.join(sorted(undefined))}", 
                "LinkerError"
            )
        
        return result


# ==========================================
#  MAIN EXECUTION
# ==========================================

# =============================================================================
#                              ESECUZIONE PRINCIPALE
# =============================================================================

def print_bytecode(ops):
    """Stampa il bytecode in formato leggibile per debug."""
    print("\n--- BYTECODE ---")
    for i, op in enumerate(ops):
        print(f"{i:4}: {op}")
    print("----------------\n")


if __name__ == "__main__":
    # Punto di ingresso principale
    # Uso: python ascension.py script.asc [-debug]
    if len(sys.argv) < 2: print("Uso: python ascension.py script.asc [-debug]"); exit()
    debug = '-debug' in sys.argv
    input_file = sys.argv[1]
    base_dir = os.path.dirname(os.path.abspath(input_file)) or '.'

    v = None
    try:
        with open(input_file, 'r') as f: src = f.read()
        print(f"--- Ascension v12.7 (Math Edition): {input_file} ---")
        c = AscensionCompiler(); bc = c.compile(src, base_dir)
        if debug: print_bytecode(bc)
        v = AscensionVM(); v.load_program(bc, c.structs); v.run()
        print("\n--- Fine ---")
    except FileNotFoundError as e: print(f"Errore: File non trovato: {e}")
    except Exception as e:
        print(f"Errore: {e}")
        if debug: import traceback; traceback.print_exc()
    finally:
        if v and v.current_screen:
            try: curses.nocbreak(); curses.echo(); curses.endwin()
            except: pass
