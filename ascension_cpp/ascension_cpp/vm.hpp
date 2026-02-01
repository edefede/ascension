/*
 * ASCENSION C++ - vm.hpp
 * Virtual Machine Stack-Based
 */
#ifndef ASCENSION_VM_HPP
#define ASCENSION_VM_HPP

#include <vector>
#include <unordered_map>
#include <random>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include "value.hpp"
#include "modules/mod_fileio.hpp"
#include "modules/mod_curses.hpp"
#include "modules/mod_network.hpp"

namespace asc {

class AscensionVM {
private:
    std::vector<Value> stack;
    std::unordered_map<std::string, Value> globalMemory;
    std::vector<std::unordered_map<std::string, Value>> localFrames;
    std::unordered_map<std::string, std::vector<std::string>> structs;
    std::vector<std::pair<size_t, size_t>> callStack;
    std::vector<std::tuple<std::string, size_t, size_t>> tryStack;
    size_t ip = 0;
    std::vector<Opcode> program;
    std::unordered_map<std::string, size_t> labels;
    std::mt19937 rng;
    
    // Modules
    FileIOModule fileIO;
    CursesModule curses;
    NetworkModule network;

public:
    AscensionVM() : rng(std::random_device{}()) { localFrames.push_back({}); }
    
    Value getVar(const std::string& name) {
        if (localFrames.back().count(name)) return localFrames.back()[name];
        if (globalMemory.count(name)) return globalMemory[name];
        return Value(0);
    }
    
    void setVar(const std::string& name, const Value& value, bool forceGlobal = false) {
        if (forceGlobal || localFrames.size() == 1) {
            globalMemory[name] = value;
        } else {
            if (globalMemory.count(name) && !localFrames.back().count(name))
                globalMemory[name] = value;
            else
                localFrames.back()[name] = value;
        }
    }
    
    void loadProgram(const std::vector<Opcode>& code, 
                     const std::unordered_map<std::string, std::vector<std::string>>& structDefs) {
        program = code;
        structs = structDefs;
        for (size_t i = 0; i < program.size(); i++)
            if (program[i].op == "LABEL") labels[program[i].arg] = i;
    }
    
    void run() {
        while (ip < program.size()) {
            const auto& [op, arg, argCount] = program[ip];
            
            try {
                // Stack ops
                if (op == "PUSH") {
                    if (!arg.empty() && arg[0] == '"') {
                        std::string val = arg.substr(1, arg.size() - 2);
                        std::string processed;
                        for (size_t i = 0; i < val.size(); i++) {
                            if (val[i] == '\\' && i + 1 < val.size()) {
                                char n = val[++i];
                                if (n == 'n') processed += '\n';
                                else if (n == 't') processed += '\t';
                                else if (n == 'r') processed += '\r';
                                else if (n == '"') processed += '"';
                                else if (n == '\\') processed += '\\';
                                else { processed += '\\'; processed += n; }
                            } else processed += val[i];
                        }
                        stack.push_back(Value(processed));
                    } else if (arg.find('.') != std::string::npos) {
                        stack.push_back(Value(std::stod(arg)));
                    } else {
                        stack.push_back(Value(static_cast<int64_t>(std::stoll(arg))));
                    }
                }
                else if (op == "POP") { if (!stack.empty()) stack.pop_back(); }
                else if (op == "DUP") { if (!stack.empty()) stack.push_back(stack.back()); }
                else if (op == "PUSH_DICT") { stack.push_back(Value(std::make_shared<Dict>())); }
                else if (op == "PUSH_NULL") { stack.push_back(Value(nullptr)); }
                else if (op == "DICT_SET") {
                    std::string key = stack.back().asString(); stack.pop_back();
                    Value val = stack.back(); stack.pop_back();
                    if (!stack.empty() && stack.back().isDict()) {
                        if (!key.empty() && key[0] == '"') key = key.substr(1, key.size() - 2);
                        (*stack.back().asDict())[key] = val;
                    }
                }
                
                // Variables
                else if (op == "LOAD") { stack.push_back(getVar(arg)); }
                else if (op == "STORE") { setVar(arg, stack.back()); stack.pop_back(); }
                else if (op == "STORE_GLOBAL") { setVar(arg, stack.back(), true); stack.pop_back(); }
                else if (op == "LOAD_GLOBAL") { stack.push_back(globalMemory.count(arg) ? globalMemory[arg] : Value(0)); }
                
                // Struct
                else if (op == "NEW_STRUCT") {
                    auto inst = std::make_shared<Dict>();
                    (*inst)["__type__"] = Value(arg);
                    if (structs.count(arg)) for (const auto& f : structs[arg]) (*inst)[f] = Value(0);
                    stack.push_back(Value(inst));
                }
                else if (op == "GET_ATTR") {
                    Value obj = stack.back(); stack.pop_back();
                    stack.push_back(obj.isDict() && obj.asDict()->count(arg) ? (*obj.asDict())[arg] : Value(0));
                }
                else if (op == "SET_ATTR") {
                    Value obj = stack.back(); stack.pop_back();
                    Value val = stack.back(); stack.pop_back();
                    if (obj.isDict()) (*obj.asDict())[arg] = val;
                }
                
                // Array 1D
                else if (op == "STORE_IDX") {
                    Value idx = stack.back(); stack.pop_back();
                    Value val = stack.back(); stack.pop_back();
                    auto* ref = localFrames.back().count(arg) ? &localFrames.back() : 
                                globalMemory.count(arg) ? &globalMemory : 
                                (localFrames.size() == 1 ? &globalMemory : &localFrames.back());
                    if (!ref->count(arg) || !(*ref)[arg].isDict()) (*ref)[arg] = Value(std::make_shared<Dict>());
                    (*(*ref)[arg].asDict())[idx.asString()] = val;
                }
                else if (op == "LOAD_IDX") {
                    Value idx = stack.back(); stack.pop_back();
                    Value arr = getVar(arg);
                    if (arr.isString()) {
                        int64_t i = idx.asInt();
                        const auto& s = std::get<std::string>(arr.data);
                        stack.push_back(i >= 0 && i < (int64_t)s.size() ? Value(std::string(1, s[i])) : Value(""));
                    } else if (arr.isDict()) {
                        auto& d = arr.asDict();
                        stack.push_back(d->count(idx.asString()) ? (*d)[idx.asString()] : Value(0));
                    } else stack.push_back(Value(0));
                }
                
                // Array 2D
                else if (op == "LOAD_IDX_2D") {
                    Value col = stack.back(); stack.pop_back();
                    Value row = stack.back(); stack.pop_back();
                    Value arr = getVar(arg);
                    std::string key = std::to_string(row.asInt()) + "," + std::to_string(col.asInt());
                    stack.push_back(arr.isDict() && arr.asDict()->count(key) ? (*arr.asDict())[key] : Value(0));
                }
                else if (op == "STORE_IDX_2D") {
                    Value col = stack.back(); stack.pop_back();
                    Value row = stack.back(); stack.pop_back();
                    Value val = stack.back(); stack.pop_back();
                    auto* ref = localFrames.back().count(arg) ? &localFrames.back() : 
                                globalMemory.count(arg) ? &globalMemory : 
                                (localFrames.size() == 1 ? &globalMemory : &localFrames.back());
                    if (!ref->count(arg) || !(*ref)[arg].isDict()) {
                        auto d = std::make_shared<Dict>();
                        (*d)["__matrix__"] = Value(1); (*d)["__rows__"] = Value(0); (*d)["__cols__"] = Value(0);
                        (*ref)[arg] = Value(d);
                    }
                    std::string key = std::to_string(row.asInt()) + "," + std::to_string(col.asInt());
                    auto& d = (*ref)[arg].asDict();
                    (*d)[key] = val;
                    if ((*d)["__rows__"].asInt() <= row.asInt()) (*d)["__rows__"] = Value(row.asInt() + 1);
                    if ((*d)["__cols__"].asInt() <= col.asInt()) (*d)["__cols__"] = Value(col.asInt() + 1);
                }
                else if (op == "CREATE_MATRIX") {
                    Value init = stack.back(); stack.pop_back();
                    int64_t cols = stack.back().asInt(); stack.pop_back();
                    int64_t rows = stack.back().asInt(); stack.pop_back();
                    auto m = std::make_shared<Dict>();
                    (*m)["__matrix__"] = Value(1); (*m)["__rows__"] = Value(rows); (*m)["__cols__"] = Value(cols);
                    for (int64_t r = 0; r < rows; r++)
                        for (int64_t c = 0; c < cols; c++)
                            (*m)[std::to_string(r) + "," + std::to_string(c)] = init;
                    stack.push_back(Value(m));
                }
                else if (op == "MATRIX_ROWS") {
                    Value arr = stack.back(); stack.pop_back();
                    stack.push_back(arr.isDict() && arr.asDict()->count("__matrix__") ? (*arr.asDict())["__rows__"] : Value(0));
                }
                else if (op == "MATRIX_COLS") {
                    Value arr = stack.back(); stack.pop_back();
                    stack.push_back(arr.isDict() && arr.asDict()->count("__matrix__") ? (*arr.asDict())["__cols__"] : Value(arr.isDict() ? 1 : 0));
                }
                else if (op == "MATRIX_DIM") {
                    Value arr = stack.back(); stack.pop_back();
                    stack.push_back(arr.isDict() ? (arr.asDict()->count("__matrix__") ? Value(2) : Value(1)) : Value(0));
                }
                
                // Functions
                else if (op == "CALL") {
                    if (!labels.count(arg)) throw AscensionException("Funzione non definita: '" + arg + "'", "LinkerError");
                    callStack.push_back({ip + 1, localFrames.size()});
                    localFrames.push_back({});
                    ip = labels[arg]; continue;
                }
                else if (op == "RET") {
                    if (!callStack.empty()) {
                        ip = callStack.back().first; callStack.pop_back(); localFrames.pop_back(); continue;
                    } else break;
                }
                else if (op == "RET_VAL") {
                    Value ret = stack.empty() ? Value(0) : stack.back(); if (!stack.empty()) stack.pop_back();
                    if (!callStack.empty()) {
                        ip = callStack.back().first; callStack.pop_back(); localFrames.pop_back();
                        stack.push_back(ret); continue;
                    } else break;
                }
                
                // Built-ins
                else if (op == "READ") { std::string s; std::cout << "INPUT > "; std::getline(std::cin, s); stack.push_back(Value(s)); }
                else if (op == "LEN") {
                    Value t = stack.back(); stack.pop_back();
                    if (t.isString()) stack.push_back(Value((int64_t)std::get<std::string>(t.data).size()));
                    else if (t.isDict()) {
                        int64_t c = 0; for (const auto& [k, v] : *t.asDict()) if (k[0] != '_') c++;
                        stack.push_back(Value(c));
                    } else stack.push_back(Value(0));
                }
                else if (op == "KEYS") {
                    Value c = stack.back(); stack.pop_back();
                    auto r = std::make_shared<Dict>();
                    if (c.isDict()) {
                        std::vector<std::string> keys;
                        for (const auto& [k, v] : *c.asDict()) if (k[0] != '_') keys.push_back(k);
                        std::sort(keys.begin(), keys.end());
                        for (size_t i = 0; i < keys.size(); i++) (*r)[std::to_string(i)] = Value(keys[i]);
                    }
                    stack.push_back(Value(r));
                }
                else if (op == "TO_INT") {
                    Value v = stack.back(); stack.pop_back();
                    if (v.isNumber()) stack.push_back(Value(v.asInt()));
                    else if (v.isString()) {
                        const auto& s = std::get<std::string>(v.data);
                        try { stack.push_back(Value((int64_t)std::stod(s))); }
                        catch (...) { stack.push_back(s.size() == 1 ? Value((int64_t)s[0]) : Value(0)); }
                    } else stack.push_back(Value(0));
                }
                else if (op == "TO_FLOAT") { Value v = stack.back(); stack.pop_back(); stack.push_back(Value(v.asDouble())); }
                else if (op == "SUBSTR") {
                    int64_t len = stack.back().asInt(); stack.pop_back();
                    int64_t start = stack.back().asInt(); stack.pop_back();
                    Value sv = stack.back(); stack.pop_back();
                    if (sv.isString()) {
                        const auto& s = std::get<std::string>(sv.data);
                        stack.push_back(start >= (int64_t)s.size() ? Value("") : Value(s.substr(start < 0 ? 0 : start, len)));
                    } else stack.push_back(Value(""));
                }
                else if (op == "CHR") {
                    int64_t c = stack.back().asInt(); stack.pop_back();
                    stack.push_back(c >= 0 && c <= 127 ? Value(std::string(1, (char)c)) : Value(""));
                }
                else if (op == "SYSTEM") {
                    std::string cmd = stack.back().asString(); stack.pop_back();
                    if (!cmd.empty() && cmd[0] == '"') cmd = cmd.substr(1, cmd.size() - 2);
                    stack.push_back(Value(std::system(cmd.c_str())));
                }
                else if (op == "EXEC") {
                    std::string cmd = stack.back().asString(); stack.pop_back();
                    if (!cmd.empty() && cmd[0] == '"') cmd = cmd.substr(1, cmd.size() - 2);
                    std::string out;
                    #ifdef _WIN32
                    FILE* p = _popen(cmd.c_str(), "r");
                    #else
                    FILE* p = popen(cmd.c_str(), "r");
                    #endif
                    if (p) { char buf[128]; while (fgets(buf, sizeof(buf), p)) out += buf; 
                    #ifdef _WIN32
                    _pclose(p);
                    #else
                    pclose(p);
                    #endif
                    }
                    stack.push_back(Value(out));
                }
                
                // File I/O
                else if (op == "FILE_OPEN") {
                    std::string mode = stack.back().asString(); stack.pop_back();
                    std::string fname = stack.back().asString(); stack.pop_back();
                    stack.push_back(fileIO.fileOpen(fname, mode));
                }
                else if (op == "FILE_WRITE") {
                    std::string content = stack.back().asString(); stack.pop_back();
                    int64_t hid = stack.back().asInt(); stack.pop_back();
                    stack.push_back(fileIO.fileWrite(hid, content));
                }
                else if (op == "FILE_READLINE") { int64_t h = stack.back().asInt(); stack.pop_back(); stack.push_back(fileIO.fileReadLine(h)); }
                else if (op == "FILE_READALL") { int64_t h = stack.back().asInt(); stack.pop_back(); stack.push_back(fileIO.fileReadAll(h)); }
                else if (op == "FILE_CLOSE") { int64_t h = stack.back().asInt(); stack.pop_back(); stack.push_back(fileIO.fileClose(h)); }
                
                // Curses
                else if (op == "CURSES_INIT") { stack.push_back(curses.init()); }
                else if (op == "CURSES_END") { stack.push_back(curses.end()); }
                else if (op == "CURSES_CLEAR") { stack.push_back(curses.clear()); }
                else if (op == "CURSES_REFRESH") { stack.push_back(curses.refresh()); }
                else if (op == "CURSES_MOVE") { int x = stack.back().asInt(); stack.pop_back(); int y = stack.back().asInt(); stack.pop_back(); stack.push_back(curses.move(y, x)); }
                else if (op == "CURSES_WRITE") { std::string s = stack.back().asString(); stack.pop_back(); stack.push_back(curses.write(s)); }
                else if (op == "CURSES_READ_KEY") { stack.push_back(curses.readKey()); }
                else if (op == "CURSES_ROWS") { stack.push_back(curses.getMaxY()); }
                else if (op == "CURSES_COLS") { stack.push_back(curses.getMaxX()); }
                
                // Network
                else if (op == "SOCKET_OPEN") { std::string proto = stack.back().asString(); stack.pop_back(); std::string type = stack.back().asString(); stack.pop_back(); stack.push_back(network.socketOpen(type, proto)); }
                else if (op == "SOCKET_BIND") { int port = stack.back().asInt(); stack.pop_back(); std::string ip = stack.back().asString(); stack.pop_back(); int64_t sid = stack.back().asInt(); stack.pop_back(); stack.push_back(network.socketBind(sid, ip, port)); }
                else if (op == "SOCKET_LISTEN") { int bl = stack.back().asInt(); stack.pop_back(); int64_t sid = stack.back().asInt(); stack.pop_back(); stack.push_back(network.socketListen(sid, bl)); }
                else if (op == "SOCKET_ACCEPT") { int64_t sid = stack.back().asInt(); stack.pop_back(); stack.push_back(network.socketAccept(sid)); }
                else if (op == "SOCKET_CONNECT") { int port = stack.back().asInt(); stack.pop_back(); std::string ip = stack.back().asString(); stack.pop_back(); int64_t sid = stack.back().asInt(); stack.pop_back(); stack.push_back(network.socketConnect(sid, ip, port)); }
                else if (op == "SOCKET_SEND") { std::string data = stack.back().asString(); stack.pop_back(); int64_t sid = stack.back().asInt(); stack.pop_back(); stack.push_back(network.socketSend(sid, data)); }
                else if (op == "SOCKET_RECV") { int mb = stack.back().asInt(); stack.pop_back(); int64_t sid = stack.back().asInt(); stack.pop_back(); stack.push_back(network.socketRecv(sid, mb)); }
                else if (op == "SOCKET_CLOSE") { int64_t sid = stack.back().asInt(); stack.pop_back(); stack.push_back(network.socketClose(sid)); }
                else if (op == "GET_IP") { std::string h = stack.back().asString(); stack.pop_back(); stack.push_back(network.getIP(h)); }
                else if (op == "HTTP_GET") { std::string url = stack.back().asString(); stack.pop_back(); stack.push_back(network.httpGet(url)); }
                else if (op == "HTTP_POST") { std::string data = stack.back().asString(); stack.pop_back(); std::string url = stack.back().asString(); stack.pop_back(); stack.push_back(network.httpPost(url, data)); }
                
                // Try/Catch
                else if (op == "TRY_START") { tryStack.push_back({arg, localFrames.size(), callStack.size()}); }
                else if (op == "TRY_END") { if (!tryStack.empty()) tryStack.pop_back(); ip = labels[arg]; continue; }
                else if (op == "THROW") { std::string msg = stack.empty() ? "Error" : stack.back().asString(); if (!stack.empty()) stack.pop_back(); throw AscensionException(msg); }
                else if (op == "CATCH_START" || op == "CATCH_END") {}
                
                // Math ops
                else if (op == "ADD" || op == "SUB" || op == "MUL" || op == "DIV" || op == "MOD" ||
                         op == "GT" || op == "LT" || op == "EQ" || op == "NEQ" || op == "GTE" || op == "LTE" || 
                         op == "AND" || op == "OR") {
                    Value b = stack.back(); stack.pop_back();
                    Value a = stack.back(); stack.pop_back();
                    if (op == "EQ") stack.push_back(Value(a == b ? 1 : 0));
                    else if (op == "NEQ") stack.push_back(Value(a != b ? 1 : 0));
                    else if (op == "AND") stack.push_back(Value(a.toBool() && b.toBool() ? 1 : 0));
                    else if (op == "OR") stack.push_back(Value(a.toBool() || b.toBool() ? 1 : 0));
                    else if (a.isNull() || b.isNull()) stack.push_back(Value(nullptr));
                    else if (op == "ADD" && (a.isString() || b.isString())) stack.push_back(Value(a.asString() + b.asString()));
                    else {
                        double av = a.asDouble(), bv = b.asDouble(), r = 0;
                        if (op == "ADD") r = av + bv;
                        else if (op == "SUB") r = av - bv;
                        else if (op == "MUL") r = av * bv;
                        else if (op == "DIV") { if (bv == 0) throw AscensionException("DivZero"); r = av / bv; }
                        else if (op == "MOD") r = std::fmod(av, bv);
                        else if (op == "GT") r = av > bv ? 1 : 0;
                        else if (op == "LT") r = av < bv ? 1 : 0;
                        else if (op == "GTE") r = av >= bv ? 1 : 0;
                        else if (op == "LTE") r = av <= bv ? 1 : 0;
                        stack.push_back(r == std::floor(r) ? Value((int64_t)r) : Value(r));
                    }
                }
                else if (op == "NOT") { Value v = stack.back(); stack.pop_back(); stack.push_back(Value(v.toBool() ? 0 : 1)); }
                
                // Math functions
                else if (op == "RANDOM") { std::uniform_real_distribution<double> d(0.0, 1.0); stack.push_back(Value(d(rng))); }
                else if (op == "RANDOM_MAX") { int64_t m = stack.back().asInt(); stack.pop_back(); std::uniform_int_distribution<int64_t> d(0, m - 1); stack.push_back(Value(d(rng))); }
                else if (op == "RANDOM_RANGE") { int64_t mx = stack.back().asInt(); stack.pop_back(); int64_t mn = stack.back().asInt(); stack.pop_back(); std::uniform_int_distribution<int64_t> d(mn, mx - 1); stack.push_back(Value(d(rng))); }
                else if (op == "SQRT") { double v = stack.back().asDouble(); stack.pop_back(); if (v < 0) throw AscensionException("sqrt negativo", "MathError"); stack.push_back(Value(std::sqrt(v))); }
                else if (op == "POW") { double e = stack.back().asDouble(); stack.pop_back(); double b = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value(std::pow(b, e))); }
                else if (op == "EXP") { double v = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value(std::exp(v))); }
                else if (op == "LOG") { double v = stack.back().asDouble(); stack.pop_back(); if (v <= 0) throw AscensionException("log non positivo", "MathError"); stack.push_back(Value(std::log(v))); }
                else if (op == "ABS") { stack.push_back(Value(std::abs(stack.back().asDouble()))); stack.erase(stack.end() - 2); }
                else if (op == "FLOOR") { double v = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value((int64_t)std::floor(v))); }
                else if (op == "CEIL") { double v = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value((int64_t)std::ceil(v))); }
                else if (op == "SIN") { double v = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value(std::sin(v))); }
                else if (op == "COS") { double v = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value(std::cos(v))); }
                else if (op == "TAN") { double v = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value(std::tan(v))); }
                else if (op == "ASIN") { double v = stack.back().asDouble(); stack.pop_back(); if (v < -1 || v > 1) throw AscensionException("asin range", "MathError"); stack.push_back(Value(std::asin(v))); }
                else if (op == "ACOS") { double v = stack.back().asDouble(); stack.pop_back(); if (v < -1 || v > 1) throw AscensionException("acos range", "MathError"); stack.push_back(Value(std::acos(v))); }
                else if (op == "ATAN") { double v = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value(std::atan(v))); }
                else if (op == "ATAN2") { double x = stack.back().asDouble(); stack.pop_back(); double y = stack.back().asDouble(); stack.pop_back(); stack.push_back(Value(std::atan2(y, x))); }
                
                // Control flow
                else if (op == "JMP") { ip = labels[arg]; continue; }
                else if (op == "JZ") { if (!stack.back().toBool()) { stack.pop_back(); ip = labels[arg]; continue; } stack.pop_back(); }
                else if (op == "JNZ") { if (stack.back().toBool()) { stack.pop_back(); ip = labels[arg]; continue; } stack.pop_back(); }
                else if (op == "PRINT") {
                    std::vector<std::string> args;
                    for (int i = 0; i < argCount; i++) { args.push_back(stack.back().asString()); stack.pop_back(); }
                    std::cout << "OUTPUT > ";
                    for (auto it = args.rbegin(); it != args.rend(); ++it) std::cout << (it != args.rbegin() ? " " : "") << *it;
                    std::cout << std::endl;
                }
                else if (op == "LABEL") {}
                
                ip++;
                
            } catch (AscensionException& e) {
                bool handled = false;
                while (!tryStack.empty()) {
                    auto [lbl, fd, cd] = tryStack.back(); tryStack.pop_back();
                    while (localFrames.size() > fd) localFrames.pop_back();
                    while (callStack.size() > cd) callStack.pop_back();
                    stack.push_back(Value(e.message));
                    ip = labels[lbl]; handled = true; break;
                }
                if (!handled) { std::cerr << "Uncaught: " << e.message << std::endl; break; }
            } catch (std::exception& e) {
                std::cerr << "Runtime Error: " << e.what() << std::endl; break;
            }
        }
    }
};

} // namespace asc
#endif
