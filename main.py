import speedtest
import time


def testar_velocidade():
    print("Iniciando teste de velocidade...")
    tester = speedtest.Speedtest()

    print("Buscando melhor servidor...")
    tester.get_best_server()

    print("Testando download...")
    tester.download()

    print("Testando upload...")
    tester.upload()

    resultados = tester.results.dict()
    download_mbps = resultados['download'] / 1_000_000
    upload_mbps = resultados['upload'] / 1_000_000
    ping_ms = resultados['ping']

    print(f"\nResultados:")
    print(f"Download: {download_mbps:.2f} Mbps")
    print(f"Upload: {upload_mbps:.2f} Mbps")
    print(f"Ping: {ping_ms:.2f} ms")

    return resultados


if __name__ == "__main__":
    testar_velocidade()
