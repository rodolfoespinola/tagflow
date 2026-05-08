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

Tagflow operates in two independent layers:

### Layer 1 — Instant metadata (WordPress plugin)

No AI. No external dependencies. Runs in milliseconds at upload time.

```
Photographer exports photos from Lightroom
with IPTC keywords embedded (event, commission, city)
        ↓
Editor uploads to WordPress (same workflow as today)
        ↓
Plugin intercepts upload via wp_generate_attachment_metadata hook
        ↓
Checks filename against ISO 8601 convention:
  YYYY-MM-DD_EVENT-TYPE_[SUBTYPE]_[DESC]_[MUN-CITY]_PHO-SEQ.jpg
        ↓
Files from other departments ignored automatically
        ↓
Parses filename → extracts date, event type, commission,
  municipality, photographer
        ↓
Auto-fills WordPress fields:
  Title, Caption, Alt text, Photographer,
  Event type, Commission, Municipality, Year
        ↓
Photo immediately searchable by event, photographer, commission
```

### Layer 2 — Facial recognition (Python worker)

Runs asynchronously. Never blocks publication.

```
Python worker monitors photo folder (Montreal server)
        ↓
RetinaFace detects faces in each image
        ↓
ArcFace compares against reference database of deputies
        ↓
Results saved to review queue (JSON + SQLite)
        ↓
Reviewer opens Flask interface when available
        ↓
Confirms identities, corrects errors, approves
        ↓
WordPress updated with deputy names and party affiliations
        ↓
Photo becomes searchable by person and political party
```

---

## Project Structure

```
tagflow/
├── monitor.py                      # Python worker — facial recognition engine
├── app.py                          # Flask review web interface
├── requirements.txt
├── wordpress-plugin/
│   ├── README.md
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

Tagflow follows the ALESC ISO 8601 Nomenclature Manual. The plugin only processes files that match this convention — files from other departments are automatically ignored.

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

| Code          | Name                                    |
| ------------- | --------------------------------------- |
| `S-ORDINARIA` | Sessão Ordinária                        |
| `S-ESPECIAL`  | Sessão Especial                         |
| `S-SOLENE`    | Sessão Solene                           |
| `PAB`         | Programa Antonieta de Barros            |
| `COMISSAO`    | Comissão (requires subtype — see below) |
| `AUDIENCIA`   | Audiência Pública                       |
| `SEMINARIO`   | Seminário                               |
| `CURSO`       | Curso                                   |
| `ENTREVISTA`  | Entrevista                              |
| `PODCAST`     | Podcast                                 |
| `ESPECIAL`    | Matéria Especial                        |
| `MOCAO`       | Moção de Aplauso                        |
| `PRESIDENCIA` | Presidência                             |
| `SUSPENSAO`   | Suspensão de Sessão                     |
| `LITERARIO`   | Lançamento Literário                    |
| `EXPOARTE`    | Exposição de Arte                       |
| `CULTURAL`    | Evento Cultural                         |

### Supported commissions (COMISSAO subtype)

| Code            | Full name                                 |
| --------------- | ----------------------------------------- |
| `CCJ`           | Comissão de Constituição e Justiça        |
| `EDUCACAO`      | Comissão de Educação e Cultura            |
| `SEGURANCA`     | Comissão de Segurança Pública             |
| `MEIO-AMBIENTE` | Comissão de Meio Ambiente                 |
| `ECONOMIA`      | Comissão de Economia                      |
| `SAUDE`         | Comissão de Saúde                         |
| `CPI`           | Comissão Parlamentar de Inquérito         |
| `MISTA`         | Comissão Mista                            |
| _(+ 15 others)_ | See `tagflow-connector.php` for full list |

### Municipality prefix

Use `MUN-` prefix to unambiguously identify municipalities. Works for all 295 SC cities without maintaining a complete list.

```
MUN-CHAPECO       → Chapecó
MUN-SAO-JOSE      → São José
MUN-JOINVILLE     → Joinville
MUN-ARARANGUA     → Araranguá
```

Cities in the built-in dictionary receive correct accents automatically. Cities outside the dictionary receive automatic formatting without accents — acceptable for MVP.

---

## WordPress Plugin (v1.8)

### What it does

- Runs automatically on every image upload — no action required
- Ignores files from other departments (no ISO 8601 date prefix → ignored)
- Ignores unknown event types → ignored without touching the database
- Prevents reprocessing of manually edited fields (`_alesc_processado` flag)
- Fills native WordPress fields: title, caption, alt text
- Fills custom fields: photographer, date, event, commission, municipality, year
- Logs all processing decisions to PHP error log for auditability
- Compatible with PHP 7.2+ — safe fallback if `mbstring` is not available

### WordPress fields populated

| Field                      | Source   | Notes                                        |
| -------------------------- | -------- | -------------------------------------------- |
| Title                      | Filename | Event type — Commission — Description — Date |
| Caption                    | Filename | `Foto: Photographer Name/Agência Alesc`      |
| Alt text                   | Filename | Event — Location — ALESC                     |
| `_wp_attachment_image_alt` | Filename | Standard WordPress alt text meta             |
| `fotografo`                | Filename | Photographer full name — **adapt meta_key**  |
| `alesc_data`               | Filename | Date DD/MM/YYYY — **adapt meta_key**         |
| `alesc_evento`             | Filename | Event type name — **adapt meta_key**         |
| `alesc_comissao`           | Filename | Commission full name — **adapt meta_key**    |
| `alesc_municipio`          | Filename | Municipality — **adapt meta_key**            |
| `alesc_ano`                | Filename | Year — **adapt meta_key**                    |
| `alesc_filename_original`  | Filename | Original filename for traceability — fixed   |

> Meta keys marked **adapt meta_key** must be updated to match the actual field names in the ALESC WordPress installation. Contact the WordPress developer for the correct `meta_key` values.

### Installation

1. Copy `wordpress-plugin/tagflow-connector/` to `wp-content/plugins/`
2. Activate at Admin → Plugins
3. Update `meta_keys` marked `// adaptar` in `tagflow-connector.php`

### Multi-sector safety

The plugin operates on an opt-in basis. Two filtering layers protect uploads from other departments:

1. **Filename must start with `YYYY-MM-DD_`** — immediate return if not matched
2. **Event type must be in the known types dictionary** — return without touching the database if not recognized

Files from Legal, HR, TV ALESC, or any other department are never processed.

---

## Lightroom Integration

Photographers export photos from Adobe Lightroom with IPTC keywords pre-embedded. This eliminates manual tagging at upload time.

### Setup

1. Import `ALESC_Palavras_Chave_Lightroom.txt` into Lightroom keyword panel
2. Create export preset with ISO 8601 filename template
3. Before each export, select relevant keywords (2–3 clicks per event batch)

### Keyword hierarchy

The keyword file includes hierarchical terms with synonyms for automatic expansion:

```
ALESC
  └── Sessões
        ├── Sessão Ordinária {plenário, votação, legislativo, ALESC, SC}
        ├── Sessão Especial  {plenário, legislativo, ALESC, SC}
        └── Sessão Solene    {plenário, homenagem, título honorífico, ALESC, SC}
  └── Comissões e Frentes Parlamentares
        ├── Comissão de Constituição e Justiça {CCJ, ALESC}
        └── ...
FOTÓGRAFOS
MUNICÍPIOS
DEPUTADOS
TEMAS
FORMATO
```

Selecting "Sessão Ordinária" automatically exports: `Sessão Ordinária, Plenário, Sessões, ALESC, Santa Catarina`.

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

Add reference photos to `referencias/deputados/` following this naming pattern:

```
ana_campagnolo_01.jpg
ana_campagnolo_02.jpg
lucas_neves_01.jpg
```

Multiple photos per person improve accuracy. 20+ photos with controlled lighting and varied angles recommended. The system was tested with 359 reference photos across 40 deputies.

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

1. Reviewer opens Flask interface when time allows — no deadline pressure
2. Each photo shows AI suggestions with confidence scores
3. Pre-approved matches (≥55% confidence) require only confirmation
4. Reviewer corrects errors, adds unrecognized individuals, approves
5. WordPress updated with confirmed deputy identities and party affiliations

### Recognition performance

Tested on real ALESC plenary session photos:

| Metric                       | Result                                         |
| ---------------------------- | ---------------------------------------------- |
| Face detection confidence    | 1.0 (maximum) on frontal/3/4 shots             |
| Recognition on lateral shots | ~52% confidence (correctly flagged for review) |
| Recognition on frontal shots | 60–76% confidence                              |
| Multiple deputies per photo  | ✓ Tested up to 4 simultaneous                  |
| Processing per photo         | 3–8 seconds (CPU, no GPU required)             |

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

Tagflow is designed to work with **Relevanssi** (WordPress search plugin). Once Relevanssi is configured to index custom fields and keywords, photos become searchable by:

- Event type (Sessão Ordinária, CCJ, Audiência Pública...)
- Photographer name
- Municipality
- Deputy name (after facial recognition review)
- Political party
- Year and month
- Thematic keywords (from Lightroom export)

No additional search plugin required beyond what is already installed.

---

## Privacy & Data Protection

- Biometric embeddings stored **locally only** — never sent to external servers
- All facial recognition runs on local hardware (CPU-based, no GPU required)
- Purpose restricted to internal institutional archive indexing
- `storage/embeddings/` must not be web-accessible
- Full audit trail: reviewer name, timestamp, AI suggestion, and human correction per image
- Anti-reprocessing flag prevents accidental overwrite of manually corrected fields
- Compliant with Brazil's LGPD and analogous EU frameworks (GDPR)

---

## Roadmap

### Current (v1.x) — MVP

- [x] WordPress plugin with filename parsing
- [x] Multi-sector safety (opt-in pattern matching)
- [x] Facial recognition with human review
- [x] Lightroom keyword hierarchy
- [x] SQLite audit log

### Phase 2

- [ ] WordPress admin panel for processed uploads
- [ ] WP-CLI command for bulk reprocessing of existing library
- [ ] External JSON/WordPress options for configuration (no PHP edits)
- [ ] WordPress REST API integration for deputy field updates
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
| Keyword export        | Adobe Lightroom                                  |

---

## Português

# Tagflow

**Pipeline automatizado de tagging de metadados e reconhecimento facial para acervos fotográficos institucionais.**

---

## Sobre

O Tagflow é um sistema open-source desenvolvido para eliminar o gargalo operacional de tagging manual de centenas de fotos por dia em ambientes institucionais — assembleias legislativas, agências de imprensa, arquivos públicos e veículos de comunicação.

O sistema foi projetado em torno de um princípio central: **a publicação das fotos não pode esperar o processamento de metadados**. As fotos vão ao ar imediatamente após o upload. O enriquecimento de metadados acontece em segundo plano, sem pressão editorial.

Desenvolvido para a Assembleia Legislativa de Santa Catarina (ALESC), Brasil.

---

## Arquitetura

### Camada 1 — Metadados instantâneos (plugin WordPress)

Sem IA. Sem dependências externas. Executa em milissegundos no upload.

```
Fotógrafo exporta pelo Lightroom com keywords IPTC embutidas
        ↓
Editor faz upload no WordPress (fluxo igual ao atual)
        ↓
Plugin verifica se o nome segue o padrão ISO 8601 da Agência ALESC
Arquivos de outros setores são ignorados automaticamente
        ↓
Parseia nome do arquivo → extrai data, tipo de evento,
  comissão, município, fotógrafo
        ↓
Preenche campos do WordPress automaticamente:
  Título, Legenda, Alt text, Fotógrafo,
  Tipo de evento, Comissão, Município, Ano
        ↓
Foto imediatamente buscável por evento, fotógrafo, comissão
```

### Camada 2 — Reconhecimento facial (worker Python)

Executa de forma assíncrona. Nunca bloqueia a publicação.

```
Worker Python monitora pasta de fotos no servidor Montreal
        ↓
RetinaFace detecta rostos em cada imagem
        ↓
ArcFace compara com banco de referência dos deputados
        ↓
Resultados salvos na fila de revisão
        ↓
Revisor acessa interface Flask quando tiver tempo
        ↓
Confirma identificações, corrige erros, aprova
        ↓
WordPress atualizado com nomes dos deputados e partidos
        ↓
Foto buscável por nome de deputado e partido político
```

---

## Convenção de nomenclatura

O Tagflow segue o Manual de Nomenclatura ISO 8601 da Agência ALESC:

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

## Segurança multisetorial

O plugin opera em modo opt-in. Duas camadas de filtragem protegem uploads de outros setores:

1. **Nome deve começar com `AAAA-MM-DD_`** — retorno imediato se não corresponder
2. **Tipo de evento deve estar no dicionário** — retorno sem tocar no banco se não reconhecido

Arquivos da Assessoria Jurídica, RH, TV ALESC ou qualquer outro setor nunca são processados.

---

## Instalação

### Plugin WordPress

1. Copiar `wordpress-plugin/tagflow-connector/` para `wp-content/plugins/`
2. Ativar em Admin → Plugins
3. Atualizar `meta_keys` marcados com `// adaptar` conforme os campos reais do WordPress da ALESC

### Worker Python

```bash
git clone https://github.com/rodolfoespinola/tagflow.git
cd tagflow

python3 -m venv venv-tagflow
source venv-tagflow/bin/activate

pip install -r requirements.txt

mkdir -p referencias/deputados fotos/entrada storage/{json,embeddings,logs}
```

### Lightroom

Importar `ALESC_Palavras_Chave_Lightroom.txt` no painel de palavras-chave do Lightroom. A hierarquia completa com sinônimos automáticos aparece pronta para uso.

---

## Privacidade e LGPD

- Embeddings biométricos armazenados localmente — nenhum dado enviado a servidores externos
- Todo o processamento de IA roda no hardware local (CPU, sem necessidade de GPU)
- Finalidade restrita a indexação interna de acervo institucional
- Log de auditoria rastreia todas as decisões humanas com revisor, timestamp e sugestão da IA
- Flag anti-reprocessamento impede sobrescrita acidental de campos corrigidos manualmente
- Compatível com a LGPD e frameworks análogos da União Europeia (GDPR)
