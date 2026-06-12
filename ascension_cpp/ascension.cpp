/*
 * ASCENSION v12.7 (Math Edition) - C++ Port
 * Interprete modulare con supporto opzionale per Curses e Networking
 *
 * Compilazione:
 *   Base:        g++ -std=c++17 -O2 ascension.cpp -o ascension
 *   +Curses:     g++ -std=c++17 -O2 -DHAS_CURSES ascension.cpp -o ascension -lncurses
 *   +Network:    g++ -std=c++17 -O2 -DHAS_NETWORK ascension.cpp -o ascension
 *   Full:        g++ -std=c++17 -O2 -DHAS_CURSES -DHAS_NETWORK ascension.cpp -o ascension -lncurses
 *
 * Uso: ./ascension script.asc [-debug] [-allow-exec]
 *
 * (c) 2026 EdeFede - GPL v3
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include "compiler.hpp"
#include "vm.hpp"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "ASCENSION v12.7 (Math Edition) C++\n";
        std::cout << "Uso: " << argv[0] << " <file.asc> [-debug] [-allow-exec]\n";
        std::cout << "  -debug       stampa il bytecode prima dell'esecuzione\n";
        std::cout << "  -allow-exec  abilita system() ed exec() (disabilitati di default)\n\n";
        std::cout << "Moduli compilati:\n";
        std::cout << "  [*] File I/O\n";
#ifdef HAS_CURSES
        std::cout << "  [*] Curses (TUI)\n";
#else
        std::cout << "  [ ] Curses (TUI) - compilare con -DHAS_CURSES -lncurses\n";
#endif
#ifdef HAS_NETWORK
        std::cout << "  [*] Network (TCP/UDP)\n";
#else
        std::cout << "  [ ] Network (TCP/UDP) - compilare con -DHAS_NETWORK\n";
#endif
        return 1;
    }
    
    std::string filename = argv[1];
    bool debug = false, allowExec = false;
    for (int i = 2; i < argc; i++) {
        std::string opt = argv[i];
        if (opt == "-debug") debug = true;
        else if (opt == "-allow-exec") allowExec = true;
        else { std::cerr << "Opzione sconosciuta: " << opt << std::endl; return 1; }
    }
    
    // Estrai directory base
    std::string baseDir = ".";
    size_t lastSlash = filename.find_last_of("/\\");
    if (lastSlash != std::string::npos) {
        baseDir = filename.substr(0, lastSlash);
    }
    
    // Leggi file sorgente
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Errore: impossibile aprire " << filename << std::endl;
        return 1;
    }
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string source = buffer.str();
    
    std::cout << "--- Ascension v12.7 (Math Edition) C++: " << filename << " ---\n";
    
    try {
        // Compila
        asc::AscensionCompiler compiler;
        auto bytecode = compiler.compile(source, baseDir);
        
        // Debug: stampa bytecode
        if (debug) {
            std::cout << "\n=== BYTECODE ===\n";
            for (size_t i = 0; i < bytecode.size(); i++) {
                const auto& op = bytecode[i];
                std::cout << i << ": " << op.op;
                if (!op.arg.empty()) std::cout << " " << op.arg;
                if (op.argCount > 0) std::cout << " [" << op.argCount << "]";
                std::cout << "\n";
            }
            std::cout << "=== ESECUZIONE ===\n\n";
        }
        
        // Esegui
        asc::AscensionVM vm;
        vm.setAllowExec(allowExec);
        vm.loadProgram(bytecode, compiler.getStructs());
        vm.run();
        
    } catch (const asc::AscensionException& e) {
        std::cerr << "[" << e.errorType << "] " << e.message << std::endl;
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "[FatalError] " << e.what() << std::endl;
        return 1;
    }
    
    std::cout << "\n--- Fine ---\n";
    return 0;
}
