import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from deepface import DeepFace
from pathlib import Path
import sys

PASTA_DEPUTADOS = Path("referencias/deputados")
FOTO_TESTE = sys.argv[1] if len(sys.argv) > 1 else None

THRESHOLD = 0.55
THRESHOLD_AUTO = 0.45

if not FOTO_TESTE:
    print("Uso: python teste_reconhecimento.py caminho/para/foto.jpg")
    sys.exit(1)

print(f"\nAnalisando: {FOTO_TESTE}\n")

try:
    resultado = DeepFace.find(
        img_path=FOTO_TESTE,
        db_path=str(PASTA_DEPUTADOS),
        model_name="ArcFace",
        detector_backend="retinaface",
        distance_metric="cosine",
        threshold=THRESHOLD,
        silent=True
    )

    # Agrega melhor match por deputado em todos os rostos
    melhores = {}
    for df in resultado:  # itera sobre cada rosto detectado
        if len(df) == 0:
            continue
        for _, row in df.iterrows():
            arquivo = Path(row["identity"]).stem
            nome = "_".join(arquivo.split("_")[:-1]).replace("_", " ").title()
            distancia = row["distance"]
            if nome not in melhores or distancia < melhores[nome]:
                melhores[nome] = distancia

    if not melhores:
        print("Nenhum deputado reconhecido.")
        sys.exit(0)

    print("Deputados reconhecidos:")
    for nome, distancia in sorted(melhores.items(), key=lambda x: x[1]):
        confianca = round((1 - distancia) * 100, 1)
        status = "✓ pré-aprovado" if distancia < THRESHOLD_AUTO else "? revisar"
        print(f"  {status} — {nome} ({confianca}%)")

except Exception as e:
    print(f"Erro: {e}")