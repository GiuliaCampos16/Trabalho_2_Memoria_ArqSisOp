"""Leitura dos endereços lógicos e da memória secundária simulada."""

from pathlib import Path


def InitializeLogicalAddressLista() -> list[int]:
    """Cria a lista que receberá endereços na ordem do arquivo de entrada."""

    logicalAddressLista: list[int] = []
    return logicalAddressLista


def ReadLogicalAddresses(
    logicalAddressesFilePath: Path, maximumLogicalAddress: int
) -> list[int]:
    """Lê um endereço decimal por linha, respeitando o limite da memória virtual."""

    logicalAddressLista: list[int] = InitializeLogicalAddressLista()

    try:
        with logicalAddressesFilePath.open(encoding="utf-8") as addressesFile:
            for lineNumber, fileLine in enumerate(addressesFile, start=1):
                addressText = fileLine.strip()
                location = f"{logicalAddressesFilePath}, linha {lineNumber}"

                if not addressText:
                    raise ValueError(f"{location}: a linha está vazia.")

                # Uma referência negativa merece uma mensagem própria: ela não pode
                # representar uma posição no espaço de endereços virtuais.
                if addressText.startswith("-"):
                    negativeDigits = addressText[1:]
                    if negativeDigits.isascii() and negativeDigits.isdecimal():
                        raise ValueError(
                            f"{location}: endereço negativo {addressText}."
                        )

                # Apenas dígitos ASCII são aceitos, como no arquivo fornecido. Assim,
                # números com sinal, separadores ou outros alfabetos não são ambíguos.
                if not addressText.isascii() or not addressText.isdecimal():
                    raise ValueError(
                        f"{location}: endereço decimal inválido {addressText!r}."
                    )

                logicalAddress = int(addressText)
                if logicalAddress > maximumLogicalAddress:
                    raise ValueError(
                        f"{location}: endereço {logicalAddress} supera o máximo "
                        f"{maximumLogicalAddress}."
                    )

                logicalAddressLista.append(logicalAddress)
    except OSError as error:
        raise OSError(
            f"Não foi possível ler o arquivo de endereços "
            f"{logicalAddressesFilePath}: {error}"
        ) from error
    except UnicodeError as error:
        raise ValueError(
            f"O arquivo de endereços {logicalAddressesFilePath} não está em UTF-8: "
            f"{error}"
        ) from error

    return logicalAddressLista


def ReadBackingStore(
    backingStoreFilePath: Path, expectedSizeBytes: int
) -> bytes:
    """Lê o arquivo binário que contém todas as páginas virtuais."""

    try:
        backingStoreBytes = backingStoreFilePath.read_bytes()
    except OSError as error:
        raise OSError(
            f"Não foi possível ler o backing store {backingStoreFilePath}: {error}"
        ) from error

    actualSizeBytes = len(backingStoreBytes)
    if actualSizeBytes != expectedSizeBytes:
        raise ValueError(
            f"O backing store {backingStoreFilePath} deve ter "
            f"{expectedSizeBytes} bytes; recebido: {actualSizeBytes} bytes."
        )

    return backingStoreBytes
