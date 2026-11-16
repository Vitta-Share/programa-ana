# Diagnóstico da bateria v73 (16/nov/2026)

Bateria `v73`: três rodadas de `cenarios/capacidades.json` (29 cenários) com a v7.3 em teste, segunda tentativa da issue #19 (PRD #30). Plataforma fazer.ai agents 1.59.0, `gpt-6-luna` com `reasoningEffort: none`, checagem de fatos em só registrar (#54), trava da ouvidoria desligada (#53). De 14:42Z a 16:20Z de 16/nov (11h42 a 13h20 em Brasília, horário comercial). Só homologação da Global Health e API do Hospital, sem `--com-escrita`: nenhuma linha gravada no painel da ouvidoria.

## Resumo

Placar: **26/29, 26/29 e 29/29**, contra 29, 29 e 28 da v72 (fora as três falhas da GH com horário). O placar caiu e, pela regra da triagem, a plataforma **voltou ao export às 16:21Z**: prompt v7.2 (sha `5331eb0a977b`), orientação do `handoff_to_human` e descrição da `consultar_exames` como estavam. Conferido depois: prompt, settings, `modelConfig` e descrição iguais aos exports.

O que fica desta tentativa é o cenário: o C13-1, o C14-1 e o C16-1 agora cobrem a GH sem resposta e a GH com horário (turno 4 condicional, `so_se`). A GH devolveu horário nas nove conversas desses três cenários; o C13-1 e o C16-1 passaram nas três rodadas pelo caminho novo, e o C14-1 pegou duas vezes defeito real da Ana. Custo da OpenAI por conversa US$ 0,0040 a 0,0041 (v72: 0,0034), com 1,33 a 1,43 mensagens da Ana por conversa (v72: 1,24); a diferença vem dos turnos 4 novos.

## O que foi para o ar e voltou

| Momento | O que mudou | Prova |
|---|---|---|
| 14:24Z | Prompt v7.3 (44.997 caracteres, sha `8a87bc7ee858`): na 2.4A PASSO 3, "Vieram horários, mesmo um só: a lista numerada e a pergunta [...]; nunca anotar a preferência sem o número do paciente". Orientação do `handoff_to_human` (`settings.handoff.instructions`, que a plataforma cola na descrição da ferramenta como "Operator guidance") com uma exceção para o turno da oferta. | Rodada direcionada `v73d`: C14-1 com horário passou; C10-2 falhou uma em quatro; C10-3 falhou uma em quatro (sem `agendamento-convenio`). |
| 14:37Z | Descrição da `consultar_exames` (ferramenta 2): "ofereça encaminhar [...] não substitui esse encaminhamento" virou "pergunte, em texto, se quer que a equipe confirme [...] o `handoff_to_human` só vem depois do sim". A primeira versão (2.173 caracteres) foi recusada com 422; o teto medido é 2.000. | Rodada direcionada `v73e`: C10-2 falhou uma em cinco. |
| 14:42Z a 16:20Z | Bateria v73, três rodadas. | Tabela abaixo. |
| 16:21Z | `publicar-prompt.py voltar` e a descrição do export. | Prompt `5331eb0a977b`, settings e descrição iguais aos exports. |

Por que a orientação do handoff era suspeita: no C10-2 da v72 R3 a Ana pôs `emergencia` e `fora-horario` às 9h de segunda e escalou. São exatamente as duas condições da orientação ("qualquer sinal de urgência médica (imediatamente...)" e "Fora do horário comercial"). Por que a descrição da ferramenta 2 era suspeita: o C10-2 é o único cenário do C10 que passa por ela, e ela pedia "encaminhamento" como ação no turno da pergunta. Nenhuma das duas trocas zerou a falha.

## Tabela

| Cenário | v72 R1 R2 R3 | v73 R1 | R2 | R3 | Classe | Causa em uma linha |
|---|---|---|---|---|---|---|
| C02-1 Saudação | ok ok ok | falhou | ok | ok | intermitente | Ana: `kanban_move_card` num "oi, boa tarde", ferramenta proibida no cenário. |
| C09-1 Cobertura de convênio | ok ok ok | ok | falhou | ok | intermitente | Ana: respondeu o portal sem a etiqueta `agendamento-convenio` e moveu para `AGUARDANDO CONFIRMAÇÃO`. |
| C10-1 Item fora da tabela | ok ok ok | falhou | ok | ok | intermitente | Ana: a oferta com a frase antiga ("na tabela oficial"), `get_current_time`, `fora-horario` às 11h e `handoff_to_human` no turno da oferta. |
| C14-1 Horários reais | ok ok falhou | falhou | falhou | ok | Ana, com a GH devolvendo horário | R1: "Anotei sua preferência de horário" no turno 3, sem lista. R2: lista e escalada no mesmo turno, e uma ferramenta de dado 3x. |
| C26-1 Prontuário | ok ok ok | ok | falhou | ok | intermitente | Ana: `skip_reply` duas vezes no turno 1; o paciente ficou sem resposta. |
| C13-1, C16-1 | ok ok falhou | ok | ok | ok | melhorou (cenário) | GH com horário nas três; o turno 4 conferiu a escalada. |
| C10-2 | ok ok falhou | ok | ok | ok | passa na bateria | Nas rodadas direcionadas, ainda uma em quatro e uma em cinco. |
| Outros 22 | ok ok ok | ok | ok | ok | passa | |

Por tipo de falha: **Ana 6** (C02-1, C09-1, C10-1, C14-1 duas vezes, C26-1), dado da GH 0, runner 0, cenário 0. Falha por Global Health lenta: **0**.

## Evidências

### C14-1, rodada 1 (GH com horário, o defeito da v72 R3 de novo)

- Turno 3, paciente: nome e CPF de teste.
- Veio: "Perfeito, Teste! Anotei sua preferência de horário. Nossa equipe vai entrar em contato em breve para confirmar tudo com você."
- Ferramentas: a cadeia inteira (`consultar_especialidades_agenda`, `consultar_convenios_agenda`, `consultar_planos_convenio`, `consultar_horarios_livres`), `set_labels`, `kanban_move_card`, `handoff_to_human`.
- Esperado: a lista numerada e a pergunta, sem anotar nada antes do número.
- Leitura: a regra nova do PASSO 3 estava no ar e o modelo usou a mensagem modelo do PASSO A3 ("Com horário escolhido") no turno da lista. O detector novo do cenário (`nao_contem` "anotei sua preferência") pegou; o turno 4 não foi enviado porque não houve lista.

### C14-1, rodada 2

- Turno 2, paciente: "pode ser, quero marcar sim". Veio: "O CPF ainda não foi validado [...] Pode conferir os 11 dígitos", com `buscar_paciente_por_cpf` três vezes sem CPF na conversa.
- Turno 3: a lista com um horário e "Qual opção você prefere?", e no mesmo turno `set_labels`, `kanban_move_card` e `handoff_to_human`. O turno 4 ("quero o 1") ficou sem resposta.
- Falha conferida: ferramenta de dado 3x no turno. A escalada no turno da lista não tem conferência própria hoje (ver pacote, item 3).

### C10-1, rodada 1

- Turno 1, paciente: "quanto custa a consulta de reumatologia?"
- Veio: "Não encontrei o valor da consulta de reumatologia na tabela oficial. Quer que nossa equipe confirme para você?"
- Ferramentas: `consultar_precos_consultas`, `kanban_move_card`, `get_current_time`, `set_labels` (`fora-horario`), `handoff_to_human`.
- Esperado: a oferta, sem handoff. Mesmo desvio do C10-2 da v72 R3: etiqueta de fora do horário em horário comercial e escalada antes do sim.

### C09-1, rodada 2

- Turno 1, paciente: Unimed e cardiologia. Veio a resposta do portal ("a cobertura de cardiologia depende do seu plano [...] tentar agendar pelo portal"), sem `set_labels`.
- Esperado: etiqueta `agendamento-convenio` (Caso 1 do convênio). A rodada direcionada teve a mesma falha no C10-3. Pode ter vindo da orientação nova do handoff ("não ponha etiqueta" no turno da oferta), lida como regra geral; não dá para separar do acaso com uma rodada.

### C26-1, rodada 2

- Turno 1, paciente: "preciso pegar meu prontuário médico". Ferramentas: `kanban_move_card`, `set_labels` (`prontuario`), `skip_reply` duas vezes. Sem resposta nos dois turnos.
- É o choque com a regra 8.3 já visto na v70.

### C02-1, rodada 1

- Turno 1, paciente: "oi, boa tarde". Veio a saudação certa, com `kanban_move_card`, que o cenário proíbe na saudação.

## Pacote de mudanças (proposta, nada aplicado)

1. **Camada do modelo (decisão do Pedro).** O desvio do turno da oferta (etiqueta sem apoio, escalada antes do sim) apareceu na v71, na v72 e na v73, no C10-1 e no C10-2, depois de mexer no prompt (Seção 6, Regras 9 e 13, descrição do handoff no prompt), na orientação do handoff da plataforma e na descrição da ferramenta 2. Texto não fecha a falha. O próximo passo é medir `reasoningEffort: low` no `gpt-6-luna` num clone do agente. Isso reabre o ADR-0013, que fixou `none`, e por isso fica com o Pedro.
2. **C14-1, anotar sem lista:** a mensagem modelo "Com horário escolhido no PASSO A3" aparece no turno da lista. Proposta: o rótulo da mensagem passa a ser "Só depois que o paciente respondeu o número da lista" e a regra do PASSO 3 da v7.3 volta junto. Medir só com `--so C14-1` repetido, antes da bateria.
3. **Cenário C14-1:** conferir que o turno 4 tem resposta da Ana, para pegar a escalada no turno da lista (R2). Hoje o turno sem resposta passa calado.
4. **Runner (da v72, segue aberto):** trace não coletado deveria virar alerta no veredito.

## Riscos para os cenários que passam

- O turno 4 condicional aumenta a conversa nos três cenários da agenda quando a GH responde: custo e duração da rodada sobem (rodada 2 levou 37 minutos).
- O `so_se` confere a lista pela regex `^\s*1[.)]\s`. Se a Ana mudar o formato da lista (por exemplo "Opção 1:"), o turno 4 não vai e a conferência do fim cai no turno 3, que acusa a falta da escalada.
- A plataforma está de volta na v7.2: o que a v72 mostrou (C10-2 intermitente, C14-1 anotando sem lista quando a GH devolve horário) continua valendo.
