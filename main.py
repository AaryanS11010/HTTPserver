import socket  # noqa: F401
import threading
import sys
import os
import gzip


echo_uri = "/echo/"
user_agent_uri = "/user-agent"
files_url = "/files/"


def on_connect(conn, addr):
    while True:
        print(f"Connected by: {addr}")
        data = conn.recv(1024).decode("utf-8")
        if not data:
            break
        request, body = data.split("\r\n\r\n")
        if len(data) > 0:
            request_line, *headers = request.split("\r\n")
            if request_line:
                method, uri, *_ = request_line.split()
                if uri == "/":
                    send_200(conn)
                elif uri.startswith(echo_uri):
                    send_echo(conn, uri, headers)
                elif uri == user_agent_uri:
                    send_user_agent(conn, headers)
                elif uri.startswith(files_url):
                    if method == "POST":
                        send_write_file(conn, uri, body)
                    else:
                        send_read_file(conn, uri)
                else:
                    send_404(conn)


def send_200(conn):
    conn.send(b"HTTP/1.1 200 OK\r\n\r\n")


def send_404(conn):
    conn.send(b"HTTP/1.1 404 Not Found\r\n\r\n")


def send_echo(conn, uri, headers):
    message = uri[len(echo_uri) :]
    print(f"message {message}")
    parsed_headers = parse_headers(headers)
    if (
        len(encodings := parsed_headers.get("Accept-Encoding") or []) > 0
        and "gzip" in encodings
    ):
        compressed_message = gzip.compress(bytes(message, "utf-8"))
        response = "\r\n".join(
            [
                "HTTP/1.1 200 OK",
                "Content-Type: text/plain",
                "Content-Encoding: gzip",
                f"Content-Length: {len(compressed_message)}",
                "",
                "",
            ]
        )
        print(repr(response))
        conn.send(bytes(response, "utf-8") + compressed_message)
    else:
        response = "\r\n".join(
            [
                "HTTP/1.1 200 OK",
                "Content-Type: text/plain",
                f"Content-Length: {len(message)}",
                "",
                f"{message}",
            ]
        )
        print(repr(response))
        conn.send(bytes(response, "utf-8"))


def send_user_agent(conn, headers):
    parsed_headers = parse_headers(headers)
    user_agent = (parsed_headers.get("User-Agent") or ["not given"])[0]
    response = "\r\n".join(
        [
            "HTTP/1.1 200 OK",
            "Content-Type: text/plain",
            f"Content-Length: {len(user_agent)}",
            "",
            f"{user_agent}",
        ]
    )
    print(repr(response))
    conn.send(bytes(response, "utf-8"))


def send_read_file(conn, uri):
    directory_path = sys.argv[-1]
    p = os.path.join(directory_path, uri[len(files_url) :])
    if os.path.exists(p):
        with open(p, "rb") as file:
            contents = file.read()
            response = "\r\n".join(
                [
                    "HTTP/1.1 200 OK",
                    "Content-Type: application/octet-stream",
                    f"Content-Length: {len(contents)}",
                    "",
                    "",
                ]
            )
            conn.send(bytes(response, "utf-8") + contents)
    else:
        print(f"file not found: {p}")
        send_404(conn)


def send_write_file(conn, uri, body):
    directory_path = sys.argv[-1]
    p = os.path.join(directory_path, uri[len(files_url) :])
    with open(p, "wb") as file:
        file.write(bytes(body, "utf-8"))
    conn.send(b"HTTP/1.1 201 Created\r\n\r\n")


def parse_headers(headers):
    parsed = {}
    for header in headers:
        pos = header.find(":")
        if pos >= 0:
            header_name = header[:pos]
            header_values = [v.strip() for v in header[pos + 1 :].split(",")]
            parsed[header_name] = header_values
    return parsed


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        conn, addr = server_socket.accept()  # wait for client
        threading.Thread(target=on_connect, args=(conn, addr)).start()


if __name__ == "__main__":
    main()