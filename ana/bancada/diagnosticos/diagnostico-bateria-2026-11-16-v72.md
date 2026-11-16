# Diagnóstico da bateria v72 (16/nov/2026)

Bateria `v72`: três rodadas de `cenarios/capacidades.json` (29 cenários) com o prompt v7.2, a v7.1 da #25 com a oferta de encaminhar endurecida (issue #19, PRD #30). Plataforma fazer.ai agents 1.59.0, `gpt-6-luna`, checagem de fatos em só registrar (#54), trava da ouvidoria desligada (#53). De 10:07Z a 13:29Z de 16/nov (segunda, 7h07 a 10h29 no horário de Brasília: **dentro do horário comercial**, ao contrário da v71, que rodou de madrugada). Só homologação da Global Health e API do Hospital; sem `--com-escrita`, então nenhuma linha foi gravada no painel da ouvidoria.

## Resumo

Placar do runner: **29/29, 29/29 e 25/29**. Tirando as três falhas da rodada 3 que vieram da Global Health voltando a responder com horário (C13-1, C14-1, C16-1, ver abaixo), o placar é **29, 29 e 28**, contra 28, 29 e 29 da v71: empate. A única falha fora da GH é de novo o C10-2 (rodada 3), a ressonância sem valor que escala no turno da oferta. Custo da OpenAI por conversa igual ao da v71 (US$ 0,0034 a 0,0035); mensagens da Ana por conversa iguais (1,24).

Fato novo: na rodada 3 a **cadeia de horários da GH rodou inteira pela primeira vez** nas baterias (`consultar_convenios_agenda`, `consultar_planos_convenio`, `consultar_horarios_livres`) e devolveu um horário de cardiologia. Os cenários C13-1, C14-1 e C16-1 foram escritos para a GH sem resposta (o turno 3 espera a escalada pelo PASSO A2); com horário na mão, o caminho certo é outro.

## Carimbo

| Momento | Prompt vivo | Tamanho | sha |
|---|---|---|---|
| Antes de tudo (export em `ana/plataforma/export-prompt-v71.md`) | v7.1 | 44.253 | `d76d3785c5d6` |
| Tentativa `v72a`, rodada 1 (09:06Z a 09:39Z) | só Seções 6 e 10 | 44.461 | `6a921aa55187` |
| Volta ao export (09:40Z), o placar caiu | v7.1 | 44.253 | `d76d3785c5d6` |
| Rodadas direcionadas (09:40Z a 09:55Z) | mais Regras 9 e 13, depois `customerMessage` | 44.643 e 44.776 | `b07a7d4084ed`, `1eb24a99d4c2` |
| Bateria v72, R1 a R3 | v7.2 | 44.994 | `5331eb0a977b` |

Conferido antes da rodada 2: o prompt vivo seguia o `5331eb0a977b`, `updatedAt` 09:55:16Z (a publicação desta sessão).

## O caminho até a v7.2

A v71 deixou uma falha só, o C10-2 (uma em três): a oferta "Posso encaminhar?" certa e, no mesmo turno, `get_current_time`, `fora-horario` e `handoff_to_human`.

1. **Tentativa `v72a`** (a proposta 1 da v71 ao pé da letra): a regra da oferta ganhou "o turno termina na pergunta: sem `get_current_time`, sem `fora-horario`" e a Seção 10 passou a dizer que a etiqueta não vem no turno da oferta. Rodada 1: **26/29** (C09-1 com a GH cortando a cobertura em 30 s, C10-1 e C10-2 escalando). O placar caiu e o prompt voltou ao export da v7.1.
2. **O que puxava a escalada.** A pergunta da oferta saía pelo campo `customerMessage` do `handoff_to_human` (146 e 152 caracteres, os mesmos da resposta que o paciente viu). A descrição da ferramenta no prompt manda pôr "a mensagem ao paciente no turno da escalada" nesse campo, e o modelo tratava a oferta como turno de escalada. Duas regras globais empurravam na mesma direção: a 9 ("nunca escalar sem antes conferir o horário") e o "em dúvida, escalar".
3. **A v7.2** soma: Regra 9 ("oferecer encaminhar não é escalar"), Regra 13 (sem valor, a oferta da Seção 6), a descrição do `handoff_to_human` ("a pergunta da oferta é resposta de texto e nunca vai no `customerMessage`"), uma **mensagem modelo** da oferta sem a palavra "tabela" e a **lista fechada** das ferramentas do turno (só a consulta e o card em `EM ATENDIMENTO`). Nas rodadas direcionadas, a cada passo, o C10-1 passou de duas falhas em quatro para nenhuma em três.

## Tabela

| Cenário | v71 R1 R2 R3 | v72 R1 | R2 | R3 | Classe | Causa em uma linha |
|---|---|---|---|---|---|---|
| C10-2 Item fora da tabela | falhou ok ok | ok | ok | falhou | intermitente (uma em três, igual à v71) | Ana: a mensagem modelo saiu certa, mas o modelo pôs `fora-horario` e `emergencia` às 9h12 de segunda, moveu para a `FILA ATENDIMENTO` e escalou. |
| C13-1 Achar o cadastro | ok ok ok | ok | ok | falhou | dado da GH | A GH devolveu um horário; a Ana mostrou a lista e esperou o número (PASSO 3 da 2.4A, certo). O cenário espera a escalada do PASSO A2. |
| C16-1 Levar o caso para a equipe | ok ok ok | ok | ok | falhou | dado da GH | Idem: lista com um horário, sem escalada no turno 3. |
| C14-1 Horários reais | ok ok ok | ok | ok | falhou | dado da GH, com defeito da Ana | A GH devolveu um horário só; a Ana escolheu por ele ("Anotei sua preferência para 26/11, às 9h15") sem mostrar a lista e sem escalar. |
| Outros 25 cenários | ok ok ok | ok | ok | ok | passa | |

Por tipo de falha: **Ana 1** (C10-2 R3), **dado da GH 3** (C13-1, C14-1, C16-1 na R3; a C14-1 esconde um defeito da Ana que só aparece com horário), runner 0, cenário 0. Falha por Global Health lenta: **0**.

## Evidências

### C10-2, rodada 3 (bateria v72)

- Turno 1, paciente: "quanto custa a ressonância magnética?"
- Veio: "Não tenho o valor da ressonância magnética para te passar agora. Quer que nossa equipe confirme para você?" (a mensagem modelo, palavra por palavra).
- Esperado: a oferta, sem handoff.
- Ferramentas: `consultar_exames`, `set_labels` três vezes (`fora-horario` e `emergencia`; a `agente-off` é da plataforma), `kanban_move_card` três vezes (duas para `EM ATENDIMENTO`, uma para `FILA ATENDIMENTO`), `handoff_to_human`.
- Leitura: a fala obedeceu, a escolha de ferramentas não. `fora-horario` às 9h12 de segunda e `emergencia` numa pergunta de preço não têm apoio em regra nenhuma: é o modelo com reasoning `none` saindo do trilho. Sem `get_current_time` no turno (a v7.2 tirou), a etiqueta de horário veio de palpite.

### C13-1 e C16-1, rodada 3

- Turno 3, paciente: nome e CPF de teste. Veio a lista numerada com um horário de cardiologia em 26/11 e "Quer que eu anote sua preferência por esse horário?".
- Ferramentas: `buscar_paciente_por_cpf` e a cadeia inteira (`consultar_especialidades_agenda`, `consultar_convenios_agenda`, `consultar_planos_convenio`, `consultar_horarios_livres`). Nas rodadas 1 e 2 a `consultar_convenios_agenda` não respondeu e a Ana seguiu o PASSO A2 (escalada), que é o que os cenários conferem.
- Esperado pelo cenário: etiqueta `agendamento-particular` e raia `FILA COMERCIAL` no turno 3.
- Leitura: a Ana fez o certo para uma agenda com horário. O cenário precisa de um turno 4 (o paciente escolhe o número) para conferir a escalada.

### C14-1, rodada 3

- Turno 3, paciente: nome e CPF de teste. Veio: "Perfeito, Teste! Anotei sua preferência para 26/11, às 9h15. Nossa equipe vai entrar em contato em breve para confirmar tudo com você."
- Ferramentas: a cadeia inteira, `update_kanban_task`, `set_labels`, `kanban_move_card`. Sem `handoff_to_human`.
- Esperado: handoff no turno 3 (cenário da GH vazia). Pela 2.4A, com horário: a lista e esperar o número.
- Leitura: com um horário só, a Ana pulou a escolha do paciente e anotou por ele. É a primeira vez que esse caminho roda numa bateria.

## Custo e mensagens

| Medida | v7.1 (v71) | v7.2 (v72) |
|---|---|---|
| Caracteres do prompt | 44.243 | 44.994 |
| Placar (três rodadas, fora a GH) | 28, 29, 29 | 29, 29, 28 |
| OpenAI por conversa | US$ 0,0034 | US$ 0,0034, 0,0034 e 0,0035 |
| Mensagens da Ana por conversa | 1,24 | 1,24 |

A rodada 2 levou 63 minutos e a 3 levou 110 (a 1, 29): a rota de logs da plataforma não respondeu no C24-1 da rodada 2 (o trace ficou sem coleta e o cenário passou sem conferir ferramenta) e a GH respondendo devagar alongou a rodada 3.

## Pacote de mudanças (proposta, nada aplicado)

1. **Cenários C13-1, C14-1 e C16-1:** ganhar um turno 4 (o paciente responde "1") e conferir a escalada nele, ou ter duas versões, uma para a GH sem resposta e outra com horário. Hoje eles só passam com a GH fora do ar.
2. **2.4A PASSO 3, horário único:** somar "Mesmo com um horário só, a mensagem é a lista com o número 1 e a pergunta; nunca anotar a preferência sem o número do paciente." Mata a falha da Ana escondida no C14-1.
3. **C10-2:** a falha mudou de forma (etiquetas sem apoio, não mais a oferta no `customerMessage`). Próximo passo é medir com `reasoning: low` num clone do agente, já sugerido na #19 em outubro, antes de mais texto no prompt.
4. **Runner:** trace não coletado deveria virar alerta no veredito (hoje o C24-1 da rodada 2 passou sem conferir ferramenta).

## Riscos para os cenários que passam

- A v7.2 tirou o `get_current_time` do turno da oferta. Num pedido de valor fora da tabela, de madrugada, a etiqueta `fora-horario` passa a vir no turno do sim, junto com a escalada, como a Seção 10 já pede.
- A mensagem modelo da oferta troca "Não encontrei o valor... na tabela oficial" por "Não tenho o valor de [item] para te passar agora". Nenhum cenário confere essa frase; o C10-1 e o C10-3 continuam passando.
- A bateria v72 rodou toda em horário comercial e a v71 toda de madrugada: o empate no placar vale com essa ressalva.
