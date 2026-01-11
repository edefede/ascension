# ascension
<p align="center">
  <h1 align="center">🚀 Ascension</h1>
  <p align="center">
    <strong>A lightweight programming language with C-style syntax, without explicit typing</strong>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#examples">Examples</a> •
    <a href="#documentation">Documentation</a>
  </p>
</p>

---

**Ascension** is a lightweight, interpreted programming language written in Python. It features familiar C-like syntax but removes the complexity of explicit type declarations, making it perfect for learning, rapid prototyping, and scripting.

```c
// Hello World in Ascension
message = "Hello, World!";
print(message);
```

## ✨ Features

- **C-style syntax** — Familiar to anyone who knows C, Java, or JavaScript
- **No explicit typing** — Variables are dynamically typed
- **Built-in GUI support** — Create windows and interfaces with Tkinter integration
- **Networking** — HTTP requests and TCP sockets out of the box
- **File I/O** — Read and write files easily
- **Terminal UI** — Curses support for terminal-based interfaces
- **Structs** — Organize data with custom structures
- **Arrays & Matrices** — Full support for 1D and 2D arrays
- **Error handling** — Try/catch blocks for robust code
- **Interactive Shell** — REPL environment for quick experiments

## 🚀 Quick Start

### Requirements

- Python 3.x

### Installation

```bash
git clone https://github.com/edefede/ascension.git
cd ascension
```

### Run a program

```bash
python ascension_12_6.py your_program.asc
```

### Interactive Shell (REPL)

```bash
python ascension_shell_12_6.py
```

## 📝 Examples

### Variables and Output

```c
name = "Federico";
age = 30;
pi = 3.14159;

print("Name: " + name);
print("Age: " + str(age));
```

### Control Flow

```c
x = 10;

if (x > 5) {
    print("x is greater than 5");
} else {
    print("x is 5 or less");
}

// Loops
for (i = 0; i < 5; i = i + 1) {
    print("Iteration: " + str(i));
}

while (x > 0) {
    print(x);
    x = x - 1;
}
```

### Functions

```c
func add(a, b) {
    return a + b;
}

func greet(name) {
    print("Hello, " + name + "!");
}

result = add(5, 3);
print("5 + 3 = " + str(result));

greet("World");
```

### Structs

```c
struct Person {
    name,
    age,
    city
}

p = Person("Alice", 25, "Rome");
print(p.name + " is " + str(p.age) + " years old");
```

### File I/O

```c
// Write to file
f = fopen("test.txt", "w");
fwrite(f, "Hello from Ascension!\n");
fclose(f);

// Read from file
f = fopen("test.txt", "r");
content = fread(f);
print(content);
fclose(f);
```

### HTTP Requests

```c
response = http_get("https://api.github.com");
print(response);
```

### GUI Window (Tkinter)

```c
win = gui_window("My App", 400, 300);
gui_label(win, "Welcome to Ascension!", 150, 50);
gui_button(win, "Click Me", 150, 100, "on_click");

func on_click() {
    print("Button clicked!");
}

gui_run(win);
```

### Error Handling

```c
try {
    result = 10 / 0;
} catch {
    print("Error: Division by zero!");
}
```

### Arrays and Matrices

```c
// Array
arr = [1, 2, 3, 4, 5];
print(arr[0]);  // Output: 1

// Matrix
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]];
print(matrix[1][1]);  // Output: 5
// Or using comma syntax:
print(matrix[1, 1]);  // Output: 5
```

## 📚 Documentation

Complete documentation is available in the `docs/` folder:

- **[User Manual (PDF)](docs/)** — Comprehensive 21-chapter guide covering all language features

## 🗂️ Project Structure

```
ascension/
├── ascension_12_6.py        # Main interpreter
├── ascension_shell_12_6.py  # Interactive REPL shell
├── ascension_examples/      # Example programs
├── docs/                    # Documentation
├── LICENSE                  # GPL-3.0 license
└── README.md
```

## 🔧 Built-in Functions

| Category | Functions |
|----------|-----------|
| **I/O** | `print()`, `input()` |
| **Type Conversion** | `str()`, `int()`, `float()` |
| **String** | `len()`, `substr()`, `chr()`, `upper()`, `lower()` |
| **Math** | `abs()`, `sqrt()`, `pow()`, `sin()`, `cos()`, `tan()` |
| **File** | `fopen()`, `fclose()`, `fread()`, `fwrite()` |
| **Network** | `http_get()`, `http_post()`, `socket_create()`, `socket_connect()` |
| **GUI** | `gui_window()`, `gui_label()`, `gui_button()`, `gui_input()`, `gui_run()` |
| **System** | `system()`, `exec()`, `sleep()`, `time()` |

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests

## 📄 License

This project is licensed under the **GPL-3.0 License** — see the [LICENSE](LICENSE) file for details.

## 👤 Author

**EdeFede** ([@edefede](https://github.com/edefede))

---

<p align="center">
  <sub>Built with ❤️ and Python</sub>
</p>
