from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

PORT = 8080

server = ThreadingHTTPServer(
    ("127.0.0.1", PORT),
    SimpleHTTPRequestHandler
)

print("")
print("========================================")
print(" NUSANTARA GRAPH VIEWER")
print("========================================")
print("URL    : http://127.0.0.1:8080")
print("ROOT   :", ROOT)
print("STATUS : RUNNING")
print("")
print("Tekan CTRL+C untuk menghentikan server.")
print("")

server.serve_forever()
