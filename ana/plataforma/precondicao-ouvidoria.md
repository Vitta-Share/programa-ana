# Trava da ouvidoria na plataforma (issue #53)

Em 16/nov/2026 a ferramenta 11 (`registrar_ouvidoria`) ganhou na plataforma uma trava para só rodar depois que o paciente confirma o que vai ser gravado. A trava existe só no prompt (Seção 7.3, "Com todos os dados confirmados pelo paciente"), e o modelo decide de novo a cada turno se obedece.

**Estado hoje: desligada.** Na bateria, ela recusou o registro nas três rodadas mesmo com o paciente confirmando, e a Ana disse ao paciente que tinha registrado sem gravar nada (Placar, abaixo). O script e o export ficam para religar quando houver um jeito de a trava acertar.

## O que foi ligado (e desligado)

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

## Placar: a trava piorou o registro e foi desligada

Bateria `p53`, 16/nov de 06:13Z a 06:28Z (madrugada de segunda, fora do horário comercial, como a v159), três rodadas de C21-1, C22-1 e C10-2 com `--com-escrita`, plataforma 1.59.0, prompt vivo sha `fdfadc07ff6e`. Comparação com o placar da 1.59 (#51): o C22-1 não roda na bateria sem escrita, então a referência dele é a conversa 606 da #52, na mesma 1.59.

| Cenário | 1.59 (#51, #52) | Com a trava R1 | R2 | R3 | Sem a trava |
| --- | --- | --- | --- | --- | --- |
| C21-1 Acolher e coletar | ok ok ok | ok | ok | ok | |
| C22-1 Registrar e devolver o protocolo | ok (1 de 1) | falhou | falhou | falhou | ok (protocolo 2026-0218) |
| C10-2 Item fora da tabela | falhou ok falhou | ok | ok | ok | |

O juiz recusou a `registrar_ouvidoria` nas três rodadas (linha `phase: precondition`, `preconditionKind: customer_choice`, em `info`, nas conversas 821, 824 e 827), sempre no turno em que o paciente diz "isso mesmo, pode registrar por favor". É recusa de mérito, não falha do juiz (essa seria `precondition_unreadable`, em `warn`). Na R3 a Ana tinha mostrado o resumo inteiro (solicitante, data, setor e relato) logo antes do sim; na R2 ela chegou a perguntar "posso classificar o relato como demora na recepção do ambulatório?" e o paciente confirmou. Mesmo assim, NO.

Pior que a recusa foi o que veio depois. A plataforma manda o modelo perguntar de novo ao paciente, e a Ana não perguntou:

- R1 (821): "Registrei sua solicitação e nosso time vai te contatar" sem gravar nada e sem encaminhar.
- R2 (824): encaminhou para a equipe sem protocolo e sem mensagem que chegasse ao paciente em 150 s.
- R3 (827): a mensagem sem protocolo da Seção 7.3 ("registrada com todo o cuidado") e o encaminhamento.

Nenhuma das três gravou linha no painel da ouvidoria. O C10-2 passou nas três, mas isso não vem da trava (o `handoff_to_human` segue sem regra): é a mesma intermitência da v159. O C21-1 não chega ao registro e ficou igual.

Pela regra da issue ("se a trava piorar o placar, ela é desligada"), a trava foi desligada às 06:29Z (`desligar`, `toolPreconditions: {}`) e uma rodada de conferência do C22-1 sem ela gravou o protocolo 2026-0218 na conversa 828 e passou.

Por que o juiz recusa: a plataforma não expõe a resposta do juiz nos Logs, e daqui não dá para repetir a chamada dele. A hipótese mais forte está no próprio `CHOICE_JUDGE_PROMPT`: ele exige que cada valor que "escolhe uma opção" esteja nas palavras do paciente, e os argumentos da ferramenta 11 são todos escritos pela Ana (o `resumo` em "paciente relata que...", a `categoria` de uma lista de sete que o paciente nunca vê, o `setor` normalizado). O tipo `customer_choice` foi medido pela fazer.ai em catálogo, pedido e agenda, onde o paciente escolhe um valor; a ouvidoria registra um relato, e "confirmou o resumo" não é o que o juiz confere. Para religar, o caminho é pedir à fazer.ai um modo "o paciente confirmou a ação" (o mesmo que o handoff precisaria) ou testar a trava com a Ana repetindo `categoria` e `setor` no resumo que o paciente confirma, o que mexe no prompt e é da #25.

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
