import socket
import speedtest
import time


def obter_servidor_brasil(tester, apenas_cc_br=False):
    try:
        servidores = tester.get_servers([])
        servidores_br = []
        for lista in servidores.values():
            for s in lista:
                cc = s.get("cc", "").upper()
                if apenas_cc_br:
                    if cc == "BR":
                        servidores_br.append(s)
                    continue
                pais = s.get("country", "").lower()
                if ("brazil" in pais or "brasil" in pais
                        or cc == "BR"):
                    servidores_br.append(s)
        if servidores_br:
            servidores_br.sort(key=lambda s: float(s.get("d") or 0))
            servidores_br = servidores_br[:30]
            try:
                return tester.get_best_server(servidores_br)
            except Exception:
                for s in servidores_br[:10]:
                    latencia = medir_ping(s)
                    if latencia is not None:
                        s = dict(s)
                        s["latency"] = latencia
                        tester._best.update(s)
                        tester.results.server = s
                        tester.results.ping = latencia
                        return s
                raise
    except Exception:
        pass
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
    melhor_servidor = obter_servidor_brasil(tester)

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
