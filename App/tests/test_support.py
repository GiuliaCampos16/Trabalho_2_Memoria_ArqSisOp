"""Utilitários compartilhados exclusivamente pelos testes automatizados."""

import sys
from pathlib import Path


def add_app_directory_to_import_path() -> None:
    """Permite que testes em App/tests importem os arquivos simples de App."""

    app_directory = Path(__file__).resolve().parent.parent
    app_directory_text = str(app_directory)
    if app_directory_text not in sys.path:
        sys.path.insert(0, app_directory_text)
