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

# Categorias que têm comissão/nome específico no lugar do evento
LOCAIS_COM_ESPECIFICIDADE = {
    "Comissoes e Frentes Parlamentares": "comissao",
    "Audiencias Publicas, Foruns e Seminarios": "municipio",
    "Eventos Gerais": "municipio",
}

# Normalização de nomes de locais para IPTC
LOCAIS_NORMALIZADOS = {
    "Plenario": "Plenário",
    "Comissoes e Frentes Parlamentares": "Comissões e Frentes Parlamentares",
    "Audiencias Publicas, Foruns e Seminarios": "Audiências Públicas, Fóruns e Seminários",
    "Sessao Especiais e Solenes": "Sessões Especiais e Solenes",
    "Presidencia": "Presidência",
    "Eventos Gerais": "Eventos Gerais",
    "Agencia ALESC": "Agência ALESC",
    "Fotos Painel": "Fotos Painel",
    "Galeria de Artes e Hall": "Galeria de Artes e Hall",
    "Gerencia Cultural": "Gerência Cultural",
    "Banco de Imagens": "Banco de Imagens",
}

DB_PATH          = PASTA_LOGS / "auditoria.db"
# ────────────────────────────────────────────────────────────────


def remover_acentos(texto):
    """Normaliza texto removendo acentos e caracteres especiais."""
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")


def extrair_metadados_caminho(caminho_foto):
    """
    Extrai metadados da estrutura de pastas e nome do arquivo.

    Estrutura atual:
    RAIZ / Fotos AAAA / MM - Mês / Local / DDMMAAAA_Evento_Fotografo / foto.jpg

    Estrutura futura:
    RAIZ / Fotos AAAA / MM - Mês / Local / DDMMAAAA_Evento / DDMMAAAA_Evento_Municipio_Tema_Fotografo_SEQ.jpg
    """
    partes = caminho_foto.relative_to(PASTA_RAIZ).parts
    meta = {
        "ano": None,
        "mes": None,
        "local": None,
        "local_normalizado": None,
        "comissao": None,
        "municipio": None,
        "data": None,
        "evento": None,
        "tema": None,
        "fotografo": None,
        "sequencial": None,
    }

    # Nível 0: "Fotos 2026" → ano
    if len(partes) > 0:
        match = re.search(r"\d{4}", partes[0])
        if match:
            meta["ano"] = match.group()

    # Nível 1: "03 - Março" → mês
    if len(partes) > 1:
        mes = re.sub(r"^\d+\s*-\s*", "", partes[1]).strip()
        meta["mes"] = mes

    # Nível 2: local
    if len(partes) > 2:
        local_raw = partes[2]
        local_ascii = remover_acentos(local_raw)
        meta["local"] = local_raw
        meta["local_normalizado"] = LOCAIS_NORMALIZADOS.get(local_ascii, local_raw)

    # Nível 3: pasta do evento "DDMMAAAA_Evento_Fotografo"
    if len(partes) > 3:
        nome_pasta = partes[3]
        # aceita underscore ou espaço como separador
        separador = "_" if "_" in nome_pasta else " "
        segmentos = nome_pasta.split(separador)

        # Data DDMMAAAA ou DDMMAA
        if segmentos:
            match_data = re.match(r"^(\d{6}|\d{8})$", segmentos[0])
            if match_data:
                d = segmentos[0]
                try:
                    if len(d) == 8:
                        meta["data"] = f"{d[0:2]}/{d[2:4]}/{d[4:8]}"
                    elif len(d) == 6:
                        meta["data"] = f"{d[0:2]}/{d[2:4]}/20{d[4:6]}"
                except Exception:
                    pass
                segmentos = segmentos[1:]

        # Fotógrafo no último segmento (estrutura atual)
        if segmentos and re.match(r"^[A-Z]{2,3}$", segmentos[-1]):
            codigo = segmentos[-1]
            meta["fotografo"] = FOTOGRAFOS.get(codigo, codigo)
            segmentos = segmentos[:-1]

        # O que sobrou depende do tipo de local
        local_ascii = remover_acentos(meta["local"] or "")
        tipo_especifico = LOCAIS_COM_ESPECIFICIDADE.get(local_ascii)

        if segmentos:
            if tipo_especifico == "comissao":
                # Tudo que sobrou é o nome da comissão
                meta["comissao"] = remover_acentos(" ".join(segmentos)).title()
            elif tipo_especifico == "municipio":
                # Primeiro segmento é o município
                meta["municipio"] = remover_acentos(segmentos[0]).title()
                if len(segmentos) > 1:
                    meta["evento"] = remover_acentos(segmentos[1]).title()
                if len(segmentos) > 2:
                    meta["tema"] = remover_acentos(" ".join(segmentos[2:])).title()
            else:
                # Plenário e demais — tudo é evento
                meta["evento"] = remover_acentos(" ".join(segmentos)).title()

    # Nome do arquivo: extrai fotógrafo e sequencial se estrutura futura
    nome_arquivo = caminho_foto.stem
    seg_arquivo = nome_arquivo.split("_")

    # Remove data do início
    if seg_arquivo and re.match(r"^(\d{6}|\d{8})$", seg_arquivo[0]):
        seg_arquivo = seg_arquivo[1:]

    # Sequencial no final
    seq_match = re.match(r"^(\d{2,}|[A-Z]+-\d+)$", seg_arquivo[-1]) if seg_arquivo else None
    if seq_match:
        meta["sequencial"] = seg_arquivo[-1]
        seg_arquivo = seg_arquivo[:-1]

    # Fotógrafo antes do sequencial
    if seg_arquivo and re.match(r"^[A-Z]{2,3}$", seg_arquivo[-1]):
        codigo = seg_arquivo[-1]
        meta["fotografo"] = FOTOGRAFOS.get(codigo, codigo)

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
        print(f"  📁 Local: {meta['local']} | Evento: {meta['evento']} | "
              f"Data: {meta['data']} | Fotógrafo: {meta['fotografo']}")

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