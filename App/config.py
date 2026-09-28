"""Configurações editáveis e valores derivados do simulador."""

from pathlib import Path

from models import PageReplacementPolicyName, TlbReplacementPolicyName


# Define quantos bits formam um endereço lógico. O padrão 16 cria um espaço virtual de
# 65.536 bytes. Aceita inteiros positivos e afeta o tamanho virtual, o maior endereço e
# a quantidade de bits reservada ao número da página.
LOGICAL_ADDRESS_BITS: int = 16

# Define simultaneamente o tamanho de cada página virtual e quadro físico. O padrão é
# 256 bytes. Deve ser uma potência de dois, não pode superar o espaço virtual e afeta o
# deslocamento, a quantidade de páginas e o tamanho total da memória física.
PAGE_SIZE_BYTES: int = 256

# Define quantos quadros existem na memória física. O padrão 128 deve ser uma potência
# de dois e produzir uma memória física menor que a virtual. Quanto menor o valor, mais
# cedo será necessário aplicar uma política de substituição de páginas.
PHYSICAL_FRAME_COUNT: int = 128

# Define quantas traduções página-quadro cabem na TLB. O padrão 16 deve ser positivo e
# menor que a quantidade de páginas virtuais. Capacidades menores tendem a gerar mais
# TLB misses, mas não alteram diretamente a quantidade de falhas de página.
TLB_ENTRY_CAPACITY: int = 16

# Seleciona a política aplicada quando todos os quadros estiverem ocupados. Os valores
# aceitos são "fifo" e "second_chance"; o padrão "fifo" preserva a ordem de carregamento.
PAGE_REPLACEMENT_POLICY: PageReplacementPolicyName = "fifo"

# Seleciona a política de remoção de traduções da TLB. Nesta versão somente "fifo" é
# aceito, mantendo a entrada mais antiga como próxima candidata à remoção.
TLB_REPLACEMENT_POLICY: TlbReplacementPolicyName = "fifo"

# Estes diretórios são obtidos pela localização deste arquivo, não pelo terminal. Isso
# permite executar main.py pela raiz, de dentro de App ou pelo botão Run do VS Code.
APP_DIRECTORY: Path = Path(__file__).resolve().parent
PROJECT_ROOT_DIRECTORY: Path = APP_DIRECTORY.parent

# Indica o arquivo texto com um endereço lógico decimal por linha. Alterar este caminho
# muda a sequência de referências processada, mas o conteúdo será validado na Etapa 2.
LOGICAL_ADDRESSES_FILE_PATH: Path = (
    PROJECT_ROOT_DIRECTORY / "addresses.txt"
)

# Indica o arquivo binário que representa a memória secundária. Seu tamanho deverá ser
# igual ao espaço virtual calculado; essa validação de arquivo será feita na Etapa 2.
BACKING_STORE_FILE_PATH: Path = PROJECT_ROOT_DIRECTORY / "BACKING_STORE.bin"

# Define onde o rastreamento completo será salvo. A saída será sobrescrita a cada
# execução e espelhada no terminal quando o reporter for implementado.
SIMULATION_OUTPUT_FILE_PATH: Path = (
    APP_DIRECTORY / "output" / "simulation_output.txt"
)


def _is_power_of_two(candidate_value: int) -> bool:
    """Informa se um inteiro positivo pode ser representado como potência de dois."""

    if candidate_value <= 0:
        return False

    # Potências de dois possuem apenas um bit igual a 1 na representação binária.
    return candidate_value.bit_count() == 1


def validate_configuration() -> None:
    """Valida as relações estruturais entre as configurações editáveis.

    A existência e o conteúdo dos arquivos serão verificados na Etapa 2, junto aos
    leitores. Aqui ficam apenas as premissas necessárias para calcular endereços e
    selecionar as políticas de substituição.
    """

    numeric_settings = (
        ("LOGICAL_ADDRESS_BITS", LOGICAL_ADDRESS_BITS),
        ("PAGE_SIZE_BYTES", PAGE_SIZE_BYTES),
        ("PHYSICAL_FRAME_COUNT", PHYSICAL_FRAME_COUNT),
        ("TLB_ENTRY_CAPACITY", TLB_ENTRY_CAPACITY),
    )
    for setting_name, setting_value in numeric_settings:
        # bool também é int em Python, mas não representa uma medida de memória.
        if type(setting_value) is not int:
            raise ValueError(
                f"{setting_name} deve ser um inteiro positivo; "
                f"recebido: {setting_value!r}."
            )
        if setting_value <= 0:
            raise ValueError(
                f"{setting_name} deve ser um inteiro positivo; "
                f"recebido: {setting_value!r}."
            )

    if not _is_power_of_two(PAGE_SIZE_BYTES):
        raise ValueError(
            "PAGE_SIZE_BYTES deve ser uma potência de dois; "
            f"recebido: {PAGE_SIZE_BYTES}."
        )
    if not _is_power_of_two(PHYSICAL_FRAME_COUNT):
        raise ValueError(
            "PHYSICAL_FRAME_COUNT deve ser uma potência de dois; "
            f"recebido: {PHYSICAL_FRAME_COUNT}."
        )

    virtual_memory_size_bytes = 2 ** LOGICAL_ADDRESS_BITS
    if PAGE_SIZE_BYTES > virtual_memory_size_bytes:
        raise ValueError(
            "PAGE_SIZE_BYTES não pode superar o tamanho da memória virtual."
        )

    virtual_page_count = virtual_memory_size_bytes // PAGE_SIZE_BYTES
    physical_memory_size_bytes = PHYSICAL_FRAME_COUNT * PAGE_SIZE_BYTES
    if physical_memory_size_bytes >= virtual_memory_size_bytes:
        raise ValueError(
            "A memória física deve ser estritamente menor que a memória virtual."
        )
    if TLB_ENTRY_CAPACITY >= virtual_page_count:
        raise ValueError(
            "TLB_ENTRY_CAPACITY deve ser menor que a quantidade de páginas virtuais."
        )

    if PAGE_REPLACEMENT_POLICY not in ("fifo", "second_chance"):
        raise ValueError(
            "PAGE_REPLACEMENT_POLICY deve ser 'fifo' ou 'second_chance'; "
            f"recebido: {PAGE_REPLACEMENT_POLICY!r}."
        )
    if TLB_REPLACEMENT_POLICY != "fifo":
        raise ValueError(
            "TLB_REPLACEMENT_POLICY deve ser 'fifo'; "
            f"recebido: {TLB_REPLACEMENT_POLICY!r}."
        )


# A validação ocorre antes das derivações para produzir mensagens claras caso alguém
# edite uma constante com valor que causaria divisão por zero ou cálculo inconsistente.
validate_configuration()

# Calculado automaticamente — não editar diretamente.
VIRTUAL_MEMORY_SIZE_BYTES: int = 2 ** LOGICAL_ADDRESS_BITS

# Calculado automaticamente — não editar diretamente.
MAXIMUM_LOGICAL_ADDRESS: int = VIRTUAL_MEMORY_SIZE_BYTES - 1

# Calculado automaticamente — não editar diretamente.
VIRTUAL_PAGE_COUNT: int = VIRTUAL_MEMORY_SIZE_BYTES // PAGE_SIZE_BYTES

# Calculado automaticamente — não editar diretamente.
PAGE_OFFSET_BIT_COUNT: int = PAGE_SIZE_BYTES.bit_length() - 1

# Calculado automaticamente — não editar diretamente.
VIRTUAL_PAGE_NUMBER_BIT_COUNT: int = (
    LOGICAL_ADDRESS_BITS - PAGE_OFFSET_BIT_COUNT
)

# Calculado automaticamente — não editar diretamente.
PHYSICAL_MEMORY_SIZE_BYTES: int = PHYSICAL_FRAME_COUNT * PAGE_SIZE_BYTES

# Calculado automaticamente — não editar diretamente.
PHYSICAL_ADDRESS_BIT_COUNT: int = (
    PHYSICAL_MEMORY_SIZE_BYTES.bit_length() - 1
)
