"""Ponto de entrada executável do simulador de memória virtual."""

import sys

import config
from io_utils import ReadBackingStore, ReadLogicalAddresses


def Main() -> int:
    """Valida a configuração e carrega as entradas necessárias ao simulador."""

    try:
        config.ValidateConfiguration()
        logicalAddressLista = ReadLogicalAddresses(
            config.logicalAddressesFilePath,
            config.maximumLogicalAddress,
        )
        # O arquivo fornecido codifica números em grupos de quatro bytes, mas o
        # simulador preserva cada byte individual para a paginação.
        backingStoreBytes = ReadBackingStore(
            config.backingStoreFilePath,
            config.virtualMemorySizeBytes,
        )
    except (OSError, ValueError) as error:
        print(f"Erro ao carregar os dados: {error}", file=sys.stderr)
        return 1

    print(f"Endereços lógicos carregados: {len(logicalAddressLista)}")
    print(f"Bytes carregados do backing store: {len(backingStoreBytes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(Main())
