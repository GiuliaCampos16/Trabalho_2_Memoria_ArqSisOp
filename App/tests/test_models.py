"""Testes das dataclasses compartilhadas criadas na Etapa 1."""

import unittest
from dataclasses import FrozenInstanceError

from test_support import add_app_directory_to_import_path


add_app_directory_to_import_path()

from models import (  # noqa: E402  # Depende do caminho configurado acima.
    PageTableEntry,
    SimulationStatistics,
    TranslationResult,
)


class ModelTests(unittest.TestCase):
    """Verifica valores iniciais, mutabilidade de estado e resultados imutáveis."""

    def test_page_table_entry_starts_as_absent(self) -> None:
        page_table_entry = PageTableEntry()

        self.assertIsNone(page_table_entry.physical_frame_number)
        self.assertFalse(page_table_entry.is_loaded_in_physical_memory)
        self.assertFalse(page_table_entry.reference_bit)

    def test_page_table_entry_is_mutable_runtime_state(self) -> None:
        page_table_entry = PageTableEntry()

        page_table_entry.physical_frame_number = 7
        page_table_entry.is_loaded_in_physical_memory = True
        page_table_entry.reference_bit = True

        self.assertEqual(page_table_entry.physical_frame_number, 7)
        self.assertTrue(page_table_entry.is_loaded_in_physical_memory)
        self.assertTrue(page_table_entry.reference_bit)

    def test_translation_result_is_immutable(self) -> None:
        translation_result = TranslationResult(
            logical_address=16_916,
            virtual_page_number=66,
            page_offset=20,
            physical_frame_number=0,
            physical_address=20,
            unsigned_byte_value=0,
            signed_byte_value=0,
            was_tlb_hit=False,
            was_page_fault=True,
            evicted_virtual_page_number=None,
            translation_steps=("Falha de página", "Página carregada"),
        )

        with self.assertRaises(FrozenInstanceError):
            translation_result.physical_address = 21  # type: ignore[misc]

    def test_simulation_statistics_are_mutable_counters(self) -> None:
        simulation_statistics = SimulationStatistics()

        simulation_statistics.translated_address_count += 1
        simulation_statistics.page_fault_count += 1
        simulation_statistics.tlb_hit_count += 1

        self.assertEqual(simulation_statistics.translated_address_count, 1)
        self.assertEqual(simulation_statistics.page_fault_count, 1)
        self.assertEqual(simulation_statistics.tlb_hit_count, 1)


if __name__ == "__main__":
    unittest.main()
