# PrinterAssistant — Estado da Versão

## Objetivo

Esta versão consolida a coleta e normalização de informações de impressoras através de PJL, SYSDEBUG e SNMP.

## Funcionalidades implementadas

### Device

- `PrinterDevice` coordena PJL, SYSDEBUG e SNMP.
- SYSDEBUG possui prioridade para contador.
- SYSDEBUG possui prioridade para serial da máquina.
- PJL funciona como fonte auxiliar.
- Identificação normalizada:
  - fabricante
  - modelo
  - família
  - tipo
  - serial
  - firmware
  - contador
- Validação de modelos inválidos.
- Detecção automática de fabricante, família e tipo.
- Estado de conectividade:
  - EXCELENTE
  - PARCIAL
  - OFFLINE
- Preservação de `raw_sysdebug`.

### Timeout

- PJL: 15 s
- SYSDEBUG: 15 s
- SNMP: 45 s

PJL e SYSDEBUG são executados em threads daemon com timeout real, evitando que operações bloqueadas impeçam o encerramento da coleta.

### SNMP

- SNMPv2c com fallback para SNMPv1.
- Community padrão: `public`.
- Coleta da Printer-MIB.
- Parser baseado explicitamente no OID base.
- Campos tratados:
  - descrição
  - unidade
  - capacidade
  - nível

### Cálculo dos consumíveis

O nível não é tratado diretamente como percentual.

```text
percentual = level / maxCapacity * 100
Valores negativos do Printer-MIB são tratados como desconhecidos.

São calculados:

percentual
restante
consumido
condição
Classificação

Tipos reconhecidos:

toner
unidade de imagem
fusor
Condição

50% → OK

30% → ATENÇÃO

15% → BAIXO

<= 15% → CRÍTICO
desconhecido → DESCONHECIDO
Seriais dos consumíveis

O sistema separa:

SYSDEBUG → números de série
SNMP     → dados quantitativos

Os seriais encontrados no SYSDEBUG podem ser associados aos consumíveis obtidos pelo SNMP através de:

tipo;
nome normalizado.

O fusor não recebe número de série na interface.

Part Number

O Part Number permanece disponível internamente para diagnóstico/processamento futuro, mas não é apresentado nesta etapa.

Garantia

A regra de garantia é aplicada somente à unidade de imagem.

>= 50% → POSSÍVEL
< 50%  → NÃO ELEGÍVEL

Toner e fusor não recebem essa regra.

Dados brutos

São preservados para diagnóstico:

raw_sysdebug
raw_supplies
raw_identificadores

Isso permite investigar estruturas proprietárias de diferentes modelos sem perder os dados originais.

Equipamento de laboratório

A MX611dhe continua sendo o equipamento principal de laboratório.

Ela não é uma limitação arquitetural do sistema.

Estado

Esta versão deve ser considerada um ponto de estabilização da camada de coleta.

Próxima etapa

A próxima etapa poderá avançar para:

identidade persistente pelo número de série;
descoberta de impressoras na rede;
inventário persistente;
histórico de contadores;
histórico de consumíveis;
associação entre impressora física e registros;
interface;
expansão para outros modelos.

Data: 2026-08-17