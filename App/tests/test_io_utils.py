"""Testes dos leitores de endereços e da memória secundária simulada."""

import tempfile
import unittest
from pathlib import Path

from test_support import add_app_directory_to_import_path


add_app_directory_to_import_path()

import config  # noqa: E402  # Os arquivos simples de App entram no caminho acima.
from io_utils import read_backing_store, read_logical_addresses  # noqa: E402


class InputReaderTests(unittest.TestCase):
    """Verifica a conversão dos arquivos e as mensagens dos erros de entrada."""

    def test_addresses_accept_boundaries_and_surrounding_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            addresses_path = Path(temporary_directory) / "addresses.txt"
            addresses_path.write_text(" 0 \n 65535\t\n", encoding="utf-8")

            addresses = read_logical_addresses(addresses_path, 65_535)

        self.assertEqual(addresses, [0, 65_535])

    def test_empty_addresses_file_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            addresses_path = Path(temporary_directory) / "empty.txt"
            addresses_path.write_text("", encoding="utf-8")

            addresses = read_logical_addresses(addresses_path, 65_535)

        self.assertEqual(addresses, [])

    def test_invalid_address_lines_report_path_and_line(self) -> None:
        invalid_cases = (
            ("12\n \n", "linha está vazia"),
            ("12\nabc\n", "decimal inválido"),
            ("12\n-3\n", "negativo"),
            ("12\n65536\n", "supera o máximo"),
        )

        for file_contents, expected_message in invalid_cases:
            with self.subTest(file_contents=file_contents):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    addresses_path = Path(temporary_directory) / "addresses.txt"
                    addresses_path.write_text(file_contents, encoding="utf-8")

                    with self.assertRaises(ValueError) as raised_error:
                        read_logical_addresses(addresses_path, 65_535)

                    error_message = str(raised_error.exception)
                    self.assertIn(str(addresses_path), error_message)
                    self.assertIn("linha 2", error_message)
                    self.assertIn(expected_message, error_message)

    def test_backing_store_returns_exact_binary_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            backing_store_path = Path(temporary_directory) / "backing.bin"
            expected_bytes = bytes((0, 127, 128, 255))
            backing_store_path.write_bytes(expected_bytes)

            actual_bytes = read_backing_store(backing_store_path, 4)

        self.assertEqual(actual_bytes, expected_bytes)

    def test_backing_store_rejects_incorrect_size(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            backing_store_path = Path(temporary_directory) / "backing.bin"
            backing_store_path.write_bytes(bytes((1, 2, 3)))

            with self.assertRaises(ValueError) as raised_error:
                read_backing_store(backing_store_path, 4)

        error_message = str(raised_error.exception)
        self.assertIn(str(backing_store_path), error_message)
        self.assertIn("4 bytes", error_message)
        self.assertIn("3 bytes", error_message)

    def test_missing_input_files_report_their_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_addresses_path = Path(temporary_directory) / "missing.txt"
            missing_backing_store_path = Path(temporary_directory) / "missing.bin"

            with self.assertRaises(OSError) as addresses_error:
                read_logical_addresses(missing_addresses_path, 65_535)
            with self.assertRaises(OSError) as backing_store_error:
                read_backing_store(missing_backing_store_path, 4)

        self.assertIn(str(missing_addresses_path), str(addresses_error.exception))
        self.assertIn(
            str(missing_backing_store_path), str(backing_store_error.exception)
        )

    def test_supplied_work_files_match_stage_two_assumptions(self) -> None:
        logical_addresses = read_logical_addresses(
            config.LOGICAL_ADDRESSES_FILE_PATH,
            config.MAXIMUM_LOGICAL_ADDRESS,
        )
        backing_store_bytes = read_backing_store(
            config.BACKING_STORE_FILE_PATH,
            config.VIRTUAL_MEMORY_SIZE_BYTES,
        )

        self.assertEqual(len(logical_addresses), 1_000)
        self.assertEqual(min(logical_addresses), 39)
        self.assertEqual(max(logical_addresses), 65_449)
        self.assertEqual(len(backing_store_bytes), 65_536)


if __name__ == "__main__":
    unittest.main()
