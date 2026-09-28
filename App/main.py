"""Ponto de entrada executável do simulador de memória virtual."""

import sys

import config
from io_utils import read_backing_store, read_logical_addresses


def main() -> int:
    """Valida a configuração e carrega as entradas necessárias ao simulador."""

    try:
        config.validate_configuration()
        logical_addresses = read_logical_addresses(
            config.LOGICAL_ADDRESSES_FILE_PATH,
            config.MAXIMUM_LOGICAL_ADDRESS,
        )
        ## Observações, lendo o arquivo manualmente após a função read_backing_stroe
        ## deu para perceber que o arquivo binario parece um array de inteiros de 4 bytes
        ## em sequencia
        backing_store_bytes = read_backing_store(
            config.BACKING_STORE_FILE_PATH,
            config.VIRTUAL_MEMORY_SIZE_BYTES,
        )
    except (OSError, ValueError) as error:
        print(f"Erro ao carregar os dados: {error}", file=sys.stderr)
        return 1
    
    # for i in range(100):
    #     print(f"{backing_store_bytes[i]}\n")
    
    print(f"Endereços lógicos carregados: {len(logical_addresses)}")
    print(f"Bytes carregados do backing store: {len(backing_store_bytes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
