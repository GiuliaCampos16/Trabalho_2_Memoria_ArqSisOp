"""Contratos para leitura dos arquivos fornecidos ao simulador."""

from pathlib import Path


def read_logical_addresses(
    logical_addresses_file_path: Path, maximum_logical_address: int
) -> list[int]:
    """Lê e valida a sequência de endereços lógicos do arquivo texto."""

    raise NotImplementedError("A leitura de endereços será implementada na Etapa 2.")


def read_backing_store(
    backing_store_file_path: Path, expected_size_bytes: int
) -> bytes:
    """Lê a memória secundária e valida seu tamanho em bytes."""

    raise NotImplementedError("A leitura do backing store será implementada na Etapa 2.")
