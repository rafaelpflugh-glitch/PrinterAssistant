# Printer Assistant (v1.0.0-beta)

Sistema profissional para diagnóstico técnico, gestão de suprimentos e produção de etiquetas para impressoras corporativas e térmicas (Lexmark, TSC, etc.).

---

## 🚀 Funcionalidades Principais

- **Descoberta e Ficha Técnica:**
  - Varredura de rede e identificação automática de impressoras (PJL, SNMP e EWS).
  - Leitura avançada de consumíveis: Toner, Unidade de Imagem e Fusor com números de série dos chips e data de instalação.
  - Avaliação automática de garantia de fotocondutor/drum.

- **Impressão de Etiquetas de Produção (TSC / TSPL):**
  - Etiquetas de consumíveis em 50x38mm (Toner e Unidade de Imagem).
  - Suporte a marcas REM, GLOBAL e LEXMARK com conversão automática de Part Numbers e código de barras 1D Code 128.
  - Sincronização inteligente de gap térmico.

- **Relatórios Técnicos:**
  - **Relatório de Ativo Patrimonial:** Etiqueta e identificação completa da máquina.
  - **Relatório RMA:** Processamento e emissão técnica para devolução de peças.
  - **Configuração e Suprimentos:** Preview na tela, impressão PCL direta na porta 9100 e geração de PDF A4 em `W:\TEC\Digitalizacao`.
  - **Análise da Unidade de Imagem:** Diagnóstico exclusivo do drum com verificação de garantia.

- **Geração de PDF Nativa:**
  - Gerador PDF 1.4 nativo integrado em Python puro (funciona sem dependência de DLLs ou PyMuPDF).

---

## 🛠️ Requisitos e Instalação

### Pré-requisitos
- **Windows 10 / 11**
- **Python 3.10+** (adicionado ao PATH do Windows)

### Instalação Rápida

1. Clone o repositório ou extraia a pasta do projeto:
   ```bash
   git clone https://github.com/SEU_USUARIO/PrinterAssistant.git
   cd PrinterAssistant
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Inicie o sistema:
   - Dê um duplo clique em `Iniciar_Printer_Assistant.bat`
   - Ou execute no terminal:
     ```bash
     python main.py
     ```

---

## ⚙️ Configuração de IPs (`config.json`)

O arquivo `config.json` define os IPs padrão das etiquetadoras térmicas na bancada técnica:
- `producao_ip_padrao`: IP padrão da etiquetadora TSC para consumíveis (ex: `192.168.14.111`).
- `producao_ip_excecao`: IP de contingência da bancada (ex: `192.168.14.151`).
- `rma_ip_padrao`: IP padrão para etiquetas de RMA e Ativo (100x150mm).

---

## 📦 Gerando o Executável (.exe) com PyInstaller

Para gerar um executável independente que seu colega possa rodar sem precisar de Python:

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "PrinterAssistant_Beta" --add-data "assets;assets" main.py
```

O aplicativo compilado estará localizado em `dist\PrinterAssistant_Beta\PrinterAssistant_Beta.exe`.
Basta compactar essa pasta em `.zip` e distribuir.
