/*
 * ASCENSION C++ - mod_curses.hpp
 * Modulo Curses (TUI)
 * Compilare con: -DHAS_CURSES -lncurses
 */
#ifndef ASCENSION_MOD_CURSES_HPP
#define ASCENSION_MOD_CURSES_HPP

#include "../value.hpp"

#ifdef HAS_CURSES
#include <ncurses.h>

namespace asc {

class CursesModule {
public:
    WINDOW* screen = nullptr;
    
    Value init() {
        screen = initscr();
        if (screen) {
            noecho();
            cbreak();
            keypad(screen, TRUE);
            return Value(1);
        }
        return Value(0);
    }
    
    Value end() {
        if (screen) {
            nocbreak();
            echo();
            endwin();
            screen = nullptr;
            return Value(1);
        }
        return Value(0);
    }
    
    Value clear() {
        if (screen) { ::clear(); return Value(1); }
        return Value(0);
    }
    
    Value refresh() {
        if (screen) { ::refresh(); return Value(1); }
        return Value(0);
    }
    
    Value move(int y, int x) {
        if (screen) { ::move(y, x); return Value(1); }
        return Value(0);
    }
    
    Value write(const std::string& s) {
        if (screen) { addstr(s.c_str()); return Value(1); }
        return Value(0);
    }
    
    Value readKey() {
        if (screen) return Value(static_cast<int64_t>(getch()));
        return Value(-1);
    }
    
    Value getMaxY() {
        if (screen) return Value(static_cast<int64_t>(LINES));
        return Value(0);
    }
    
    Value getMaxX() {
        if (screen) return Value(static_cast<int64_t>(COLS));
        return Value(0);
    }
    
    ~CursesModule() { if (screen) end(); }
};

} // namespace asc

#else // !HAS_CURSES - Stub implementation

namespace asc {

class CursesModule {
public:
    Value init() { return Value(0); }
    Value end() { return Value(0); }
    Value clear() { return Value(0); }
    Value refresh() { return Value(0); }
    Value move(int, int) { return Value(0); }
    Value write(const std::string&) { return Value(0); }
    Value readKey() { return Value(-1); }
    Value getMaxY() { return Value(0); }
    Value getMaxX() { return Value(0); }
};

} // namespace asc

#endif // HAS_CURSES
#endif // ASCENSION_MOD_CURSES_HPP
