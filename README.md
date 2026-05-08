# Tagflow

**Automated metadata tagging and facial recognition pipeline for institutional photo archives.**

**English** | [Português](#português)

---

## About

Tagflow is an open-source system built to eliminate the operational bottleneck of manually tagging hundreds of photos per day in institutional settings — legislative assemblies, press agencies, public archives, and media organizations.

The system was designed around one core principle: **photo publication cannot wait for metadata processing**. Photos go live immediately after upload. Metadata enrichment happens in the background, without editorial pressure.

Built for the Legislative Assembly of Santa Catarina (ALESC), Brazil. Generalizable to any media-heavy institutional environment.

---

## Architecture

Tagflow operates in two independent layers that can be deployed separately or together.

### Layer 1 — Instant metadata (WordPress plugin)

No AI. No external dependencies. Runs in milliseconds at upload time.

```
Photographer exports photos following ISO 8601 naming convention
        ↓
Editor uploads to WordPress (same workflow as today)
        ↓
Plugin parses filename automatically:
  2026-05-08_S-ORDINARIA_BC-001.jpg
        ↓
Files from other departments ignored automatically
        ↓
WordPress fields populated immediately:
  Title, Caption, Alt text, Photographer,
  Event type, Commission, Municipality, Year
        ↓
Photo searchable by event, photographer, commission
```

### Layer 2 — Facial recognition (Python worker)

Runs asynchronously. Never blocks publication.

```
Python worker monitors photo folder on internal server
        ↓
RetinaFace detects faces in each image
        ↓
ArcFace compares against reference database of known individuals
        ↓
Results saved to review queue (JSON + SQLite audit log)
        ↓
Reviewer opens Flask interface when available — no deadline pressure
        ↓
Confirms identities, corrects errors, approves
        ↓
WordPress updated with deputy names and party affiliations
        ↓
Photo searchable by person and political party
```

---

## Project Structure

```
tagflow/
├── monitor.py                      # Python worker — folder watcher + facial recognition
├── app.py                          # Flask review web interface
├── teste_reconhecimento.py         # Diagnostic tool — threshold calibration and testing
├── requirements.txt
├── README.md
├── wordpress-plugin/
│   └── tagflow-connector/
│       └── tagflow-connector.php   # WordPress plugin (v1.8)
├── referencias/
│   └── deputados/                  # Reference photos — not versioned
├── fotos/
│   └── entrada/                    # Monitored input folder — not versioned
├── storage/
│   ├── json/                       # Review queue — not versioned
│   ├── embeddings/                 # Biometric data — not versioned
│   └── logs/                       # SQLite audit log — not versioned
└── templates/
    └── revisao.html                # Flask review interface template
```

---

## Filename Convention

The plugin only processes files that match the ALESC ISO 8601 convention — files from other departments are automatically ignored.

```
YYYY-MM-DD_EVENT-TYPE_[SUBTYPE]_[DESCRIPTION]_[MUN-CITY]_PHO-SEQ.jpg
```

### Examples

```
2026-05-08_S-ORDINARIA_BC-001.jpg
2026-05-08_COMISSAO_CCJ_REFORMA-TRIBUTARIA_MUN-CHAPECO_BC-001.jpg
2026-05-08_AUDIENCIA_SAUDE-PUBLICA_MUN-JOINVILLE_RC-003.jpg
2026-04-08_LITERARIO_100-ANOS-PONTE-HERCILIO-LUZ_DC-012.jpg
```

### Automatically extracted fields

| Segment       | Field                       | Example output                     |
| ------------- | --------------------------- | ---------------------------------- |
| `2026-05-08`  | Date, Year, Month           | 08/05/2026                         |
| `S-ORDINARIA` | Event type                  | Sessão Ordinária                   |
| `CCJ`         | Commission (after COMISSAO) | Comissão de Constituição e Justiça |
| `MUN-CHAPECO` | Municipality                | Chapecó                            |
| `BC`          | Photographer                | Bruno Collaço/Agência Alesc        |
| `001`         | Sequence number             | 001                                |

### Supported event types

| Code          | Name                         |
| ------------- | ---------------------------- |
| `S-ORDINARIA` | Sessão Ordinária             |
| `S-ESPECIAL`  | Sessão Especial              |
| `S-SOLENE`    | Sessão Solene                |
| `PAB`         | Programa Antonieta de Barros |
| `COMISSAO`    | Comissão (requires subtype)  |
| `AUDIENCIA`   | Audiência Pública            |
| `SEMINARIO`   | Seminário                    |
| `CURSO`       | Curso                        |
| `ENTREVISTA`  | Entrevista                   |
| `PODCAST`     | Podcast                      |
| `ESPECIAL`    | Matéria Especial             |
| `MOCAO`       | Moção de Aplauso             |
| `PRESIDENCIA` | Presidência                  |
| `SUSPENSAO`   | Suspensão de Sessão          |
| `LITERARIO`   | Lançamento Literário         |
| `EXPOARTE`    | Exposição de Arte            |
| `CULTURAL`    | Evento Cultural              |

### Municipality prefix

Use `MUN-` prefix to unambiguously identify any of SC's 295 municipalities:

```
MUN-CHAPECO       → Chapecó
MUN-SAO-JOSE      → São José
MUN-JOINVILLE     → Joinville
```

---

## WordPress Plugin (v1.8)

### What it does

- Runs automatically on every image upload — no action required from editors
- **Ignores files from other departments** — files without `YYYY-MM-DD_` prefix are skipped immediately
- Ignores unknown event types without touching the database
- Prevents accidental overwrite of manually edited fields (`_alesc_processado` flag)
- Fills native WordPress fields: title, caption, alt text
- Fills custom fields: photographer, date, event, commission, municipality, year
- Logs all processing decisions to PHP error log for auditability
- Compatible with PHP 7.2+ with safe fallback if `mbstring` is unavailable

### WordPress fields populated

| Field                     | Content                                                     |
| ------------------------- | ----------------------------------------------------------- |
| Title                     | Event type — Commission — Description — Municipality — Date |
| Caption                   | `Foto: Photographer Name/Agência Alesc`                     |
| Alt text                  | Event — Location — Assembleia Legislativa de Santa Catarina |
| `fotografo`               | Photographer full name — **adapt meta_key**                 |
| `alesc_data`              | Date DD/MM/YYYY — **adapt meta_key**                        |
| `alesc_evento`            | Event type name — **adapt meta_key**                        |
| `alesc_comissao`          | Commission full name — **adapt meta_key**                   |
| `alesc_municipio`         | Municipality — **adapt meta_key**                           |
| `alesc_ano`               | Year — **adapt meta_key**                                   |
| `alesc_filename_original` | Original filename for traceability                          |

> Meta keys marked **adapt meta_key** must be updated to match the actual field names in the WordPress installation.

### Installation

1. Copy `wordpress-plugin/tagflow-connector/` to `wp-content/plugins/`
2. Activate at Admin → Plugins
3. Update `meta_keys` marked `// adaptar` in `tagflow-connector.php`

---

## Python Worker — Facial Recognition

### Installation

```bash
git clone https://github.com/rodolfoespinola/tagflow.git
cd tagflow

python3 -m venv venv-tagflow
source venv-tagflow/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs}
```

### Reference database

Add reference photos to `referencias/deputados/`:

```
ana_campagnolo_01.jpg
ana_campagnolo_02.jpg
```

Multiple photos per person improve accuracy. 20+ photos with varied angles recommended. Tested with 359 reference photos across 40 deputies.

### Usage

```bash
# Start folder monitor
source venv-tagflow/bin/activate
python monitor.py

# Start review interface (separate terminal)
python app.py
```

Open `http://localhost:5000` in browser.

### Review workflow

1. Reviewer opens interface when time allows — no deadline pressure
2. Each photo shows AI suggestions with confidence scores
3. High-confidence matches (≥55%) require only confirmation
4. Reviewer corrects errors, adds unrecognized individuals, approves
5. WordPress updated via REST API with confirmed identities and parties

### Recognition performance

Tested on real ALESC plenary session photos:

| Metric                      | Result                               |
| --------------------------- | ------------------------------------ |
| Face detection confidence   | 1.0 on frontal and 3/4 shots         |
| Lateral shot recognition    | ~52% confidence (flagged for review) |
| Frontal shot recognition    | 60–76% confidence                    |
| Multiple deputies per photo | ✓ Tested up to 4 simultaneous        |
| Processing time per photo   | 3–8 seconds (CPU, no GPU required)   |

### Configuration

```python
THRESHOLD      = 0.55  # Maximum cosine distance to accept a match
THRESHOLD_AUTO = 0.45  # Below this → pre-approved automatically

FOTOGRAFOS = {
    "BC":  "Bruno Collaço/Agência Alesc",
    "DC":  "Daniel Conzi/Agência Alesc",
    "LGD": "Lucas Gabriel Diniz/Agência Alesc",
    "RC":  "Rodrigo Coelho/Agência Alesc",
    "AQ":  "Ana Quinto/Agência Alesc",
    "JB":  "Jefferson Baldo/Agência Alesc",
}
```

---

## Search Integration

Tagflow is designed to work with **Relevanssi** (WordPress search plugin). Once configured to index custom fields, photos become searchable by:

- Event type (Sessão Ordinária, CCJ, Audiência Pública...)
- Photographer name
- Municipality
- Deputy name and political party (after facial recognition review)
- Year and month

---

## Privacy & Data Protection

- Biometric embeddings stored **locally only** — never sent to external servers
- All processing runs on local hardware — CPU-based, no GPU required
- Purpose restricted to internal institutional archive indexing
- `storage/embeddings/` must not be web-accessible
- Full audit trail per image: reviewer, timestamp, AI suggestion, human correction
- Anti-reprocessing flag prevents accidental overwrite of manually edited fields
- Compliant with Brazil's LGPD and analogous EU frameworks (GDPR)

---

## Roadmap

### Current (v1.x)

- [x] WordPress plugin with filename parsing and multi-sector safety
- [x] Facial recognition with human review interface
- [x] SQLite audit log with full traceability

### Phase 2

- [ ] WordPress admin panel for processed uploads and reprocessing
- [ ] WP-CLI command for bulk reprocessing of existing library
- [ ] External configuration (JSON or WordPress options — no PHP edits required)
- [ ] REST API integration for deputy field updates
- [ ] Taxonomy support for faceted search

---

## Tech Stack

| Component             | Technology                                       |
| --------------------- | ------------------------------------------------ |
| Facial detection      | [RetinaFace](https://arxiv.org/abs/1905.00641)   |
| Facial recognition    | [ArcFace](https://arxiv.org/abs/1801.07698)      |
| ML framework          | [DeepFace](https://github.com/serengil/deepface) |
| Review interface      | [Flask](https://flask.palletsprojects.com/)      |
| WordPress integration | PHP plugin (v1.8)                                |
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

O sistema foi projetado em torno de um princípio central: **a publicação das fotos não pode esperar o processamento de metadados**. As fotos vão ao ar imediatamente após o upload. O enriquecimento de metadados acontece em segundo plano, sem pressão editorial.

Desenvolvido para a Assembleia Legislativa de Santa Catarina (ALESC), Brasil. Adaptável para qualquer organização com grande volume de produção fotográfica.

---

## Arquitetura

### Camada 1 — Metadados instantâneos (plugin WordPress)

Sem IA. Sem dependências externas. Executa em milissegundos no upload.

```
Fotógrafo exporta fotos seguindo a convenção de nomenclatura ISO 8601
        ↓
Editor faz upload no WordPress (fluxo igual ao atual)
        ↓
Plugin parseia o nome do arquivo automaticamente:
  2026-05-08_S-ORDINARIA_BC-001.jpg
        ↓
Arquivos de outros setores são ignorados automaticamente
        ↓
Campos do WordPress preenchidos imediatamente:
  Título, Legenda, Alt text, Fotógrafo,
  Tipo de evento, Comissão, Município, Ano
        ↓
Foto buscável por evento, fotógrafo e comissão
```

### Camada 2 — Reconhecimento facial (worker Python)

Executa de forma assíncrona. Nunca bloqueia a publicação.

```
Worker Python monitora pasta de fotos no servidor interno
        ↓
RetinaFace detecta rostos em cada imagem
        ↓
ArcFace compara com banco de referência dos deputados
        ↓
Resultados salvos na fila de revisão
        ↓
Revisor acessa interface Flask quando tiver tempo — sem pressão de prazo
        ↓
Confirma identificações, corrige erros, aprova
        ↓
WordPress atualizado com nomes dos deputados e partidos
        ↓
Foto buscável por nome de deputado e partido político
```

---

## Convenção de nomenclatura

O plugin só processa arquivos que seguem a convenção ISO 8601 da Agência ALESC. Arquivos de outros setores são ignorados automaticamente.

```
AAAA-MM-DD_TIPO-EVENTO_[SUBTIPO]_[DESCRICAO]_[MUN-CIDADE]_FOT-SEQ.jpg
```

Exemplos:

```
2026-05-08_S-ORDINARIA_BC-001.jpg
2026-05-08_COMISSAO_CCJ_REFORMA-TRIBUTARIA_MUN-CHAPECO_BC-001.jpg
2026-05-08_AUDIENCIA_SAUDE-PUBLICA_MUN-JOINVILLE_RC-003.jpg
```

O prefixo `MUN-` identifica municípios sem ambiguidade para todos os 295 municípios de SC.

---

## Plugin WordPress (v1.8)

- Executa automaticamente em cada upload — sem ação do editor
- **Ignora arquivos de outros setores** — sem o prefixo `AAAA-MM-DD_`, é ignorado imediatamente
- Ignora tipos de evento desconhecidos sem tocar no banco
- Impede sobrescrita acidental de campos editados manualmente
- Compatível com PHP 7.2+ com fallback seguro sem `mbstring`

### Instalação

1. Copiar `wordpress-plugin/tagflow-connector/` para `wp-content/plugins/`
2. Ativar em Admin → Plugins
3. Atualizar `meta_keys` marcados com `// adaptar` conforme os campos reais da instalação

---

## Worker Python — Reconhecimento facial

```bash
git clone https://github.com/rodolfoespinola/tagflow.git
cd tagflow

python3 -m venv venv-tagflow
source venv-tagflow/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs}
```

Adicionar fotos de referência em `referencias/deputados/` com o padrão `nome_deputado_01.jpg`. Múltiplas fotos por pessoa melhoram a precisão.

```bash
source venv-tagflow/bin/activate
python monitor.py          # monitor de pasta
python app.py              # interface de revisão (terminal separado)
# python teste_reconhecimento.py foto.jpg  # diagnóstico e calibração de threshold
```

Acessar `http://localhost:5000` no navegador.

---

## Privacidade e LGPD

- Embeddings biométricos armazenados localmente — nenhum dado enviado a servidores externos
- Todo o processamento roda no hardware local (CPU, sem GPU)
- Finalidade restrita a indexação interna de acervo institucional
- Log de auditoria rastreia todas as decisões humanas com revisor e timestamp
- Compatível com a LGPD e frameworks análogos da União Europeia (GDPR)
