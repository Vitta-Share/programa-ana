---
status: accepted
date: 2026-11-16
---

# Prompt v7.1: a v7.0 comprimida, sem travessão

## Contexto

O prompt da Ana tinha 63.657 caracteres (uns 17 mil tokens), com regra dita duas e três vezes (os Lembretes Críticos repetiam as Regras Globais; a trava do protocolo da ouvidoria aparecia três vezes na 7.3; o aviso "fora do horário, aplicar a Seção 10" aparecia em cinco seções) e 29 travessões, que a Ana copiava na fala. Desde 01/out/2026 a Meta cobra por mensagem da Ana, e cada turno paga o prompt inteiro na OpenAI. A issue #25 (PRD #30) pediu o mesmo prompt mais curto, sem perder função.

## Decisão

1. **A v7.1 é a v7.0 dita uma vez só.** Cada regra mora num lugar; os Lembretes Críticos saíram, e o pouco que só existia lá foi para o Tom e para o fim das Regras Globais. O checklist `ana/prompt/regras-v69.md` dá o endereço na v7.1 de cada uma das 172 regras, templates e travas da v7.0.
2. **Nada muda de nome nem de ordem:** as 10 colunas do kanban, as 8 etiquetas, os atributos `nome_completo`, `cpf` e `convenio`, as ferramentas e a ordem das chamadas. As 31 mensagens modelo ao paciente vão iguais, caractere a caractere.
3. **Travessão só nos nomes das colunas** (EM ATENDIMENTO ANA, ENCERRADO RESOLVIDO e ENCERRADO DESISTÊNCIA levam travessão entre as palavras), que são assim na plataforma e o `kanban_move_card` move pelo nome exato. Fora deles, zero, e a Ana tem a regra "Nunca use travessão nem meia-risca na resposta".
4. **Saiu do prompt só o que a plataforma faz:** "nunca gravar atributo vazio", porque a 1.59 recusa `set_custom_attribute` vazio. Ficam no prompt o horário (#56 virou wontfix), a confirmação antes de registrar a ouvidoria (a trava da #53 foi desligada) e as travas do encaminhamento (a plataforma não tem regra que sirva ao `handoff_to_human`).
5. **Entraram quatro regras curtas:** a oferta de encaminhar espera o sim do paciente (Seção 6, proposta 1 da v159); a mensagem de prazo nunca antecipa uma escalada (Seção 10, proposta 2 da v159 e os dois acertos da checagem de fatos); o prontuário pergunta a finalidade antes de orientar (decisão do Pedro de 13/out na #25); e `set_labels` no lugar de `assign_label` na fonte.
6. **Publicação com trava de export.** `ana/plataforma/scripts/publicar-prompt.py` guarda o prompt vivo antes (`ana/plataforma/export-prompt-v70.md`) e só publica se o prompt no ar ainda é o esperado; `voltar` devolve a v7.0.

## Alternativas

- **Meta dura de 40 mil caracteres.** Teria custado regra de bateria: a primeira compressão (43.907) já perdeu a proibição de narrar a verificação no Caso 3, e a bateria pegou. Ficou em 44.243.
- **Tirar o horário e a confirmação da ouvidoria para a plataforma.** As duas tentativas (#56 e #53) não deram certo; ficaram no prompt.
- **Trocar os nomes das colunas para tirar o travessão.** Mexe no kanban do Chatwoot e nos cenários da bancada. Fora do escopo.

## Consequências

- Bateria v71 (três rodadas): 28, 29 e 29 de 29, contra 26, 27 e 27 da v7.0 na 1.59. OpenAI por conversa de US$ 0,0060 para US$ 0,0034; mensagens da Ana por conversa iguais. Diagnóstico em `ana/bancada/diagnosticos/diagnostico-bateria-2026-11-16-v71.md`.
- O C10-2 segue intermitente (uma em três). A proposta está no diagnóstico.
- O Mapa do SOP (`os/dados/sop-fluxo.json`) ancora trechos da v6.4 e já estava fora de dia; a v7.1 não muda isso.
- `tools/test_prompt_v7.py` trava o que a v7.1 promete: tamanho, travessão, nomes, as 31 mensagens modelo e o checklist.
