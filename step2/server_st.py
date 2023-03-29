import socket
from datetime import datetime as dt
import os
import math

str400 = "400 Bad Request"
str404 = "404 Not Found"
str408 = "408 Request Timeout"

def send_HTTP(conn, code, data="", last_mod_timestamp=""):
    response = ""
    # Chrome won't let me see raw response headers if it's just status line, so I add this
    server_header = "Server: Python\r\n"
    match code:
        case "200":
            datetime = dt.fromtimestamp(last_mod_timestamp)
            fmt = dt.strftime(datetime, "%a, %d %b %Y %H:%M:%S %Z")
            last_mod_header = "Last-Modified: " + fmt + "GMT\r\n"
            response = "HTTP/1.1 200 OK\r\n" + last_mod_header + server_header + "\r\n" + data
        case "304":
            response = "HTTP/1.1 304 Not Modified\r\n" + server_header + "\r\n"
        case "400":
            html400 = "<!DOCTYPE html><html><h1>400 Bad Request &#x1F635</h1></html>"
            response = "HTTP/1.1 400 Bad Request\r\n" + server_header + "\r\n" + html400
        case "404":
            html404 = "<!DOCTYPE html><html><h1>404 Not Found &#x1F937</h1></html>"
            response = "HTTP/1.1 404 Not Found\r\n" + server_header +"\r\n" + html404
        case "408":
            html408 = "<!DOCTYPE html><html><h1>408 Request Timeout &#x23F1</h1></html>"
            response = "HTTP/1.1 408 Request Timeout\r\n" + server_header + "\r\n" + html408

    conn.sendall(response.encode())
    conn.close()

def count_host_headers(request_lines) -> int:
    count = 0
    for l in request_lines:
        if l.startswith("Host:"): count += 1
    return count

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
    
    return datetime.timestamp() if success else None

def print_error(status_code, error_msg):
    print(f"{status_code}. {error_msg}\n")

def handle_connection(conn):
    try:
        conn.settimeout(8.0)
        request = conn.recv(4096).decode()
        print(f"NEW REQUEST:\n{request}")

        request_lines = request.split('\r\n')
        if count_host_headers(request_lines) != 1:
            print_error(str400, "HTTP/1.1 needs exactly one Host request header")
            send_HTTP(conn, "400")
            return
        if_modified_since = if_modified_since_header(request_lines)

        # client.py doesn't test this case!
        start_line = request_lines[0]
        if start_line == "":
            print_error(str400, "Received empty request")
            send_HTTP(conn, "400")
            return

        start_line_split = start_line.split()
        if len(start_line_split) != 3:
            print_error(str400, "Start line too short")
            send_HTTP(conn, "400")
            return

        http_method, request_target, http_version = start_line_split
        if (http_method != 'GET'):
            print_error(str400, "Request's method is not GET")
            send_HTTP(conn, "400")
            return
        if http_version != 'HTTP/1.1':
            print_error(str400, "Request's HTTP version is not HTTP/1.1")
            send_HTTP(conn, "400")
            return

        file_to_open = request_target.lstrip('/')
        if file_to_open == "": # open index.html if user asks for root resource "/"
            file_to_open = "index.html"
        try:
            send_304 = False
            with open(file_to_open, "r") as file:
                data = file.read()
                if os.path.exists(file_to_open):
                    last_mod_timestamp = math.floor(os.path.getmtime(file_to_open))
                if if_modified_since is not None:
                    if last_mod_timestamp <= if_modified_since:
                        send_304 = True

            send_HTTP(conn, "200" if not send_304 else "304", data, last_mod_timestamp)
        except FileNotFoundError as e:
            print_error(str404, f"File {file_to_open} does not exist on server.")
            send_HTTP(conn, "404")
        except OSError as e:
            print_error(str400, "File to open has an invalid filename.")
            send_HTTP(conn, "400")
            
    except socket.timeout as e:
        print_error(str408, "Request timed out")
        send_HTTP(conn, "408")

# ================================
# =========== MAIN CODE ==========
# ================================

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print(f"Server is listening on port {SERVER_PORT}\n")

while True:
    conn, addr = server_socket.accept()
    print(f"***** t={dt.now().time()}, Got new connection: {addr} *****")
    handle_connection(conn)