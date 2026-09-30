"""Utilitários compartilhados exclusivamente pelos testes automatizados."""

import sys
from pathlib import Path


def AddAppDirectoryToImportPath() -> None:
    """Permite que testes em App/tests importem os arquivos simples de App."""

    appDirectory = Path(__file__).resolve().parent.parent
    appDirectoryText = str(appDirectory)
    if appDirectoryText not in sys.path:
        sys.path.insert(0, appDirectoryText)
