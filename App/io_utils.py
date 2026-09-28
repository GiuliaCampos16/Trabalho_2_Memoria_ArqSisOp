"""Leitura dos endereços lógicos e da memória secundária simulada."""

from pathlib import Path


def read_logical_addresses(
    logical_addresses_file_path: Path, maximum_logical_address: int
) -> list[int]:
    """Lê um endereço decimal por linha, respeitando o limite da memória virtual."""

    logical_addresses: list[int] = []

    try:
        with logical_addresses_file_path.open(encoding="utf-8") as addresses_file:
            for line_number, file_line in enumerate(addresses_file, start=1):
                address_text = file_line.strip()
                location = f"{logical_addresses_file_path}, linha {line_number}"

                if not address_text:
                    raise ValueError(f"{location}: a linha está vazia.")

                # Uma referência negativa merece uma mensagem própria: ela não pode
                # representar uma posição no espaço de endereços virtuais.
                if address_text.startswith("-"):
                    negative_digits = address_text[1:]
                    if negative_digits.isascii() and negative_digits.isdecimal():
                        raise ValueError(
                            f"{location}: endereço negativo {address_text}."
                        )

                # Apenas dígitos ASCII são aceitos, como no arquivo fornecido. Assim,
                # números com sinal, separadores ou outros alfabetos não são ambíguos.
                if not address_text.isascii() or not address_text.isdecimal():
                    raise ValueError(
                        f"{location}: endereço decimal inválido {address_text!r}."
                    )

                logical_address = int(address_text)
                if logical_address > maximum_logical_address:
                    raise ValueError(
                        f"{location}: endereço {logical_address} supera o máximo "
                        f"{maximum_logical_address}."
                    )

                logical_addresses.append(logical_address)
    except OSError as error:
        raise OSError(
            f"Não foi possível ler o arquivo de endereços "
            f"{logical_addresses_file_path}: {error}"
        ) from error
    except UnicodeError as error:
        raise ValueError(
            f"O arquivo de endereços {logical_addresses_file_path} não está em UTF-8: "
            f"{error}"
        ) from error

    return logical_addresses


def read_backing_store(
    backing_store_file_path: Path, expected_size_bytes: int
) -> bytes:
    """Lê o arquivo binário que contém todas as páginas virtuais."""

    try:
        backing_store_bytes = backing_store_file_path.read_bytes()
    except OSError as error:
        raise OSError(
            f"Não foi possível ler o backing store {backing_store_file_path}: {error}"
        ) from error

    actual_size_bytes = len(backing_store_bytes)
    if actual_size_bytes != expected_size_bytes:
        raise ValueError(
            f"O backing store {backing_store_file_path} deve ter "
            f"{expected_size_bytes} bytes; recebido: {actual_size_bytes} bytes."
        )

    return backing_store_bytes
