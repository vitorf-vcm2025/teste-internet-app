import speedtest


def selecionar_melhor_servidor(tester):
    try:
        servidores_br = tester.get_servers().get("BR", [])
    except Exception:
        servidores_br = []
    if servidores_br:
        return tester.get_best_server(servidores_br)
    return tester.get_best_server()


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

    print("Testando ping...")
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
