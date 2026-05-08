import os
import re
import json
import sqlite3
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
from deepface import DeepFace

# ─── CONFIGURAÇÃO ───────────────────────────────────────────────
PASTA_RAIZ       = Path("fotos/entrada")       # simula o servidor Montreal
PASTA_DEPUTADOS  = Path("referencias/deputados")
PASTA_JSON       = Path("storage/json")
PASTA_LOGS       = Path("storage/logs")

THRESHOLD        = 0.55   # distância máxima para aceitar match
THRESHOLD_AUTO   = 0.45   # abaixo disso → pré-aprovado

EXTENSOES        = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

FOTOGRAFOS = {
    "BC":  "Bruno Collaço/Agência Alesc",
    "DC":  "Daniel Conzi/Agência Alesc",
    "LGD": "Lucas Gabriel Diniz/Agência Alesc",
    "RC":  "Rodrigo Coelho/Agência Alesc",
    "AQ":  "Ana Quinto/Agência Alesc",
    "JB":  "Jefferson Baldo/Agência Alesc",
}

CATEGORIAS = {
    "AGENCIA-ALESC-E-OUTROS",
    "CURSOS-AUDIENCIAS-FORUNS-SEMINARIOS",
    "BANCO-DE-IMAGENS",
    "COMISSOES-E-FRENTES",
    "GALERIAS-E-HALL",
    "SESSOES",
}

TIPO_PARA_CATEGORIA = {
    "PODCAST":      "AGENCIA-ALESC-E-OUTROS",
    "ENTREVISTA":   "AGENCIA-ALESC-E-OUTROS",
    "MOCAO":        "AGENCIA-ALESC-E-OUTROS",
    "SUSPENSAO":    "AGENCIA-ALESC-E-OUTROS",
    "PRESIDENCIA":  "AGENCIA-ALESC-E-OUTROS",
    "ESPECIAL":     "AGENCIA-ALESC-E-OUTROS",
    "CULTURAL":     "GALERIAS-E-HALL",
    "EXPOARTE":     "GALERIAS-E-HALL",
    "LITERARIO":    "GALERIAS-E-HALL",
    "CURSO":        "CURSOS-AUDIENCIAS-FORUNS-SEMINARIOS",
    "AUDIENCIA":    "CURSOS-AUDIENCIAS-FORUNS-SEMINARIOS",
    "SEMINARIO":    "CURSOS-AUDIENCIAS-FORUNS-SEMINARIOS",
    "S-ORDINARIA":  "SESSOES",
    "S-ESPECIAL":   "SESSOES",
    "S-SOLENE":     "SESSOES",
    "PAB":          "SESSOES",
    "COMISSAO":     "COMISSOES-E-FRENTES",
}

TIPO_PARA_NOME = {
    "PODCAST":      "Podcast",
    "CULTURAL":     "Evento Cultural",
    "CURSO":        "Curso",
    "AUDIENCIA":    "Audiência Pública",
    "ENTREVISTA":   "Entrevista",
    "EXPOARTE":     "Exposição de Arte",
    "LITERARIO":    "Lançamento Literário",
    "MOCAO":        "Moção de Aplauso",
    "SEMINARIO":    "Seminário",
    "SUSPENSAO":    "Suspensão de Sessão",
    "S-ESPECIAL":   "Sessão Especial",
    "S-ORDINARIA":  "Sessão Ordinária",
    "S-SOLENE":     "Sessão Solene",
    "PAB":          "Programa Antonieta de Barros",
    "PRESIDENCIA":  "Presidência",
    "ESPECIAL":     "Matéria Especial",
    "COMISSAO":     "Comissão",
}

COMISSOES = {
    "AGRICULTURA":            "Comissão de Agricultura e Desenvolvimento Rural",
    "ASSUNTOS-MUNICIPAIS":    "Comissão de Assuntos Municipais",
    "BEM-ESTAR-ANIMAL":       "Comissão de Bem-Estar Animal",
    "COMBATE-AS-DROGAS":      "Comissão de Combate às Drogas",
    "CCJ":                    "Comissão de Constituição e Justiça",
    "DEFESA-CIVIL":           "Comissão de Defesa Civil",
    "DIREITOS-HUMANOS":       "Comissão de Direitos Humanos e Família",
    "ECONOMIA":               "Comissão de Economia",
    "EDUCACAO":               "Comissão de Educação e Cultura",
    "ESPORTE":                "Comissão de Esporte",
    "ETICA":                  "Comissão de Ética",
    "MEIO-AMBIENTE":          "Comissão de Meio Ambiente",
    "PESCA":                  "Comissão de Pesca e Aquicultura",
    "SEGURANCA":              "Comissão de Segurança Pública",
    "TRABALHO":               "Comissão de Trabalho",
    "TRANSPORTE":             "Comissão de Transporte",
    "TURISMO":                "Comissão de Turismo",
    "CONSUMIDOR":             "Comissão dos Direitos do Consumidor",
    "CRIANCA-E-ADOLESCENTE":  "Comissão dos Direitos da Criança e do Adolescente",
    "PESSOA-COM-DEFICIENCIA": "Comissão dos Direitos da Pessoa com Deficiência",
    "PESSOA-IDOSA":           "Comissão dos Direitos da Pessoa Idosa",
    "MISTA":                  "Comissão Mista",
    "CPI":                    "Comissão Parlamentar de Inquérito",
}

DB_PATH          = PASTA_LOGS / "auditoria.db"
# ────────────────────────────────────────────────────────────────


def remover_acentos(texto):
    """Normaliza texto removendo acentos e caracteres especiais."""
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")


def extrair_metadados_caminho(caminho_foto):
    """
    Extrai metadados da estrutura de pastas e nome do arquivo
    seguindo o Manual de Nomenclatura oficial da Agência ALESC.

    Estrutura de pasta:
    RAIZ / AAAA / MM / CATEGORIA / AAAA-MM-DD_TIPO_DESCRICAO[_MUNICIPIO] /

    Estrutura de arquivo:
    AAAA-MM-DD_TIPO_DESCRICAO[_MUNICIPIO]_COD-SEQ.jpg
    """
    partes = caminho_foto.relative_to(PASTA_RAIZ).parts
    meta = {
        "ano":        None,
        "mes":        None,
        "categoria":  None,
        "data":       None,
        "tipo":       None,
        "tipo_nome":  None,
        "descricao":  None,
        "comissao":   None,
        "municipio":  None,
        "fotografo":  None,
        "sequencial": None,
    }

    # Nível 0: ano (AAAA)
    if len(partes) > 0 and re.match(r"^\d{4}$", partes[0]):
        meta["ano"] = partes[0]

    # Nível 1: mês (MM)
    if len(partes) > 1 and re.match(r"^\d{2}$", partes[1]):
        meses = {
            "01": "Janeiro", "02": "Fevereiro", "03": "Março",
            "04": "Abril",   "05": "Maio",      "06": "Junho",
            "07": "Julho",   "08": "Agosto",    "09": "Setembro",
            "10": "Outubro", "11": "Novembro",  "12": "Dezembro"
        }
        meta["mes"] = meses.get(partes[1], partes[1])

    # Nível 2: categoria
    if len(partes) > 2 and partes[2].upper() in CATEGORIAS:
        meta["categoria"] = partes[2].upper()

    # Nível 3: pasta do evento AAAA-MM-DD_TIPO_DESCRICAO[_MUNICIPIO]
    if len(partes) > 3:
        blocos = partes[3].split("_")

        # Bloco 0: data AAAA-MM-DD
        if blocos and re.match(r"^\d{4}-\d{2}-\d{2}$", blocos[0]):
            try:
                dt = datetime.strptime(blocos[0], "%Y-%m-%d")
                meta["data"] = dt.strftime("%d/%m/%Y")
                if not meta["ano"]:
                    meta["ano"] = dt.strftime("%Y")
                if not meta["mes"]:
                    meta["mes"] = dt.strftime("%B")
            except ValueError:
                pass
            blocos = blocos[1:]

        # Bloco 1: tipo do evento
        if blocos:
            tipo_raw = blocos[0].upper()

            # Comissão tem subtipo: COMISSAO_CCJ → tipo=COMISSAO, comissao=CCJ
            if tipo_raw == "COMISSAO" and len(blocos) > 1:
                subtipo = blocos[1].upper()
                meta["tipo"] = "COMISSAO"
                meta["tipo_nome"] = TIPO_PARA_NOME.get("COMISSAO", "Comissão")
                meta["comissao"] = COMISSOES.get(subtipo, subtipo.replace("-", " ").title())
                meta["categoria"] = "COMISSOES-E-FRENTES"
                blocos = blocos[2:]
            else:
                meta["tipo"] = tipo_raw
                meta["tipo_nome"] = TIPO_PARA_NOME.get(tipo_raw, tipo_raw.replace("-", " ").title())
                if not meta["categoria"]:
                    meta["categoria"] = TIPO_PARA_CATEGORIA.get(tipo_raw)
                blocos = blocos[1:]

        # Blocos restantes: descrição e município opcional
        if blocos:
            # Município é o último bloco se não contiver hífen interno
            # e não for código de fotógrafo
            ultimo = blocos[-1].upper()
            if (not re.match(r"^[A-Z]{2,3}$", ultimo) and
                not re.match(r"^[A-Z]{2,3}-\d+$", ultimo) and
                len(blocos) > 1):
                meta["municipio"] = blocos[-1].replace("-", " ").title()
                blocos = blocos[:-1]

            meta["descricao"] = " ".join(
                b.replace("-", " ").title() for b in blocos
            )

    # Nome do arquivo: AAAA-MM-DD_TIPO_DESCRICAO[_MUNICIPIO]_COD-SEQ.jpg
    nome_arquivo = caminho_foto.stem.upper()
    seg_arquivo  = nome_arquivo.split("_")

    # Remove data do início se existir
    if seg_arquivo and re.match(r"^\d{4}-\d{2}-\d{2}$", seg_arquivo[0]):
        seg_arquivo = seg_arquivo[1:]

    # Último segmento: COD-SEQ (ex: BC-001)
    if seg_arquivo:
        ultimo = seg_arquivo[-1]
        match = re.match(r"^([A-Z]{2,3})-(\d+)$", ultimo)
        if match:
            codigo          = match.group(1)
            meta["sequencial"] = match.group(2)
            meta["fotografo"]  = FOTOGRAFOS.get(codigo, codigo)
            seg_arquivo = seg_arquivo[:-1]

    return meta

def reconhecer_deputados(caminho_foto):
    """Reconhece deputados na foto usando ArcFace + RetinaFace."""
    import shutil
    caminho_ascii = Path("/tmp/alesc_temp_foto.jpg")
    try:
        shutil.copy2(caminho_foto, caminho_ascii)
        resultado = DeepFace.find(
            img_path=str(caminho_ascii),
            db_path=str(PASTA_DEPUTADOS),
            model_name="ArcFace",
            detector_backend="retinaface",
            distance_metric="cosine",
            threshold=THRESHOLD,
            silent=True,
        )

        melhores = {}
        for df in resultado:
            if len(df) == 0:
                continue
            for _, row in df.iterrows():
                arquivo = Path(row["identity"]).stem
                nome = "_".join(arquivo.split("_")[:-1]).replace("_", " ").title()
                dist = row["distance"]
                if nome not in melhores or dist < melhores[nome]["distancia"]:
                    melhores[nome] = {
                        "distancia": round(dist, 4),
                        "confianca": round((1 - dist) * 100, 1),
                        "status": "pre_aprovado" if dist < THRESHOLD_AUTO else "revisar",
                    }

        return melhores

    except Exception as e:
        print(f"  ⚠ Erro no reconhecimento: {e}")
        return {}
    finally:
        if caminho_ascii.exists():
            caminho_ascii.unlink()


def salvar_json(caminho_foto, metadados, deputados):
    """Salva arquivo JSON na fila de revisão."""
    PASTA_JSON.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_json = f"{caminho_foto.stem}_{timestamp}.json"

    dados = {
        "arquivo": str(caminho_foto),
        "processado_em": datetime.now().isoformat(),
        "metadados": metadados,
        "deputados_sugeridos": deputados,
        "status": "aguardando_revisao",
        "revisado_por": None,
        "revisado_em": None,
    }

    destino = PASTA_JSON / nome_json
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2))
    return destino


def inicializar_banco():
    """Cria tabela de auditoria no SQLite se não existir."""
    PASTA_LOGS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo TEXT,
            processado_em TEXT,
            evento TEXT,
            local TEXT,
            fotografo TEXT,
            deputados_ia TEXT,
            deputados_aprovados TEXT,
            revisado_por TEXT,
            revisado_em TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()


def registrar_processamento(caminho_foto, metadados, deputados):
    """Registra o processamento inicial no banco de auditoria."""
    conn = sqlite3.connect(DB_PATH)
    deputados_ia = ", ".join(deputados.keys()) if deputados else ""
    conn.execute("""
        INSERT INTO auditoria
        (arquivo, processado_em, evento, local, fotografo, deputados_ia, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(caminho_foto),
        datetime.now().isoformat(),
        metadados.get("evento", ""),
        metadados.get("local", ""),
        metadados.get("fotografo", ""),
        deputados_ia,
        "aguardando_revisao",
    ))
    conn.commit()
    conn.close()


class MonitorFotos(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        caminho = Path(event.src_path)
        if caminho.suffix.lower() not in EXTENSOES:
            return

        # Aguarda o arquivo terminar de ser copiado
        time.sleep(2)

        print(f"\n📷 Nova foto detectada: {caminho.name}")

        # Extrai metadados da estrutura de pastas
        meta = extrair_metadados_caminho(caminho)
        evento_display = meta.get("comissao") or meta.get("tipo_nome") or "—"
        print(f"  📁 Categoria: {meta['categoria']} | "
            f"Tipo: {meta['tipo_nome']} | "
            f"Evento: {evento_display} | "
            f"Data: {meta['data']} | "
            f"Fotógrafo: {meta['fotografo']}")
        if meta.get("municipio"):
            print(f"  📍 Município: {meta['municipio']}")
        if meta.get("descricao"):
            print(f"  📝 Descrição: {meta['descricao']}")

        # Reconhecimento facial
        print(f"  🔍 Reconhecendo deputados...")
        deputados = reconhecer_deputados(caminho)

        if deputados:
            for nome, info in deputados.items():
                icone = "✓" if info["status"] == "pre_aprovado" else "?"
                print(f"  {icone} {nome} ({info['confianca']}%)")
        else:
            print(f"  — Nenhum deputado reconhecido")

        # Salva JSON na fila de revisão
        json_path = salvar_json(caminho, meta, deputados)
        print(f"  💾 Fila: {json_path.name}")

        # Registra no banco de auditoria
        registrar_processamento(caminho, meta, deputados)


def main():
    inicializar_banco()
    PASTA_RAIZ.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Monitor ALESC Fotos iniciado")
    print(f"   Monitorando: {PASTA_RAIZ.resolve()}")
    print(f"   Deputados:   {len(list(PASTA_DEPUTADOS.glob('*.jpg')))} fotos de referência")
    print(f"   Aguardando novas fotos...\n")

    observer = Observer()
    observer.schedule(MonitorFotos(), str(PASTA_RAIZ), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n⏹ Monitor encerrado.")

    observer.join()


if __name__ == "__main__":
    main()