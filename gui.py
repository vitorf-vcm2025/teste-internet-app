import json
import os
import socket
import sys
import threading
import time
from datetime import datetime

if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import speedtest
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SpeedTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Teste de Velocidade de Internet")
        self.geometry("700x650")
        self.minsize(700, 650)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self._executando = False
        self._historico = []
        self._info_servidor = None

        self._criar_widgets()

    def _criar_widgets(self):
        cabecalho = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=30, pady=(15, 4))
        cabecalho.grid_columnconfigure(0, weight=1)

        titulo = ctk.CTkLabel(
            cabecalho, text="Teste de Velocidade",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        titulo.grid(row=0, column=0, pady=(0, 2))

        subtitulo = ctk.CTkLabel(
            cabecalho, text="Clique em 'Iniciar Teste' para medir sua conexão",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        subtitulo.grid(row=1, column=0)

        self.info_servidor_frame = ctk.CTkFrame(
            self, fg_color="transparent"
        )
        self.info_servidor_frame.grid(
            row=1, column=0, sticky="ew", padx=30, pady=(0, 4)
        )
        self.info_servidor_frame.grid_columnconfigure(0, weight=1)
        self.info_servidor_frame.grid_remove()

        self.info_servidor_texto = ctk.CTkLabel(
            self.info_servidor_frame, text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left"
        )
        self.info_servidor_texto.grid(
            row=0, column=0, sticky="w"
        )

        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.grid(row=2, column=0, sticky="nsew", padx=30, pady=(2, 0))
        corpo.grid_columnconfigure(0, weight=1)
        corpo.grid_columnconfigure(1, weight=1)
        corpo.grid_columnconfigure(2, weight=1)
        corpo.grid_rowconfigure(0, weight=1)
        corpo.grid_rowconfigure(1, weight=0)
        corpo.grid_rowconfigure(2, weight=0)
        corpo.grid_rowconfigure(3, weight=0)

        self.card_download = self._criar_card(
            corpo, "Download", "0 Mbps", "#2ecc71", 0, 0
        )
        self.card_upload = self._criar_card(
            corpo, "Upload", "0 Mbps", "#3498db", 0, 1
        )
        self.card_ping = self._criar_card(
            corpo, "Ping", "0 ms", "#e67e22", 0, 2
        )

        self.barra_progresso = ctk.CTkProgressBar(corpo, mode="indeterminate")
        self.barra_progresso.grid(row=1, column=0, columnspan=3,
                                  sticky="ew", pady=(12, 0))
        self.barra_progresso.grid_remove()

        self.status_label = ctk.CTkLabel(
            corpo, text="Pronto para testar",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=2, column=0, columnspan=3, pady=(6, 0))

        self.qualidade_label = ctk.CTkLabel(
            corpo, text="",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.qualidade_label.grid(row=3, column=0, columnspan=3,
                                  pady=(4, 0))

        historico_container = ctk.CTkFrame(self, fg_color="transparent")
        historico_container.grid(row=3, column=0, sticky="nsew",
                                 padx=30, pady=(6, 5))
        historico_container.grid_columnconfigure(0, weight=1)
        historico_container.grid_rowconfigure(1, weight=1)

        historico_header = ctk.CTkFrame(
            historico_container, fg_color="transparent"
        )
        historico_header.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        historico_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            historico_header, text="Histórico de Medições",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.lbl_quantidade = ctk.CTkLabel(
            historico_header, text="0 registro(s)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.lbl_quantidade.grid(row=0, column=1, sticky="e")

        self.historico_scroll = ctk.CTkScrollableFrame(
            historico_container, corner_radius=10,
            height=100
        )
        self.historico_scroll.grid(row=1, column=0, sticky="nsew")
        self.historico_scroll.grid_columnconfigure(0, weight=1)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew", padx=30, pady=(5, 15))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.btn_iniciar = ctk.CTkButton(
            btn_frame, text="Iniciar Teste",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=42, corner_radius=8,
            command=self._iniciar_teste
        )
        self.btn_iniciar.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_exportar = ctk.CTkButton(
            btn_frame, text="Salvar Relatório",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=42, corner_radius=8,
            fg_color="#2c3e50", hover_color="#34495e",
            state="disabled",
            command=self._exportar_historico
        )
        self.btn_exportar.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _criar_card(self, parent, titulo, valor_inicial, cor, row, col):
        frame = ctk.CTkFrame(parent, corner_radius=12)
        frame.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        lbl_titulo = ctk.CTkLabel(
            frame, text=titulo,
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        lbl_titulo.grid(row=0, column=0, pady=(10, 0))

        lbl_valor = ctk.CTkLabel(
            frame, text=valor_inicial,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=cor
        )
        lbl_valor.grid(row=1, column=0, pady=4)

        lbl_unidade = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        lbl_unidade.grid(row=2, column=0, pady=(0, 8))

        return {
            "frame": frame, "valor": lbl_valor, "unidade": lbl_unidade,
        }

    def _iniciar_teste(self):
        if self._executando:
            return
        self._executando = True
        self.btn_iniciar.configure(state="disabled", text="Testando...")
        self.barra_progresso.grid()
        self.barra_progresso.start()
        self.status_label.configure(
            text="Iniciando teste...", text_color="#f39c12"
        )
        for card in [self.card_download, self.card_upload, self.card_ping]:
            card["valor"].configure(text="--")
            card["unidade"].configure(text="")

        self._info_servidor = None
        self.info_servidor_frame.grid_remove()
        self.qualidade_label.configure(text="")

        thread = threading.Thread(target=self._executar_teste, daemon=True)
        thread.start()

    def _executar_teste(self):
        try:
            self.after(0, lambda: self.status_label.configure(
                text="Buscando servidor...", text_color="#f39c12"))

            tester = speedtest.Speedtest()

            self.after(0, lambda: self.status_label.configure(
                text="Buscando melhor servidor...", text_color="#f39c12"))

            melhor_servidor = self._obter_servidor_brasil(tester)

            self.after(0, lambda: self.status_label.configure(
                text="Medindo ping...", text_color="#f39c12"))

            ping_ms = self._medir_ping(melhor_servidor)
            if ping_ms is None:
                ping_ms = self._tratar_ping(
                    tester.results.ping, melhor_servidor)

            self.after(0, lambda: self.status_label.configure(
                text="Medindo Download...", text_color="#f39c12"))
            tester.download()

            self.after(0, lambda: self.status_label.configure(
                text="Medindo Upload...", text_color="#f39c12"))
            tester.upload()

            download_mbps = tester.results.download / 1_000_000
            upload_mbps = tester.results.upload / 1_000_000

            qual = self._classificar_qualidade(download_mbps, ping_ms)

            dados = {
                "horario": datetime.now().strftime("%H:%M:%S"),
                "download": f"{download_mbps:.2f}",
                "upload": f"{upload_mbps:.2f}",
                "ping": f"{ping_ms:.2f}",
                "download_bps": tester.results.download,
                "upload_bps": tester.results.upload,
                "ping_ms": ping_ms,
                "qualidade": qual,
            }

            info = {
                "isp": tester.results.client.get("isp", "N/A"),
                "ip": tester.results.client.get("ip", "N/A"),
                "servidor": (
                    f"{tester.results.server.get('sponsor', 'N/A')} "
                    f"({tester.results.server.get('name', 'N/A')})"
                ),
            }
            self._info_servidor = info

            self.after(0, lambda d=dados, i=info: self._exibir_info(i, d))
            self.after(0, lambda d=dados: self._atualizar_card(
                self.card_download, f"{d['download']}", "Mbps"
            ))
            self.after(0, lambda d=dados: self._atualizar_card(
                self.card_upload, f"{d['upload']}", "Mbps"
            ))
            self.after(0, lambda d=dados: self._atualizar_card(
                self.card_ping, f"{d['ping']}", "ms"
            ))
            self.after(0, lambda d=dados: self._adicionar_historico(d))
            self.after(0, lambda: self.status_label.configure(
                text="Teste concluído!", text_color="#2ecc71"))

        except speedtest.SpeedtestException as e:
            self.after(0, lambda: self.status_label.configure(
                text="Sem conexão com a internet", text_color="#e74c3c"))
            self.after(0, lambda: messagebox.showwarning(
                "Sem Conexão",
                "Não foi possível conectar aos servidores do Speedtest.\n\n"
                "Verifique sua conexão com a internet e tente novamente."
            ))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(
                text=f"Erro inesperado", text_color="#e74c3c"))
            self.after(0, lambda: messagebox.showerror(
                "Erro", f"Falha ao executar teste:\n{str(e)}"))
        finally:
            self.after(0, self._finalizar)

    @staticmethod
    def _obter_servidor_brasil(tester, apenas_cc_br=False):
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
                        latencia = SpeedTestApp._medir_ping(s)
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

    @staticmethod
    def _medir_ping(servidor=None, tentativas=2):
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
                    with socket.create_connection((host, porta),
                                                  timeout=1.5):
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

    @staticmethod
    def _tratar_ping(ping, servidor=None):
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

    @staticmethod
    def _classificar_qualidade(download_mbps, ping_ms):
        if download_mbps >= 100 and ping_ms < 50:
            return "Excelente", "#2ecc71"
        if download_mbps >= 50 and ping_ms < 80:
            return "Boa", "#f39c12"
        if download_mbps >= 20 and ping_ms < 150:
            return "Regular", "#3498db"
        return "Lenta", "#e74c3c"

    def _exibir_info(self, info, dados):
        qual, cor = dados["qualidade"]
        self.info_servidor_texto.configure(
            text=(
                f"ISP: {info['isp']}  |  IP: {info['ip']}\n"
                f"Servidor: {info['servidor']}"
            )
        )
        self.qualidade_label.configure(
            text=f"Qualidade da Conexão: {qual}",
            text_color=cor
        )
        self.info_servidor_frame.grid()

    def _atualizar_card(self, card, valor, unidade):
        card["valor"].configure(text=valor)
        card["unidade"].configure(text=unidade)

    def _adicionar_historico(self, dados):
        self._historico.append(dados)
        self.lbl_quantidade.configure(
            text=f"{len(self._historico)} registro(s)"
        )
        self.btn_exportar.configure(state="normal")

        item = ctk.CTkFrame(
            self.historico_scroll, corner_radius=8
        )
        item.grid(row=len(self._historico) - 1, column=0,
                  sticky="ew", pady=3)
        item.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(
            item, text=dados["horario"],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray"
        ).grid(row=0, column=0, padx=6, pady=6)

        for col, (chave, cor, unidade) in enumerate(
            [
                ("download", "#2ecc71", "Mbps"),
                ("upload", "#3498db", "Mbps"),
                ("ping", "#e67e22", "ms"),
            ],
            start=1,
        ):
            ctk.CTkLabel(
                item,
                text=f"{dados[chave]} {unidade}",
                font=ctk.CTkFont(size=12),
                text_color=cor,
            ).grid(row=0, column=col, padx=6, pady=6)

        qual, cor_qual = dados["qualidade"]
        ctk.CTkLabel(
            item,
            text=f"  {qual}  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=cor_qual,
            fg_color=cor_qual + "22",
            corner_radius=4,
        ).grid(row=0, column=4, padx=6, pady=6)

        self.historico_scroll._parent_canvas.yview_moveto(1.0)

    def _exportar_historico(self):
        if not self._historico:
            messagebox.showinfo(
                "Exportar", "Nenhum registro para exportar."
            )
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON", "*.json"),
                ("Texto", "*.txt"),
            ],
            title="Salvar Relatório de Velocidade",
        )
        if not arquivo:
            return

        caminho = Path(arquivo)
        try:
            if caminho.suffix == ".json":
                with open(caminho, "w", encoding="utf-8") as f:
                    json.dump(self._historico, f, indent=2, ensure_ascii=False)
            else:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("Relatório de Teste de Velocidade\n")
                    f.write("=" * 40 + "\n\n")
                    for i, item in enumerate(self._historico, 1):
                        qual = item["qualidade"][0]
                        f.write(
                            f"Medição #{i} - {item['horario']}\n"
                            f"  Download: {item['download']} Mbps\n"
                            f"  Upload:   {item['upload']} Mbps\n"
                            f"  Ping:     {item['ping']} ms\n"
                            f"  Qualidade: {qual}\n\n"
                        )
            messagebox.showinfo(
                "Exportar",
                f"Relatório salvo com sucesso em:\n{caminho}"
            )
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}"
            )

    def _finalizar(self):
        self._executando = False
        self.barra_progresso.stop()
        self.barra_progresso.grid_remove()
        self.btn_iniciar.configure(state="normal", text="Iniciar Teste")


if __name__ == "__main__":
    app = SpeedTestApp()
    app.mainloop()
