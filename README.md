# ALESC Fotos — Sistema Inteligente de Gestão de Acervo Fotográfico

**Português** | [English](#english)

---

## Sobre o Projeto

Sistema de automação para gestão do acervo fotográfico da **Assembleia Legislativa de Santa Catarina (ALESC)**, desenvolvido para resolver o gargalo operacional de tagging manual de centenas de fotos por dia.

O sistema combina:

- **Monitoramento automático** da pasta de entrada de fotos
- **Reconhecimento facial** dos 40 deputados estaduais via ArcFace + RetinaFace
- **Extração de metadados** da estrutura de diretórios (data, local, evento, fotógrafo)
- **Interface web de revisão humana** para validação das sugestões da IA
- **Injeção IPTC** nos arquivos aprovados, compatível com WordPress e outros CMS
- **Log de auditoria** em SQLite com rastreabilidade completa

## Arquitetura

Fotógrafo copia fotos para pasta no servidor
↓
monitor.py detecta arquivos novos automaticamente
↓
RetinaFace detecta rostos → ArcFace compara com banco de referência
↓
Metadados extraídos da estrutura de pastas:
Fotos 2026 / 03 - Março / Plenário / 03032026_Sessao_Ordinaria_BC
↓
JSON salvo na fila de revisão
↓
Revisor acessa app.py (Flask) no navegador
↓
Confirma deputados, corrige erros, aprova
↓
ExifTool injeta IPTC no arquivo original:
Keywords: deputado:Nome, partido:PL, Plenario, 2026...
↓
Foto pronta para upload no WordPress

## Estrutura de Pastas

alesc-fotos/
├── monitor.py # Monitor de pasta + reconhecimento facial
├── app.py # Interface web Flask para revisão
├── requirements.txt
├── referencias/
│ └── deputados/ # Fotos de referência (não versionadas)
│ ├── ana_campagnolo_01.jpg
│ └── ...
├── fotos/
│ └── entrada/ # Pasta monitorada (não versionada)
├── storage/
│ ├── json/ # Fila de revisão (não versionada)
│ ├── embeddings/ # Dados biométricos (não versionados)
│ └── logs/ # Banco SQLite de auditoria (não versionado)
└── templates/
└── revisao.html # Interface de revisão

## Estrutura de Nomenclatura Esperada

Fotos 2026/
└── 03 - Março/
└── Plenário/
└── 03032026_Sessao_Ordinaria_BC/
├── 03032026_Sessao_Ordinaria_BC-01.jpg
└── ...

Campos extraídos automaticamente:
| Segmento | Campo |
|---|---|
| `Fotos 2026` | Ano |
| `03 - Março` | Mês |
| `Plenário` | Local |
| `03032026` | Data (DD/MM/AAAA) |
| `Sessao_Ordinaria` | Evento |
| `BC` | Fotógrafo (mapeado para nome completo) |

## Instalação

### Requisitos

- Python 3.10+
- ExifTool (`sudo apt install libimage-exiftool-perl`)
- CMake e build tools (`sudo apt install cmake build-essential`)

### Passos

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/alesc-fotos.git
cd alesc-fotos

# Crie o ambiente virtual
python3 -m venv venv-alesc-fotos
source venv-alesc-fotos/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Crie a estrutura de diretórios
mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs} templates
```

### Banco de Referência

Adicione fotos de referência dos deputados em `referencias/deputados/` com nomenclatura:
nome_do_deputado_01.jpg
nome_do_deputado_02.jpg

## Uso

### 1. Iniciar o monitor de pasta

```bash
source venv-alesc-fotos/bin/activate
python monitor.py
```

### 2. Iniciar a interface de revisão (terminal separado)

```bash
source venv-alesc-fotos/bin/activate
python app.py
```

Acesse `http://localhost:5000` no navegador.

### 3. Fluxo de revisão

1. Copie fotos para `fotos/entrada/` seguindo a estrutura de pastas
2. O monitor processa automaticamente
3. Acesse a interface web e revise as sugestões da IA
4. Confirme deputados, adicione os não reconhecidos, remova os incorretos
5. Clique "Aprovar e injetar IPTC"

## Configuração

### Fotógrafos (`monitor.py` e `app.py`)

```python
FOTOGRAFOS = {
    "BC":  "Bruno Collaço/Agência Alesc",
    "DC":  "Daniel Conzi/Agência Alesc",
    # ...
}
```

### Thresholds de reconhecimento

```python
THRESHOLD      = 0.55  # distância máxima para aceitar match
THRESHOLD_AUTO = 0.45  # abaixo disso → pré-aprovado automaticamente
```

## Privacidade e LGPD

- Embeddings biométricos armazenados localmente, sem envio a servidores externos
- Finalidade restrita a indexação interna de acervo institucional
- Diretório `storage/embeddings/` não deve ter acesso web
- Log de auditoria rastreia todas as decisões humanas

## Tecnologias

- [DeepFace](https://github.com/serengil/deepface) — framework de reconhecimento facial
- [ArcFace](https://arxiv.org/abs/1801.07698) — modelo de embedding facial
- [RetinaFace](https://arxiv.org/abs/1905.00641) — detector de rostos
- [Flask](https://flask.palletsprojects.com/) — interface web de revisão
- [ExifTool](https://exiftool.org/) — injeção de metadados IPTC
- [Watchdog](https://github.com/gorakhargosh/watchdog) — monitoramento de pasta
- [SQLite](https://www.sqlite.org/) — log de auditoria

---

## English

# ALESC Photos — Intelligent Photographic Archive Management System

## About

An automation system for managing the photographic archive of the **Legislative Assembly of Santa Catarina (ALESC)**, Brazil. Built to eliminate the operational bottleneck of manually tagging hundreds of photos per day.

The system combines:

- **Automatic folder monitoring** for incoming photos
- **Facial recognition** of 40 state deputies via ArcFace + RetinaFace
- **Metadata extraction** from directory structure (date, location, event, photographer)
- **Human review web interface** for validating AI suggestions
- **IPTC injection** into approved files, compatible with WordPress and other CMS
- **Audit log** in SQLite with full traceability

## Architecture

Photographer copies photos to server folder
↓
monitor.py detects new files automatically
↓
RetinaFace detects faces → ArcFace compares against reference database
↓
Metadata extracted from folder structure:
Fotos 2026 / 03 - Março / Plenário / 03032026_Sessao_Ordinaria_BC
↓
JSON saved to review queue
↓
Reviewer accesses app.py (Flask) in browser
↓
Confirms deputies, corrects errors, approves
↓
ExifTool injects IPTC into original file:
Keywords: deputado:Name, partido:PL, Plenario, 2026...
↓
Photo ready for WordPress upload

## Installation

### Requirements

- Python 3.10+
- ExifTool (`sudo apt install libimage-exiftool-perl`)
- CMake and build tools (`sudo apt install cmake build-essential`)

### Steps

```bash
git clone https://github.com/your-username/alesc-fotos.git
cd alesc-fotos

python3 -m venv venv-alesc-fotos
source venv-alesc-fotos/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs} templates
```

## Privacy and Data Protection

- Biometric embeddings stored locally, never sent to external servers
- Purpose restricted to internal institutional archive indexing
- `storage/embeddings/` directory must not have web access
- Audit log tracks all human review decisions

## Tech Stack

- [DeepFace](https://github.com/serengil/deepface) — facial recognition framework
- [ArcFace](https://arxiv.org/abs/1801.07698) — facial embedding model
- [RetinaFace](https://arxiv.org/abs/1905.00641) — face detector
- [Flask](https://flask.palletsprojects.com/) — review web interface
- [ExifTool](https://exiftool.org/) — IPTC metadata injection
- [Watchdog](https://github.com/gorakhargosh/watchdog) — folder monitoring
- [SQLite](https://www.sqlite.org/) — audit log
