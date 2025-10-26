import socket
import json
import sys

HOST = "127.0.0.1"
PORT = 5001

def send_req(sock: socket.socket, payload: dict) -> dict:
    sock.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
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
    try:
        return json.loads(buf.split(b"\n", 1)[0].decode("utf-8", errors="replace"))
    except Exception:
        return {"status": "error", "message": "respuesta no es JSON"}

def main() -> None:
    print("Cliente. Comandos: uppercase <txt> | hash <txt> | echo <txt> | salir")
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as c:
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
                    if isinstance(resp, dict) and resp.get("status") != "ok":
                        print("Error:", resp)
                    else:
                        print(resp)
                except (BrokenPipeError, ConnectionResetError):
                    print("La conexión con el servidor se cerró.")
                    break
    except ConnectionRefusedError:
        print(f"No pude conectar con el servidor. ¿Está corriendo en {HOST}:{PORT}?")
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
