/*
 * ASCENSION C++ - mod_network.hpp
 * Modulo Networking (TCP/UDP Sockets)
 * Compilare con: -DHAS_NETWORK
 */
#ifndef ASCENSION_MOD_NETWORK_HPP
#define ASCENSION_MOD_NETWORK_HPP

#include "../value.hpp"
#include <unordered_map>
#include <cstring>

#ifdef HAS_NETWORK

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef int socklen_t;
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <netdb.h>
    #include <unistd.h>
    #include <fcntl.h>
    #define SOCKET int
    #define INVALID_SOCKET -1
    #define SOCKET_ERROR -1
    #define closesocket close
#endif

namespace asc {

class NetworkModule {
public:
    std::unordered_map<int64_t, SOCKET> sockets;
    int64_t idCounter = 0;
    bool initialized = false;

    static constexpr int    HTTP_TIMEOUT_SEC  = 10;
    static constexpr size_t MAX_HTTP_RESPONSE = 8 * 1024 * 1024;
    static constexpr int    MAX_RECV_BYTES    = 1024 * 1024;

    NetworkModule() {
#ifdef _WIN32
        WSADATA wsaData;
        initialized = (WSAStartup(MAKEWORD(2, 2), &wsaData) == 0);
#else
        initialized = true;
#endif
    }

    ~NetworkModule() {
        for (auto& [id, sock] : sockets) closesocket(sock);
#ifdef _WIN32
        if (initialized) WSACleanup();
#endif
    }

    // Risolve hostname/IP (IPv4) con getaddrinfo. Ritorna false se fallisce.
    static bool resolve(const std::string& host, int port, sockaddr_in& out) {
        addrinfo hints{}, *res = nullptr;
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;
        if (getaddrinfo(host.c_str(), nullptr, &hints, &res) != 0 || !res) return false;
        out = *(sockaddr_in*)res->ai_addr;
        out.sin_port = htons((uint16_t)port);
        freeaddrinfo(res);
        return true;
    }

    static void setTimeout(SOCKET s, int seconds) {
#ifdef _WIN32
        DWORD ms = seconds * 1000;
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, (const char*)&ms, sizeof(ms));
        setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, (const char*)&ms, sizeof(ms));
#else
        timeval tv{seconds, 0};
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
#endif
    }

    Value socketOpen(const std::string& type, const std::string&) {
        if (!initialized) return Value(nullptr);
        int sockType = (type == "TCP") ? SOCK_STREAM : SOCK_DGRAM;
        SOCKET s = socket(AF_INET, sockType, 0);
        if (s == INVALID_SOCKET) return Value(nullptr);
        sockets[++idCounter] = s;
        return Value(idCounter);
    }

    Value socketBind(int64_t sid, const std::string& ip, int port) {
        if (!sockets.count(sid) || port < 0 || port > 65535) return Value(nullptr);
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons((uint16_t)port);
        if (ip == "0.0.0.0") addr.sin_addr.s_addr = INADDR_ANY;
        else if (inet_pton(AF_INET, ip.c_str(), &addr.sin_addr) != 1) return Value(nullptr);
        if (bind(sockets[sid], (sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR)
            return Value(nullptr);
        return Value(1);
    }

    Value socketListen(int64_t sid, int backlog) {
        if (!sockets.count(sid)) return Value(nullptr);
        if (listen(sockets[sid], backlog) == SOCKET_ERROR) return Value(nullptr);
        return Value(1);
    }

    Value socketAccept(int64_t sid) {
        if (!sockets.count(sid)) return Value(nullptr);
        sockaddr_in clientAddr{};
        socklen_t addrLen = sizeof(clientAddr);
        SOCKET client = accept(sockets[sid], (sockaddr*)&clientAddr, &addrLen);
        if (client == INVALID_SOCKET) return Value(nullptr);
        sockets[++idCounter] = client;
        return Value(idCounter);
    }

    Value socketConnect(int64_t sid, const std::string& host, int port) {
        if (!sockets.count(sid) || port < 0 || port > 65535) return Value(nullptr);
        sockaddr_in addr{};
        if (!resolve(host, port, addr)) return Value(nullptr);
        if (connect(sockets[sid], (sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR)
            return Value(nullptr);
        return Value(1);
    }

    Value socketSend(int64_t sid, const std::string& data) {
        if (!sockets.count(sid)) return Value(nullptr);
        long sent = send(sockets[sid], data.c_str(), data.size(), 0);
        if (sent < 0) return Value(nullptr);
        return Value(static_cast<int64_t>(sent));
    }

    Value socketRecv(int64_t sid, int maxBytes) {
        if (!sockets.count(sid) || maxBytes <= 0) return Value(nullptr);
        if (maxBytes > MAX_RECV_BYTES) maxBytes = MAX_RECV_BYTES;
        std::string buf(maxBytes, '\0');
        long received = recv(sockets[sid], &buf[0], maxBytes, 0);
        if (received <= 0) return Value(nullptr);
        buf.resize(received);
        return Value(buf);
    }

    Value socketClose(int64_t sid) {
        if (!sockets.count(sid)) return Value(nullptr);
        closesocket(sockets[sid]);
        sockets.erase(sid);
        return Value(1);
    }

    Value getIP(const std::string& hostname) {
        sockaddr_in addr{};
        if (!resolve(hostname, 0, addr)) return Value("");
        char buf[INET_ADDRSTRLEN] = {0};
        if (!inet_ntop(AF_INET, &addr.sin_addr, buf, sizeof(buf))) return Value("");
        return Value(std::string(buf));
    }

    Value httpGet(const std::string& url) { return httpRequest("GET", url, ""); }
    Value httpPost(const std::string& url, const std::string& data) { return httpRequest("POST", url, data); }

private:
    Value httpRequest(const std::string& method, const std::string& url, const std::string& data) {
        std::string host, path = "/";
        int port = 80;

        std::string urlCopy = url;
        if (urlCopy.substr(0, 7) == "http://") urlCopy = urlCopy.substr(7);
        else if (urlCopy.substr(0, 8) == "https://")
            throw AscensionException("https:// non supportato (nessun TLS): usare http://", "NetworkError");

        size_t slashPos = urlCopy.find('/');
        if (slashPos != std::string::npos) {
            host = urlCopy.substr(0, slashPos);
            path = urlCopy.substr(slashPos);
        } else {
            host = urlCopy;
        }

        size_t colonPos = host.find(':');
        if (colonPos != std::string::npos) {
            try { port = std::stoi(host.substr(colonPos + 1)); }
            catch (...) { return Value(""); }
            if (port < 1 || port > 65535) return Value("");
            host = host.substr(0, colonPos);
        }
        if (host.empty()) return Value("");

        sockaddr_in addr{};
        if (!resolve(host, port, addr)) return Value("");

        SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
        if (s == INVALID_SOCKET) return Value("");
        setTimeout(s, HTTP_TIMEOUT_SEC);

        if (connect(s, (sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR) {
            closesocket(s);
            return Value("");
        }

        std::string request = method + " " + path + " HTTP/1.0\r\nHost: " + host + "\r\n";
        if (method == "POST")
            request += "Content-Type: application/x-www-form-urlencoded\r\nContent-Length: " +
                       std::to_string(data.size()) + "\r\n";
        request += "Connection: close\r\n\r\n" + data;

        if (send(s, request.c_str(), request.size(), 0) < 0) {
            closesocket(s);
            return Value("");
        }

        std::string response;
        char buf[4096];
        long received;
        while ((received = recv(s, buf, sizeof(buf), 0)) > 0) {
            response.append(buf, received);
            if (response.size() > MAX_HTTP_RESPONSE) break;
        }
        closesocket(s);

        size_t bodyStart = response.find("\r\n\r\n");
        if (bodyStart != std::string::npos)
            return Value(response.substr(bodyStart + 4));
        return Value(response);
    }
};

} // namespace asc

#else // !HAS_NETWORK - Stub

namespace asc {

class NetworkModule {
public:
    Value socketOpen(const std::string&, const std::string&) { return Value(nullptr); }
    Value socketBind(int64_t, const std::string&, int) { return Value(nullptr); }
    Value socketListen(int64_t, int) { return Value(nullptr); }
    Value socketAccept(int64_t) { return Value(nullptr); }
    Value socketConnect(int64_t, const std::string&, int) { return Value(nullptr); }
    Value socketSend(int64_t, const std::string&) { return Value(nullptr); }
    Value socketRecv(int64_t, int) { return Value(nullptr); }
    Value socketClose(int64_t) { return Value(nullptr); }
    Value getIP(const std::string&) { return Value(""); }
    Value httpGet(const std::string&) { return Value(""); }
    Value httpPost(const std::string&, const std::string&) { return Value(""); }
};

} // namespace asc

#endif // HAS_NETWORK
#endif // ASCENSION_MOD_NETWORK_HPP
