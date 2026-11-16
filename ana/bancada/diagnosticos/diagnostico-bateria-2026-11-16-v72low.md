# Diagnóstico da bateria v72low (16/nov/2026)

Bateria `v72low`: três rodadas de `cenarios/capacidades.json` (29 cenários) num **clone da Ana** com `reasoningEffort: low`, terceira tentativa da issue #19 (PRD #30), caminho A decidido pelo Pedro em 16/nov. O clone (agente 2) tinha o prompt v7.2 (sha `5331eb0a977b`), os mesmos settings e as mesmas 14 ferramentas da Ana 1; só o `modelConfig.reasoningEffort` mudou, de `none` para `low`, no `gpt-6-luna`. Plataforma fazer.ai agents 1.59.0. De 17:10Z a 18:41Z de 16/nov (14h10 a 15h41 em Brasília, horário comercial). Só homologação da Global Health e API do Hospital, sem `--com-escrita`: nenhuma linha gravada no painel da ouvidoria.

## Resumo

Placar: **29/29, 28/29 e 28/29** (85 de 87), contra 29, 29 e 28 da v72 fora a Global Health (86) e 28, 29 e 29 da v71 (86). **O placar não subiu, então a Ana 1 não mudou** e o ADR-0013 segue como está (`reasoningEffort: none`).

O `low` acertou onde o `none` tropeçava: o C10-2 (a Ana encaminha antes do sim) passou nas três rodadas, e o C14-1 com horário da GH mostrou a lista e esperou o número nas três (na v72 e na v73 falhou três vezes em seis). Mas a falha intermitente mudou de lugar: o C10-3 pulou o `set_labels` uma vez e o C03-1 tropeçou no detector rígido de "vendemos". Custo e tempo quase iguais aos do `none`: US$ 0,0035 a 0,0036 por conversa, mediana de 9,2 a 9,4 s por chamada ao modelo.

## O que foi para o ar e voltou

| Momento (UTC) | O que mudou | Prova |
|---|---|---|
| 17:08 | Export da Ana 1 em `ana/plataforma/export-ana-pre-reasoning-low.json`. Prompt no ar conferido: sha `5331eb0a977b`, `updatedAt` 16:21:25Z. | `GET /api/v1/agents/1` |
| 17:08 | `agent_clone` da Ana 1 (dry_run antes): agente 2, "Ana clone reasoning low (#19)". Prompt, settings e grants iguais aos da Ana 1 (conferido campo a campo; os grants só mudam de ordem). | `agent_get`, `agent_tools_get` |
| 17:09 | `agent_update` do clone (dry_run antes): `reasoningEffort` de `none` para `low`, `enabled` e `mode: test`. Fumaça no playground com ferramenta: sem 400. | diff do dry_run |
| 17:09 | `inbox_bind` da inbox "Ana E2E (API)" no clone (dry_run antes). A Ana 1 ficou só com a inbox do Telegram de teste; a configuração dela não foi tocada. | `inbox_list` |
| 17:10 a 18:41 | Bateria v72low, três rodadas. Cada rodada registrou nas janelas "agente 2, gpt-6-luna, reasoning low". | `janelas-v72low.txt` |
| 18:41 | `inbox_bind` da inbox de volta na Ana 1 e `agent_delete` do clone (dry_run antes de cada um). | `agent_list` só com a Ana 1 |
| 18:42 | Ana 1 conferida contra o export: prompt `5331eb0a977b`, `updatedAt` 16:21:25Z, `reasoningEffort: none`, todos os campos iguais. Fumaça C05-1 na inbox de teste: respondeu a Ana 1 e passou. | `GET /api/v1/agents/1` |

As conversas gravadas (`ana/bancada/conversas/`) **não** foram atualizadas neste PR: são do clone, que não existe mais, e o player do Ana OS segue mostrando a última bateria da Ana 1 (v73, rodada 3). As cópias das três rodadas ficaram em `resultados/conversas-v72low-rodada{1,2,3}/`, fora do git.

## Tabela

| Cenário | v72 R1 R2 R3 | v73 R1 R2 R3 | v72low R1 | R2 | R3 | Classe | Causa em uma linha |
|---|---|---|---|---|---|---|---|
| C10-3 Item fora da tabela não vira negativa (convênio) | ok ok ok | ok ok ok | ok | falhou | ok | intermitente | Ana: resposta certa (Porto Seguro atendida e o portal), mas sem o `set_labels` `agendamento-convenio`. |
| C03-1 Recusar o que está fora do escopo | ok ok ok | ok ok ok | ok | ok | falhou | cenário rígido | A resposta "Não vendemos planos de saúde" está certa; o `nao_contem` "vendemos" pega a negação. Mesma leitura do diagnóstico da v70. |
| C10-2 Item fora da tabela | ok ok falhou | ok ok ok | ok | ok | ok | melhorou | A oferta sem handoff nas três. |
| C14-1 Oferecer horários reais | ok ok falhou | falhou falhou ok | ok | ok | ok | melhorou | GH com horário nas três: a lista, "Qual opção você prefere?", e a escalada só no turno 4. |
| C13-1, C16-1 | ok ok falhou | ok ok ok | ok | ok | ok | passa | GH com horário nas três; lista no turno 3 e escalada no turno 4. |
| Outros 23 | | | ok | ok | ok | passa | |

Por tipo de falha: **Ana 1** (C10-3), cenário 1 (C03-1), dado da GH 0, runner 0. Falha por Global Health lenta (mais de 2 min): **0**. A GH devolveu horário nas nove conversas do C13-1, C14-1 e C16-1.

Contagem: v72 com os cenários de hoje teria falhado o C14-1 na R3 (defeito da Ana), então a referência justa é 29, 29 e 28 (86). Sem o C03-1, que é do cenário, o clone faria 29, 28 e 29 (86): empate, não subida.

## Evidências

### C10-3, rodada 2

- Turno 1, paciente: "meu plano é a Porto Seguro Saúde, vocês cobrem dermatologia?"
- Veio: "Atendemos Porto Seguro Saúde no hospital. Você já pode tentar agendar dermatologia pelo nosso portal [...] Se aparecer alguma questão de cobertura por lá, me avisa que a equipe te ajuda, combinado?"
- Ferramentas: `kanban_move_card`, `consultar_especialidades_agenda`, `search_knowledge`, `kanban_move_card`.
- Esperado: a mesma resposta com a etiqueta `agendamento-convenio` e o card em `AGUARDANDO CONFIRMAÇÃO`. Faltou só a chamada do `set_labels`: o padrão de chamada pulada que a v69 e a v70 já mostravam no C10-3, agora com reasoning low.

### C03-1, rodada 3

- Turno 1, paciente: "vocês vendem plano de saúde?"
- Veio: "Não vendemos planos de saúde. O hospital atende pacientes por convênios e também no particular."
- Ferramentas: `search_knowledge`.
- Esperado: dizer que o hospital não vende plano, sem a palavra "vendemos". A resposta está certa; o detector é que confunde a negação com a afirmação.

## Custo e tempo

| Bateria | reasoning | US$ OpenAI por conversa | Tokens de saída por conversa | Mensagens da Ana por conversa | Mediana por chamada ao modelo |
|---|---|---|---|---|---|
| v72 (Ana 1) | none | 0,0034 a 0,0035 | sem medida | 1,24 | 9,2 s |
| v73 R3 (Ana 1, cenários de hoje) | none | 0,0038 | 522 | 1,34 | 10,3 s (bateria inteira) |
| v72low (clone) | low | 0,0035 a 0,0036 | 524 a 617 | 1,34 | 9,2 a 9,4 s |

O `low` gastou no máximo uns 100 tokens de saída a mais por conversa e não pesou no tempo. Custo não é motivo para recusar o `low`; o placar é.

## Pacote de mudanças (proposta, nada aplicado)

1. **Nada na Ana 1.** Pela regra da decisão (só mudar se o placar subir), o `reasoningEffort` segue `none`.
2. **C03-1, cenário.** Trocar o `nao_contem` "vendemos" por frases que só a afirmação tem ("vendemos planos", "temos planos à venda"), ou conferir só a ausência de oferta de plano. É mudança de cenário, para uma sessão de `/testes`.
3. **C10-2 e C14-1 com o `low`.** Se a decisão for aceitar uma chamada pulada no lugar do encaminhamento antes do sim, o `low` resolve os dois defeitos que o prompt não resolveu. A troca é uma linha (`agent_update` com `reasoningEffort: low`) e reabre o ADR-0013. Fica com o Pedro.

## Riscos para os cenários que passam

- Com o `low`, a falha intermitente não sumiu, mudou de lugar: o C10-3 pulou o `set_labels`, que no `none` falhava do mesmo jeito em outras baterias. Uma rodada a mais do `low` pode mostrar outra chamada pulada.
- O detector do C03-1 vai seguir pegando a negação certa, com qualquer modelo, até o cenário mudar.
