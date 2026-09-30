"""Configurações editáveis e valores derivados do simulador."""

from pathlib import Path

from models import PageReplacementPolicyName, TlbReplacementPolicyName


# Define quantos bits formam um endereço lógico. O padrão 16 cria um espaço virtual de
# 65.536 bytes. Aceita inteiros positivos e afeta o tamanho virtual, o maior endereço e
# a quantidade de bits reservada ao número da página.
logicalAddressBits: int = 16

# Define simultaneamente o tamanho de cada página virtual e quadro físico. O padrão é
# 256 bytes. Deve ser uma potência de dois, não pode superar o espaço virtual e afeta o
# deslocamento, a quantidade de páginas e o tamanho total da memória física.
pageSizeBytes: int = 256

# Define quantos quadros existem na memória física. O padrão 128 deve ser uma potência
# de dois e produzir uma memória física menor que a virtual. Quanto menor o valor, mais
# cedo será necessário aplicar uma política de substituição de páginas.
physicalFrameCount: int = 128

# Define quantas traduções página-quadro cabem na TLB. O padrão 16 deve ser positivo e
# menor que a quantidade de páginas virtuais. Capacidades menores tendem a gerar mais
# TLB misses, mas não alteram diretamente a quantidade de falhas de página.
tlbEntryCapacity: int = 16

# Seleciona a política aplicada quando todos os quadros estiverem ocupados. Os valores
# aceitos são "fifo" e "second_chance"; o padrão "fifo" preserva a ordem de carregamento.
pageReplacementPolicy: PageReplacementPolicyName = "fifo"

# Seleciona a política de remoção de traduções da TLB. Nesta versão somente "fifo" é
# aceito, mantendo a entrada mais antiga como próxima candidata à remoção.
tlbReplacementPolicy: TlbReplacementPolicyName = "fifo"

# Estes diretórios são obtidos pela localização deste arquivo, não pelo terminal. Isso
# permite executar main.py pela raiz, de dentro de App ou pelo botão Run do VS Code.
appDirectory: Path = Path(__file__).resolve().parent
projectRootDirectory: Path = appDirectory.parent

# Indica o arquivo texto com um endereço lógico decimal por linha. Alterar este caminho
# muda a sequência de referências processada; o leitor valida seu conteúdo.
logicalAddressesFilePath: Path = (
    projectRootDirectory / "addresses.txt"
)

# Indica o arquivo binário que representa a memória secundária. Seu tamanho deverá ser
# igual ao espaço virtual calculado; o leitor verifica esse tamanho.
backingStoreFilePath: Path = projectRootDirectory / "BACKING_STORE.bin"

# Define onde o rastreamento completo será salvo. A saída será sobrescrita a cada
# execução e espelhada no terminal quando o reporter for implementado.
simulationOutputFilePath: Path = (
    appDirectory / "output" / "simulation_output.txt"
)


def IsPowerOfTwo(candidateValue: int) -> bool:
    """Informa se um inteiro positivo pode ser representado como potência de dois."""

    if candidateValue <= 0:
        return False

    # Potências de dois possuem apenas um bit igual a 1 na representação binária.
    return candidateValue.bit_count() == 1


def ValidatePositiveInteger(settingName: str, settingValue: int) -> None:
    """Exige um inteiro positivo para os tamanhos usados nos cálculos."""

    # bool também é int em Python, mas não representa uma medida de memória.
    if type(settingValue) is not int:
        raise ValueError(
            f"{settingName} deve ser um inteiro positivo; "
            f"recebido: {settingValue!r}."
        )
    if settingValue <= 0:
        raise ValueError(
            f"{settingName} deve ser um inteiro positivo; "
            f"recebido: {settingValue!r}."
        )


def ValidateConfiguration() -> None:
    """Valida as relações estruturais entre as configurações editáveis.

    A existência e o conteúdo dos arquivos são verificados pelos leitores.
    Aqui ficam apenas as premissas necessárias para calcular endereços e
    selecionar as políticas de substituição.
    """

    ValidatePositiveInteger("logicalAddressBits", logicalAddressBits)
    ValidatePositiveInteger("pageSizeBytes", pageSizeBytes)
    ValidatePositiveInteger("physicalFrameCount", physicalFrameCount)
    ValidatePositiveInteger("tlbEntryCapacity", tlbEntryCapacity)

    if not IsPowerOfTwo(pageSizeBytes):
        raise ValueError(
            "pageSizeBytes deve ser uma potência de dois; "
            f"recebido: {pageSizeBytes}."
        )
    if not IsPowerOfTwo(physicalFrameCount):
        raise ValueError(
            "physicalFrameCount deve ser uma potência de dois; "
            f"recebido: {physicalFrameCount}."
        )

    virtualMemorySizeBytes = 2 ** logicalAddressBits
    if pageSizeBytes > virtualMemorySizeBytes:
        raise ValueError(
            "pageSizeBytes não pode superar o tamanho da memória virtual."
        )

    virtualPageCount = virtualMemorySizeBytes // pageSizeBytes
    physicalMemorySizeBytes = physicalFrameCount * pageSizeBytes
    if physicalMemorySizeBytes >= virtualMemorySizeBytes:
        raise ValueError(
            "A memória física deve ser estritamente menor que a memória virtual."
        )
    if tlbEntryCapacity >= virtualPageCount:
        raise ValueError(
            "tlbEntryCapacity deve ser menor que a quantidade de páginas virtuais."
        )

    if pageReplacementPolicy != "fifo" and pageReplacementPolicy != "second_chance":
        raise ValueError(
            "pageReplacementPolicy deve ser 'fifo' ou 'second_chance'; "
            f"recebido: {pageReplacementPolicy!r}."
        )
    if tlbReplacementPolicy != "fifo":
        raise ValueError(
            "tlbReplacementPolicy deve ser 'fifo'; "
            f"recebido: {tlbReplacementPolicy!r}."
        )


# A validação ocorre antes das derivações para produzir mensagens claras caso alguém
# edite uma constante com valor que causaria divisão por zero ou cálculo inconsistente.
ValidateConfiguration()

# Calculado automaticamente — não editar diretamente.
virtualMemorySizeBytes: int = 2 ** logicalAddressBits

# Calculado automaticamente — não editar diretamente.
maximumLogicalAddress: int = virtualMemorySizeBytes - 1

# Calculado automaticamente — não editar diretamente.
virtualPageCount: int = virtualMemorySizeBytes // pageSizeBytes

# Calculado automaticamente — não editar diretamente.
pageOffsetBitCount: int = pageSizeBytes.bit_length() - 1

# Calculado automaticamente — não editar diretamente.
virtualPageNumberBitCount: int = (
    logicalAddressBits - pageOffsetBitCount
)

# Calculado automaticamente — não editar diretamente.
physicalMemorySizeBytes: int = physicalFrameCount * pageSizeBytes

# Calculado automaticamente — não editar diretamente.
physicalAddressBitCount: int = (
    physicalMemorySizeBytes.bit_length() - 1
)
