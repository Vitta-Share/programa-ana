# Diagnóstico da bateria v159 (16/nov/2026)

Bateria `v159`: três rodadas de `cenarios/capacidades.json` (29 cenários) na plataforma fazer.ai agents **1.59.0**, de 02:16Z a 03:47Z de 16/nov (domingo 23h16 a segunda 0h47 no horário de Brasília, fora do horário comercial nas três). Issue #51, PRD #30. Só homologação da Global Health e API do Hospital; modo leitura: nada foi aplicado no prompt, nas ferramentas, nos cenários ou no runner.

## Resumo

Placar do runner: **26/29, 27/29 e 27/29** (v70: 27, 27 e 27). Tirando a falha que é do runner (C14-1 na rodada 1), o placar real é 27, 27 e 27: **empate com a v70**. Nenhuma falha constante. Quatro cenários da v70 melhoraram (C03-1, C05-2, C09-1, C26-1) e quatro regrediram (C08-2, C10-1, C13-1, C14-1, este último falso).

Padrão principal: cinco das seis falhas reais são a mesma, **a Ana pergunta "posso encaminhar?" e escala no mesmo turno**, sem esperar o sim (C08-2 duas vezes, C10-2 duas vezes, C10-1 uma). É a proposta 2 da v70, que não foi aplicada (Seções 6.B e 6.C do prompt seguem iguais). Agravante novo: a Ana agora reconhece o fora de horário muito mais (etiqueta `fora-horario` em 6 e 7 conversas por rodada, contra 0 a 2 na v70, que também rodou de madrugada), e o caminho do fora de horário puxa o encaminhamento. A C13-1 da rodada 2 é a mesma raiz: escalou no turno 2, antes do CPF.

Infra: a Global Health de homologação **não respondeu nenhuma vez** a `consultar_convenios_agenda` (12 de 12 chamadas cortadas pela plataforma em 30 s). Nenhum cenário falhou por isso, porque a Ana cobriu todas com o Caso 3 da Seção 3.2, mas a cadeia de horários (`consultar_planos_convenio`, `consultar_horarios_livres`) **não rodou em nenhuma das 87 conversas**. Uma falha mista: API do Hospital com HTTP 503 no C08-2 da rodada 3.

## Carimbo da plataforma em cada rodada

As issues #52 e #57 mexiam nas ferramentas 7 e 11 em paralelo. Medido por `GET /api/v1/agents/1`, `/export` e `/api/v1/tools` antes da rodada 1 e depois de cada rodada:

| Momento | Plataforma | Modelo | Prompt vivo | Ferramenta 7 `cadastrar_paciente` | Ferramenta 11 `registrar_ouvidoria` | Ferramenta 13 `consultar_convenios_agenda` |
|---|---|---|---|---|---|---|
| Antes da R1 (02:16Z) | 1.59.0 | gpt-6-luna, none | 63.657 chars, sha `fdfadc07ff6e` | 07/ago 18:22Z | 18/ago 19:24Z | 15/nov 23:33Z |
| Depois da R1 (02:44Z) | 1.59.0 | igual | igual | **16/nov 02:17:38Z** | **16/nov 02:17:38Z** | igual |
| Depois da R2 (03:18Z) | 1.59.0 | igual | igual | 16/nov 02:17:38Z | 16/nov 02:17:38Z | igual |
| Depois da R3 (03:47Z) | 1.59.0 | igual | igual | 16/nov 02:17:38Z | 16/nov 02:17:38Z | igual |

As ferramentas 7 e 11 mudaram às 02:17:38Z, no primeiro minuto da rodada 1 (durante o C01-1). Daí em diante as três rodadas rodaram com a mesma versão de tudo. Nenhum cenário automático exercita as duas: a 7 está fora do grant (ADR-0014) e o C22-1, único que chama a 11, só roda com `--com-escrita`. O agente 1 teve `updatedAt` 02:18:36Z sem mudar prompt, modelo nem grants. Nas mesmas janelas, duas conversas de outras sessões (#606 e #608) passaram pela inbox de API: o custo por janela dos primeiros cenários da R1 pode vir inflado.

**Prompt vivo:** é o v7.0 com `assign_label` trocado por `set_labels` (16 ocorrências; fora isso, idêntico byte a byte a `ana/prompt/prompt-compilado.md`). A ferramenta nativa mudou de nome na plataforma e o prompt publicado acompanhou; a fonte no repositório não.

**Grant de RAG:** conferido no export do agente 1: a fonte `RAG` concede `search_knowledge` com `knowledgeBases: ["Base Hospital São Matheus"]`. A base está escolhida, então a mudança da 1.47 (grant sem base não pesquisa mais em todas) não afeta a Ana. `search_knowledge` rodou 30 vezes nas três rodadas (mediana 0,6 s) e respondeu certo (endereço no C29-1, convênio no Caso 3). Grants: 10 nativas, 1 RAG, 12 HTTP.

## Tabela

| Cenário | v70 R1 R2 R3 | v159 R1 | R2 | R3 | Classe | Causa em uma linha |
|---|---|---|---|---|---|---|
| C08-2 Estimativa de cirurgia | ok ok ok | falhou | ok | falhou | regrediu, intermitente | Ana: ofereceu conectar e chamou `handoff_to_human` no mesmo turno (6.C sem "só se aceitar"). R3 com a API do Hospital em 503 (infra mais Ana). |
| C10-1 Item fora da tabela | ok ok ok | ok | falhou | ok | regrediu, intermitente | Ana: caminho de fora do horário ("Registrei sua solicitação") com escalada antes do sim. |
| C10-2 Item fora da tabela | ok falhou ok | falhou | ok | falhou | intermitente | Ana: "Posso encaminhar?" e `handoff_to_human` no mesmo turno (6.B, proposta 2 da v70 não aplicada). |
| C13-1 Achar o cadastro | ok ok ok | ok | falhou | ok | regrediu, intermitente | Ana: no turno 2 pediu o nome e já escalou pelo fora de horário; no turno 3 a conversa estava com humano e o bot calou. |
| C14-1 Horários reais | ok ok ok | falhou | ok | ok | falso (runner) | Runner: a 1.59 grava duas linhas de log por `set_labels`; duas etiquetas viram "4 chamadas" e estouram o teto de 2 por turno. |
| C03-1 Fora do escopo | falhou ok ok | ok | ok | ok | melhorou | |
| C05-2 Preço (último item) | ok ok falhou | ok | ok | ok | melhorou | A falha da v70 era API do Hospital fora. |
| C09-1 Cobertura de convênio | ok ok falhou | ok | ok | ok | melhorou | Com a GH sem resposta nas três, a Ana seguiu o Caso 3 literal. |
| C26-1 Prontuário | falhou falhou ok | ok | ok | ok | melhorou | |
| Outros 20 cenários | ok ok ok | ok | ok | ok | passa | Ver ressalvas de falso verde no C21-1 e no C29-1, abaixo. |

Por tipo de falha (as 7 do runner): **Ana 5** (C08-2 R1, C10-1 R2, C10-2 R1 e R3, C13-1 R2), **mista infra mais Ana 1** (C08-2 R3, API do Hospital 503), **runner 1** (C14-1 R1), **cenário 0**. Falha por Global Health lenta: **0** contadas, mas a GH cobrou cobertura (ver Resumo).

## O que a plataforma nova mudou no comportamento

- **Turno vazio que pergunta de novo ao modelo (1.31).** `effective.limits.retrySilence` está `true`. Nas três rodadas nenhum log de `generate` mostrou uma segunda chamada por resposta vazia; o único retry visto foi de erro (`failure: HTTP 400`, `willRetry: true` no C05-3 da R1, que passou). Os turnos sem texto da v159 (C13-1 R2 turno 3, C14-1 R2 turno 3, C21-1 R2 turno 1, C29-1 turno 2 nas três) não vieram de resposta vazia: vieram de handoff, de `skip_reply` ou de card ganho (itens seguintes). Não deu para provar o recurso em ação.
- **Histórico datado (1.25).** Não há rota que mostre o histórico que o modelo recebe. O sinal indireto é forte: as notas privadas da Ana citam o dia e a hora ("Fora do horário comercial (segunda-feira 00:..."), e a etiqueta `fora-horario` saiu em 6, 7 e 7 conversas por rodada, contra 0, 1 e 2 na v70 (também de madrugada, numa terça). Fator de confusão: a v159 rodou na virada de domingo para segunda. Mesmo assim, no domingo às 23h57 a Ana usou o Cenário A ("próximo expediente") e não a MENSAGEM_FDS.
- **`skip_reply` (1.44).** O log agora traz `skipReason` e `turnDelivered`. Depois de já ter mandado a mensagem (`turnDelivered: true`, C13-1 R1, C14-1 R3) o `skip_reply` é inofensivo. Antes de mandar qualquer coisa (`turnDelivered: false`, C21-1 R2), o paciente fica sem resposta e a plataforma abre a conversa para a equipe com a nota "O agente não respondeu". O runner deu esse C21-1 como aprovado.
- **Outros achados da 1.59 que mexem na bancada:**
  - `assign_label` virou `set_labels`, e cada chamada gera duas linhas no log (uma de `phase: labels`). O runner conta as duas: falso vermelho no C14-1 R1 e alerta de "tool repetida" em vários cenários.
  - O tempo limite das ferramentas HTTP subiu de 10 s (v70) para 30 s. Um turno com a GH fora agora leva uns 50 s, e o teto de 10 chamadas por turno (`toolLimitHit`) bateu em 4 turnos.
  - `set_custom_attribute` com valor vazio é recusado pela plataforma (`phase: attribute_refused`, `rule: empty`), em 4 chamadas.
  - A plataforma posta duas notas privadas por turno: "Ferramentas usadas pelo agente neste turno" e "Erros neste turno do agente", com o HTTP de cada falha. Ajudou a fechar as causas deste diagnóstico.
  - A conversa da inbox de API agora ganha card no funil "Hospital São Matheus". No C29-1, o `kanban_move_card` da despedida ganha a tarefa, a conversa é resolvida e **a mensagem de despedida não sai** (nas três rodadas; na v70 a Ana se despedia nas três). O runner aprova porque o turno 2 só confere ferramentas.
  - Os atributos de contato `cpf` e `nome_completo` (`attributeContext.contact`) ficam no contato de teste entre rodadas. No C14-1 da R2 a Ana já sabia nome e CPF no turno 2, pulou a coleta e escalou; o turno 3 do cenário caiu no vazio.

## Evidências

### C08-2, rodada 1 (conversa 617)

- Turno 1, paciente: "quanto custa a cirurgia de apendicite por videolaparoscopia?"
- Veio: a estimativa de R$ 8.300 com o aviso completo, terminando em "Quer que eu te conecte com nossa equipe para um orçamento personalizado?"
- Esperado: R$ 8.300 com o aviso, sem handoff (`handoff: false`).
- Ferramentas: `consultar_cirurgias_estimativas`, `kanban_move_card`, `handoff_to_human`.
- Leitura: a 6.C diz só "oferecer conectar com a equipe". Sem o "só se aceitar", a Ana pergunta e escala junto.

### C08-2, rodada 3 (conversa 675)

- Turno 1: a mesma pergunta. Veio: "Não consegui confirmar a estimativa agora. O orçamento depende de avaliação médica presencial. Posso encaminhar você à nossa equipe para verificar o valor?"
- Ferramentas: `kanban_move_card`, `consultar_cirurgias_estimativas` (HTTP 503, nota "Erros neste turno"), `handoff_to_human`.
- Leitura: a API do Hospital caiu (infra). A Ana respondeu a indisponibilidade de forma aceitável, mas de novo escalou antes do sim.

### C10-1, rodada 2 (conversa 649)

- Turno 1, paciente: "quanto custa a consulta de reumatologia?"
- Veio: "Não encontrei o valor de reumatologia na tabela oficial. Posso encaminhar para a equipe confirmar para você. Nossa equipe de atendimento funciona de segunda a sexta, das 7h às 18h. Registrei sua solicitação e nosso time vai te contatar assim que iniciar o próximo expediente."
- Esperado: a oferta de encaminhar, sem handoff.
- Ferramentas: `kanban_move_card`, `consultar_precos_consultas`, `set_labels` (`fora-horario`, `particular-aquecido`), `handoff_to_human`.
- Leitura: a Seção 6.A diz "Se o paciente aceitar, seguir a 2.4A", mas a mensagem do Cenário A da Seção 10 ("Registrei sua solicitação") puxou a escalada junto.

### C10-2, rodadas 1 e 3 (conversas 621 e 679)

- Turno 1, paciente: "quanto custa a ressonância magnética?"
- R1 veio: "Não encontrei o valor da ressonância magnética na tabela oficial. Posso encaminhar sua pergunta para a equipe confirmar o valor e a disponibilidade. Como estamos fora do horário, nosso time vai te responder assim que iniciar o próximo expediente." Ferramentas: `consultar_exames`, `set_labels`, `kanban_move_card`, `handoff_to_human`.
- R3 veio: "Não encontrei o valor da ressonância magnética na informação oficial disponível. Posso encaminhar sua dúvida para a equipe confirmar?" Ferramentas: `consultar_exames`, `handoff_to_human`.
- Esperado: a oferta, sem handoff.
- Leitura: a 6.B segue com "não estimar; oferecer encaminhar à equipe", sem o "só se aceitar". Mesma falha da v70 R2.

### C13-1, rodada 2 (conversa 652)

- Turno 1: preço da cardiologia (R$ 380) e "Quer que eu veja os horários disponíveis?". Ok.
- Turno 2, paciente: "pode ser, quero marcar sim". Veio: "Claro! Para deixar o agendamento pronto, me passa seu nome completo, por favor? Nossa equipe de atendimento funciona de segunda a sexta, das 7h às 18h. Registrei sua solicitação e nosso time vai te contatar assim que iniciar o próximo expediente." Ferramentas: `set_labels` (`fora-horario`), `set_custom_attribute` (2x), `handoff_to_human`.
- Turno 3, paciente: nome e CPF. Veio: nada (a conversa estava com humano).
- Esperado no turno 3: `buscar_paciente_por_cpf`, etiqueta `agendamento-particular`, raia FILA COMERCIAL.
- Leitura: a regra da v6.8 "nada de handoff antes do CPF" perdeu para o fora de horário. A Ana pediu o nome e escalou na mesma mensagem.

### C14-1, rodada 1 (conversa 624), falha do runner

- Turno 3, paciente: nome e CPF. Veio: "Prontinho, Teste! A agenda online não me retornou horários agora, então nossa equipe vai entrar em contato para confirmar o melhor horário com você." É o comportamento que o cenário pede.
- Conferência que falhou: "repetição de ferramenta, no máximo 2x por turno", veio 4.
- Log da plataforma: `set_labels` chamado duas vezes no turno, cada chamada com duas linhas (`phase: labels` e a chamada). A nota da própria plataforma diz `set_labels` uma vez por etiqueta. `consultar_convenios_agenda` chamada duas vezes, ambas cortadas em 30 s.
- Leitura: `TOOLS_DE_ESCRITURACAO` no `e2e.py` ainda lista `assign_label` e não `set_labels`, e o `Trace` não descarta a linha de `phase`.

## Pacote de mudanças (proposta, nada aplicado)

1. **Prompt, Seções 6.B e 6.C** (repete a proposta 2 da v70, agora com cinco falhas de prova). No lugar de "não estimar; oferecer encaminhar à equipe" (6.B) e de "oferecer conectar com a equipe" (6.C):
   > não informar valor nenhum. Dizer que a equipe confirma e perguntar se pode encaminhar. Só se o paciente aceitar, seguir a Seção 2.4A. Não executar `kanban_move_card` para fila humana nem `handoff_to_human` antes da resposta do paciente, nem fora do horário comercial.
   Na 6.A, que já tem "Se o paciente aceitar", somar a mesma última frase. Mata C08-2, C10-1 e C10-2.

2. **Prompt, Seção 10 (fora do horário)**, logo depois da linha da etiqueta `fora-horario`:
   > Fora do horário, a mensagem de prazo só vai junto com a escalada que o fluxo já mandava fazer. Ela nunca antecipa uma escalada: se o fluxo ainda está coletando (nome, CPF) ou esperando um sim, terminar a coleta ou esperar a resposta antes.
   Mata a C13-1 R2 e protege a C10-1.

3. **Fonte do prompt** (`ana/prompt/`): trocar `assign_label` por `set_labels` nas 16 ocorrências e recompilar, para a fonte voltar a bater com o prompt vivo. Sem mudar o texto, é só alinhamento. Hoje qualquer publicação a partir da fonte reverteria o nome.

4. **Runner** (`ana/bancada/e2e.py`): pôr `set_labels` em `TOOLS_DE_ESCRITURACAO` (manter `assign_label` para ler baterias antigas) e, no `Trace.por_conversa`, descartar as linhas de log com `detail.phase` (as de etiqueta e de atributo recusado), que não são chamadas. Mata o falso vermelho do C14-1 e os alertas falsos de repetição.

5. **Runner, falso verde em turno sem texto**: quando o turno tem `espere` e a Ana não manda nada, marcar a conferência "resposta" como falha (ou ao menos alerta). Hoje passam calados o C21-1 R2 (`skip_reply` sem resposta no primeiro turno da ouvidoria) e o C29-1 nas três rodadas (despedida que não sai).

6. **C29-1 e o funil**: decidir se a despedida deve sair antes do card ganho. Caminhos: a Ana manda a despedida e só depois move o card, se o prompt da Seção 11 puder ditar a ordem; ou o card final deixa de resolver a conversa sozinho no Chatwoot. Precisa de teste antes de escolher.

7. **Contatos de teste**: o runner limpar `cpf` e `nome_completo` do contato antes de cada cenário (ou usar um contato novo por rodada), para a memória da rodada anterior não contaminar a seguinte (C14-1 R2).

8. **Fora do prompt, para registro**: `consultar_convenios_agenda` não respondeu em 30 s em nenhuma das 12 chamadas. Toda a cadeia de horários ficou sem prova nesta bateria. Antes da próxima bateria vale um `smoke-gh.py` e, se a GH seguir lenta, rodar os cenários de agenda (C09, C13, C14, C16, C20) à parte quando ela voltar.

## Riscos para os cenários que passam

- Mudanças 1 e 2: C05-1, C05-3, C06-2, C06-3 e C08-1 (tabela com valor) não mudam. C10-3 e C09-2 passam a depender de a Ana esperar o sim, que é o que já fazem. Risco: fora do horário, um paciente que pede humano direto (C01-1 urgência, C16-1) precisa continuar escalando na hora; a frase vale só para a oferta de encaminhar, e a urgência já é exceção escrita no prompt (Regras 9, 10 e 11).
- Mudança 3: nenhuma mudança de comportamento, porque o prompt vivo já usa `set_labels`. Risco nulo, desde que a publicação confira o hash.
- Mudanças 4 e 5 (runner): o placar das baterias antigas pode mudar se forem reprocessadas; a 5 pode virar vermelho no C29-1 e no C21-1, que é o certo. Rodar uma bateria limpa depois.
- Mudança 7: cenários que dependem de cadastro já existente (nenhum hoje) passariam a pedir nome e CPF sempre.
- Risco geral: o prompt vivo tem 63.657 chars. As frases 1 e 2 somam umas 400; vale juntar com a compressão da #25.
