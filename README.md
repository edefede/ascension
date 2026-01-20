# 🚀 Ascension

**A lightweight, interpreted programming language**  
C-like syntax • No explicit typing • Built-in GUI, Networking, Neural Networks

![Version](https://img.shields.io/badge/version-12.7-green?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--3.0-orange?style=flat-square)
![Python](https://img.shields.io/badge/python-3.x-blue?style=flat-square)
![C++](https://img.shields.io/badge/C%2B%2B-17-blue?style=flat-square)

> **"Ascension IS the syntax"** — The same language, multiple implementations.

Ascension is an educational programming language with C-like syntax and dynamic typing. Write once, run on **Python** (reference implementation) or **C++** (high-performance port).

## 🎯 Two Implementations, One Language

Ascension is **the syntax**. The implementation is just how you run it:

### 🐍 Python (Reference Implementation)
```bash
# Run a program
python3 ascension_12_7.py examples/hello.asc

# Interactive shell
python3 ascension_shell_12_7.py
```
Full-featured, batteries-included, perfect for rapid development.

### ⚡ C++ (High Performance)
```bash
# Compile
g++ -std=c++17 cpp/ascension.cpp -o ascension

# With optional features
g++ -std=c++17 -DHAS_CURSES -DHAS_NETWORK cpp/ascension.cpp -o ascension -lncurses

# Run
./ascension examples/hello.asc
```
Header-only modular design, 15% more compact, blazing fast.

**Compile Flags:**
- `-DHAS_CURSES` — Terminal UI support (requires ncurses)
- `-DHAS_NETWORK` — HTTP and socket networking

## ✨ Features

- **C-like Syntax** — Familiar and easy to learn
- **No Explicit Typing** — Variables are dynamically typed
- **Stack-based VM** — Compiled to bytecode, then executed
- **GUI Support** — Built-in Tkinter integration
- **Networking** — HTTP requests and TCP sockets
- **File I/O** — Read, write, and manage files
- **Terminal UI** — Curses support for console apps
- **Math Functions** — Trigonometry, random, exponentials (v12.7)
- **Neural Networks** — Built-in library for ML experiments (v12.7)

## 📝 Examples

### Variables and Output
```ascension
name = "Ascension";
version = 12.7;
print("Welcome to", name, "v" + version);
```

### Functions
```ascension
func factorial(n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

print("5! =", factorial(5));  // Output: 120
```

### Control Flow
```ascension
for (i = 0; i < 5; i += 1) {
    if (i % 2 == 0) {
        print(i, "is even");
    } else {
        print(i, "is odd");
    }
}
```

### Structs
```ascension
struct Person { name, age, city };

p = new Person;
p.name = "Alice";
p.age = 30;
p.city = "Rome";

print(p.name, "lives in", p.city);
```

### Arrays and Matrices
```ascension
// 1D Array
numbers = [10, 20, 30, 40, 50];
print("First:", numbers[0]);

// 2D Matrix
grid = matrix(3, 3, 0);
grid[1, 1] = 99;
print("Center:", grid[1, 1]);
```

### File I/O
```ascension
// Write to file
f = open("data.txt", "w");
write(f, "Hello, File!\n");
close(f);

// Read from file
f = open("data.txt", "r");
content = read_all(f);
print(content);
close(f);
```

### HTTP Requests
```ascension
response = http_get("https://api.github.com");
status = response_status(response);
body = response_body(response);
print("Status:", status);
```

### TCP Sockets
```ascension
sock = socket_open();
socket_connect(sock, "example.com", 80);
socket_send(sock, "GET / HTTP/1.0\r\n\r\n");
data = socket_recv(sock, 1024);
socket_close(sock);
print(data);
```

### GUI with Tkinter
```ascension
root = tk_root("My App", "400x300");
label = tk_widget(root, "label", "text=Hello GUI!");
tk_pack(label);
button = tk_widget(root, "button", "text=Click Me");
tk_pack(button);
tk_mainloop(root);
```

### Terminal UI with Curses
```ascension
scr = curses_init();
curses_print(scr, 0, 0, "Press any key...");
curses_refresh(scr);
key = curses_getkey(scr);
curses_end(scr);
print("You pressed:", key);
```

### Error Handling
```ascension
try {
    x = 10 / 0;
} catch {
    print("Caught an error!");
}
```

### System Commands
```ascension
result = exec("ls -la");
print(result);

system("echo 'Hello from shell!'");
```

### String Operations
```ascension
text = "Hello, World!";
print("Length:", len(text));
print("Substring:", substr(text, 0, 5));  // "Hello"
print("Char code:", ord("A"));             // 65
print("From code:", chr(65));              // "A"
```

## 🧮 Math Functions (v12.7)

```ascension
// Random numbers
r = random();           // Float 0.0 - 1.0
r = random(100);        // Int 0 - 99
r = random(10, 20);     // Int 10 - 19

// Basic math
print(sqrt(16));        // 4
print(pow(2, 10));      // 1024
print(abs(-42));        // 42
print(floor(3.7));      // 3
print(ceil(3.2));       // 4

// Exponential and logarithm
print(exp(1));          // 2.718... (e)
print(log(E));          // 1.0

// Trigonometry
print(sin(PI / 2));     // 1.0
print(cos(0));          // 1.0
print(tan(PI / 4));     // 1.0
print(atan2(1, 1));     // 0.785... (PI/4)

// Constants
print(PI);              // 3.14159...
print(E);               // 2.71828...
```

## 🧠 Neural Network Library (v12.7)

Ascension includes `neural_network.asc`, a library for building and training neural networks:

```ascension
include "lib/neural_network.asc";

// Sigmoid activation
print(sigmoid(0));      // 0.5
print(sigmoid(5));      // ~0.99

// Initialize MLP (2 inputs, 2 hidden, 1 output)
mlp_init();

// Train on XOR problem
// ... training loop ...

// Predict
result = mlp_predict(1, 0);  // ~0.99 (XOR: 1)
result = mlp_predict(1, 1);  // ~0.01 (XOR: 0)

// Save/Load weights
mlp_save_weights("xor_trained.weights");
mlp_load_weights("xor_trained.weights");
```

**Features:**
- Activation functions: sigmoid, relu, step, tanh
- Single neuron implementation
- Perceptron with training (AND/OR gates)
- Multi-Layer Perceptron (MLP) with backpropagation
- XOR problem solver (2-2-1 architecture)
- Weight persistence (save/load to file)

## 🔧 Built-in Functions

| Category | Functions |
|----------|-----------|
| **I/O** | `print`, `read` |
| **Math** | `sqrt`, `pow`, `exp`, `log`, `abs`, `floor`, `ceil`, `random` |
| **Trig** | `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2` |
| **String** | `len`, `substr`, `chr`, `ord`, `to_int`, `to_float` |
| **Array** | `matrix`, `rows`, `cols`, `dim`, `keys` |
| **File** | `open`, `close`, `read_line`, `read_all`, `write` |
| **Network** | `http_get`, `http_post`, `response_status`, `response_body` |
| **Socket** | `socket_open`, `socket_connect`, `socket_send`, `socket_recv`, `socket_close`, `socket_bind`, `socket_listen`, `socket_accept`, `get_ip` |
| **GUI** | `tk_root`, `tk_widget`, `tk_pack`, `tk_grid`, `tk_bind`, `tk_mainloop`, `tk_canvas_*`, `tk_dialog_*` |
| **TUI** | `curses_init`, `curses_end`, `curses_print`, `curses_refresh`, `curses_getkey`, `curses_clear` |
| **System** | `system`, `exec` |

## 🔑 Keywords

| Category | Keywords |
|----------|----------|
| **Control** | `if`, `else`, `for`, `while`, `switch`, `case`, `default`, `break`, `continue` |
| **Functions** | `func`, `return` |
| **Data** | `struct`, `new`, `null`, `true`, `false` |
| **Error** | `try`, `catch`, `throw` |
| **Module** | `include` |
| **Constants** | `PI`, `E` |

## 🏆 Stress Tests Passed

✅ **Sieve of Eratosthenes** — 1,000,000 numbers, found all 78,498 primes up to 999,983  
✅ **Neural Network XOR** — MLP 2-2-1 with backpropagation  
✅ **Recursive Fibonacci** — Deep recursion handling  
✅ **Nested loops** — Complex iteration patterns

## 🗂️ Project Structure

```
ascension/
├── ascension_12_7.py        # Main interpreter (v12.7 Math Edition)
├── ascension_shell_12_7.py  # Interactive REPL shell
├── cpp/                     # C++ implementation
│   ├── ascension.cpp        # Main C++ interpreter
│   ├── value.hpp            # Value types
│   ├── compiler.hpp         # Bytecode compiler
│   ├── vm.hpp               # Virtual machine
│   └── modules/             # Optional modules
│       ├── mod_fileio.hpp   # File I/O (always included)
│       ├── mod_curses.hpp   # Terminal UI (optional)
│       └── mod_network.hpp  # HTTP/Sockets (optional)
├── ascension_examples/      # Example programs
│   ├── hello.asc
│   ├── calculator.asc
│   ├── fibonacci.asc
│   ├── sieve.asc            # Sieve of Eratosthenes (tested on 1M numbers!)
│   └── ...
├── lib/                     # Libraries
│   ├── neural_network.asc   # Neural network library
│   └── nn_demo.asc          # Neural network demo
├── docs/                    # Documentation
│   └── ascension_manual.pdf
├── LICENSE                  # GPL v3
└── README.md
```

## 📚 Documentation

- **User Manual (PDF)** — Complete 21-chapter guide
- **Shell Guide** — Interactive REPL documentation
- **Examples** — Sample programs

## 📜 Version History

| Version | Name | Highlights |
|---------|------|------------|
| **12.7** | **Math Edition** | 17 math functions, neural network library, PI/E constants |
| 12.6 | Substr Edition | `substr()`, `chr()` string functions |
| 12.5 | String Edition | Enhanced string operations |
| 12.4 | System Edition | `system()`, `exec()` commands |
| 12.3 | Matrix Edition | 2D arrays, `matrix()` function |

## 👤 Author

**EdeFede** — [GitHub](https://github.com/edefede)

Created through "vibe coding" with LLMs, exploring programming language development and generative thinking patterns.

## 📄 License

This project is licensed under the **GPL v3 License**. See LICENSE for details.

---

**Remember**: Whether you choose Python for rapid development or C++ for performance, you're writing the same Ascension language. The implementation is just a detail — **Ascension IS the syntax**.

```ascension
// The same code runs on both implementations
func main() {
    print("One language. Multiple runtimes. Infinite possibilities.");
}
```
