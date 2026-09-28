"""Estado da memória física e operações básicas de paginação."""

from collections import deque

import config
from models import PageTableEntry, TranslationResult
from policies import PageReplacementPolicy
from tlb import TranslationLookasideBuffer


class MemoryManager:
    """Mantém páginas virtuais, quadros físicos e seus mapeamentos.

    A Etapa 3 carrega páginas somente em quadros livres. O fluxo completo de tradução,
    com TLB e substituição de páginas, será implementado na Etapa 4.
    """

    def __init__(
        self,
        backing_store_bytes: bytes,
        page_replacement_policy: PageReplacementPolicy,
        translation_lookaside_buffer: TranslationLookasideBuffer,
    ) -> None:
        """Prepara as estruturas usadas para relacionar páginas e quadros.

        backing_store_bytes contém todo o espaço virtual, lido do arquivo binário.
        page_replacement_policy escolherá a página a remover quando a RAM estiver cheia.
        translation_lookaside_buffer guardará traduções recentes de página para quadro.
        As duas últimas dependências serão usadas no fluxo completo da Etapa 4.
        """

        if len(backing_store_bytes) != config.VIRTUAL_MEMORY_SIZE_BYTES:
            raise ValueError(
                "O backing store deve ter "
                f"{config.VIRTUAL_MEMORY_SIZE_BYTES} bytes para a configuração atual."
            )

        # Fonte permanente dos bytes das páginas, mesmo após saírem da memória física.
        self._backing_store_bytes: bytes = backing_store_bytes

        # Regra que escolherá uma página vítima quando não restarem quadros livres.
        self._page_replacement_policy: PageReplacementPolicy = (
            page_replacement_policy
        )

        # Cache dos mapeamentos página virtual -> quadro físico mais recentes.
        self._translation_lookaside_buffer: TranslationLookasideBuffer = (
            translation_lookaside_buffer
        )

        # Uma entrada por página virtual; todas começam ausentes da memória física.
        self._page_table_entries: list[PageTableEntry] = [
            PageTableEntry() for _ in range(config.VIRTUAL_PAGE_COUNT)
        ]

        # Simula os bytes da RAM, divididos em quadros do tamanho de uma página.
        self._physical_memory: bytearray = bytearray(
            config.PHYSICAL_MEMORY_SIZE_BYTES
        )

        # Mantém os números dos quadros disponíveis, começando pelo quadro zero.
        self._free_physical_frame_numbers: deque[int] = deque(
            range(config.PHYSICAL_FRAME_COUNT)
        )

        # Mapa inverso: em cada posição de quadro, guarda a página ocupante ou None.
        self._virtual_page_by_physical_frame: list[int | None] = [
            None for _ in range(config.PHYSICAL_FRAME_COUNT)
        ]

    def decompose_logical_address(self, logical_address: int) -> tuple[int, int]:
        """Separa um endereço lógico em número de página e deslocamento."""

        if logical_address < 0 or logical_address > config.MAXIMUM_LOGICAL_ADDRESS:
            raise ValueError(
                f"Endereço lógico {logical_address} fora da faixa "
                f"0 a {config.MAXIMUM_LOGICAL_ADDRESS}."
            )

        virtual_page_number = logical_address // config.PAGE_SIZE_BYTES
        page_offset = logical_address % config.PAGE_SIZE_BYTES
        return virtual_page_number, page_offset

    def load_virtual_page_into_free_frame(self, virtual_page_number: int) -> int:
        """Copia uma página ausente do backing store para o próximo quadro livre."""

        if virtual_page_number < 0 or virtual_page_number >= config.VIRTUAL_PAGE_COUNT:
            raise ValueError(f"Página virtual inválida: {virtual_page_number}.")

        page_table_entry = self._page_table_entries[virtual_page_number]
        if page_table_entry.is_loaded_in_physical_memory:
            raise ValueError(f"A página virtual {virtual_page_number} já está carregada.")

        if not self._free_physical_frame_numbers:
            raise RuntimeError(
                "Não há quadros físicos livres. A substituição de páginas "
                "será implementada na Etapa 4."
            )

        physical_frame_number = self._free_physical_frame_numbers.popleft()
        source_start = virtual_page_number * config.PAGE_SIZE_BYTES
        source_end = source_start + config.PAGE_SIZE_BYTES
        destination_start = physical_frame_number * config.PAGE_SIZE_BYTES
        destination_end = destination_start + config.PAGE_SIZE_BYTES

        # O arquivo contém bytes individuais. Copiar a fatia inteira preserva todos os
        # deslocamentos da página, independentemente do padrão de quatro bytes visto no
        # backing store fornecido.
        page_bytes = self._backing_store_bytes[source_start:source_end]
        self._physical_memory[destination_start:destination_end] = page_bytes

        page_table_entry.physical_frame_number = physical_frame_number
        page_table_entry.is_loaded_in_physical_memory = True
        self._virtual_page_by_physical_frame[physical_frame_number] = (
            virtual_page_number
        )
        return physical_frame_number

    def compose_physical_address(
        self, physical_frame_number: int, page_offset: int
    ) -> int:
        """Combina um quadro físico e o deslocamento original da página."""

        if physical_frame_number < 0 or physical_frame_number >= config.PHYSICAL_FRAME_COUNT:
            raise ValueError(f"Quadro físico inválido: {physical_frame_number}.")
        if page_offset < 0 or page_offset >= config.PAGE_SIZE_BYTES:
            raise ValueError(f"Deslocamento inválido: {page_offset}.")

        frame_start_address = physical_frame_number * config.PAGE_SIZE_BYTES
        physical_address = frame_start_address + page_offset
        return physical_address

    def read_byte_at_physical_address(self, physical_address: int) -> tuple[int, int]:
        """Lê um byte físico e devolve suas interpretações sem sinal e com sinal."""

        if physical_address < 0 or physical_address >= config.PHYSICAL_MEMORY_SIZE_BYTES:
            raise ValueError(f"Endereço físico inválido: {physical_address}.")

        unsigned_byte_value = self._physical_memory[physical_address]
        if unsigned_byte_value < 128:
            signed_byte_value = unsigned_byte_value
        else:
            # Um byte com o bit mais alto ligado representa um número negativo na
            # interpretação com sinal, sem alterar o byte armazenado na memória.
            signed_byte_value = unsigned_byte_value - 256

        return unsigned_byte_value, signed_byte_value

    def translate(self, logical_address: int) -> TranslationResult:
        """Traduz um endereço lógico e devolve o registro completo da operação."""

        raise NotImplementedError(
            "O fluxo completo de tradução será implementado na Etapa 4."
        )
