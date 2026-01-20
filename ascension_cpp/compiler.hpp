/*
 * ASCENSION C++ - compiler.hpp
 * Compilatore da sorgente a bytecode
 */
#ifndef ASCENSION_COMPILER_HPP
#define ASCENSION_COMPILER_HPP

#include <vector>
#include <string>
#include <regex>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <cmath>
#include "value.hpp"

namespace asc {

class AscensionCompiler {
private:
    std::vector<Opcode> ops;
    std::unordered_map<std::string, std::vector<std::string>> structs;
    int labelCounter = 0;
    bool inFunction = false;
    std::vector<std::pair<std::string, std::string>> loopStack;
    std::string baseDir = ".";
    std::unordered_map<std::string, std::vector<std::string>> functionPrototypes;
    std::unordered_set<std::string> functionDefined;
    
    std::vector<std::string> builtinKeywords = {
        "if", "while", "for", "print", "switch", "try", "throw", "return",
        "read", "len", "keys", "to_int", "to_float", "system", "exec",
        "random", "sqrt", "pow", "exp", "log", "abs", "floor", "ceil",
        "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
        "open", "write", "close", "read_line", "read_all", "substr", "chr",
        "matrix", "rows", "cols", "dim", "get_ip",
        "curses_init", "curses_end", "curses_clear", "curses_refresh",
        "curses_move", "curses_write", "curses_read_key", "curses_max_y", "curses_max_x",
        "socket_open", "socket_bind", "socket_listen", "socket_accept",
        "socket_connect", "socket_send", "socket_recv", "socket_close"
    };
    
    std::string getLabel(const std::string& s = "") { return "L" + std::to_string(++labelCounter) + "_" + s; }
    
    std::string trim(const std::string& s) {
        size_t start = s.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        return s.substr(start, s.find_last_not_of(" \t\r\n") - start + 1);
    }
    
    std::string extractBalancedArg(const std::string& expr, const std::string& func) {
        std::string prefix = func + "(";
        if (expr.substr(0, prefix.size()) != prefix) return "";
        int pd = 0, bd = 0; bool inStr = false;
        for (size_t i = prefix.size(); i < expr.size(); i++) {
            char c = expr[i];
            if (c == '"' && (i == 0 || expr[i-1] != '\\')) inStr = !inStr;
            if (!inStr) {
                if (c == '(') pd++; else if (c == ')') { if (pd == 0 && bd == 0 && i == expr.size() - 1) return expr.substr(prefix.size(), i - prefix.size()); pd--; }
                else if (c == '{') bd++; else if (c == '}') bd--;
            }
        }
        return "";
    }
    
    std::pair<std::string, size_t> extractBracedBlock(const std::string& text, size_t pos) {
        if (pos >= text.size() || text[pos] != '{') return {"", std::string::npos};
        int d = 0; bool inStr = false;
        for (size_t i = pos; i < text.size(); i++) {
            if (text[i] == '"' && (i == 0 || text[i-1] != '\\')) inStr = !inStr;
            if (!inStr) { if (text[i] == '{') d++; else if (text[i] == '}') { d--; if (d == 0) return {text.substr(pos + 1, i - pos - 1), i + 1}; } }
        }
        return {"", std::string::npos};
    }
    
    std::string cleanSource(const std::string& src) {
        std::vector<std::string> lines; std::istringstream iss(src); std::string line; bool inML = false;
        while (std::getline(iss, line)) {
            while (line.find("/*") != std::string::npos || inML) {
                if (inML) { size_t p = line.find("*/"); if (p != std::string::npos) { line = line.substr(p + 2); inML = false; } else { line = ""; break; } }
                else { size_t s = line.find("/*"), e = line.find("*/", s); if (e != std::string::npos) line = line.substr(0, s) + line.substr(e + 2); else { line = line.substr(0, s); inML = true; } }
            }
            if (!inML && line.find("//") != std::string::npos) {
                bool inQ = false;
                for (size_t i = 0; i < line.size(); i++) {
                    if (line[i] == '"' && (i == 0 || line[i-1] != '\\')) inQ = !inQ;
                    if (!inQ && i + 1 < line.size() && line[i] == '/' && line[i+1] == '/') { line = line.substr(0, i); break; }
                }
            }
            std::string t = trim(line); if (!t.empty()) lines.push_back(t);
        }
        std::string r; for (const auto& l : lines) { if (!r.empty()) r += " "; r += l; } return r;
    }
    
    std::vector<std::string> smartSplit(const std::string& src) {
        std::vector<std::string> stmts; std::string cur; int br = 0, pr = 0; bool qt = false;
        for (size_t i = 0; i < src.size(); i++) {
            char c = src[i];
            if (c == '"') qt = !qt;
            if (!qt) {
                if (c == '{') { br++; cur += c; continue; }
                else if (c == '}') { br--; cur += c; if (br == 0 && pr == 0) { std::string rest = trim(src.substr(i + 1)); if (!rest.empty() && rest.substr(0, 4) != "else" && rest.substr(0, 5) != "catch") { std::string t = trim(cur); if (!t.empty()) stmts.push_back(t); cur = ""; } } continue; }
                else if (c == '(') pr++; else if (c == ')') pr--;
            }
            if (c == ';' && br == 0 && pr == 0 && !qt) { std::string t = trim(cur); if (!t.empty()) stmts.push_back(t); cur = ""; }
            else cur += c;
        }
        std::string t = trim(cur); if (!t.empty()) stmts.push_back(t);
        return stmts;
    }
    
    std::vector<std::string> splitArgs(const std::string& s) {
        std::vector<std::string> args; std::string cur; int pr = 0, br = 0, bk = 0; bool qt = false;
        for (char c : s) {
            if (c == '"') qt = !qt;
            if (!qt) { if (c == '(') pr++; else if (c == ')') pr--; else if (c == '{') br++; else if (c == '}') br--; else if (c == '[') bk++; else if (c == ']') bk--; }
            if (c == ',' && pr == 0 && br == 0 && bk == 0 && !qt) { std::string t = trim(cur); if (!t.empty()) args.push_back(t); cur = ""; }
            else cur += c;
        }
        std::string t = trim(cur); if (!t.empty()) args.push_back(t);
        return args;
    }
    
    bool isBuiltin(const std::string& n) { return std::find(builtinKeywords.begin(), builtinKeywords.end(), n) != builtinKeywords.end(); }
    
    void parseExpression(const std::string& exprRaw) {
        std::string expr = trim(exprRaw);
        if (expr.empty()) return;
        
        // String literal
        if (expr[0] == '"' && expr.back() == '"') {
            int qc = 0; for (size_t i = 0; i < expr.size(); i++) if (expr[i] == '"' && (i == 0 || expr[i-1] != '\\')) qc++;
            if (qc == 2) { ops.push_back(Opcode("PUSH", expr)); return; }
        }
        
        std::string arg;
        // Built-ins
        if ((arg = extractBalancedArg(expr, "len")) != "") { parseExpression(arg); ops.push_back(Opcode("LEN")); return; }
        if ((arg = extractBalancedArg(expr, "keys")) != "") { parseExpression(arg); ops.push_back(Opcode("KEYS")); return; }
        if ((arg = extractBalancedArg(expr, "to_int")) != "") { parseExpression(arg); ops.push_back(Opcode("TO_INT")); return; }
        if ((arg = extractBalancedArg(expr, "to_float")) != "") { parseExpression(arg); ops.push_back(Opcode("TO_FLOAT")); return; }
        if ((arg = extractBalancedArg(expr, "substr")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); parseExpression(a[2]); ops.push_back(Opcode("SUBSTR")); return; }
        if ((arg = extractBalancedArg(expr, "chr")) != "") { parseExpression(arg); ops.push_back(Opcode("CHR")); return; }
        if ((arg = extractBalancedArg(expr, "system")) != "") { parseExpression(arg); ops.push_back(Opcode("SYSTEM")); return; }
        if ((arg = extractBalancedArg(expr, "exec")) != "") { parseExpression(arg); ops.push_back(Opcode("EXEC")); return; }
        if ((arg = extractBalancedArg(expr, "open")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("FILE_OPEN")); return; }
        if ((arg = extractBalancedArg(expr, "file_open")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("FILE_OPEN")); return; }
        if ((arg = extractBalancedArg(expr, "http_get")) != "") { parseExpression(arg); ops.push_back(Opcode("HTTP_GET")); return; }
        if ((arg = extractBalancedArg(expr, "http_post")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("HTTP_POST")); return; }
        if ((arg = extractBalancedArg(expr, "write")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("FILE_WRITE")); return; }
        if ((arg = extractBalancedArg(expr, "file_write")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("FILE_WRITE")); return; }
        if ((arg = extractBalancedArg(expr, "read_line")) != "") { parseExpression(arg); ops.push_back(Opcode("FILE_READLINE")); return; }
        if ((arg = extractBalancedArg(expr, "file_read_line")) != "") { parseExpression(arg); ops.push_back(Opcode("FILE_READLINE")); return; }
        if ((arg = extractBalancedArg(expr, "read_all")) != "") { parseExpression(arg); ops.push_back(Opcode("FILE_READALL")); return; }
        if ((arg = extractBalancedArg(expr, "file_read_all")) != "") { parseExpression(arg); ops.push_back(Opcode("FILE_READALL")); return; }
        if ((arg = extractBalancedArg(expr, "close")) != "") { parseExpression(arg); ops.push_back(Opcode("FILE_CLOSE")); return; }
        if ((arg = extractBalancedArg(expr, "file_close")) != "") { parseExpression(arg); ops.push_back(Opcode("FILE_CLOSE")); return; }
        if ((arg = extractBalancedArg(expr, "matrix")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); if (a.size() >= 3) parseExpression(a[2]); else ops.push_back(Opcode("PUSH", "0")); ops.push_back(Opcode("CREATE_MATRIX")); return; }
        if ((arg = extractBalancedArg(expr, "rows")) != "") { parseExpression(arg); ops.push_back(Opcode("MATRIX_ROWS")); return; }
        if ((arg = extractBalancedArg(expr, "cols")) != "") { parseExpression(arg); ops.push_back(Opcode("MATRIX_COLS")); return; }
        if ((arg = extractBalancedArg(expr, "dim")) != "") { parseExpression(arg); ops.push_back(Opcode("MATRIX_DIM")); return; }
        if ((arg = extractBalancedArg(expr, "get_ip")) != "") { parseExpression(arg); ops.push_back(Opcode("GET_IP")); return; }
        
        // Curses
        if (std::regex_match(expr, std::regex("^curses_init\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("CURSES_INIT")); return; }
        if (std::regex_match(expr, std::regex("^curses_end\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("CURSES_END")); return; }
        if (std::regex_match(expr, std::regex("^curses_clear\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("CURSES_CLEAR")); return; }
        if (std::regex_match(expr, std::regex("^curses_refresh\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("CURSES_REFRESH")); return; }
        if ((arg = extractBalancedArg(expr, "curses_move")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("CURSES_MOVE")); return; }
        if ((arg = extractBalancedArg(expr, "curses_write")) != "") { parseExpression(arg); ops.push_back(Opcode("CURSES_WRITE")); return; }
        if (std::regex_match(expr, std::regex("^curses_read_key\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("CURSES_READ_KEY")); return; }
        if (std::regex_match(expr, std::regex("^curses_max_y\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("CURSES_MAX_Y")); return; }
        if (std::regex_match(expr, std::regex("^curses_max_x\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("CURSES_MAX_X")); return; }
        
        // Sockets
        if ((arg = extractBalancedArg(expr, "socket_open")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("SOCKET_OPEN")); return; }
        if ((arg = extractBalancedArg(expr, "socket_bind")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); parseExpression(a[2]); ops.push_back(Opcode("SOCKET_BIND")); return; }
        if ((arg = extractBalancedArg(expr, "socket_listen")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("SOCKET_LISTEN")); return; }
        if ((arg = extractBalancedArg(expr, "socket_accept")) != "") { parseExpression(arg); ops.push_back(Opcode("SOCKET_ACCEPT")); return; }
        if ((arg = extractBalancedArg(expr, "socket_connect")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); parseExpression(a[2]); ops.push_back(Opcode("SOCKET_CONNECT")); return; }
        if ((arg = extractBalancedArg(expr, "socket_send")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("SOCKET_SEND")); return; }
        if ((arg = extractBalancedArg(expr, "socket_recv")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("SOCKET_RECV")); return; }
        if ((arg = extractBalancedArg(expr, "socket_close")) != "") { parseExpression(arg); ops.push_back(Opcode("SOCKET_CLOSE")); return; }
        
        // Math functions
        if (std::regex_match(expr, std::regex("^random\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("RANDOM")); return; }
        if ((arg = extractBalancedArg(expr, "random")) != "") { auto a = splitArgs(arg); if (a.size() == 1) { parseExpression(a[0]); ops.push_back(Opcode("RANDOM_MAX")); } else { parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("RANDOM_RANGE")); } return; }
        if ((arg = extractBalancedArg(expr, "sqrt")) != "") { parseExpression(arg); ops.push_back(Opcode("SQRT")); return; }
        if ((arg = extractBalancedArg(expr, "pow")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("POW")); return; }
        if ((arg = extractBalancedArg(expr, "exp")) != "") { parseExpression(arg); ops.push_back(Opcode("EXP")); return; }
        if ((arg = extractBalancedArg(expr, "log")) != "") { parseExpression(arg); ops.push_back(Opcode("LOG")); return; }
        if ((arg = extractBalancedArg(expr, "abs")) != "") { parseExpression(arg); ops.push_back(Opcode("ABS")); return; }
        if ((arg = extractBalancedArg(expr, "floor")) != "") { parseExpression(arg); ops.push_back(Opcode("FLOOR")); return; }
        if ((arg = extractBalancedArg(expr, "ceil")) != "") { parseExpression(arg); ops.push_back(Opcode("CEIL")); return; }
        if ((arg = extractBalancedArg(expr, "sin")) != "") { parseExpression(arg); ops.push_back(Opcode("SIN")); return; }
        if ((arg = extractBalancedArg(expr, "cos")) != "") { parseExpression(arg); ops.push_back(Opcode("COS")); return; }
        if ((arg = extractBalancedArg(expr, "tan")) != "") { parseExpression(arg); ops.push_back(Opcode("TAN")); return; }
        if ((arg = extractBalancedArg(expr, "asin")) != "") { parseExpression(arg); ops.push_back(Opcode("ASIN")); return; }
        if ((arg = extractBalancedArg(expr, "acos")) != "") { parseExpression(arg); ops.push_back(Opcode("ACOS")); return; }
        if ((arg = extractBalancedArg(expr, "atan")) != "") { parseExpression(arg); ops.push_back(Opcode("ATAN")); return; }
        if ((arg = extractBalancedArg(expr, "atan2")) != "") { auto a = splitArgs(arg); parseExpression(a[0]); parseExpression(a[1]); ops.push_back(Opcode("ATAN2")); return; }
        
        // Constants
        if (expr == "PI") { ops.push_back(Opcode("PUSH", std::to_string(M_PI))); return; }
        if (expr == "E") { ops.push_back(Opcode("PUSH", std::to_string(M_E))); return; }
        if (expr == "NULL") { ops.push_back(Opcode("PUSH_NULL")); return; }
        if (expr == "true") { ops.push_back(Opcode("PUSH", "1")); return; }
        if (expr == "false") { ops.push_back(Opcode("PUSH", "0")); return; }
        if (std::regex_match(expr, std::regex("^read\\s*\\(\\s*\\)$"))) { ops.push_back(Opcode("READ")); return; }
        
        // new struct
        if (expr.substr(0, 4) == "new ") { size_t pp = expr.find('('); std::string sn = trim(expr.substr(4, (pp != std::string::npos ? pp : expr.size()) - 4)); ops.push_back(Opcode("NEW_STRUCT", sn)); return; }
        
        // Logic operators
        if (expr.find(" && ") != std::string::npos) { size_t p = expr.find(" && "); parseExpression(expr.substr(0, p)); parseExpression(expr.substr(p + 4)); ops.push_back(Opcode("AND")); return; }
        if (expr.find(" || ") != std::string::npos) { size_t p = expr.find(" || "); parseExpression(expr.substr(0, p)); parseExpression(expr.substr(p + 4)); ops.push_back(Opcode("OR")); return; }
        if (expr[0] == '!' && expr.substr(0, 2) != "!=") { parseExpression(expr.substr(1)); ops.push_back(Opcode("NOT")); return; }
        
        // Binary operators
        std::vector<std::pair<std::string, std::string>> opList = {{"==", "EQ"}, {"!=", "NEQ"}, {">=", "GTE"}, {"<=", "LTE"}, {">", "GT"}, {"<", "LT"}, {"+", "ADD"}, {"-", "SUB"}, {"*", "MUL"}, {"/", "DIV"}, {"%", "MOD"}};
        for (const auto& [opStr, opName] : opList) {
            int pd = 0, bkd = 0; bool inStr = false;
            for (int i = expr.size() - 1; i >= 0; i--) {
                char c = expr[i];
                if (c == '"' && (i == 0 || expr[i-1] != '\\')) inStr = !inStr;
                if (!inStr) {
                    if (c == ')') pd++; else if (c == '(') pd--; else if (c == ']') bkd++; else if (c == '[') bkd--;
                    if (pd == 0 && bkd == 0 && i >= (int)opStr.size() - 1 && expr.substr(i - opStr.size() + 1, opStr.size()) == opStr) {
                        if ((opStr == ">" || opStr == "<") && i + 1 < (int)expr.size() && expr[i+1] == '=') continue;
                        if (opStr == "-" && i == 0) continue;
                        std::string left = trim(expr.substr(0, i - opStr.size() + 1)), right = trim(expr.substr(i + 1));
                        if (!left.empty() && !right.empty()) { parseExpression(left); parseExpression(right); ops.push_back(Opcode(opName)); return; }
                    }
                }
            }
        }
        
        // Function call
        std::regex funcRx("^([a-zA-Z_]\\w*)\\s*\\((.*)\\)$"); std::smatch m;
        if (std::regex_match(expr, m, funcRx) && !isBuiltin(m[1])) { auto args = splitArgs(m[2]); for (const auto& a : args) parseExpression(a); ops.push_back(Opcode("CALL", m[1])); return; }
        
        // Parentheses
        if (expr[0] == '(' && expr.back() == ')') { int d = 0; bool bal = true; for (size_t i = 0; i < expr.size(); i++) { if (expr[i] == '(') d++; else if (expr[i] == ')') d--; if (d == 0 && i < expr.size() - 1) { bal = false; break; } } if (bal) { parseExpression(expr.substr(1, expr.size() - 2)); return; } }
        
        // Number
        bool isNum = true; bool hasDot = false; for (size_t i = 0; i < expr.size(); i++) { char c = expr[i]; if (c == '-' && i == 0) continue; if (c == '.' && !hasDot) { hasDot = true; continue; } if (!std::isdigit(c)) { isNum = false; break; } }
        if (isNum && !expr.empty()) { ops.push_back(Opcode("PUSH", expr)); return; }
        
        // Dict
        if (expr == "{}") { ops.push_back(Opcode("PUSH_DICT")); return; }
        if (expr[0] == '{' && expr.back() == '}') {
            ops.push_back(Opcode("PUSH_DICT"));
            std::string content = expr.substr(1, expr.size() - 2);
            if (!content.empty()) {
                std::string cur; int pd = 0, bd = 0; bool qt = false;
                auto addPair = [&](const std::string& pair) {
                    size_t col = std::string::npos; bool q = false;
                    for (size_t i = 0; i < pair.size(); i++) { if (pair[i] == '"') q = !q; if (pair[i] == ':' && !q) { col = i; break; } }
                    if (col != std::string::npos) {
                        std::string key = trim(pair.substr(0, col)), val = trim(pair.substr(col + 1));
                        parseExpression(val);
                        if (!key.empty() && key[0] == '"') key = key.substr(1, key.size() - 2);
                        ops.push_back(Opcode("PUSH", "\"" + key + "\"")); ops.push_back(Opcode("DICT_SET"));
                    }
                };
                for (char c : content) {
                    if (c == '"') qt = !qt; if (!qt) { if (c == '(') pd++; else if (c == ')') pd--; else if (c == '{') bd++; else if (c == '}') bd--; }
                    if (c == ',' && pd == 0 && bd == 0 && !qt) { addPair(trim(cur)); cur = ""; } else cur += c;
                }
                if (!trim(cur).empty()) addPair(trim(cur));
            }
            return;
        }
        
        // Array access
        if (expr.find('[') != std::string::npos) {
            size_t bs = expr.find('['); std::string arrName = expr.substr(0, bs);
            int d = 0; size_t be = std::string::npos;
            for (size_t i = bs; i < expr.size(); i++) { if (expr[i] == '[') d++; else if (expr[i] == ']') { d--; if (d == 0) { be = i; break; } } }
            std::string idx = expr.substr(bs + 1, be - bs - 1), rem = be + 1 < expr.size() ? expr.substr(be + 1) : "";
            
            if (idx.find(',') != std::string::npos && idx[0] != '"') {
                size_t cp = idx.find(','); parseExpression(trim(idx.substr(0, cp))); parseExpression(trim(idx.substr(cp + 1)));
                ops.push_back(Opcode("LOAD_IDX_2D", arrName));
            } else if (!rem.empty() && rem[0] == '[') {
                int d2 = 0; size_t be2 = std::string::npos;
                for (size_t i = 0; i < rem.size(); i++) { if (rem[i] == '[') d2++; else if (rem[i] == ']') { d2--; if (d2 == 0) { be2 = i; break; } } }
                parseExpression(idx); parseExpression(rem.substr(1, be2 - 1)); ops.push_back(Opcode("LOAD_IDX_2D", arrName));
            } else {
                parseExpression(idx); ops.push_back(Opcode("LOAD_IDX", arrName));
            }
            if (!rem.empty() && rem[0] == '.') { size_t fe = rem.find_first_of(".[", 1); ops.push_back(Opcode("GET_ATTR", rem.substr(1, fe == std::string::npos ? rem.size() - 1 : fe - 1))); }
            return;
        }
        
        // Struct access
        if (expr.find('.') != std::string::npos) {
            bool isNum = true; int dc = 0; for (char c : expr) { if (c == '.') dc++; else if (!std::isdigit(c) && c != '-') isNum = false; }
            if (!isNum || dc > 1) { size_t dp = expr.find('.'); ops.push_back(Opcode("LOAD", expr.substr(0, dp))); ops.push_back(Opcode("GET_ATTR", expr.substr(dp + 1))); return; }
        }
        
        // Variable
        ops.push_back(Opcode("LOAD", expr));
    }
    
    void compileInternal(const std::string& src) {
        for (const auto& lineRaw : smartSplit(cleanSource(src))) {
            std::string line = trim(lineRaw); if (line.empty()) continue;
            
            if (line.substr(0, 8) == "include ") { std::regex rx("include\\s+\"([^\"]+)\""); std::smatch m; if (std::regex_search(line, m, rx)) { std::ifstream f(baseDir + "/" + std::string(m[1])); if (f) { std::stringstream ss; ss << f.rdbuf(); compileInternal(ss.str()); } } continue; }
            if (line == "break") { ops.push_back(Opcode("JMP", loopStack.back().second)); continue; }
            if (line == "continue") { ops.push_back(Opcode("JMP", loopStack.back().first)); continue; }
            if (line.substr(0, 7) == "struct ") { std::regex rx("struct\\s+(\\w+)\\s*\\{(.*?)\\}"); std::smatch m; if (std::regex_search(line, m, rx)) { std::vector<std::string> flds; std::istringstream iss(m[2]); std::string f; while (std::getline(iss, f, ',')) { std::string t = trim(f); if (!t.empty()) flds.push_back(t); } structs[m[1]] = flds; } continue; }
            
            if (line.substr(0, 5) == "func ") {
                std::regex protoRx("func\\s+(\\w+)\\s*\\((.*?)\\)\\s*;?\\s*$"); std::smatch pm;
                if (std::regex_match(line, pm, protoRx) && line.find('{') == std::string::npos) continue;
                std::regex funcRx("func\\s+(\\w+)\\s*\\((.*?)\\)\\s*\\{(.*)\\}"); std::smatch m;
                if (std::regex_search(line, m, funcRx)) {
                    std::string fn = m[1], ls = getLabel("skip");
                    ops.push_back(Opcode("JMP", ls)); ops.push_back(Opcode("LABEL", fn));
                    bool oldIn = inFunction; inFunction = true;
                    auto args = splitArgs(m[2]); for (auto it = args.rbegin(); it != args.rend(); ++it) ops.push_back(Opcode("STORE", *it));
                    compileInternal(m[3]); ops.push_back(Opcode("RET")); ops.push_back(Opcode("LABEL", ls));
                    inFunction = oldIn;
                }
                continue;
            }
            if (line.substr(0, 6) == "return") { std::string e = trim(line.substr(6)); if (!e.empty()) { parseExpression(e); ops.push_back(Opcode("RET_VAL")); } else ops.push_back(Opcode("RET")); continue; }
            if (line.substr(0, 6) == "throw ") { parseExpression(line.substr(6)); ops.push_back(Opcode("THROW")); continue; }
            
            if (line.substr(0, 3) == "try") {
                std::regex rx1("try\\s*\\{(.*?)\\}\\s*catch\\s*\\((\\w+)\\)\\s*\\{(.*?)\\}"); std::smatch m1;
                if (std::regex_search(line, m1, rx1)) { std::string lc = getLabel("c"), le = getLabel("e"); ops.push_back(Opcode("TRY_START", lc)); compileInternal(m1[1]); ops.push_back(Opcode("TRY_END", le)); ops.push_back(Opcode("LABEL", lc)); ops.push_back(Opcode("CATCH_START")); ops.push_back(Opcode("STORE", m1[2])); compileInternal(m1[3]); ops.push_back(Opcode("CATCH_END")); ops.push_back(Opcode("LABEL", le)); continue; }
                std::regex rx2("try\\s*\\{(.*?)\\}\\s*catch\\s*\\{(.*?)\\}"); std::smatch m2;
                if (std::regex_search(line, m2, rx2)) { std::string lc = getLabel("c"), le = getLabel("e"); ops.push_back(Opcode("TRY_START", lc)); compileInternal(m2[1]); ops.push_back(Opcode("TRY_END", le)); ops.push_back(Opcode("LABEL", lc)); ops.push_back(Opcode("CATCH_START")); ops.push_back(Opcode("POP")); compileInternal(m2[2]); ops.push_back(Opcode("CATCH_END")); ops.push_back(Opcode("LABEL", le)); continue; }
            }
            if (line.substr(0, 7) == "global ") { std::regex rx("global\\s+(\\w+)\\s*=\\s*(.+)"); std::smatch m; if (std::regex_match(line, m, rx)) { parseExpression(m[2]); ops.push_back(Opcode("STORE_GLOBAL", m[1])); } continue; }
            if (line.substr(0, 6) == "print(") { std::regex rx("print\\((.*)\\)"); std::smatch m; if (std::regex_search(line, m, rx)) { auto args = splitArgs(m[1]); for (const auto& a : args) parseExpression(a); ops.push_back(Opcode("PRINT", (int)args.size())); } continue; }
            
            if (line.substr(0, 6) == "switch") {
                std::regex rx("switch\\s*\\((.*?)\\)\\s*\\{(.*)\\}"); std::smatch m;
                if (std::regex_search(line, m, rx)) {
                    parseExpression(m[1]); std::string les = getLabel("es");
                    std::regex crx("case\\s+(.*?):\\s*\\{(.*?)\\};"); std::sregex_iterator cb(std::string(m[2]).begin(), std::string(m[2]).end(), crx), ce;
                    loopStack.push_back({"", les});
                    for (auto it = cb; it != ce; ++it) { std::string lnc = getLabel("nc"); ops.push_back(Opcode("DUP")); parseExpression((*it)[1]); ops.push_back(Opcode("EQ")); ops.push_back(Opcode("JZ", lnc)); compileInternal((*it)[2]); ops.push_back(Opcode("JMP", les)); ops.push_back(Opcode("LABEL", lnc)); }
                    std::regex drx("default:\\s*\\{(.*?)\\};"); std::smatch dm; std::string body = m[2]; if (std::regex_search(body, dm, drx)) compileInternal(dm[1]);
                    ops.push_back(Opcode("LABEL", les)); ops.push_back(Opcode("POP")); loopStack.pop_back();
                }
                continue;
            }
            
            if (line.substr(0, 3) == "for") {
                std::regex rx("for\\s*\\((.*?)\\)\\s*\\{"); std::smatch m;
                if (std::regex_search(line, m, rx)) {
                    std::string h = m[1]; size_t bs = line.find('{'); auto [body, ab] = extractBracedBlock(line, bs);
                    std::vector<std::string> parts; std::istringstream iss(h); std::string p; while (std::getline(iss, p, ';')) parts.push_back(p);
                    if (parts.size() == 3) { std::string ls = getLabel("fs"), le = getLabel("fe"); loopStack.push_back({ls, le}); compileInternal(parts[0] + ";"); ops.push_back(Opcode("LABEL", ls)); parseExpression(parts[1]); ops.push_back(Opcode("JZ", le)); compileInternal(body); compileInternal(parts[2] + ";"); ops.push_back(Opcode("JMP", ls)); ops.push_back(Opcode("LABEL", le)); loopStack.pop_back(); }
                }
                continue;
            }
            
            if (line.substr(0, 5) == "while") {
                std::regex rx("while\\s*\\((.*?)\\)\\s*\\{"); std::smatch m;
                if (std::regex_search(line, m, rx)) {
                    size_t bs = line.find('{'); auto [body, ab] = extractBracedBlock(line, bs);
                    std::string ls = getLabel("ws"), le = getLabel("we"); loopStack.push_back({ls, le});
                    ops.push_back(Opcode("LABEL", ls)); parseExpression(m[1]); ops.push_back(Opcode("JZ", le)); compileInternal(body); ops.push_back(Opcode("JMP", ls)); ops.push_back(Opcode("LABEL", le)); loopStack.pop_back();
                }
                continue;
            }
            
            if (line.substr(0, 2) == "if") {
                std::regex rx("if\\s*\\((.*?)\\)\\s*\\{"); std::smatch m;
                if (std::regex_search(line, m, rx)) {
                    size_t bs = line.find('{'); auto [body, ab] = extractBracedBlock(line, bs);
                    std::string lec = getLabel("if_end"), lnc = getLabel("next");
                    parseExpression(m[1]); ops.push_back(Opcode("JZ", lnc)); compileInternal(body); ops.push_back(Opcode("JMP", lec)); ops.push_back(Opcode("LABEL", lnc));
                    std::string rem = ab < line.size() ? trim(line.substr(ab)) : "";
                    while (true) {
                        if (rem.substr(0, 7) == "else if") {
                            std::regex erx("else\\s+if\\s*\\((.*?)\\)\\s*\\{"); std::smatch em;
                            if (std::regex_search(rem, em, erx)) {
                                size_t ebs = rem.find('{'); auto [ebody, eab] = extractBracedBlock(rem, ebs);
                                std::string lne = getLabel("elif_next"); parseExpression(em[1]); ops.push_back(Opcode("JZ", lne)); compileInternal(ebody); ops.push_back(Opcode("JMP", lec)); ops.push_back(Opcode("LABEL", lne));
                                rem = eab < rem.size() ? trim(rem.substr(eab)) : ""; continue;
                            }
                        } else if (rem.substr(0, 4) == "else") {
                            std::regex erx("else\\s*\\{"); std::smatch em;
                            if (std::regex_search(rem, em, erx)) { size_t ebs = rem.find('{'); auto [ebody, eab] = extractBracedBlock(rem, ebs); compileInternal(ebody); }
                        }
                        break;
                    }
                    ops.push_back(Opcode("LABEL", lec));
                }
                continue;
            }
            
            // Shorthand operators
            std::vector<std::pair<std::string, std::string>> shOps = {{"+=", "ADD"}, {"-=", "SUB"}, {"*=", "MUL"}, {"/=", "DIV"}, {"%=", "MOD"}};
            bool foundSh = false;
            for (const auto& [opStr, opCode] : shOps) {
                size_t pos = line.find(opStr);
                if (pos != std::string::npos && line.substr(0, 2) != "if" && line.substr(0, 5) != "while" && line.substr(0, 3) != "for") {
                    std::string tgt = trim(line.substr(0, pos)), ex = trim(line.substr(pos + 2));
                    if (tgt.empty() || tgt.find('=') != std::string::npos) continue;
                    if (tgt.find('.') != std::string::npos && tgt.find('[') == std::string::npos) {
                        size_t dp = tgt.find('.'); std::string o = tgt.substr(0, dp), f = tgt.substr(dp + 1);
                        ops.push_back(Opcode("LOAD", o)); ops.push_back(Opcode("GET_ATTR", f)); parseExpression(ex); ops.push_back(Opcode(opCode)); ops.push_back(Opcode("LOAD", o)); ops.push_back(Opcode("SET_ATTR", f));
                    } else if (tgt.find('[') != std::string::npos) {
                        size_t bs = tgt.find('['); std::string an = tgt.substr(0, bs); int d = 0; size_t be = 0; for (size_t i = bs; i < tgt.size(); i++) { if (tgt[i] == '[') d++; else if (tgt[i] == ']') { d--; if (d == 0) { be = i; break; } } } std::string idx = tgt.substr(bs + 1, be - bs - 1);
                        ops.push_back(Opcode("LOAD", an)); parseExpression(idx); ops.push_back(Opcode("LOAD_IDX", an)); parseExpression(ex); ops.push_back(Opcode(opCode)); parseExpression(idx); ops.push_back(Opcode("STORE_IDX", an));
                    } else { ops.push_back(Opcode("LOAD", tgt)); parseExpression(ex); ops.push_back(Opcode(opCode)); ops.push_back(Opcode("STORE", tgt)); }
                    foundSh = true; break;
                }
            }
            if (foundSh) continue;
            
            // Assignment
            if (line.find('=') != std::string::npos && line.substr(0, 2) != "if" && line.substr(0, 5) != "while" && line.substr(0, 3) != "for" && line.substr(0, 6) != "global" && line.substr(0, 5) != "print") {
                size_t ep = line.find('=');
                if (!((ep > 0 && (line[ep-1] == '!' || line[ep-1] == '<' || line[ep-1] == '>' || line[ep-1] == '=')) || (ep + 1 < line.size() && line[ep+1] == '='))) {
                    std::string tgt = trim(line.substr(0, ep)), ex = trim(line.substr(ep + 1));
                    if (!tgt.empty() && !ex.empty()) {
                        if (tgt.find('.') != std::string::npos && tgt.find('[') == std::string::npos) {
                            size_t dp = tgt.find('.'); parseExpression(ex); ops.push_back(Opcode("LOAD", tgt.substr(0, dp))); ops.push_back(Opcode("SET_ATTR", tgt.substr(dp + 1)));
                        } else if (tgt.find('[') != std::string::npos) {
                            size_t bs = tgt.find('['); std::string an = tgt.substr(0, bs); int d = 0; size_t be = 0; for (size_t i = bs; i < tgt.size(); i++) { if (tgt[i] == '[') d++; else if (tgt[i] == ']') { d--; if (d == 0) { be = i; break; } } } std::string idx = tgt.substr(bs + 1, be - bs - 1); std::string rem = be + 1 < tgt.size() ? tgt.substr(be + 1) : "";
                            if (idx.find(',') != std::string::npos && idx[0] != '"') { size_t cp = idx.find(','); parseExpression(ex); parseExpression(trim(idx.substr(0, cp))); parseExpression(trim(idx.substr(cp + 1))); ops.push_back(Opcode("STORE_IDX_2D", an)); }
                            else if (!rem.empty() && rem[0] == '[') { int d2 = 0; size_t be2 = 0; for (size_t i = 0; i < rem.size(); i++) { if (rem[i] == '[') d2++; else if (rem[i] == ']') { d2--; if (d2 == 0) { be2 = i; break; } } } parseExpression(ex); parseExpression(idx); parseExpression(rem.substr(1, be2 - 1)); ops.push_back(Opcode("STORE_IDX_2D", an)); }
                            else if (!rem.empty() && rem[0] == '.') { parseExpression(ex); parseExpression(idx); ops.push_back(Opcode("LOAD_IDX", an)); ops.push_back(Opcode("SET_ATTR", rem.substr(1))); }
                            else { parseExpression(ex); parseExpression(idx); ops.push_back(Opcode("STORE_IDX", an)); }
                        } else { parseExpression(ex); ops.push_back(Opcode("STORE", tgt)); }
                    }
                }
                continue;
            }
            
            // Function call as statement
            std::regex fcRx("^[a-zA-Z_]\\w*\\s*\\(.*\\)$");
            if (std::regex_match(line, fcRx)) { parseExpression(line); ops.push_back(Opcode("POP")); }
        }
    }
    
    void collectPrototypes(const std::string& src) {
        for (const auto& lineRaw : smartSplit(cleanSource(src))) {
            std::string line = trim(lineRaw);
            if (line.substr(0, 8) == "include ") { std::regex rx("include\\s+\"([^\"]+)\""); std::smatch m; if (std::regex_search(line, m, rx)) { std::ifstream f(baseDir + "/" + std::string(m[1])); if (f) { std::stringstream ss; ss << f.rdbuf(); collectPrototypes(ss.str()); } } continue; }
            std::regex protoRx("func\\s+(\\w+)\\s*\\((.*?)\\)\\s*;?\\s*$"); std::smatch pm;
            if (std::regex_match(line, pm, protoRx) && line.find('{') == std::string::npos) { if (!functionPrototypes.count(pm[1])) functionPrototypes[pm[1]] = splitArgs(pm[2]); continue; }
            std::regex funcRx("func\\s+(\\w+)\\s*\\((.*?)\\)\\s*\\{"); std::smatch m;
            if (std::regex_search(line, m, funcRx)) { functionPrototypes[m[1]] = splitArgs(m[2]); functionDefined.insert(m[1]); }
        }
    }
    
public:
    std::vector<Opcode> compile(const std::string& src, const std::string& bd = ".") {
        baseDir = bd;
        collectPrototypes(src);
        compileInternal(src);
        for (const auto& [n, a] : functionPrototypes) if (!functionDefined.count(n)) throw AscensionException("Funzione non definita: " + n, "LinkerError");
        return ops;
    }
    
    const std::unordered_map<std::string, std::vector<std::string>>& getStructs() const { return structs; }
};

} // namespace asc
#endif
