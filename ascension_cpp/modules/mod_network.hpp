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
    
    Value socketOpen(const std::string& type, const std::string& proto) {
        if (!initialized) return Value(nullptr);
        int sockType = (type == "TCP") ? SOCK_STREAM : SOCK_DGRAM;
        SOCKET s = socket(AF_INET, sockType, 0);
        if (s == INVALID_SOCKET) return Value(nullptr);
        sockets[++idCounter] = s;
        return Value(idCounter);
    }
    
    Value socketBind(int64_t sid, const std::string& ip, int port) {
        if (!sockets.count(sid)) return Value(nullptr);
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = ip == "0.0.0.0" ? INADDR_ANY : inet_addr(ip.c_str());
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
    
    Value socketConnect(int64_t sid, const std::string& ip, int port) {
        if (!sockets.count(sid)) return Value(nullptr);
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = inet_addr(ip.c_str());
        if (connect(sockets[sid], (sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR)
            return Value(nullptr);
        return Value(1);
    }
    
    Value socketSend(int64_t sid, const std::string& data) {
        if (!sockets.count(sid)) return Value(nullptr);
        int sent = send(sockets[sid], data.c_str(), data.size(), 0);
        if (sent == SOCKET_ERROR) return Value(nullptr);
        return Value(static_cast<int64_t>(sent));
    }
    
    Value socketRecv(int64_t sid, int maxBytes) {
        if (!sockets.count(sid)) return Value(nullptr);
        std::string buf(maxBytes, '\0');
        int received = recv(sockets[sid], &buf[0], maxBytes, 0);
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
        hostent* he = gethostbyname(hostname.c_str());
        if (!he) return Value("");
        in_addr* addr = (in_addr*)he->h_addr;
        return Value(std::string(inet_ntoa(*addr)));
    }
    
    Value httpGet(const std::string& url) {
        // Parse URL
        std::string host, path = "/";
        int port = 80;
        
        std::string urlCopy = url;
        if (urlCopy.substr(0, 7) == "http://") urlCopy = urlCopy.substr(7);
        else if (urlCopy.substr(0, 8) == "https://") { urlCopy = urlCopy.substr(8); port = 443; }
        
        size_t slashPos = urlCopy.find('/');
        if (slashPos != std::string::npos) {
            host = urlCopy.substr(0, slashPos);
            path = urlCopy.substr(slashPos);
        } else {
            host = urlCopy;
        }
        
        size_t colonPos = host.find(':');
        if (colonPos != std::string::npos) {
            port = std::stoi(host.substr(colonPos + 1));
            host = host.substr(0, colonPos);
        }
        
        // Resolve hostname
        hostent* he = gethostbyname(host.c_str());
        if (!he) return Value("");
        
        // Create socket
        SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
        if (s == INVALID_SOCKET) return Value("");
        
        // Connect
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        memcpy(&addr.sin_addr, he->h_addr, he->h_length);
        
        if (connect(s, (sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR) {
            closesocket(s);
            return Value("");
        }
        
        // Send HTTP request
        std::string request = "GET " + path + " HTTP/1.0\r\nHost: " + host + "\r\nConnection: close\r\n\r\n";
        send(s, request.c_str(), request.size(), 0);
        
        // Receive response
        std::string response;
        char buf[4096];
        int received;
        while ((received = recv(s, buf, sizeof(buf) - 1, 0)) > 0) {
            buf[received] = '\0';
            response += buf;
        }
        closesocket(s);
        
        // Extract body (skip headers)
        size_t bodyStart = response.find("\r\n\r\n");
        if (bodyStart != std::string::npos) {
            return Value(response.substr(bodyStart + 4));
        }
        return Value(response);
    }
    
    Value httpPost(const std::string& url, const std::string& data) {
        // Parse URL
        std::string host, path = "/";
        int port = 80;
        
        std::string urlCopy = url;
        if (urlCopy.substr(0, 7) == "http://") urlCopy = urlCopy.substr(7);
        else if (urlCopy.substr(0, 8) == "https://") { urlCopy = urlCopy.substr(8); port = 443; }
        
        size_t slashPos = urlCopy.find('/');
        if (slashPos != std::string::npos) {
            host = urlCopy.substr(0, slashPos);
            path = urlCopy.substr(slashPos);
        } else {
            host = urlCopy;
        }
        
        size_t colonPos = host.find(':');
        if (colonPos != std::string::npos) {
            port = std::stoi(host.substr(colonPos + 1));
            host = host.substr(0, colonPos);
        }
        
        hostent* he = gethostbyname(host.c_str());
        if (!he) return Value("");
        
        SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
        if (s == INVALID_SOCKET) return Value("");
        
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        memcpy(&addr.sin_addr, he->h_addr, he->h_length);
        
        if (connect(s, (sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR) {
            closesocket(s);
            return Value("");
        }
        
        std::string request = "POST " + path + " HTTP/1.0\r\nHost: " + host + 
            "\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: " + 
            std::to_string(data.size()) + "\r\nConnection: close\r\n\r\n" + data;
        send(s, request.c_str(), request.size(), 0);
        
        std::string response;
        char buf[4096];
        int received;
        while ((received = recv(s, buf, sizeof(buf) - 1, 0)) > 0) {
            buf[received] = '\0';
            response += buf;
        }
        closesocket(s);
        
        size_t bodyStart = response.find("\r\n\r\n");
        if (bodyStart != std::string::npos) {
            return Value(response.substr(bodyStart + 4));
        }
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
