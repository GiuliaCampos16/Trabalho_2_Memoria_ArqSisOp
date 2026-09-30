"""Testes dos leitores de endereços e da memória secundária simulada."""

import tempfile
import unittest
from pathlib import Path

from test_support import AddAppDirectoryToImportPath


AddAppDirectoryToImportPath()

import config  # noqa: E402  # Os arquivos simples de App entram no caminho acima.
from io_utils import ReadBackingStore, ReadLogicalAddresses  # noqa: E402


def InitializeExpectedAddressLista() -> list[int]:
    """Define os dois limites válidos esperados na leitura de endereços."""

    expectedAddressLista: list[int] = []
    expectedAddressLista.append(0)
    expectedAddressLista.append(65_535)
    return expectedAddressLista


def InitializeEmptyAddressLista() -> list[int]:
    """Define a saída esperada quando o arquivo de endereços está vazio."""

    emptyAddressLista: list[int] = []
    return emptyAddressLista


def InitializeInvalidCaseLista() -> list[tuple[str, str]]:
    """Reúne linhas inválidas e os trechos esperados nas mensagens de erro."""

    invalidCaseLista: list[tuple[str, str]] = []
    invalidCaseLista.append(("12\n \n", "linha está vazia"))
    invalidCaseLista.append(("12\nabc\n", "decimal inválido"))
    invalidCaseLista.append(("12\n-3\n", "negativo"))
    invalidCaseLista.append(("12\n65536\n", "supera o máximo"))
    return invalidCaseLista


def InitializeExpectedBackingStoreBytes() -> bytes:
    """Monta os bytes de fronteira usados no teste de leitura binária."""

    expectedBackingStoreBytes = bytearray()
    expectedBackingStoreBytes.append(0)
    expectedBackingStoreBytes.append(127)
    expectedBackingStoreBytes.append(128)
    expectedBackingStoreBytes.append(255)
    return bytes(expectedBackingStoreBytes)


def InitializeShortBackingStoreBytes() -> bytes:
    """Monta um backing store menor que o tamanho exigido pelo teste."""

    shortBackingStoreBytes = bytearray()
    shortBackingStoreBytes.append(1)
    shortBackingStoreBytes.append(2)
    shortBackingStoreBytes.append(3)
    return bytes(shortBackingStoreBytes)


class InputReaderTests(unittest.TestCase):
    """Verifica a conversão dos arquivos e as mensagens dos erros de entrada."""

    def test_addresses_accept_boundaries_and_surrounding_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectory:
            addressesPath = Path(temporaryDirectory) / "addresses.txt"
            addressesPath.write_text(" 0 \n 65535\t\n", encoding="utf-8")

            addressesLista = ReadLogicalAddresses(addressesPath, 65_535)

        self.assertEqual(addressesLista, InitializeExpectedAddressLista())

    def test_empty_addresses_file_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectory:
            addressesPath = Path(temporaryDirectory) / "empty.txt"
            addressesPath.write_text("", encoding="utf-8")

            addressesLista = ReadLogicalAddresses(addressesPath, 65_535)

        self.assertEqual(addressesLista, InitializeEmptyAddressLista())

    def test_invalid_address_lines_report_path_and_line(self) -> None:
        invalidCaseLista = InitializeInvalidCaseLista()

        for fileContents, expectedMessage in invalidCaseLista:
            with self.subTest(fileContents=fileContents):
                with tempfile.TemporaryDirectory() as temporaryDirectory:
                    addressesPath = Path(temporaryDirectory) / "addresses.txt"
                    addressesPath.write_text(fileContents, encoding="utf-8")

                    with self.assertRaises(ValueError) as raisedError:
                        ReadLogicalAddresses(addressesPath, 65_535)

                    errorMessage = str(raisedError.exception)
                    self.assertIn(str(addressesPath), errorMessage)
                    self.assertIn("linha 2", errorMessage)
                    self.assertIn(expectedMessage, errorMessage)

    def test_backing_store_returns_exact_binary_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectory:
            backingStorePath = Path(temporaryDirectory) / "backing.bin"
            expectedBytes = InitializeExpectedBackingStoreBytes()
            backingStorePath.write_bytes(expectedBytes)

            actualBytes = ReadBackingStore(backingStorePath, 4)

        self.assertEqual(actualBytes, expectedBytes)

    def test_backing_store_rejects_incorrect_size(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectory:
            backingStorePath = Path(temporaryDirectory) / "backing.bin"
            backingStorePath.write_bytes(InitializeShortBackingStoreBytes())

            with self.assertRaises(ValueError) as raisedError:
                ReadBackingStore(backingStorePath, 4)

        errorMessage = str(raisedError.exception)
        self.assertIn(str(backingStorePath), errorMessage)
        self.assertIn("4 bytes", errorMessage)
        self.assertIn("3 bytes", errorMessage)

    def test_missing_input_files_report_their_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectory:
            missingAddressesPath = Path(temporaryDirectory) / "missing.txt"
            missingBackingStorePath = Path(temporaryDirectory) / "missing.bin"

            with self.assertRaises(OSError) as addressesError:
                ReadLogicalAddresses(missingAddressesPath, 65_535)
            with self.assertRaises(OSError) as backingStoreError:
                ReadBackingStore(missingBackingStorePath, 4)

        self.assertIn(str(missingAddressesPath), str(addressesError.exception))
        self.assertIn(
            str(missingBackingStorePath), str(backingStoreError.exception)
        )

    def test_supplied_work_files_match_stage_two_assumptions(self) -> None:
        logicalAddressLista = ReadLogicalAddresses(
            config.logicalAddressesFilePath,
            config.maximumLogicalAddress,
        )
        backingStoreBytes = ReadBackingStore(
            config.backingStoreFilePath,
            config.virtualMemorySizeBytes,
        )

        self.assertEqual(len(logicalAddressLista), 1_000)
        self.assertEqual(min(logicalAddressLista), 39)
        self.assertEqual(max(logicalAddressLista), 65_449)
        self.assertEqual(len(backingStoreBytes), 65_536)


if __name__ == "__main__":
    unittest.main()
