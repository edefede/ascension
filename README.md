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

**Ascension** is a lightweight, stack-based interpreted programming language written in Python. It features familiar C-like syntax but removes the complexity of explicit type declarations, making it perfect for learning, rapid prototyping, and scripting.

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
- **Arrays & Matrices** — Full support for 1D and 2D arrays with multiple syntaxes
- **Error handling** — Try/catch blocks for robust code
- **Interactive Shell** — REPL environment for quick experiments
- **System commands** — Execute shell commands with `system()` and `exec()`

## 🚀 Quick Start

### Requirements

- Python 3.x
- Optional: `requests` library for HTTP functionality
- Optional: `tkinter` for GUI (usually included with Python)

### Installation

```bash
git clone https://github.com/edefede/ascension.git
cd ascension
```

### Run a program

```bash
python ascension_12_6.py your_program.asc
```

### Debug mode

```bash
python ascension_12_6.py your_program.asc -debug
```

### Interactive Shell (REPL)

```bash
python ascension_shell_12_6.py
```

## 📝 Examples

### Variables and Output

```c
name = "EdeFede";
age = 30;
pi = 3.14159;
active = true;

print(name);
print(age);
print("Pi is:", pi);
```

### User Input

```c
print("What is your name?");
name = read();
print("Hello,", name);
```

### Control Flow

```c
x = 10;

if (x > 5) {
    print("x is greater than 5");
} else if (x == 5) {
    print("x is exactly 5");
} else {
    print("x is less than 5");
}

// For loop
for (i = 0; i < 5; i = i + 1) {
    print("Iteration:", i);
}

// While loop
while (x > 0) {
    print(x);
    x = x - 1;
}

// Switch statement
switch (x) {
    case 1: { print("One"); };
    case 2: { print("Two"); };
    default: { print("Other"); };
}
```

### Functions

```c
func add(a, b) {
    return a + b;
}

func greet(name) {
    print("Hello,", name);
}

// Function prototypes for mutual recursion
func isEven(n);
func isOdd(n);

func isEven(n) {
    if (n == 0) { return true; }
    return isOdd(n - 1);
}

func isOdd(n) {
    if (n == 0) { return false; }
    return isEven(n - 1);
}

result = add(5, 3);
print("5 + 3 =", result);

greet("World");
```

### Structs

```c
struct Person {
    name,
    age,
    city
}

p = new Person;
p.name = "Alice";
p.age = 25;
p.city = "Rome";

print(p.name, "is", p.age, "years old");
```

### Arrays and Matrices

```c
// Array (dictionary-based)
arr = {};
arr[0] = 10;
arr[1] = 20;
arr[2] = 30;
print(arr[0]);  // Output: 10
print(len(arr)); // Output: 3

// Matrix creation
m = matrix(3, 3, 0);  // 3x3 matrix filled with 0

// Access with C-style syntax
m[0][0] = 1;
m[1][1] = 5;
print(m[1][1]);  // Output: 5

// Or with comma syntax
m[2, 2] = 9;
print(m[2, 2]);  // Output: 9

// Matrix info
print(rows(m));  // Output: 3
print(cols(m));  // Output: 3
print(dim(m));   // Output: 2 (2D array)
```

### File I/O

```c
// Write to file
f = open("test.txt", "w");
write(f, "Hello from Ascension!\n");
write(f, "Second line\n");
close(f);

// Read entire file
f = open("test.txt", "r");
content = read_all(f);
print(content);
close(f);

// Read line by line
f = open("data.txt", "r");
line = read_line(f);
while (line != NULL) {
    print(line);
    line = read_line(f);
}
close(f);
```

### HTTP Requests

```c
// GET request
response = http_get("https://api.github.com");
status = response_status(response);
body = response_body(response);
print("Status:", status);

// POST request
data = {};
data["name"] = "test";
response = http_post("https://httpbin.org/post", data);
```

### TCP Sockets

```c
// Create and connect socket
sock = socket_create();
socket_connect(sock, "example.com", 80);
socket_send(sock, "GET / HTTP/1.0\r\n\r\n");
response = socket_recv(sock, 4096);
print(response);
socket_close(sock);

// Server socket
server = socket_create();
socket_bind(server, "0.0.0.0", 8080);
socket_listen(server, 5);
client = socket_accept(server);
```

### GUI with Tkinter

```c
// Create main window
root = tk_root("My Application");
tk_geometry("400x300");

// Create widgets
label = tk_widget(root, "Label", {"text": "Welcome!"});
tk_pack(label, {"pady": 10});

entry = tk_widget(root, "Entry", {});
tk_pack(entry, {"pady": 5});

func on_click() {
    text = tk_get(entry);
    tk_msgbox("Hello", text);
}

btn = tk_widget(root, "Button", {"text": "Click Me"});
tk_command(btn, "on_click");
tk_pack(btn, {"pady": 10});

// Start event loop
tk_mainloop();
```

### Terminal UI with Curses

```c
curses_init();
curses_clear();
curses_move(5, 10);
curses_write("Hello Terminal!");
curses_refresh();

key = curses_read_key();
curses_end();
```

### Error Handling

```c
try {
    result = 10 / 0;
} catch (e) {
    print("Error:", e);
}

// Or without capturing the error
try {
    f = open("nonexistent.txt", "r");
} catch {
    print("File not found!");
}

// Throw custom errors
func divide(a, b) {
    if (b == 0) {
        throw "Division by zero!";
    }
    return a / b;
}
```

### System Commands

```c
// Execute command and get exit code
exit_code = system("ls -la");
print("Exit code:", exit_code);

// Execute command and capture output
output = exec("whoami");
print("Current user:", output);
```

### String Operations

```c
text = "Hello World";
print(len(text));           // Output: 11
print(substr(text, 0, 5));  // Output: Hello
print(chr(65));             // Output: A

// Convert character to ASCII code
code = to_int("A");
print(code);  // Output: 65
```

### Include Files

```c
// main.asc
include "utils.asc";
include "config.asc";

result = helper_function();
```

## 📚 Documentation

Complete documentation is available in the `docs/` folder, including a comprehensive user manual covering all language features from basic variables to advanced networking and GUI programming.

## 🗂️ Project Structure

```
ascension/
├── ascension_12_6.py        # Main interpreter/compiler
├── ascension_shell_12_6.py  # Interactive REPL shell
├── ascension_examples/      # Example programs
├── docs/                    # Documentation
├── LICENSE                  # GPL-3.0 license
└── README.md
```

## 🔧 Built-in Functions

| Category | Functions |
|----------|-----------|
| **I/O** | `print()`, `read()` |
| **Type Conversion** | `to_int()`, `to_float()` |
| **String** | `len()`, `substr()`, `chr()` |
| **Arrays** | `len()`, `keys()` |
| **Matrix** | `matrix()`, `rows()`, `cols()`, `dim()` |
| **File** | `open()`, `close()`, `write()`, `read_line()`, `read_all()` |
| **Network** | `http_get()`, `http_post()`, `response_status()`, `response_body()` |
| **Sockets** | `socket_create()`, `socket_connect()`, `socket_bind()`, `socket_listen()`, `socket_accept()`, `socket_send()`, `socket_recv()`, `socket_close()`, `get_ip()` |
| **GUI** | `tk_root()`, `tk_widget()`, `tk_pack()`, `tk_grid()`, `tk_config()`, `tk_get()`, `tk_set()`, `tk_command()`, `tk_bind()`, `tk_mainloop()`, `tk_msgbox()`, and many more |
| **Terminal** | `curses_init()`, `curses_end()`, `curses_clear()`, `curses_refresh()`, `curses_move()`, `curses_write()`, `curses_read_key()` |
| **System** | `system()`, `exec()` |

## 🔑 Keywords and Values

| Type | Values |
|------|--------|
| **Boolean** | `true`, `false` |
| **Null** | `NULL` |
| **Control** | `if`, `else`, `for`, `while`, `switch`, `case`, `default`, `break`, `continue` |
| **Functions** | `func`, `return` |
| **Error Handling** | `try`, `catch`, `throw` |
| **Data** | `struct`, `new`, `global` |
| **Other** | `include` |

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





