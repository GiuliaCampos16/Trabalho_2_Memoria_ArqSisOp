"""Testes da configuração estrutural criada na Etapa 1."""

import unittest
from pathlib import Path
from unittest.mock import patch

from test_support import add_app_directory_to_import_path


# App não é um pacote. O diretório é adicionado somente no processo de testes para que
# os mesmos imports locais usados por main.py continuem funcionando durante a descoberta.
add_app_directory_to_import_path()

import config  # noqa: E402  # Importação precisa ocorrer após o ajuste do caminho.


class ConfigurationTests(unittest.TestCase):
    """Verifica padrões, derivações e rejeição de premissas inválidas."""

    def test_default_configurable_values(self) -> None:
        self.assertEqual(config.LOGICAL_ADDRESS_BITS, 16)
        self.assertEqual(config.PAGE_SIZE_BYTES, 256)
        self.assertEqual(config.PHYSICAL_FRAME_COUNT, 128)
        self.assertEqual(config.TLB_ENTRY_CAPACITY, 16)
        self.assertEqual(config.PAGE_REPLACEMENT_POLICY, "fifo")
        self.assertEqual(config.TLB_REPLACEMENT_POLICY, "fifo")

    def test_default_derived_values(self) -> None:
        self.assertEqual(config.VIRTUAL_MEMORY_SIZE_BYTES, 65_536)
        self.assertEqual(config.MAXIMUM_LOGICAL_ADDRESS, 65_535)
        self.assertEqual(config.VIRTUAL_PAGE_COUNT, 256)
        self.assertEqual(config.PAGE_OFFSET_BIT_COUNT, 8)
        self.assertEqual(config.VIRTUAL_PAGE_NUMBER_BIT_COUNT, 8)
        self.assertEqual(config.PHYSICAL_MEMORY_SIZE_BYTES, 32_768)
        self.assertEqual(config.PHYSICAL_ADDRESS_BIT_COUNT, 15)

    def test_paths_are_resolved_from_project_location(self) -> None:
        expected_project_root = Path(__file__).resolve().parent.parent.parent

        self.assertEqual(config.PROJECT_ROOT_DIRECTORY, expected_project_root)
        self.assertEqual(
            config.LOGICAL_ADDRESSES_FILE_PATH,
            expected_project_root / "addresses.txt",
        )
        self.assertEqual(
            config.BACKING_STORE_FILE_PATH,
            expected_project_root / "BACKING_STORE.bin",
        )

    def test_default_configuration_is_valid(self) -> None:
        config.validate_configuration()

    def test_non_positive_logical_address_bits_are_rejected(self) -> None:
        with patch.object(config, "LOGICAL_ADDRESS_BITS", 0):
            with self.assertRaisesRegex(ValueError, "LOGICAL_ADDRESS_BITS"):
                config.validate_configuration()

    def test_page_size_must_be_power_of_two(self) -> None:
        with patch.object(config, "PAGE_SIZE_BYTES", 300):
            with self.assertRaisesRegex(ValueError, "potência de dois"):
                config.validate_configuration()

    def test_physical_memory_must_be_smaller_than_virtual_memory(self) -> None:
        with patch.object(config, "PHYSICAL_FRAME_COUNT", 256):
            with self.assertRaisesRegex(ValueError, "estritamente menor"):
                config.validate_configuration()

    def test_tlb_capacity_must_be_smaller_than_page_count(self) -> None:
        with patch.object(config, "TLB_ENTRY_CAPACITY", 256):
            with self.assertRaisesRegex(ValueError, "TLB_ENTRY_CAPACITY"):
                config.validate_configuration()

    def test_unknown_page_replacement_policy_is_rejected(self) -> None:
        with patch.object(config, "PAGE_REPLACEMENT_POLICY", "random"):
            with self.assertRaisesRegex(ValueError, "PAGE_REPLACEMENT_POLICY"):
                config.validate_configuration()

    def test_unknown_tlb_replacement_policy_is_rejected(self) -> None:
        with patch.object(config, "TLB_REPLACEMENT_POLICY", "lru"):
            with self.assertRaisesRegex(ValueError, "TLB_REPLACEMENT_POLICY"):
                config.validate_configuration()


if __name__ == "__main__":
    unittest.main()
