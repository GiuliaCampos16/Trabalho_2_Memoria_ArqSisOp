"""Configurações editáveis e valores derivados do simulador."""

from pathlib import Path
from typing import Final

from models import PageReplacementPolicyName, TlbReplacementPolicyName


# Define quantos bits formam um endereço lógico. O padrão 16 cria um espaço virtual de
# 65.536 bytes. Aceita inteiros positivos e afeta o tamanho virtual, o maior endereço e
# a quantidade de bits reservada ao número da página.
LOGICAL_ADDRESS_BITS: Final[int] = 16

# Define simultaneamente o tamanho de cada página virtual e quadro físico. O padrão é
# 256 bytes. Deve ser uma potência de dois, não pode superar o espaço virtual e afeta o
# deslocamento, a quantidade de páginas e o tamanho total da memória física.
PAGE_SIZE_BYTES: Final[int] = 256

# Define quantos quadros existem na memória física. O padrão 128 deve ser uma potência
# de dois e produzir uma memória física menor que a virtual. Quanto menor o valor, mais
# cedo será necessário aplicar uma política de substituição de páginas.
PHYSICAL_FRAME_COUNT: Final[int] = 128

# Define quantas traduções página-quadro cabem na TLB. O padrão 16 deve ser positivo e
# menor que a quantidade de páginas virtuais. Capacidades menores tendem a gerar mais
# TLB misses, mas não alteram diretamente a quantidade de falhas de página.
TLB_ENTRY_CAPACITY: Final[int] = 16

# Seleciona a política aplicada quando todos os quadros estiverem ocupados. Os valores
# aceitos são "fifo" e "second_chance"; o padrão "fifo" preserva a ordem de carregamento.
PAGE_REPLACEMENT_POLICY: Final[PageReplacementPolicyName] = "fifo"

# Seleciona a política de remoção de traduções da TLB. Nesta versão somente "fifo" é
# aceito, mantendo a entrada mais antiga como próxima candidata à remoção.
TLB_REPLACEMENT_POLICY: Final[TlbReplacementPolicyName] = "fifo"

# Estes diretórios são obtidos pela localização deste arquivo, não pelo terminal. Isso
# permite executar main.py pela raiz, de dentro de App ou pelo botão Run do VS Code.
APP_DIRECTORY: Final[Path] = Path(__file__).resolve().parent
PROJECT_ROOT_DIRECTORY: Final[Path] = APP_DIRECTORY.parent

# Indica o arquivo texto com um endereço lógico decimal por linha. Alterar este caminho
# muda a sequência de referências processada, mas o conteúdo será validado na Etapa 2.
LOGICAL_ADDRESSES_FILE_PATH: Final[Path] = (
    PROJECT_ROOT_DIRECTORY / "addresses.txt"
)

# Indica o arquivo binário que representa a memória secundária. Seu tamanho deverá ser
# igual ao espaço virtual calculado; essa validação de arquivo será feita na Etapa 2.
BACKING_STORE_FILE_PATH: Final[Path] = PROJECT_ROOT_DIRECTORY / "BACKING_STORE.bin"

# Define onde o rastreamento completo será salvo. A saída será sobrescrita a cada
# execução e espelhada no terminal quando o reporter for implementado.
SIMULATION_OUTPUT_FILE_PATH: Final[Path] = (
    APP_DIRECTORY / "output" / "simulation_output.txt"
)

SUPPORTED_PAGE_REPLACEMENT_POLICIES: Final[frozenset[str]] = frozenset(
    {"fifo", "second_chance"}
)
SUPPORTED_TLB_REPLACEMENT_POLICIES: Final[frozenset[str]] = frozenset({"fifo"})


def _is_power_of_two(candidate_value: int) -> bool:
    """Informa se um inteiro positivo pode ser representado como potência de dois."""

    return candidate_value > 0 and (candidate_value & (candidate_value - 1)) == 0


def _require_positive_integer(configuration_name: str, configured_value: object) -> int:
    """Valida e devolve uma configuração que precisa ser um inteiro positivo."""

    # bool deriva de int em Python; a verificação explícita evita aceitar True como 1.
    if isinstance(configured_value, bool) or not isinstance(configured_value, int):
        raise ValueError(
            f"{configuration_name} deve ser um inteiro positivo; "
            f"recebido: {configured_value!r}."
        )
    if configured_value <= 0:
        raise ValueError(
            f"{configuration_name} deve ser maior que zero; "
            f"recebido: {configured_value}."
        )
    return configured_value


def validate_configuration() -> None:
    """Valida as relações estruturais entre as configurações editáveis.

    A existência e o conteúdo dos arquivos serão verificados na Etapa 2, junto aos
    leitores. Esta função se limita às premissas numéricas, políticas e tipos dos
    caminhos, que precisam estar corretos antes de calcular os valores derivados.
    """

    logical_address_bit_count = _require_positive_integer(
        "LOGICAL_ADDRESS_BITS", LOGICAL_ADDRESS_BITS
    )
    page_size_bytes = _require_positive_integer(
        "PAGE_SIZE_BYTES", PAGE_SIZE_BYTES
    )
    physical_frame_count = _require_positive_integer(
        "PHYSICAL_FRAME_COUNT", PHYSICAL_FRAME_COUNT
    )
    tlb_entry_capacity = _require_positive_integer(
        "TLB_ENTRY_CAPACITY", TLB_ENTRY_CAPACITY
    )

    if not _is_power_of_two(page_size_bytes):
        raise ValueError(
            "PAGE_SIZE_BYTES deve ser uma potência de dois; "
            f"recebido: {page_size_bytes}."
        )
    if not _is_power_of_two(physical_frame_count):
        raise ValueError(
            "PHYSICAL_FRAME_COUNT deve ser uma potência de dois; "
            f"recebido: {physical_frame_count}."
        )

    virtual_memory_size_bytes = 2**logical_address_bit_count
    if page_size_bytes > virtual_memory_size_bytes:
        raise ValueError(
            "PAGE_SIZE_BYTES não pode superar o tamanho da memória virtual."
        )
    if virtual_memory_size_bytes % page_size_bytes != 0:
        raise ValueError(
            "O tamanho da memória virtual deve ser divisível por PAGE_SIZE_BYTES."
        )

    virtual_page_count = virtual_memory_size_bytes // page_size_bytes
    physical_memory_size_bytes = physical_frame_count * page_size_bytes
    if physical_memory_size_bytes >= virtual_memory_size_bytes:
        raise ValueError(
            "A memória física deve ser estritamente menor que a memória virtual."
        )
    if tlb_entry_capacity >= virtual_page_count:
        raise ValueError(
            "TLB_ENTRY_CAPACITY deve ser menor que a quantidade de páginas virtuais."
        )

    if PAGE_REPLACEMENT_POLICY not in SUPPORTED_PAGE_REPLACEMENT_POLICIES:
        raise ValueError(
            "PAGE_REPLACEMENT_POLICY deve ser 'fifo' ou 'second_chance'; "
            f"recebido: {PAGE_REPLACEMENT_POLICY!r}."
        )
    if TLB_REPLACEMENT_POLICY not in SUPPORTED_TLB_REPLACEMENT_POLICIES:
        raise ValueError(
            "TLB_REPLACEMENT_POLICY deve ser 'fifo'; "
            f"recebido: {TLB_REPLACEMENT_POLICY!r}."
        )

    configured_paths = {
        "LOGICAL_ADDRESSES_FILE_PATH": LOGICAL_ADDRESSES_FILE_PATH,
        "BACKING_STORE_FILE_PATH": BACKING_STORE_FILE_PATH,
        "SIMULATION_OUTPUT_FILE_PATH": SIMULATION_OUTPUT_FILE_PATH,
    }
    for configuration_name, configured_path in configured_paths.items():
        if not isinstance(configured_path, Path):
            raise ValueError(
                f"{configuration_name} deve ser pathlib.Path; "
                f"recebido: {configured_path!r}."
            )


# A validação ocorre antes das derivações para produzir mensagens claras caso alguém
# edite uma constante com valor que causaria divisão por zero ou cálculo inconsistente.
validate_configuration()

# Calculado automaticamente — não editar diretamente.
VIRTUAL_MEMORY_SIZE_BYTES: Final[int] = 2**LOGICAL_ADDRESS_BITS

# Calculado automaticamente — não editar diretamente.
MAXIMUM_LOGICAL_ADDRESS: Final[int] = VIRTUAL_MEMORY_SIZE_BYTES - 1

# Calculado automaticamente — não editar diretamente.
VIRTUAL_PAGE_COUNT: Final[int] = VIRTUAL_MEMORY_SIZE_BYTES // PAGE_SIZE_BYTES

# Calculado automaticamente — não editar diretamente.
PAGE_OFFSET_BIT_COUNT: Final[int] = PAGE_SIZE_BYTES.bit_length() - 1

# Calculado automaticamente — não editar diretamente.
VIRTUAL_PAGE_NUMBER_BIT_COUNT: Final[int] = (
    LOGICAL_ADDRESS_BITS - PAGE_OFFSET_BIT_COUNT
)

# Calculado automaticamente — não editar diretamente.
PHYSICAL_MEMORY_SIZE_BYTES: Final[int] = PHYSICAL_FRAME_COUNT * PAGE_SIZE_BYTES

# Calculado automaticamente — não editar diretamente.
PHYSICAL_ADDRESS_BIT_COUNT: Final[int] = (
    PHYSICAL_MEMORY_SIZE_BYTES.bit_length() - 1
)
