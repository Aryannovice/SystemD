from resp import encode


def eval_ping(args: list[str]) -> bytes:
    if len(args) >= 2:
        raise ValueError(
            "ERR wrong number of arguments for 'ping' command"
        )

    if len(args) == 0:
        return encode("PONG", True)

    return encode(args[0], False)


def eval_and_respond(cmd, conn):
    print("command:", cmd.cmd)

    match cmd.cmd:
        case "PING":
            response = eval_ping(cmd.args)

        case _:
            # same behavior as Go version
            response = eval_ping(cmd.args)

    conn.sendall(response)