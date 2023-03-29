import socket
import sys
from datetime import datetime as dt

help_msg = f"""
Usage: mp_client.py <arg>
Enter one of the arguments below into <arg> to test how to the server handles it.
    200 - Test 200 OK. This sends a normal request to the server for index.html. You will receive a full HTML page back.
    304 - Test 304 Not Modified. This sends a request for index.html with the header If-Modified-Since. IMS equals the current time, so the client's "cached version" is always up to date with index.html on disk. You will not receive an HTML file back as the response has no payload.
    400nohost - Test 400 Bad Request. This sends a request that doesn't have the Host header. HTTP/1.1 requires a request to have the Host header, so a request without one is bad. You'll receive a 400 error HTML page back.
    400fewpar - Test 400 Bad Request. This sends a request that has a malformed start line, making it a bad request. You'll receive a 400 error HTML page back.
    400post - Test 400 Bad Request. This sends a request that uses the POST method instead of GET. The server doesn't handle POST, so it's a bad request.
    400http2 - Test 400 Bad Request. This sends a request that uses HTTP/2 instead of HTTP/1.1. The server doesn't handle HTTP/2, so it's a bad request.
    400invalid - Test 400 Bad Request. This sends a request for a filename that contains an illegal character, making it a bad request.
    404 - Test 404 Not Found. This sends a request for x.txt, a file that doesn't exist on the server. You will receive a 404 error HTML page.
    408 - Test 408 Request Timeout. This opens a connection with the server but doesn't send a request, making it idle. After a few seconds, the connection will timeout, and you will receive a 408 error HTML page.
"""

def help_and_exit():
    print(help_msg)
    exit()

argc = len(sys.argv)
if argc != 2: help_and_exit()

code = sys.argv[1]
request = ""
test_timeout = False
host_header = "Host: localhost:12000\r\n"
eol = "\r\n"
match code:
    case "200":
        request = f"GET / HTTP/1.1\r\n{host_header}{eol}"
    case "304":
        time = dt.strftime(dt.now(), "%a, %d %b %Y %H:%M:%S %Z")
        last_mod_header = "If-Modified-Since: " + time + "GMT\r\n"
        request = f"GET / HTTP/1.1\r\n{host_header}{last_mod_header}{eol}"
    case "400nohost":
        request = "GET / HTTP/1.1\r\n"
    case "400fewpar":
        request = f"GET /\r\n{host_header}{eol}"
    case "400post":
        request = f"POST / HTTP/1.1\r\n{host_header}{eol}"
    case "400http2":
        request = f"GET / HTTP/2\r\n{host_header}{eol}"
    case "400invalid":
        request = f"GET /? HTTP/1.1\r\n{host_header}{eol}"
    case "404":
        request = f"GET /x.txt HTTP/1.1\r\n{host_header}{eol}"
    case "408":
        test_timeout = True
    case _:
        help_and_exit()

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_HOST, SERVER_PORT))

if not test_timeout:
    print(f"Request is: {request}")
    client_socket.sendall(request.encode())
else:
    print("Testing timeout. Doing nothing while waiting for server response...")

response = client_socket.recv(4096)
print(f"Response from server is:\n{response.decode()}")
client_socket.close()