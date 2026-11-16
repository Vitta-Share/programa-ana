# Ferramenta "repetida" no turno: a causa (16/nov/2026)

Issue #55, PRD #30. Na fumaça de 15/nov e na bateria v159 (#51), na plataforma 1.59, o runner acusou `consultar_precos_consultas`, `consultar_convenios_agenda` e `buscar_paciente_por_cpf` chamadas duas vezes no mesmo turno (C05-1, C13-1, C14-1 e C16-1). Fonte: `GET /api/v1/logs?stage=tool` da plataforma, 510 linhas de 15/nov 23:39Z a 16/nov 03:45Z (a fumaça e as três rodadas da v159, conversas 596 a 688 do Chatwoot). Só homologação da Global Health e API do Hospital.

## A causa: o runner contava linhas de log que não são chamada

Nenhuma das três ferramentas foi chamada duas vezes pelo modelo. A 1.59 grava na etapa `tool` do log duas linhas que não são chamada, e o `ana/bancada/e2e.py` contava as duas:

- **Linha de etapa** (`detail.phase`): o `set_labels` grava uma linha `phase: labels` a cada chamada (78 nas 510), e o `set_custom_attribute` recusado grava `phase: attribute_refused` (7).
- **Resumo do fim do turno** (`detail.failedCalls`): quando uma ferramenta falha em todas as chamadas do turno, a plataforma grava uma linha `"<ferramenta> failed on every call this turn (1): <erro>"`, sem `args` e sem `durationMs`. O `(1)` é o número de chamadas: uma.

Além disso, `TOOLS_DE_ESCRITURACAO` ainda listava `assign_label`, o nome de antes da 1.59, e não `set_labels`.

| Ferramenta | Cenários | O que o log mostra | Causa |
|---|---|---|---|
| `consultar_precos_consultas` | C05-1 (e o turno 1 de C13-1, C14-1 e C16-1) | uma chamada por turno, 28 no total, maior resposta 1.333 chars, `outputCut: false` em todas | Nenhuma repetição. O aviso vinha do `set_labels` do mesmo turno (a chamada mais a linha `phase: labels`), que o runner não tratava como escrituração. |
| `consultar_convenios_agenda` | C13-1, C14-1, C16-1 | 17 chamadas, todas cortadas pela plataforma em 30 s ("the provider did not answer within 30s"), e 17 linhas de resumo `failedCalls: 1` | Uma chamada por turno. A segunda linha é o resumo de falha da plataforma. A falha em si é a GH de homologação sem resposta (infra, já registrada na v159). |
| `buscar_paciente_por_cpf` | C13-1 (rodada 2 da v159, conversa 653) | uma chamada com HTTP 417 e uma linha de resumo `failedCalls: 1` | Uma chamada. A segunda linha é o resumo de falha. Nas outras 12 chamadas (sem erro) não houve nem a linha extra. |

Resposta cortada não foi: as 510 linhas têm `outputCut: false` (a maior resposta de dado foi a do `search_knowledge`, 4.250 chars). Nova tentativa da plataforma também não: não há duas linhas com `args` da mesma ferramenta no mesmo turno para essas três. Por isso não houve mudança na plataforma nem no limite de resposta por ferramenta (1.36): não havia o que corrigir na descrição das ferramentas.

## A correção, no runner

- `chamadas_do_log` descarta as linhas com `detail.phase` ou `detail.failedCalls` antes de contar.
- `set_labels` entrou em `TOOLS_DE_ESCRITURACAO` (o `assign_label` fica, para ler baterias antigas).
- O aviso deixou de dizer "assinatura do truncamento de 4.000 chars". Agora: "uma tool de dado foi repetida Nx no mesmo turno (a causa se le no trace do turno: outputCut, tempo da resposta ou o modelo)".

Recontado com o runner novo sobre as mesmas 510 linhas: o aviso de repetição saía em **61 das 93 conversas** e agora sai em **2**. As duas são repetição de verdade: `consultar_exames` chamada sem filtro e depois com o exame, no C10-2 (conversas 642 e 650). Fica de fora desta issue. A mesma correção tira o falso vermelho do C14-1 na R1 da v159 (o teto de 2 por turno estourava com as duas linhas de cada `set_labels`).

## Prova: C05-1, C13-1 e C16-1 três vezes

Bateria `i55`, três rodadas de `--so C05-1,C13-1,C16-1` com o runner novo, de 04:17Z a 04:38Z de 16/nov (segunda 1h17 a 1h38 em Brasília, fora do horário comercial). Mesma plataforma 1.59 e mesmo prompt da v159; nada mudou na plataforma.

| Cenário | R1 | R2 | R3 | Ferramenta de dado repetida no turno | Aviso do runner velho na mesma conversa |
|---|---|---|---|---|---|
| C05-1 (692, 708, 728) | ok | ok | ok | nenhuma | 2x nas três |
| C13-1 (693, 711, 731) | falhou | ok | ok | nenhuma | 2x, 3x e 2x |
| C16-1 (701, 720, 737) | ok | ok | ok | nenhuma | 2x, 2x e 4x |

Contado sobre o log cru da plataforma (266 linhas da janela): nas nove conversas, `consultar_precos_consultas` uma vez por turno, `buscar_paciente_por_cpf` uma vez, `consultar_convenios_agenda` uma vez (seis cortadas em 30 s, cada uma com a sua linha de resumo) e `outputCut: false` em todas. O runner velho daria o aviso nas nove; o novo, em nenhuma.

A falha do C13-1 na R1 não é de repetição: a API do Hospital respondeu HTTP 503 ao `consultar_precos_consultas` do turno 1 e, no turno 2, a Ana escalou pelo fora do horário antes do CPF (a mesma raiz do C13-1 R2 da v159, proposta 2 daquele diagnóstico). Conta como mista, infra mais Ana. A GH de homologação seguiu sem responder `consultar_convenios_agenda` (seis de seis) e `consultar_planos_convenio` (uma de uma); nenhum turno passou de 2 minutos, então nada contou à parte como infra lenta.

Comparado com a v159 (#51, 26, 27 e 27 de 29), estes três cenários passaram 8 de 9 aqui e 8 de 9 lá (C13-1 falhou uma vez nas duas). O placar não muda com a correção, porque nenhum desses cenários tem teto de repetição; o que muda é o aviso, que deixa de aparecer em quase toda conversa e volta a significar alguma coisa.
