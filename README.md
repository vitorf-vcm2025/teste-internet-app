# ⚡ Internet SpeedTest App

> Um aplicativo moderno e responsivo de teste de velocidade de internet desenvolvido em Python, com suporte para Desktop (GUI) e Web/Mobile (PWA).

![Python](https://img.shields.io/badge/Python-38701D?style=for-the-badge&logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/Flet-007ACC?style=for-the-badge&logo=flutter&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-yellow.style=for-the-badge)

---

## 🚀 Demonstração Online

O aplicativo foi publicado na nuvem e pode ser acessado de qualquer dispositivo (celular, tablet ou computador):

📱 **[Acessar o Web App Online](https://meu-teste-speed.onrender.com)**

---

## 📱 Recursos e Funcionalidades

* 🚀 **Medição em Tempo Real:** Mede velocidade de Download, Upload e Ping (Latência).
* 📱 **Interface Responsiva (Mobile First):** Layout adaptado para uso em smartphones e desktops.
* 📲 **Suporte a PWA:** Pode ser instalado direto na tela inicial do celular como um aplicativo nativo.
* 🖥️ **Versão Desktop:** Possui versão em interface gráfica para Windows/Linux (`CustomTkinter`).
* ☁️ **Deploy Automatizado:** Hospedado no Render com integração contínua via GitHub.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Interface Web/Mobile:** [Flet](https://flet.dev/) (framework baseado em Flutter)
- **Interface Desktop:** CustomTkinter
- **Medição de Rede:** `speedtest-cli`
- **Hospedagem:** Render Cloud Services

---

## 📂 Estrutura do Projeto

```text
├── app_mobile.py       # Aplicação Web/Mobile em Flet (PWA)
├── gui.py              # Interface Desktop (CustomTkinter)
├── main.py             # Script CLI via terminal
├── requirements.txt    # Lista de dependências Python
└── .gitignore          # Arquivos ignorados pelo Git
```

## ⚙️ Como Executar o Projeto Localmente

### Pré-requisitos

- Python 3.10 ou superior instalado
- Virtualenv ativo (opcional, mas recomendado)

### Passo a passo

1. Clone este repositório:

```bash
git clone https://github.com/vitorf-vcm2025/teste-internet-app.git
cd teste-internet-app
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute a versão Web/Mobile:

```bash
python app_mobile.py
```

Ou execute a versão Desktop GUI:

```bash
python gui.py
```

## ✉️ Autor

Desenvolvido por Vitor Fernandes.
