import math
from socket import *

from datetime import datetime as dt
import sys
import os

def if_modified_since_header(request_lines):
    datetime = ""
    success = False
    for l in request_lines:
        if l.startswith("If-Modified-Since:"):
            val = l[19:]
            try:
                datetime = dt.strptime(val, "%a, %d %b %Y %H:%M:%S %Z")
                success = True
            except ValueError as _: 
                print("Failed to parse value in header If-Modified-Since:")
                success = False


def send_HTTP(conn, code, data="", last_mod_timestamp=""):
    response = ""
    match code:
        case "200":
            datetime = dt.fromtimestamp(last_mod_timestamp)
            fmt = dt.strftime(datetime, "%a, %d %b %Y %H:%M:%S %Z")
            last_mod_header = "Last-Modified: " + fmt + "GMT\r\n"
            response = "HTTP/1.1 200 OK\r\n" + last_mod_header + "\r\n" + data
        case "304":
            # Chrome won't let me see raw response headers if it's just status line, so I add this
            # Without raw response headers, status code only says "304 OK"; raw header is correct
            server_header = "Server: Python\r\n" 
            response = "HTTP/1.1 304 Not Modified\r\n" + server_header + "\r\n"
        case "400":
            html400 = "<!DOCTYPE html><html><h1>400 Bad Request &#x1F635</h1></html>"
            response = "HTTP/1.1 400 Bad Request\r\n" + "\r\n" + html400
        case "404":
            html404 = "<!DOCTYPE html><html><h1>404 Not Found &#x1F937</h1></html>"
            response = "HTTP/1.1 404 Not Found\r\n" + "\r\n" + html404
        case "408":
            html408 = "<!DOCTYPE html><html><h1>408 Request Timeout &#x23F1</h1></html>"
            response = "HTTP/1.1 408 Request Timeout\r\n" + "\r\n" + html408

    conn.sendall(response.encode())
    conn.close()

str400 = "400 Bad Request"
str404 = "404 Not Found"
str408 = "408 Request Timeout"

if len(sys.argv) <= 1:
    print('enter port number')
    sys.exit(2)

tcpServerSocket = socket(AF_INET, SOCK_STREAM)
tcpServerPort = int(sys.argv[1])
tcpServerHost = "127.0.0.1"
tcpServerSocket.bind((tcpServerHost, tcpServerPort))
print(tcpServerPort)
tcpServerSocket.listen(10)

while True:
    print('Ready to serve...')
    tcpClientSocket, address = tcpServerSocket.accept()
    print('Received a connection from', address)
    message = tcpClientSocket.recv(4096)
    message = message.decode()
    print("message:", message)
    if(message == ''):
        continue

    print("message.split()[1]:", message.split()[1])
    filename = message.split()[1].partition("/")[2]
    print("filename:", filename)
    fileExists = "false"
    fileToUse = "/" + filename
    print("fileToUse:", fileToUse)

    if_modified_since = if_modified_since_header(message.split('\r\n'))

    try:
        f = open("WEB/" + fileToUse[1:], "rb")
        outputData = f.read()
        print(outputData)
        f.close()
        fileExists = "true"

        tcpClientSocket.send("HTTP/1.1 200 OK\r\n".encode())
        tcpClientSocket.send("Content-Type:text/html\r\n\r\n".encode())
        tcpClientSocket.send(outputData)
        print('Read from cache')
        
        request_lines = message.split('\r\n')
        start_line = request_lines[0]
        start_line_split = start_line.split()
        http_method, request_target, http_version = start_line_split
        file_to_open = request_target.lstrip('/')
        # if file_to_open == "": # open index.html if user asks for root resource "/"
        #     file_to_open = "index.html"
        try:
            send_304 = False
            with open(file_to_open, "r") as file:
                data = file.read()
                if os.path.exists(file_to_open):
                    last_mod_timestamp = math.floor(os.path.getmtime(file_to_open))
                if if_modified_since is not None:
                    if last_mod_timestamp <= if_modified_since:
                        send_304 = True

            send_HTTP(tcpClientSocket, "200" if not send_304 else "304", data, last_mod_timestamp)
        except FileNotFoundError as e:
            print(f"{str404}. File {file_to_open} does not exist on server.")
            send_HTTP(tcpClientSocket, "404")
        except OSError as e:
            print(f"{str400}. File to open has an invalid filename.")
            send_HTTP(tcpClientSocket, "400")

    except IOError:
        if fileExists == "false":
            c = socket(AF_INET, SOCK_STREAM)
            hostName = filename.replace("www.", "", 1)
            print("hostn:", hostName)

            try:
                serverName = hostName.partition("/")[0]
                serverPort = 12000
                print((serverName, serverPort))
                c.connect((serverName, serverPort))
                askFile = ''.join(filename.partition('/')[1:])
                print("askFile:", askFile)

                fileObj = c.makefile('rwb', 0)
                fileObj.write("GET ".encode() + askFile.encode() + "HTTP/1.0\r\nHost: ".encode() + serverName.encode() + "\r\n\r\n".encode())

                serverResponse = fileObj.read()
                filename = "WEB/" + filename
                fileSplit = filename.split('/')
                for i in range(0, len(fileSplit) - 1):
                    if not os.path.exists("/".join(fileSplit[0:i+1])):
                        os.makedirs("/".join(fileSplit[0:i+1]))
                
                tempFile = open(filename, "wb")
                print(serverResponse)
                serverResponse = serverResponse.split(b'\r\n\r\n')[1]
                print(serverResponse)
                tempFile.write(serverResponse)
                tempFile.close()
                tcpClientSocket.send("HTTP/1.1 200 OK\r\n".encode())
                tcpClientSocket.send("Content-Type:text/html\r\n\r\n".encode())
                tcpClientSocket.send(serverResponse)

            except:
                print("Try again")

            c.close()

        else:
            print("NET ERROR")
    
    tcpClientSocket.close()
tcpServerSocket.close()