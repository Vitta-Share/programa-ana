# Trava da ouvidoria na plataforma (issue #53)

Desde 16/nov/2026 a ferramenta 11 (`registrar_ouvidoria`) só roda depois que a plataforma confere que o paciente confirmou o que vai ser gravado. Antes, essa trava existia só no prompt (Seção 7.3, "Com todos os dados confirmados pelo paciente"), e o modelo decide de novo a cada turno se obedece.

## O que foi ligado

| Onde | Valor | Versão da plataforma |
| --- | --- | --- |
| `settings.toolPreconditions.registrar_ouvidoria` | `{"kind": "customer_choice"}` | 1.54 (instância na 1.59.0) |

No console: agente Ana, aba Ferramentas, "Pré-condições".

Como funciona: a cada chamada da `registrar_ouvidoria`, um juiz no modelo do próprio agente (`gpt-6-luna`, sem `settings.choiceCheck`) lê a conversa do atendimento aberto, a descrição da ferramenta, o prompt da Ana (como referência do negócio) e os argumentos da chamada, e responde YES ou NO. Só YES deixa o registro rodar. Recusada, a chamada não acontece, o modelo recebe a instrução de perguntar ao paciente e chamar de novo depois da resposta, e a plataforma grava uma linha `info` nos Logs (`preconditionKind: "customer_choice"`). Juiz que erra, demora mais de 20 s ou não lê também recusa (linha `precondition_unreadable`, em `warn`). O juiz custa uma chamada de modelo a mais por registro (a plataforma mede uns US$ 0,0001 por conversa no `gpt-6-luna`, mediana de 1 s) e aparece no custo como `choice_check`.

A trava do prompt fica onde está: quem decide o que sai do prompt é a #25.

## E o encaminhamento da agenda? Não dá

A issue pediu para avaliar o mesmo no `handoff_to_human`, porque no C10-2 a Ana pergunta "posso encaminhar?" e escala no mesmo turno, sem esperar o sim. A plataforma deixa ligar a regra numa ferramenta nativa (o mapa é por nome), mas ela não resolve esse caso e cria outro problema:

1. **O juiz não pergunta se o paciente aceitou a ação.** Ele confere uma coisa só: se cada escolha que os argumentos fazem pelo paciente (opção, quantidade, data, hora, pessoa) foi dita ou confirmada por ele. Os argumentos do `handoff_to_human` no modo da Ana (`route`) são `reason`, a nota privada para a equipe, e `customerMessage`, o texto que a própria Ana manda. Nenhum dos dois escolhe nada pelo paciente, então no C10-2 o juiz responde YES e o encaminhamento antes do sim passa do mesmo jeito.
2. **A trava fecha quando o juiz falha.** Juiz lento (mais de 20 s), com erro ou ilegível recusa a chamada. No encaminhamento isso seguraria justamente o que não pode esperar: a urgência (C01-1, Regras 9 a 11, "imediatamente, em qualquer horário") e o paciente que pede uma pessoa.
3. **A trava por atributo também não serve.** A própria documentação da plataforma mediu que o modelo escreve o atributo exigido com `set_custom_attribute` no mesmo turno e passa pela trava.

Fonte: `docs/graph.md` (seção Tool preconditions) e `src/graph/tools/customer-choice.ts` (`CHOICE_JUDGE_PROMPT`) do repositório público `fazer-ai/agents`, e `src/graph/tools/native.ts` para os argumentos do `handoff_to_human`.

O caminho para o C10-2 é o prompt: a proposta 1 do diagnóstico da v159 (Seções 6.B e 6.C, "só se o paciente aceitar"), que pertence à #25.

## Placar

BATERIA

## Como repetir

```bash
python3 ana/plataforma/scripts/precondicao-ouvidoria.py exportar   # guarda o estado antes de mudar
python3 ana/plataforma/scripts/precondicao-ouvidoria.py ligar      # para se outra sessão mudou as settings desde o export
python3 ana/plataforma/scripts/precondicao-ouvidoria.py ver        # mostra as regras vivas
python3 ana/bancada/e2e.py cenarios/capacidades.json --so C21-1,C22-1,C10-2 --com-escrita --bateria p53 --rodada 1
```

O `ligar` manda o saco de settings inteiro (o PATCH da plataforma substitui, não mescla) com `expectedUpdatedAt`, então a plataforma recusa com 409 se outra sessão gravou o agente entre a leitura e a escrita.

## Como voltar atrás

Se a trava piorar o placar, ela é desligada:

```bash
python3 ana/plataforma/scripts/precondicao-ouvidoria.py desligar
```

Tira só a regra da `registrar_ouvidoria` e preserva as outras settings. O estado anterior inteiro está em `ana/plataforma/export-ana-pre-precondicao-ouvidoria.json` (sem o prompt, que mora em `ana/prompt/`; vão o hash e o tamanho dele). No console: aba Ferramentas, "Pré-condições", remover a regra da ferramenta.
