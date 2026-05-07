import os
import json
import sqlite3
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

app = Flask(__name__)

PASTA_JSON   = Path("storage/json")
PASTA_LOGS   = Path("storage/logs")
DB_PATH      = PASTA_LOGS / "auditoria.db"
REVISOR_PADRAO = ""

FOTOGRAFOS = {
    "BC":  "Bruno Collaço/Agência Alesc",
    "DC":  "Daniel Conzi/Agência Alesc",
    "LGD": "Lucas Gabriel Diniz/Agência Alesc",
    "RC":  "Rodrigo Coelho/Agência Alesc",
    "AQ":  "Ana Quinto/Agência Alesc",
    "JB":  "Jefferson Baldo/Agência Alesc",
}

DEPUTADOS_PARTIDOS = {
    "Alex Brasil": "PL",
    "Altair Silva": "PP",
    "Ana Campagnolo": "PL",
    "Antidio Lunelli": "MDB",
    "Berlanda": "PSD",
    "Camilo Martins": "PL",
    "Carlos Humberto": "PL",
    "Dr. Vicente Caropreso": "União Brasil",
    "Fabiano Da Luz": "PT",
    "Fernando Krelling": "MDB",
    "Ivan Naatz": "PL",
    "Jair Miotto": "PL",
    "Jerry Comper": "MDB",
    "Jesse Lopes": "PL",
    "Jose Milton Scheffer": "PP",
    "Julio Garcia": "PSD",
    "Junior Cardoso": "PL",
    "Lucas Neves": "Republicanos",
    "Luciane Carminatti": "PT",
    "Marcius Machado": "PL",
    "Marcos Da Rosa": "PL",
    "Marcos Vieira": "PSDB",
    "Mario Motta": "PSD",
    "Marquito": "PSOL",
    "Matheus Cadorin": "Novo",
    "Mauricio Eskudlark": "PL",
    "Mauricio Peixer": "PL",
    "Mauro De Nadal": "MDB",
    "Napoleao Bernardes": "PSD",
    "Neodi Saretta": "PT",
    "Oscar Gutz": "PL",
    "Padre Pedro Baldissera": "PT",
    "Pepe Collaco": "PP",
    "Rodrigo Fachini": "Podemos",
    "Rodrigo Minotto": "PDT",
    "Sargento Lima": "PL",
    "Sergio Guimaraes": "União Brasil",
    "Sergio Motta": "Republicanos",
    "Tiago Zilli": "MDB",
    "Volnei Weber": "MDB",
}

def remover_acentos(texto):
    if not texto:
        return ""
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")

def listar_deputados():
    """Lista todos os deputados únicos do banco de referência."""
    pasta = Path("referencias/deputados")
    nomes = set()
    for f in pasta.glob("*.jpg"):
        partes = f.stem.split("_")
        nome = "_".join(partes[:-1]).replace("_", " ").title()
        if nome:
            nomes.add(nome)
    return sorted(nomes)

def proxima_foto():
    """Retorna o próximo JSON da fila aguardando revisão."""
    pendentes = sorted(PASTA_JSON.glob("*.json"))
    for p in pendentes:
        try:
            dados = json.loads(p.read_text())
            if dados.get("status") == "aguardando_revisao":
                dados["json_path"] = str(p)
                # Traduz código do fotógrafo se necessário
                fot = dados.get("metadados", {}).get("fotografo", "")
                if fot and len(fot) <= 3 and fot.isupper():
                    dados["metadados"]["fotografo"] = FOTOGRAFOS.get(fot, fot)
                return dados
        except Exception:
            continue
    return None

def injetar_iptc(caminho_foto, metadados, deputados):
    """Injeta metadados IPTC no arquivo via ExifTool."""
    cmd = ["exiftool", "-overwrite_original", "-codedcharacterset=UTF8"]

    # Fotógrafo
    if metadados.get("fotografo"):
        cmd += [f"-IPTC:By-line={metadados['fotografo']}"]
        cmd += [f"-IPTC:Credit=Agência Alesc"]
        cmd += [f"-IPTC:Source=ALESC"]

    # Data
    if metadados.get("data"):
        try:
            partes = metadados["data"].split("/")
            data_iptc = f"{partes[2]}{partes[1]}{partes[0]}"
            cmd += [f"-IPTC:DateCreated={data_iptc}"]
        except Exception:
            pass

    # Local
    if metadados.get("local"):
        cmd += [f"-IPTC:Sub-location={metadados['local']}"]

    # Evento ou comissão
    evento = metadados.get("comissao") or metadados.get("evento") or ""
    if evento:
        cmd += [f"-IPTC:Event={evento}"]

    # Município
    if metadados.get("municipio"):
        cmd += [f"-IPTC:City={metadados['municipio']}"]

    # Estado fixo
    cmd += [f"-IPTC:Province-State=Santa Catarina"]
    cmd += [f"-IPTC:Country-Primary-Location-Name=Brasil"]

    # Keywords — deputados
    # Keywords — deputados e partidos
    partidos_incluidos = set()
    for dep in deputados:
        dep_ascii = remover_acentos(dep)
        cmd += [f"-IPTC:Keywords+=deputado:{dep_ascii}"]
        partido = DEPUTADOS_PARTIDOS.get(dep)
        if partido and partido not in partidos_incluidos:
            cmd += [f"-IPTC:Keywords+=partido:{partido}"]
            partidos_incluidos.add(partido)

    # Keywords — metadados de busca
    if metadados.get("local"):
        cmd += [f"-IPTC:Keywords+={remover_acentos(metadados['local'])}"]
    if evento:
        cmd += [f"-IPTC:Keywords+={remover_acentos(evento)}"]
    if metadados.get("ano"):
        cmd += [f"-IPTC:Keywords+={metadados['ano']}"]
    if metadados.get("municipio"):
        cmd += [f"-IPTC:Keywords+={remover_acentos(metadados['municipio'])}"]

    # Legenda automática
    if deputados:
        nomes = ", ".join(deputados)
        legenda = f"{evento} — {nomes}" if evento else nomes
        cmd += [f"-IPTC:Caption-Abstract={legenda}"]

    cmd.append(str(caminho_foto))

    resultado = subprocess.run(cmd, capture_output=True, text=True)
    return resultado.returncode == 0

def registrar_auditoria(dados, deputados_aprovados, revisor):
    """Registra aprovação no banco SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            UPDATE auditoria SET
                deputados_aprovados = ?,
                revisado_por = ?,
                revisado_em = ?,
                status = ?
            WHERE arquivo = ?
        """, (
            ", ".join(deputados_aprovados),
            revisor,
            datetime.now().isoformat(),
            "aprovado",
            dados["arquivo"]
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro auditoria: {e}")


@app.route("/")
def index():
    foto = proxima_foto()
    pendentes = sum(1 for p in PASTA_JSON.glob("*.json")
                   if json.loads(p.read_text()).get("status") == "aguardando_revisao")
    todos_deputados = listar_deputados()
    return render_template("revisao.html",
                           foto=foto,
                           pendentes=pendentes,
                           todos_deputados=todos_deputados,
                           revisor_padrao=REVISOR_PADRAO)

@app.route("/foto/<path:caminho>")
def servir_foto(caminho):
    """Serve a imagem para exibição no navegador."""
    return send_file(caminho)

@app.route("/aprovar", methods=["POST"])
def aprovar():
    dados_req = request.json
    json_path = Path(dados_req["json_path"])
    deputados_aprovados = dados_req["deputados_aprovados"]
    revisor = dados_req["revisor"]

    try:
        dados = json.loads(json_path.read_text())
        caminho_foto = Path(dados["arquivo"])

        # Injeta IPTC
        ok = injetar_iptc(caminho_foto, dados["metadados"], deputados_aprovados)
        if not ok:
            return jsonify({"ok": False, "erro": "Falha na injeção IPTC"})

        # Atualiza JSON
        dados["status"] = "aprovado"
        dados["deputados_aprovados"] = deputados_aprovados
        dados["revisado_por"] = revisor
        dados["revisado_em"] = datetime.now().isoformat()
        json_path.write_text(json.dumps(dados, ensure_ascii=False, indent=2))

        # Registra auditoria
        registrar_auditoria(dados, deputados_aprovados, revisor)

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)})

@app.route("/pular", methods=["POST"])
def pular():
    dados_req = request.json
    json_path = Path(dados_req["json_path"])
    try:
        dados = json.loads(json_path.read_text())
        dados["status"] = "pulado"
        json_path.write_text(json.dumps(dados, ensure_ascii=False, indent=2))
    except Exception:
        pass
    return jsonify({"ok": True})


if __name__ == "__main__":
    PASTA_LOGS.mkdir(parents=True, exist_ok=True)
    print("🌐 Interface de revisão: http://localhost:5000")
    app.run(debug=True, port=5000)