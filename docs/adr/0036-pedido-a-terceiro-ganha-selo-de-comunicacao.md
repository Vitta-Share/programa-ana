---
status: accepted
date: 2026-11-15
amends: 0035
---

# Pedido a terceiro ganha o selo de comunicação

## Contexto

A Ana depende de quatro partes de fora: a Global Health, o TI do hospital (que mexe no MV), a fazer.ai e a diretoria do hospital. Até o ADR-0035, o `canal:aguardando` dizia "já pedido a terceiro". Na adoção do fluxo, ele virou `ready-for-human`, junto com o `canal:dispare`. Desde então, "o Pedro precisa agir" e "o Pedro espera a Global Health" ficaram iguais na fila, e não dava para ver de longe o que perguntar a quem nem o que cada resposta destrava. O Pedro pediu isso em 15/nov/2026, ao retomar a Ana para a apresentação ao diretor.

## Decisão

1. **Família de labels `com:`**, uma por parte: `com:global-health`, `com:ti-hospital`, `com:fazer-ai`, `com:hospital`. Pedido sobre o MV vai como `com:ti-hospital`.
2. **Um card por pedido** (Card de comunicação), com título "Perguntar à <parte>: ...", a mensagem pronta e o que ele destrava: os cards bloqueados pelo bloqueio nativo do GitHub e, para o que ainda não virou card, a linha "Destrava, ainda sem card:".
3. **O estado continua no papel de triage.** `ready-for-human` enquanto a mensagem não saiu; `needs-info` depois de enviada; fechado quando a resposta chega. O selo diz com quem; o papel diz de quem é a vez.
4. **Cobrar é Parada.** Sem prazo próprio por parte: card de comunicação sem mudança há 7 dias é a hora de cobrar.
5. **A mensagem aprovada vai também para as Mensagens a enviar do PedroOS** (issue os#855), com o link do card. O card guarda o porquê; o bloco é o lembrete de mandar.

No PedroOS, a mesma decisão pede a aba Roadmap na Página do Projeto (todos os PRDs, raias por `area:`, faixa "Esperando terceiros" pelo `com:`, progresso do milestone) e o nome da parte no O que é meu. Isso nasce como PRD no repo `pedrorezendefig/os`.

## Alternativas

- **Só `needs-info`, com a parte escrita no corpo.** O PedroOS não agrupa por texto do corpo. Descartado.
- **Voltar o `canal:aguardando`.** Mistura estado e parte de novo, e não diz qual parte. Descartado.
- **Um card por parte, com todas as perguntas.** O bloqueio fica vago: cada pergunta destrava cards diferentes. Descartado.
- **`com:mv` separado.** Hoje todo pedido sobre o MV passa pelo analista de TI. A label nasce no dia em que o Pedro falar direto com a MV.

## Consequências

- `docs/agents/triage-labels.md` e `tools/test_docs_fluxo.py` ganham as quatro labels.
- Os cards #4, #5, #7 e #12 recebem o selo e o formato de card de comunicação.
- O milestone "Apresentação ao diretor" marca o que a demo precisa; os cards da Global Health e do MV ficam fora dele, e a demo diz o que ainda depende deles.
