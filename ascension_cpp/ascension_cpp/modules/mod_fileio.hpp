/*
 * ASCENSION C++ - mod_fileio.hpp
 * Modulo File I/O
 */
#ifndef ASCENSION_MOD_FILEIO_HPP
#define ASCENSION_MOD_FILEIO_HPP

#include <fstream>
#include <sstream>
#include <unordered_map>
#include <memory>
#include "../value.hpp"

namespace asc {

class FileIOModule {
public:
    std::unordered_map<int64_t, std::shared_ptr<std::fstream>> handles;
    int64_t idCounter = 0;
    
    Value fileOpen(const std::string& filename, const std::string& mode) {
        std::ios_base::openmode om = std::ios_base::in;
        if (mode == "w") om = std::ios_base::out | std::ios_base::trunc;
        else if (mode == "a") om = std::ios_base::out | std::ios_base::app;
        else if (mode == "r+") om = std::ios_base::in | std::ios_base::out;
        
        auto f = std::make_shared<std::fstream>(filename, om);
        if (f->is_open()) {
            handles[++idCounter] = f;
            return Value(idCounter);
        }
        return Value(nullptr);
    }
    
    Value fileWrite(int64_t hid, const std::string& content) {
        if (handles.count(hid)) {
            *handles[hid] << content;
            handles[hid]->flush();
            return Value(1);
        }
        return Value(nullptr);
    }
    
    Value fileReadLine(int64_t hid) {
        if (handles.count(hid)) {
            std::string line;
            if (std::getline(*handles[hid], line)) return Value(line + "\n");
            return Value("");
        }
        return Value(nullptr);
    }
    
    Value fileReadAll(int64_t hid) {
        if (handles.count(hid)) {
            std::stringstream ss;
            ss << handles[hid]->rdbuf();
            return Value(ss.str());
        }
        return Value(nullptr);
    }
    
    Value fileClose(int64_t hid) {
        if (handles.count(hid)) {
            handles[hid]->close();
            handles.erase(hid);
            return Value(1);
        }
        return Value(nullptr);
    }
};

} // namespace asc
#endif
