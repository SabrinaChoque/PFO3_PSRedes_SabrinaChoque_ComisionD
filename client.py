# client.py
import socket, json, sys

HOST = "127.0.0.1"
PORT = 5001

def send_req(sock, payload: dict):
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
    buf = bytearray()
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            break
        buf.extend(chunk)
        if b"\n" in chunk:
            break
    if not buf:
        return {}
    return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))

def main():
    print("Cliente. Comandos: uppercase <txt> | hash <txt> | echo <txt> | salir")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        c.connect((HOST, PORT))
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd.lower() == "salir":
                break
            parts = cmd.split(" ", 1)
            op = parts[0]
            data = parts[1] if len(parts) > 1 else ""
            try:
                resp = send_req(c, {"op": op, "data": data})
                print(resp)
            except Exception as e:
                print("Error:", e)
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
