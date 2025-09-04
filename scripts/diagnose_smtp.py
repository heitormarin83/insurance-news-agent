# scripts/diagnose_smtp.py
import socket, ssl, sys, time
HOSTS = ["smtp.gmail.com"]
PORTS = [587, 465]
TIMEOUT = 8

def try_connect(host, port, family):
    af_name = "IPv4" if family == socket.AF_INET else "IPv6"
    try:
        infos = socket.getaddrinfo(host, port, family, socket.SOCK_STREAM)
        if not infos:
            print(f"[{af_name}] {host}:{port} -> getaddrinfo sem resultados")
            return
        addr = infos[0][4]
        s = socket.socket(family, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        print(f"[{af_name}] Conectando {host}:{port} -> {addr} ...", end=" ")
        s.connect(addr)
        if port == 587:
            # STARTTLS handshake simples
            s.send(b"EHLO tester\r\n")
            time.sleep(0.2)
        elif port == 465:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=host)
            s.send(b"EHLO tester\r\n")
            time.sleep(0.2)
        print("OK")
        s.close()
    except Exception as e:
        print(f"FALHA: {e.__class__.__name__}: {e}")

def main():
    print("== Diagnóstico SMTP (conectividade) ==")
    for h in HOSTS:
        for p in PORTS:
            for fam in (socket.AF_INET, socket.AF_INET6):
                try_connect(h, p, fam)

if __name__ == "__main__":
    main()
