# Uncomment this to pass the first stage
import socket
import threading
import argparse, os, gzip

OK_RESPONSE = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/plain\r\n"
    f"Content-Length: 0\r\n"
    f"\r\n"
)
NOT_FOUND_RESPONSE = (
    "HTTP/1.1 404 Not Found\r\n"
    "Content-Type: text/plain\r\n"
    f"Content-Length: 0\r\n"
    f"\r\n"
)
DATA_RESPONSE = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/plain\r\n"
    "Content-Length: {size}\r\n"
    "\r\n{data}"
)


def handler(conn, addr, directory):
    request = str(conn.recv(1024))
    url = request.split('\\r\\n')[0].split(' ')[1]
    headers = request.split('\\r\\n')
    response = NOT_FOUND_RESPONSE.encode('utf-8')

    if url == '/':
        response = OK_RESPONSE.encode('utf-8')

    elif url.startswith('/echo'):
        data = url.split('/')[-1]
        size = len(data)
        encoding = ""
        for header in headers:
            if header.lower().startswith('accept-encoding'):
                encoding = header.split(':')[1][1:]
        if 'gzip' in encoding:
            data = gzip.compress(data.encode())
            size = len(data)
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Encoding: gzip\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: {size}\r\n"
                "\r\n"
            ).format(size=size)
            response = response.encode('utf-8')
            response = response + data
        else:
            response = DATA_RESPONSE.format(size=size, data=data).encode('utf-8')

    elif url.startswith('/files'):
        file = url.split('/')[-1]

        if request.startswith("b'GET"):
            if file in os.listdir(directory):
                with open(f"/{directory}/{file}", "r") as f:
                    body = f.read()
                size = len(body)
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/octet-stream\r\n"
                    f"Content-Length: {size}\r\n"
                    f"\r\n{body}"
                ).encode('utf-8')
        elif request.startswith("b'POST"):
            data = str(headers[-1])[:-1]
            with open(f"/{directory}/{file}", "w") as f:
                f.write(data)
            response = (
                "HTTP/1.1 201 Created\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: 0\r\n"
                f"\r\n"
            ).encode('utf-8')

    elif url.startswith('/user-agent'):
        data = ""
        for header in headers:
            if header.startswith('User-Agent'):
                data = header.split(' ')[1]
                break
        size = len(data)
        if size > 0:
            response = DATA_RESPONSE.format(size=size, data=data).encode('utf-8')

    conn.sendall(response)
    conn.close()


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.

    print("Logs from your program will appear here!")
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory")
    directory = parser.parse_args().directory

    with socket.create_server(("localhost", 4221), reuse_port=False) as server_socket:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handler, args=(conn, addr, directory)).start()


if __name__ == "__main__":
    main()
