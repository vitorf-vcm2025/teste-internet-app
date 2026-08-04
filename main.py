import socket
import speedtest
import time


def selecionar_melhor_servidor(tester):
    try:
        servidores = tester.get_servers()
        servidores_br = [
            s for grupo in servidores.values()
            for s in grupo
            if s.get("cc") == "BR" or
            s.get("country", "").lower() == "brazil"
        ]
        servidores_br.sort(key=lambda s: float(s.get("d") or 0))
        servidores_br = servidores_br[:20]
    except Exception:
        servidores_br = []
    if servidores_br:
        return tester.get_best_server(servidores_br)
    return tester.get_best_server()


def medir_ping(servidor=None, tentativas=2):
    alvos = []
    if servidor:
        host = (servidor.get("host") or "").split(":")[0]
        if host:
            alvos.append((host, 443))
            alvos.append((host, 80))
    alvos += [("1.1.1.1", 443), ("1.1.1.1", 53),
              ("8.8.8.8", 443), ("8.8.8.8", 53)]
    amostras = []
    for host, porta in alvos:
        for _ in range(tentativas):
            inicio = time.perf_counter()
            try:
                with socket.create_connection((host, porta), timeout=1.5):
                    amostras.append(
                        (time.perf_counter() - inicio) * 1000.0
                    )
            except OSError:
                pass
            if len(amostras) >= 5:
                return round(min(amostras), 2)
    if not amostras:
        return None
    return round(min(amostras), 2)


def tratar_ping(ping, servidor=None):
    if ping is None and servidor:
        ping = servidor.get("latency")
    if ping is None:
        return 0.0
    if isinstance(ping, (list, tuple, dict, set)):
        try:
            ping = next(iter(ping))
        except (TypeError, StopIteration):
            return 0.0
    try:
        ping = float(ping)
    except (TypeError, ValueError):
        return 0.0
    if ping < 0:
        return 0.0
    if ping < 1:
        ping *= 1000.0
    if ping >= 1_000_000:
        return 0.0
    return round(ping, 2)


def classificar_qualidade(download_mbps, ping_ms):
    if download_mbps >= 100 and ping_ms < 50:
        return "Excelente"
    if download_mbps >= 50 and ping_ms < 80:
        return "Boa"
    if download_mbps >= 20 and ping_ms < 150:
        return "Regular"
    return "Lenta"


def testar_velocidade():
    print("Iniciando teste de velocidade...")
    tester = speedtest.Speedtest()

    print("Buscando melhor servidor...")
    melhor_servidor = selecionar_melhor_servidor(tester)

    print("Medindo ping...")
    ping_ms = medir_ping(melhor_servidor)
    if ping_ms is None:
        ping_ms = tratar_ping(tester.results.ping, melhor_servidor)

    print("Testando download...")
    tester.download()

    print("Testando upload...")
    tester.upload()

    resultados = tester.results.dict()
    download_mbps = resultados['download'] / 1_000_000
    upload_mbps = resultados['upload'] / 1_000_000

    qualidade = classificar_qualidade(download_mbps, ping_ms)

    print(f"\nResultados:")
    print(f"Download: {download_mbps:.2f} Mbps")
    print(f"Upload: {upload_mbps:.2f} Mbps")
    print(f"Ping: {ping_ms:.2f} ms")
    print(f"Qualidade da Conexão: {qualidade}")

    return resultados


if __name__ == "__main__":
    testar_velocidade()
