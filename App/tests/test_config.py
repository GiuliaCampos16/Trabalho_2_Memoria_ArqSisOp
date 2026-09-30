"""Testes da configuração estrutural criada na Etapa 1."""

import unittest
from pathlib import Path
from unittest.mock import patch

from test_support import AddAppDirectoryToImportPath


# App não é um pacote. O diretório é adicionado somente no processo de testes para que
# os mesmos imports locais usados por main.py continuem funcionando durante a descoberta.
AddAppDirectoryToImportPath()

import config  # noqa: E402  # Importação precisa ocorrer após o ajuste do caminho.


class ConfigurationTests(unittest.TestCase):
    """Verifica padrões, derivações e rejeição de premissas inválidas."""

    def test_default_configurable_values(self) -> None:
        self.assertEqual(config.logicalAddressBits, 16)
        self.assertEqual(config.pageSizeBytes, 256)
        self.assertEqual(config.physicalFrameCount, 128)
        self.assertEqual(config.tlbEntryCapacity, 16)
        self.assertEqual(config.pageReplacementPolicy, "fifo")
        self.assertEqual(config.tlbReplacementPolicy, "fifo")

    def test_default_derived_values(self) -> None:
        self.assertEqual(config.virtualMemorySizeBytes, 65_536)
        self.assertEqual(config.maximumLogicalAddress, 65_535)
        self.assertEqual(config.virtualPageCount, 256)
        self.assertEqual(config.pageOffsetBitCount, 8)
        self.assertEqual(config.virtualPageNumberBitCount, 8)
        self.assertEqual(config.physicalMemorySizeBytes, 32_768)
        self.assertEqual(config.physicalAddressBitCount, 15)

    def test_paths_are_resolved_from_project_location(self) -> None:
        expectedProjectRoot = Path(__file__).resolve().parent.parent.parent

        self.assertEqual(config.projectRootDirectory, expectedProjectRoot)
        self.assertEqual(
            config.logicalAddressesFilePath,
            expectedProjectRoot / "addresses.txt",
        )
        self.assertEqual(
            config.backingStoreFilePath,
            expectedProjectRoot / "BACKING_STORE.bin",
        )

    def test_default_configuration_is_valid(self) -> None:
        config.ValidateConfiguration()

    def test_alternative_configuration_is_valid(self) -> None:
        # A validação usa os valores editáveis; os derivados serão recalculados apenas
        # em uma nova execução, após editar config.py antes de iniciar o programa.
        with (
            patch.object(config, "logicalAddressBits", 17),
            patch.object(config, "pageSizeBytes", 512),
            patch.object(config, "physicalFrameCount", 64),
            patch.object(config, "tlbEntryCapacity", 8),
            patch.object(config, "pageReplacementPolicy", "second_chance"),
        ):
            config.ValidateConfiguration()

    def test_non_positive_logical_address_bits_are_rejected(self) -> None:
        with patch.object(config, "logicalAddressBits", 0):
            with self.assertRaisesRegex(ValueError, "logicalAddressBits"):
                config.ValidateConfiguration()

    def test_page_size_must_be_power_of_two(self) -> None:
        with patch.object(config, "pageSizeBytes", 300):
            with self.assertRaisesRegex(ValueError, "potência de dois"):
                config.ValidateConfiguration()

    def test_physical_memory_must_be_smaller_than_virtual_memory(self) -> None:
        with patch.object(config, "physicalFrameCount", 256):
            with self.assertRaisesRegex(ValueError, "estritamente menor"):
                config.ValidateConfiguration()

    def test_tlb_capacity_must_be_smaller_than_page_count(self) -> None:
        with patch.object(config, "tlbEntryCapacity", 256):
            with self.assertRaisesRegex(ValueError, "tlbEntryCapacity"):
                config.ValidateConfiguration()

    def test_unknown_page_replacement_policy_is_rejected(self) -> None:
        with patch.object(config, "pageReplacementPolicy", "random"):
            with self.assertRaisesRegex(ValueError, "pageReplacementPolicy"):
                config.ValidateConfiguration()

    def test_unknown_tlb_replacement_policy_is_rejected(self) -> None:
        with patch.object(config, "tlbReplacementPolicy", "lru"):
            with self.assertRaisesRegex(ValueError, "tlbReplacementPolicy"):
                config.ValidateConfiguration()


if __name__ == "__main__":
    unittest.main()
