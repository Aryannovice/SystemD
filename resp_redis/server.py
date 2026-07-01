import socket
import selectors

from cmd import RedisCmd
from resp import decode_array_string
from eval import eval_and_respond


selector = selectors.DefaultSelector()


def read_command(conn) -> RedisCmd:
    data = conn.recv(512)

    if not data:
        raise ConnectionError("client disconnected")

    tokens = decode_array_string(data)

    return RedisCmd(
        cmd=tokens[0].upper(),
        args=tokens[1:]
    )


def respond_error(conn, err):
    conn.sendall(
        f"-{str(err)}\r\n".encode()
    )


def accept_connection(server):
    conn, addr = server.accept()

    print(f"Accepted {addr}")

    conn.setblocking(False)

    selector.register(
        conn,
        selectors.EVENT_READ,
        handle_client
    )


def handle_client(conn):
    try:
        cmd = read_command(conn)

        print(f"Received {cmd.cmd}")

        eval_and_respond(cmd, conn)

    except Exception as e:
        respond_error(conn, e)

        selector.unregister(conn)
        conn.close()


def run_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.bind(("127.0.0.1", 6379))

    server.listen()

    server.setblocking(False)

    selector.register(
        server,
        selectors.EVENT_READ,
        accept_connection
    )

    print("Redis listening on 6379")

    while True:

        events = selector.select()

        for key, mask in events:

            callback = key.data

            callback(key.fileobj)


if __name__ == "__main__":
    run_server()