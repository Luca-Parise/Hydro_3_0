from pathlib import Path

def load_sql(filename: str) -> str:
    # path alla cartella db_manager/scripts
    script_dir = Path(__file__).resolve().parents[1] / "scripts"
    # legge il file SQL e ritorna il contenuto come stringa
    return (script_dir / filename).read_text(encoding="utf-8")