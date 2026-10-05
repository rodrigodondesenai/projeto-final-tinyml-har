"""Baixa somente da UCI; valida ZIP e registra SHA256. Nao exige TensorFlow."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://archive.ics.uci.edu/static/public/240/human+activity+recognition+using+smartphones.zip"


def safe_extract(archive, destination):
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError(f"Caminho inseguro no ZIP: {member.filename}")
        if z.testzip() is not None:
            raise ValueError("ZIP corrompido")
        z.extractall(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, help="ZIP oficial baixado manualmente")
    args = parser.parse_args()
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    archive = args.archive or raw / "uci_har_official.zip"
    if not archive.exists():
        temporary = archive.with_suffix(".part")
        print(f"Download oficial: {URL}", flush=True)
        with urllib.request.urlopen(URL, timeout=120) as response, temporary.open("wb") as out:
            shutil.copyfileobj(response, out)
        temporary.replace(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    safe_extract(archive, raw)
    nested = raw / "UCI HAR Dataset.zip"
    if nested.exists():
        safe_extract(nested, raw)
    if not (raw / "UCI HAR Dataset/train/Inertial Signals/total_acc_x_train.txt").exists():
        raise FileNotFoundError("O ZIP nao contem os sinais inerciais UCI HAR esperados")
    provenance = {"url": URL, "archive_sha256": digest, "license": "CC BY 4.0",
                  "doi": "10.24432/C54S4K"}
    (ROOT / "data/provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Dataset pronto. SHA256: {digest}")


if __name__ == "__main__":
    main()
