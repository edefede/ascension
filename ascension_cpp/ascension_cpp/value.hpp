/*
 * ASCENSION C++ - value.hpp
 * Tipi di dato dinamici per la VM
 */
#ifndef ASCENSION_VALUE_HPP
#define ASCENSION_VALUE_HPP

#include <variant>
#include <string>
#include <map>
#include <memory>
#include <cmath>

namespace asc {

struct AscensionNull {
    bool operator==(const AscensionNull&) const { return true; }
    bool operator!=(const AscensionNull&) const { return false; }
};

using Dict = std::map<std::string, struct Value>;

struct Value {
    std::variant<AscensionNull, int64_t, double, std::string, std::shared_ptr<Dict>> data;
    
    Value() : data(AscensionNull{}) {}
    Value(std::nullptr_t) : data(AscensionNull{}) {}
    Value(int v) : data(static_cast<int64_t>(v)) {}
    Value(int64_t v) : data(v) {}
    Value(double v) : data(v) {}
    Value(const std::string& v) : data(v) {}
    Value(const char* v) : data(std::string(v)) {}
    Value(std::shared_ptr<Dict> v) : data(v) {}
    
    bool isNull() const { return std::holds_alternative<AscensionNull>(data); }
    bool isInt() const { return std::holds_alternative<int64_t>(data); }
    bool isDouble() const { return std::holds_alternative<double>(data); }
    bool isNumber() const { return isInt() || isDouble(); }
    bool isString() const { return std::holds_alternative<std::string>(data); }
    bool isDict() const { return std::holds_alternative<std::shared_ptr<Dict>>(data); }
    
    int64_t asInt() const {
        if (isInt()) return std::get<int64_t>(data);
        if (isDouble()) return static_cast<int64_t>(std::get<double>(data));
        return 0;
    }
    
    double asDouble() const {
        if (isDouble()) return std::get<double>(data);
        if (isInt()) return static_cast<double>(std::get<int64_t>(data));
        return 0.0;
    }
    
    std::string asString() const {
        if (isString()) return std::get<std::string>(data);
        if (isNull()) return "NULL";
        if (isInt()) return std::to_string(std::get<int64_t>(data));
        if (isDouble()) {
            double d = std::get<double>(data);
            if (d == std::floor(d)) return std::to_string(static_cast<int64_t>(d));
            return std::to_string(d);
        }
        return "";
    }
    
    std::shared_ptr<Dict>& asDict() { return std::get<std::shared_ptr<Dict>>(data); }
    const std::shared_ptr<Dict>& asDict() const { return std::get<std::shared_ptr<Dict>>(data); }
    
    bool toBool() const {
        if (isNull()) return false;
        if (isInt()) return std::get<int64_t>(data) != 0;
        if (isDouble()) return std::get<double>(data) != 0.0;
        if (isString()) return !std::get<std::string>(data).empty();
        if (isDict()) return true;
        return false;
    }
    
    bool operator==(const Value& o) const {
        if (isNull() && o.isNull()) return true;
        if (isNull() || o.isNull()) return false;
        if (isNumber() && o.isNumber()) return asDouble() == o.asDouble();
        if (isString() && o.isString()) return std::get<std::string>(data) == std::get<std::string>(o.data);
        return false;
    }
    bool operator!=(const Value& o) const { return !(*this == o); }
    bool operator<(const Value& o) const { return isNumber() && o.isNumber() && asDouble() < o.asDouble(); }
    bool operator>(const Value& o) const { return isNumber() && o.isNumber() && asDouble() > o.asDouble(); }
    bool operator<=(const Value& o) const { return *this < o || *this == o; }
    bool operator>=(const Value& o) const { return *this > o || *this == o; }
};

struct Opcode {
    std::string op;
    std::string arg;
    int argCount = 0;
    Opcode(const std::string& o) : op(o) {}
    Opcode(const std::string& o, const std::string& a) : op(o), arg(a) {}
    Opcode(const std::string& o, int c) : op(o), argCount(c) {}
};

class AscensionException : public std::exception {
public:
    std::string message, errorType;
    AscensionException(const std::string& msg, const std::string& type = "Error") : message(msg), errorType(type) {}
    const char* what() const noexcept override { return message.c_str(); }
};

} // namespace asc
#endif
