import os
import socket
import threading
import time
from datetime import datetime

import flet as ft
import speedtest


def classificar_qualidade(download_mbps, ping_ms):
    if download_mbps >= 100 and ping_ms < 50:
        return "Excelente", ft.Colors.GREEN
    if download_mbps >= 50 and ping_ms < 80:
        return "Boa", ft.Colors.AMBER
    if download_mbps >= 20 and ping_ms < 150:
        return "Regular", ft.Colors.BLUE
    return "Ruim", ft.Colors.RED


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


def main(page: ft.Page):
    page.title = "Teste de Velocidade"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#1a1a2e"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    historico = []
    executando = False

    download_valor = ft.Text("0", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    download_unidade = ft.Text("Mbps", size=12, color=ft.Colors.GREY)
    upload_valor = ft.Text("0", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
    upload_unidade = ft.Text("Mbps", size=12, color=ft.Colors.GREY)
    ping_valor = ft.Text("0", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE)
    ping_unidade = ft.Text("ms", size=12, color=ft.Colors.GREY)

    qualidade_texto = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    status_texto = ft.Text("Pronto para testar", size=13, color=ft.Colors.GREY)
    progresso = ft.ProgressBar(visible=False, color=ft.Colors.BLUE, bgcolor="#333")

    info_isp = ft.Text("", size=12, color=ft.Colors.GREY)
    info_ip = ft.Text("", size=12, color=ft.Colors.GREY)
    info_servidor = ft.Text("", size=12, color=ft.Colors.GREY)

    historico_lista = ft.ListView(expand=True, spacing=6)
    lbl_quantidade = ft.Text("0 registro(s)", size=11, color=ft.Colors.GREY)

    btn_teste = ft.ElevatedButton(
        "Iniciar Teste",
        icon=ft.Icons.SPEED,
        on_click=lambda _: None,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_700,
            padding=20,
            shape=ft.RoundedRectangleBorder(radius=12),
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
        ),
    )

    def criar_card(titulo, valor_widget, unidade_widget, cor):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(titulo, size=12, color=ft.Colors.GREY),
                    valor_widget,
                    unidade_widget,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            bgcolor="#16213e",
            border_radius=12,
            padding=12,
            expand=True,
        )

    def criar_item_historico(dados):
        qual, cor_qual = classificar_qualidade(
            float(dados["download"]), float(dados["ping"])
        )
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(dados["horario"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY, width=50),
                    ft.Text(f"{dados['download']} Mbps", size=12, color=ft.Colors.GREEN, expand=True),
                    ft.Text(f"{dados['upload']} Mbps", size=12, color=ft.Colors.BLUE, expand=True),
                    ft.Text(f"{dados['ping']} ms", size=12, color=ft.Colors.ORANGE, expand=True),
                    ft.Container(
                        content=ft.Text(qual, size=11, weight=ft.FontWeight.BOLD, color=cor_qual),
                        bgcolor=cor_qual + "33",
                        border_radius=4,
                        padding=4,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="#1a1a3e",
            border_radius=8,
            padding=8,
        )

    def iniciar_teste(e):
        nonlocal executando
        if executando:
            return
        executando = True

        download_valor.value = "--"
        upload_valor.value = "--"
        ping_valor.value = "--"
        qualidade_texto.value = ""
        status_texto.value = "Iniciando teste..."
        status_texto.color = ft.Colors.AMBER
        info_isp.value = ""
        info_ip.value = ""
        info_servidor.value = ""
        progresso.visible = True
        btn_teste.text = "Testando..."
        btn_teste.disabled = True
        page.update()

        def rodar_teste():
            nonlocal executando
            try:
                status_texto.value = "Buscando servidor..."
                status_texto.color = ft.Colors.AMBER
                page.update()

                tester = speedtest.Speedtest()

                status_texto.value = "Buscando melhor servidor..."
                status_texto.color = ft.Colors.AMBER
                page.update()
                melhor_servidor = selecionar_melhor_servidor(tester)

                status_texto.value = "Medindo ping..."
                page.update()
                p_ms = medir_ping(melhor_servidor)
                if p_ms is None:
                    p_ms = tratar_ping(tester.results.ping, melhor_servidor)

                status_texto.value = "Medindo Download..."
                page.update()
                tester.download()

                status_texto.value = "Medindo Upload..."
                page.update()
                tester.upload()

                d_mbps = tester.results.download / 1_000_000
                u_mbps = tester.results.upload / 1_000_000
                qual, cor_qual = classificar_qualidade(d_mbps, p_ms)

                dados = {
                    "horario": datetime.now().strftime("%H:%M:%S"),
                    "download": f"{d_mbps:.2f}",
                    "upload": f"{u_mbps:.2f}",
                    "ping": f"{p_ms:.2f}",
                }
                historico.append(dados)

                download_valor.value = f"{d_mbps:.2f}"
                upload_valor.value = f"{u_mbps:.2f}"
                ping_valor.value = f"{p_ms:.2f}"
                qualidade_texto.value = f"Qualidade da Conexão: {qual}"
                qualidade_texto.color = cor_qual
                status_texto.value = "Teste concluído!"
                status_texto.color = ft.Colors.GREEN

                info_isp.value = f"ISP: {tester.results.client.get('isp', 'N/A')}"
                info_ip.value = f"IP: {tester.results.client.get('ip', 'N/A')}"
                info_servidor.value = (
                    f"Servidor: {tester.results.server.get('sponsor', 'N/A')} "
                    f"({tester.results.server.get('name', 'N/A')})"
                )

                historico_lista.controls.append(criar_item_historico(dados))
                lbl_quantidade.value = f"{len(historico)} registro(s)"

            except speedtest.SpeedtestException:
                status_texto.value = "Sem conexão com a internet"
                status_texto.color = ft.Colors.RED
                page.open(ft.AlertDialog(
                    title=ft.Text("Sem Conexão"),
                    content=ft.Text(
                        "Não foi possível conectar aos servidores do Speedtest.\n"
                        "Verifique sua conexão e tente novamente."
                    ),
                ))
            except Exception as ex:
                status_texto.value = "Erro inesperado"
                status_texto.color = ft.Colors.RED
                page.open(ft.AlertDialog(
                    title=ft.Text("Erro"),
                    content=ft.Text(f"Falha ao executar teste:\n{ex}"),
                ))
            finally:
                progresso.visible = False
                btn_teste.text = "Iniciar Teste"
                btn_teste.disabled = False
                executando = False
                page.update()

        threading.Thread(target=rodar_teste, daemon=True).start()

    btn_teste.on_click = iniciar_teste

    card_download = criar_card("Download", download_valor, download_unidade, ft.Colors.GREEN)
    card_upload = criar_card("Upload", upload_valor, upload_unidade, ft.Colors.BLUE)
    card_ping = criar_card("Ping", ping_valor, ping_unidade, ft.Colors.ORANGE)

    info_container = ft.Container(
        content=ft.Column(
            [info_isp, info_ip, info_servidor],
            spacing=2,
        ),
        bgcolor="#16213e",
        border_radius=10,
        padding=12,
        visible=False,
    )

    historico_header = ft.Row(
        [
            ft.Text("Histórico de Medições", size=14, weight=ft.FontWeight.BOLD),
            lbl_quantidade,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Teste de Velocidade", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Meça sua conexão com a internet", size=13, color=ft.Colors.GREY),
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    info_container,
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        [card_download, card_upload, card_ping],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        expand=True,
                    ),
                    qualidade_texto,
                    progresso,
                    status_texto,
                    btn_teste,
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    historico_header,
                    historico_lista,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                expand=True,
            ),
            padding=16,
            expand=True,
        )
    )

    def mostrar_info(e):
        if info_container.visible:
            info_container.visible = False
        else:
            info_container.visible = True
        page.update()

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.INFO_OUTLINE,
        on_click=mostrar_info,
        bgcolor=ft.Colors.BLUE_700,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8502))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")
