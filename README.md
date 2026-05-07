# Tagflow

**Automated metadata tagging and facial recognition pipeline for institutional photo archives.**

**English** | [Português](#português)

---

## About

Tagflow is an open-source system built to eliminate the operational bottleneck of manually tagging hundreds of photos per day in institutional settings — legislative assemblies, press agencies, public archives, and media organizations.

The system combines:

- **Automatic folder monitoring** for incoming photos
- **Facial recognition** of known individuals via ArcFace + RetinaFace
- **Metadata extraction** from directory structure (date, location, event, photographer)
- **Human review web interface** for validating AI suggestions
- **IPTC injection** into approved files, compatible with WordPress, ResourceSpace, and other CMS
- **SQLite audit log** with full reviewer traceability

Built for the Legislative Assembly of Santa Catarina (ALESC), Brazil. Generalizable to any media-heavy institutional environment.

---

## Architecture

```
Photographer copies photos to server folder
        ↓
monitor.py detects new files automatically
        ↓
RetinaFace detects faces → ArcFace compares against reference database
        ↓
Metadata extracted from folder structure:
  Photos 2026 / 03 - March / Plenary / 03032026_Ordinary_Session_BC
        ↓
JSON saved to review queue
        ↓
Reviewer opens browser → Flask interface
        ↓
Confirms identities, corrects errors, approves
        ↓
ExifTool injects IPTC into original file:
  Keywords: person:Name, party:PL, Plenary, 2026...
        ↓
Photo ready for CMS upload
```

## Project Structure

```
tagflow/
├── monitor.py              # Folder watcher + facial recognition engine
├── app.py                  # Flask review web interface
├── requirements.txt
├── referencias/
│   └── deputados/          # Reference photos (not versioned)
├── fotos/
│   └── entrada/            # Monitored input folder (not versioned)
├── storage/
│   ├── json/               # Review queue (not versioned)
│   ├── embeddings/         # Biometric data (not versioned)
│   └── logs/               # SQLite audit log (not versioned)
└── templates/
    └── revisao.html        # Review interface template
```

## Folder Naming Convention

```
Photos 2026/
└── 03 - March/
    └── Plenary/
        └── 03032026_Ordinary_Session_BC/
            ├── 03032026_Ordinary_Session_BC-01.jpg
            └── ...
```

Automatically extracted fields:

| Segment            | Field                              |
| ------------------ | ---------------------------------- |
| `Photos 2026`      | Year                               |
| `03 - March`       | Month                              |
| `Plenary`          | Location                           |
| `03032026`         | Date (DD/MM/YYYY)                  |
| `Ordinary_Session` | Event                              |
| `BC`               | Photographer (mapped to full name) |

## Installation

### Requirements

- Python 3.10+
- ExifTool (`sudo apt install libimage-exiftool-perl`)
- CMake and build tools (`sudo apt install cmake build-essential`)

### Setup

```bash
git clone https://github.com/rodolfoespinola/tagflow.git
cd tagflow

python3 -m venv venv-tagflow
source venv-tagflow/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs}
```

### Reference Database

Add reference photos of known individuals to `referencias/deputados/` using this naming pattern:

```
person_name_01.jpg
person_name_02.jpg
```

Multiple photos per person improve accuracy. Controlled lighting and varied angles recommended.

## Usage

### 1. Start the folder monitor

```bash
source venv-tagflow/bin/activate
python monitor.py
```

### 2. Start the review interface (separate terminal)

```bash
source venv-tagflow/bin/activate
python app.py
```

Open `http://localhost:5000` in your browser.

### 3. Review workflow

1. Copy photos to `fotos/entrada/` following the folder structure
2. Monitor processes files automatically
3. Open the web interface and review AI suggestions
4. Confirm identities, add unrecognized individuals, remove incorrect matches
5. Click "Approve and inject IPTC"

## Configuration

### Photographer mapping

```python
PHOTOGRAPHERS = {
    "BC":  "Bruno Collaço/Agency Name",
    "DC":  "Daniel Conzi/Agency Name",
    # Add your team
}
```

### Recognition thresholds

```python
THRESHOLD      = 0.55  # Maximum distance to accept a match
THRESHOLD_AUTO = 0.45  # Below this → pre-approved automatically
```

## Privacy & Data Protection

- Biometric embeddings stored **locally only** — never sent to external servers
- Purpose restricted to internal institutional archive indexing
- `storage/embeddings/` must not be web-accessible
- Full audit trail: every approval records reviewer name and timestamp
- Compliant with Brazil's LGPD and analogous EU frameworks

## Tech Stack

| Component          | Technology                                           |
| ------------------ | ---------------------------------------------------- |
| Facial detection   | [RetinaFace](https://arxiv.org/abs/1905.00641)       |
| Facial recognition | [ArcFace](https://arxiv.org/abs/1801.07698)          |
| ML framework       | [DeepFace](https://github.com/serengil/deepface)     |
| Web interface      | [Flask](https://flask.palletsprojects.com/)          |
| Metadata injection | [ExifTool](https://exiftool.org/)                    |
| Folder monitoring  | [Watchdog](https://github.com/gorakhargosh/watchdog) |
| Audit log          | SQLite                                               |

---

## Português

# Tagflow

**Pipeline automatizado de tagging de metadados e reconhecimento facial para acervos fotográficos institucionais.**

## Sobre

O Tagflow é um sistema open-source desenvolvido para eliminar o gargalo operacional de tagging manual de centenas de fotos por dia em ambientes institucionais — assembleias legislativas, agências de imprensa, arquivos públicos e veículos de comunicação.

Desenvolvido para a Assembleia Legislativa de Santa Catarina (ALESC), Brasil. Adaptável para qualquer organização com grande volume de produção fotográfica.

## Arquitetura

```
Fotógrafo copia fotos para pasta no servidor
        ↓
monitor.py detecta arquivos novos automaticamente
        ↓
RetinaFace detecta rostos → ArcFace compara com banco de referência
        ↓
Metadados extraídos da estrutura de pastas
        ↓
JSON salvo na fila de revisão
        ↓
Revisor acessa interface Flask no navegador
        ↓
Confirma deputados, corrige erros, aprova
        ↓
ExifTool injeta IPTC no arquivo original
        ↓
Foto pronta para upload no WordPress
```

## Instalação

```bash
git clone https://github.com/rodolfoespinola/tagflow.git
cd tagflow

python3 -m venv venv-tagflow
source venv-tagflow/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs}
```

## Privacidade e LGPD

- Embeddings biométricos armazenados localmente, sem envio a servidores externos
- Finalidade restrita a indexação interna de acervo institucional
- Log de auditoria rastreia todas as decisões humanas com nome do revisor e timestamp
- Compatível com a LGPD e frameworks análogos da União Europeia
