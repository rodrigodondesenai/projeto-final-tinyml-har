"""Seleciona o build existente no Wokwi, equivalente ao script PowerShell."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("REPLAY", "LIVE"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = "build-live" if args.mode == "LIVE" else "build"
    for artifact in ("flasher_args.json", "tinyml_har.elf"):
        if not (root / "firmware" / folder / artifact).is_file():
            parser.error(f"Build ausente. Execute bash scripts/build_firmware.sh {args.mode} primeiro.")
    (root / "wokwi.toml").write_text(
        "[wokwi]\nversion = 1\n"
        f"firmware = 'firmware/{folder}/flasher_args.json'\n"
        f"elf = 'firmware/{folder}/tinyml_har.elf'\n",
        encoding="utf-8",
    )
    print(f"Wokwi configurado para {args.mode}. Pare a simulacao e execute Wokwi: Start Simulator.")


if __name__ == "__main__":
    main()
