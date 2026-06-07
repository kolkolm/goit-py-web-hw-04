from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
import socket
import time
import threading
import json
from datetime import datetime


UDP_IP = '127.0.0.1'
UDP_PORT = 5000

def run_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            payload = json.loads(data.decode('utf-8'))

            if pathlib.Path("data.json").exists() and pathlib.Path("data.json").stat().st_size > 0:
                with open("data.json", 'r', encoding='utf-8') as f:
                    try:
                        storage = json.load(f)
                    except json.JSONDecodeError:
                        storage = {}
            else:
                storage = {}

            timestamp = str(datetime.now())
            storage[timestamp] = payload

            with open("data.json", 'w', encoding='utf-8') as f:
                json.dump(storage, f, ensure_ascii=False, indent=4)

    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()

def run_client(ip, port, data_dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    message = json.dumps(data_dict).encode('utf-8')
    sock.sendto(message, server)
    sock.close()

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split("=") for el in data_parse.split("&")]}
        run_client(UDP_IP, UDP_PORT, data_dict)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain") 
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())
    
def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

if __name__ == "__main__":
    tr1 = threading.Thread(target=run)
    tr2 = threading.Thread(target=run_server, args=(UDP_IP, UDP_PORT), daemon=True)

    tr1.start()
    tr2.start()