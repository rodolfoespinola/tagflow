# Tagflow

**Automated metadata tagging and facial recognition pipeline for institutional photo archives.**

**English** | [Português](#português)

---

## About

Tagflow is an open-source system built to eliminate the operational bottleneck of manually tagging hundreds of photos per day in institutional settings — legislative assemblies, press agencies, public archives, and media organizations.

The system combines:

- **WordPress plugin** that extracts metadata from filenames at upload time — no workflow changes
- **Facial recognition** of known individuals via ArcFace + RetinaFace, running asynchronously
- **Human review web interface** for validating AI suggestions without blocking publication
- **Automatic field population** — title, caption, alt text, description, photographer, event type, commission, municipality
- **SQLite audit log** with full reviewer traceability
- **LGPD/GDPR compliant** — all biometric processing runs locally, no data sent externally

Built for the Legislative Assembly of Santa Catarina (ALESC), Brazil. Generalizable to any media-heavy institutional environment.

---

## Architecture

The system is split into two independent layers:

**Layer 1 — Instant, no AI (WordPress plugin)**

```
Photographer uploads photo to WordPress
        ↓
Plugin intercepts upload via add_attachment hook
        ↓
Parses filename following ISO 8601 convention:
  2026-05-07_S-ORDINARIA_SESSAO-ORDINARIA_BC-001.jpg
        ↓
Auto-fills WordPress fields immediately:
  Title, Caption, Alt text, Description,
  Photographer, Event type, Commission, Municipality
        ↓
Writes file path to SQLite processing queue
```

**Layer 2 — Intelligent, asynchronous (Python worker)**

```
Python worker reads queue every 30 seconds
        ↓
RetinaFace detects faces in image
        ↓
ArcFace compares against reference database
        ↓
JSON saved to review queue
        ↓
Reviewer opens Flask interface when available
        ↓
Confirms identities, corrects errors, approves
        ↓
WordPress REST API updated with deputies and parties
        ↓
Photo becomes searchable by person and party
```

This design ensures **photos go live immediately** while metadata enrichment happens in the background without editorial pressure.

---

## Project Structure

```
tagflow/
├── monitor.py                  # Python worker — facial recognition engine
├── app.py                      # Flask review web interface
├── requirements.txt
├── wordpress-plugin/
│   ├── README.md
│   └── tagflow-connector/
│       └── tagflow-connector.php   # WordPress plugin
├── referencias/
│   └── deputados/              # Reference photos (not versioned)
├── fotos/
│   └── entrada/                # Monitored input folder (not versioned)
├── storage/
│   ├── json/                   # Review queue (not versioned)
│   ├── embeddings/             # Biometric data (not versioned)
│   └── logs/                   # SQLite audit log (not versioned)
└── templates/
    └── revisao.html            # Review interface template
```

---

## Filename Convention

Tagflow follows the ALESC ISO 8601 Nomenclature Manual:

```
YYYY-MM-DD_EVENT-TYPE_DESCRIPTION[_CITY]_PHO-SEQ.jpg
```

Examples:

```
2026-05-07_S-ORDINARIA_SESSAO-ORDINARIA_BC-001.jpg
2026-04-07_COMISSAO_CCJ_REUNIAO-ORDINARIA_LGD-012.jpg
2026-04-15_AUDIENCIA_MEIO-AMBIENTE_CHAPECO_RC-003.jpg
```

Automatically extracted fields:

| Segment            | Field             | Example                     |
| ------------------ | ----------------- | --------------------------- |
| `2026-05-07`       | Date (ISO 8601)   | 07/05/2026                  |
| `S-ORDINARIA`      | Event type        | Sessão Ordinária            |
| `SESSAO-ORDINARIA` | Description       | Sessão Ordinária            |
| `CHAPECO`          | City (optional)   | Chapecó                     |
| `BC`               | Photographer code | Bruno Collaço/Agência Alesc |
| `001`              | Sequence number   | 001                         |

### Supported Event Types

| Code          | Name                                        |
| ------------- | ------------------------------------------- |
| `S-ORDINARIA` | Sessão Ordinária                            |
| `S-ESPECIAL`  | Sessão Especial                             |
| `S-SOLENE`    | Sessão Solene                               |
| `PAB`         | Programa Antonieta de Barros                |
| `COMISSAO`    | Comissão (+ subtype e.g. `CCJ`, `EDUCACAO`) |
| `AUDIENCIA`   | Audiência Pública                           |
| `SEMINARIO`   | Seminário                                   |
| `CURSO`       | Curso                                       |
| `ENTREVISTA`  | Entrevista                                  |
| `PODCAST`     | Podcast                                     |
| `ESPECIAL`    | Matéria Especial                            |
| `MOCAO`       | Moção de Aplauso                            |
| `PRESIDENCIA` | Presidência                                 |
| `SUSPENSAO`   | Suspensão de Sessão                         |
| `LITERARIO`   | Lançamento Literário                        |
| `EXPOARTE`    | Exposição de Arte                           |
| `CULTURAL`    | Evento Cultural                             |

### Supported Commissions (COMISSAO subtype)

| Code            | Full name                                       |
| --------------- | ----------------------------------------------- |
| `CCJ`           | Comissão de Constituição e Justiça              |
| `EDUCACAO`      | Comissão de Educação e Cultura                  |
| `SEGURANCA`     | Comissão de Segurança Pública                   |
| `MEIO-AMBIENTE` | Comissão de Meio Ambiente                       |
| `ECONOMIA`      | Comissão de Economia                            |
| `SAUDE`         | Comissão de Saúde                               |
| `TRABALHO`      | Comissão de Trabalho                            |
| `TRANSPORTE`    | Comissão de Transporte                          |
| `TURISMO`       | Comissão de Turismo                             |
| `AGRICULTURA`   | Comissão de Agricultura e Desenvolvimento Rural |
| `ETICA`         | Comissão de Ética                               |
| `CPI`           | Comissão Parlamentar de Inquérito               |
| `MISTA`         | Comissão Mista                                  |
| _(+ 10 others)_ | See `tagflow-connector.php` for full list       |

---

## WordPress Integration

The plugin populates the following WordPress fields automatically on upload:

| WordPress field    | Source                         | Timing       |
| ------------------ | ------------------------------ | ------------ |
| Title              | Filename (event type + date)   | Instant      |
| Caption            | Filename (photographer credit) | Instant      |
| Alt text           | Filename (event + institution) | Instant      |
| Description        | Filename (full context)        | Instant      |
| Photographer       | Filename (code → full name)    | Instant      |
| Event type         | Filename (event type code)     | Instant      |
| Commission         | Filename (COMISSAO subtype)    | Instant      |
| Municipality       | Filename (optional city block) | Instant      |
| Event date         | Filename (ISO 8601 date)       | Instant      |
| Deputies (persons) | Facial recognition + review    | Asynchronous |
| Party              | Derived from deputy mapping    | Asynchronous |

> WordPress custom fields pending confirmation. Lines marked `# adaptar` in `tagflow-connector.php` must be updated with actual `meta_key` values.

---

## Installation

### Requirements

- Python 3.10+
- ExifTool (`sudo apt install libimage-exiftool-perl`)
- CMake and build tools (`sudo apt install cmake build-essential`)
- WordPress with media library access (for plugin)

### Python Worker Setup

```bash
git clone https://github.com/rodolfoespinola/tagflow.git
cd tagflow

python3 -m venv venv-tagflow
source venv-tagflow/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs}
```

### WordPress Plugin Setup

1. Copy `wordpress-plugin/tagflow-connector/` to `wp-content/plugins/`
2. Activate the plugin at Admin → Plugins
3. Update lines marked `# adaptar` in `tagflow-connector.php` with actual `meta_key` values from your WordPress installation

### Reference Database

Add reference photos of known individuals to `referencias/deputados/`:

```
ana_campagnolo_01.jpg
ana_campagnolo_02.jpg
lucas_neves_01.jpg
```

Multiple photos per person improve accuracy. Controlled lighting and varied angles recommended. The system supports 20+ reference photos per person.

---

## Usage

### 1. WordPress plugin (automatic)

Once activated, the plugin runs on every image upload with no action required.

### 2. Start the facial recognition worker

```bash
source venv-tagflow/bin/activate
python monitor.py
```

### 3. Start the review interface (separate terminal)

```bash
source venv-tagflow/bin/activate
python app.py
```

Open `http://localhost:5000` in your browser.

### 4. Review workflow

1. Reviewer opens the interface when time allows — no deadline pressure
2. Each photo shows AI suggestions with confidence scores
3. Pre-approved matches (≥55% confidence) require only confirmation
4. Reviewer corrects errors, adds unrecognized individuals, approves
5. WordPress is updated via REST API with confirmed identities

---

## Configuration

### Photographer codes (`monitor.py` and `tagflow-connector.php`)

```python
FOTOGRAFOS = {
    "BC":  "Bruno Collaço/Agência Alesc",
    "DC":  "Daniel Conzi/Agência Alesc",
    "LGD": "Lucas Gabriel Diniz/Agência Alesc",
    "RC":  "Rodrigo Coelho/Agência Alesc",
    "AQ":  "Ana Quinto/Agência Alesc",
    "JB":  "Jefferson Baldo/Agência Alesc",
}
```

### Recognition thresholds (`monitor.py`)

```python
THRESHOLD      = 0.55  # Maximum cosine distance to accept a match
THRESHOLD_AUTO = 0.45  # Below this → pre-approved automatically
```

### WordPress meta_keys (`tagflow-connector.php`)

Update lines marked `# adaptar` with actual field names from your WordPress setup:

```php
update_post_meta($attachment_id, 'fotografo', $meta['fotografo']); // adaptar
update_post_meta($attachment_id, 'alesc_data', $meta['data']);     // adaptar
update_post_meta($attachment_id, 'alesc_evento', $meta['tipo_nome']); // adaptar
```

---

## Privacy & Data Protection

- Biometric embeddings stored **locally only** — never sent to external servers
- All facial recognition runs on local hardware (CPU-based, no GPU required)
- Purpose restricted to internal institutional archive indexing
- `storage/embeddings/` must not be web-accessible
- Full audit trail: reviewer name, timestamp, AI suggestion, and human correction recorded per image
- Compliant with Brazil's LGPD and analogous EU frameworks (GDPR)

---

## Tech Stack

| Component             | Technology                                       |
| --------------------- | ------------------------------------------------ |
| Facial detection      | [RetinaFace](https://arxiv.org/abs/1905.00641)   |
| Facial recognition    | [ArcFace](https://arxiv.org/abs/1801.07698)      |
| ML framework          | [DeepFace](https://github.com/serengil/deepface) |
| Review interface      | [Flask](https://flask.palletsprojects.com/)      |
| WordPress integration | PHP plugin + REST API                            |
| Metadata injection    | [ExifTool](https://exiftool.org/)                |
| Processing queue      | SQLite                                           |
| Audit log             | SQLite                                           |

---

## Português

# Tagflow

**Pipeline automatizado de tagging de metadados e reconhecimento facial para acervos fotográficos institucionais.**

---

## Sobre

O Tagflow é um sistema open-source desenvolvido para eliminar o gargalo operacional de tagging manual de centenas de fotos por dia em ambientes institucionais — assembleias legislativas, agências de imprensa, arquivos públicos e veículos de comunicação.

O sistema foi projetado para **não alterar o fluxo editorial existente**: a foto vai ao ar imediatamente após o upload, e o enriquecimento de metadados acontece em segundo plano, sem pressão sobre a equipe.

Desenvolvido para a Assembleia Legislativa de Santa Catarina (ALESC), Brasil. Adaptável para qualquer organização com grande volume de produção fotográfica.

---

## Arquitetura

O sistema opera em duas camadas independentes:

**Camada 1 — Imediata, sem IA (plugin WordPress)**

```
Fotógrafo faz upload no WordPress
        ↓
Plugin intercepta o upload via hook add_attachment
        ↓
Interpreta o nome do arquivo (ISO 8601):
  2026-05-07_S-ORDINARIA_SESSAO-ORDINARIA_BC-001.jpg
        ↓
Preenche campos automaticamente:
  Título, Legenda, Alt text, Descrição,
  Fotógrafo, Tipo de evento, Comissão, Município, Data
        ↓
Registra arquivo na fila SQLite para processamento de IA
```

**Camada 2 — Inteligente, assíncrona (worker Python)**

```
Worker Python lê a fila a cada 30 segundos
        ↓
RetinaFace detecta rostos na imagem
        ↓
ArcFace compara com banco de referência dos deputados
        ↓
JSON salvo para revisão humana
        ↓
Revisor acessa interface Flask quando tiver tempo
        ↓
Confirma identificações, corrige erros, aprova
        ↓
WordPress REST API atualizada com deputados e partidos
        ↓
Foto passa a ser buscável por nome e partido
```

---

## Nomenclatura de arquivos

O Tagflow segue o Manual de Nomenclatura ISO 8601 da Agência ALESC:

```
AAAA-MM-DD_TIPO-EVENTO_DESCRICAO[_MUNICIPIO]_FOT-SEQ.jpg
```

Exemplos:

```
2026-05-07_S-ORDINARIA_SESSAO-ORDINARIA_BC-001.jpg
2026-04-07_COMISSAO_CCJ_REUNIAO-ORDINARIA_LGD-012.jpg
2026-04-15_AUDIENCIA_MEIO-AMBIENTE_CHAPECO_RC-003.jpg
```

> As categorias de pasta (`SESSOES`, `COMISSOES-E-FRENTES` etc.) existem apenas na estrutura de diretórios do servidor e não são extraídas dos nomes de arquivo.

---

## Integração com WordPress

O plugin preenche os seguintes campos automaticamente no upload:

| Campo WordPress | Origem                              | Momento    |
| --------------- | ----------------------------------- | ---------- |
| Título          | Nome do arquivo                     | Imediato   |
| Legenda         | Nome do arquivo (crédito)           | Imediato   |
| Alt text        | Nome do arquivo                     | Imediato   |
| Descrição       | Nome do arquivo                     | Imediato   |
| Fotógrafo       | Código → nome completo              | Imediato   |
| Tipo de evento  | Código do evento                    | Imediato   |
| Comissão        | Subtipo de COMISSAO                 | Imediato   |
| Município       | Bloco opcional                      | Imediato   |
| Data do evento  | Data ISO 8601                       | Imediato   |
| Deputados       | Reconhecimento facial + revisão     | Assíncrono |
| Partido         | Derivado do mapeamento de deputados | Assíncrono |

---

## Instalação

```bash
git clone https://github.com/rodolfoespinola/tagflow.git
cd tagflow

python3 -m venv venv-tagflow
source venv-tagflow/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs}
```

**Plugin WordPress:** copiar `wordpress-plugin/tagflow-connector/` para `wp-content/plugins/` e ativar em Admin → Plugins. Atualizar as linhas marcadas `# adaptar` com os `meta_key` reais do WordPress da ALESC.

---

## Privacidade e LGPD

- Embeddings biométricos armazenados localmente — nenhum dado enviado a servidores externos
- Todo o processamento de IA roda no hardware local (CPU, sem necessidade de GPU)
- Finalidade restrita a indexação interna de acervo institucional
- Diretório `storage/embeddings/` não deve ter acesso web
- Log de auditoria rastreia todas as decisões humanas com nome do revisor, timestamp, sugestão da IA e correção humana
- Compatível com a LGPD e frameworks análogos da União Europeia (GDPR)
