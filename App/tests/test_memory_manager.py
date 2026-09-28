"""Testes da memória física e da tradução básica da Etapa 3."""

import unittest
from unittest.mock import Mock

from test_support import add_app_directory_to_import_path


add_app_directory_to_import_path()

import config  # noqa: E402  # App não é um pacote; o caminho é ajustado acima.
from io_utils import read_backing_store  # noqa: E402
from memory_manager import MemoryManager  # noqa: E402
from policies import PageReplacementPolicy  # noqa: E402
from tlb import TranslationLookasideBuffer  # noqa: E402


class MemoryManagerStageThreeTests(unittest.TestCase):
    """Confere os mapeamentos e a leitura de bytes sem substituição ou TLB."""

    def setUp(self) -> None:
        backing_store_bytes = read_backing_store(
            config.BACKING_STORE_FILE_PATH,
            config.VIRTUAL_MEMORY_SIZE_BYTES,
        )
        unused_policy = Mock(spec=PageReplacementPolicy)
        unused_tlb = TranslationLookasideBuffer(config.TLB_ENTRY_CAPACITY)
        self.manager = MemoryManager(backing_store_bytes, unused_policy, unused_tlb)

    def test_initial_memory_state(self) -> None:
        self.assertEqual(len(self.manager._page_table_entries), 256)
        self.assertEqual(len(self.manager._physical_memory), 32_768)
        self.assertEqual(len(self.manager._free_physical_frame_numbers), 128)
        self.assertTrue(all(page is None for page in self.manager._virtual_page_by_physical_frame))
        self.assertTrue(
            all(
                not entry.is_loaded_in_physical_memory
                and entry.physical_frame_number is None
                for entry in self.manager._page_table_entries
            )
        )

    def test_logical_address_boundaries(self) -> None:
        expected_parts = {
            0: (0, 0),
            255: (0, 255),
            256: (1, 0),
            65_535: (255, 255),
        }

        for logical_address, expected in expected_parts.items():
            with self.subTest(logical_address=logical_address):
                actual_parts = self.manager.decompose_logical_address(logical_address)
                self.assertEqual(actual_parts, expected)

    def test_loading_maps_page_to_first_free_frame(self) -> None:
        physical_frame_number = self.manager.load_virtual_page_into_free_frame(71)
        page_table_entry = self.manager._page_table_entries[71]

        self.assertEqual(physical_frame_number, 0)
        self.assertTrue(page_table_entry.is_loaded_in_physical_memory)
        self.assertEqual(page_table_entry.physical_frame_number, 0)
        self.assertEqual(self.manager._virtual_page_by_physical_frame[0], 71)
        self.assertEqual(self.manager._free_physical_frame_numbers[0], 1)

        virtual_page_number, page_offset = self.manager.decompose_logical_address(18_295)
        self.assertEqual(virtual_page_number, 71)
        physical_address = self.manager.compose_physical_address(
            physical_frame_number, page_offset
        )
        self.assertEqual(physical_address, page_offset)
        self.assertEqual(
            self.manager.read_byte_at_physical_address(physical_address),
            (221, -35),
        )

    def test_page_boundary_reads_individual_bytes(self) -> None:
        first_frame = self.manager.load_virtual_page_into_free_frame(0)
        second_frame = self.manager.load_virtual_page_into_free_frame(1)

        last_address_of_first_page = self.manager.compose_physical_address(
            first_frame, 255
        )
        first_address_of_second_page = self.manager.compose_physical_address(
            second_frame, 0
        )

        self.assertEqual(
            self.manager.read_byte_at_physical_address(last_address_of_first_page),
            (63, 63),
        )
        self.assertEqual(
            self.manager.read_byte_at_physical_address(first_address_of_second_page),
            (0, 0),
        )
        self.assertEqual(
            list(self.manager._physical_memory[:8]),
            [0, 0, 0, 0, 0, 0, 0, 1],
        )

    def test_no_free_frame_has_clear_error_and_keeps_mapping(self) -> None:
        for virtual_page_number in range(config.PHYSICAL_FRAME_COUNT):
            loaded_frame = self.manager.load_virtual_page_into_free_frame(
                virtual_page_number
            )
            self.assertEqual(loaded_frame, virtual_page_number)

        with self.assertRaisesRegex(RuntimeError, "Não há quadros físicos livres"):
            self.manager.load_virtual_page_into_free_frame(config.PHYSICAL_FRAME_COUNT)

        self.assertFalse(self.manager._free_physical_frame_numbers)
        self.assertFalse(
            self.manager._page_table_entries[config.PHYSICAL_FRAME_COUNT]
            .is_loaded_in_physical_memory
        )
        self.assertEqual(
            self.manager._virtual_page_by_physical_frame[0], 0
        )

    def test_invalid_or_repeated_requests_do_not_change_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "fora da faixa"):
            self.manager.decompose_logical_address(-1)
        with self.assertRaisesRegex(ValueError, "Página virtual inválida"):
            self.manager.load_virtual_page_into_free_frame(config.VIRTUAL_PAGE_COUNT)

        self.manager.load_virtual_page_into_free_frame(0)
        with self.assertRaisesRegex(ValueError, "já está carregada"):
            self.manager.load_virtual_page_into_free_frame(0)

        self.assertEqual(len(self.manager._free_physical_frame_numbers), 127)


if __name__ == "__main__":
    unittest.main()
