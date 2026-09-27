"""Ponto de entrada executável do simulador de memória virtual."""

from config import validate_configuration


def main() -> int:
    """Valida a fundação do projeto enquanto as próximas etapas não estão prontas."""

    validate_configuration()
    print("Etapa 1 carregada: configuração, modelos e contratos estão válidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
