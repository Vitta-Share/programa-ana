# Diagnóstico da bateria v71 (16/nov/2026)

Bateria `v71`: três rodadas de `cenarios/capacidades.json` (29 cenários) com o prompt v7.1, a v7.0 comprimida da issue #25 (PRD #30). Plataforma fazer.ai agents 1.59.0, `gpt-6-luna`, checagem de fatos ligada em só registrar (#54), trava da ouvidoria desligada (#53). De 07:21Z a 08:51Z de 16/nov (segunda, 4h21 a 5h51 no horário de Brasília, fora do horário comercial nas três). Só homologação da Global Health e API do Hospital; sem `--com-escrita`, então nenhuma linha foi gravada no painel da ouvidoria.

## Resumo

Placar: **28/29, 29/29 e 29/29**, contra 26, 27 e 27 da v159 (`diagnostico-bateria-2026-11-16-v159.md`, mesmo prompt de conteúdo da v7.0 na mesma plataforma) e 28, 28 e 27 da v6.9. Nenhuma falha constante. A única falha é o C10-2 da rodada 1, a mesma das baterias anteriores (pergunta "posso encaminhar?" e escala no mesmo turno), agora uma vez em três em vez de duas. Custo da OpenAI por conversa caiu de US$ 0,0060 para **US$ 0,0034** (menos 43%); mensagens da Ana por conversa ficaram iguais (1,24).

Antes desta bateria rodou uma tentativa (`v71a`, 06:48Z a 07:20Z) com a primeira compressão: **27/29**. As duas falhas (C09-1 e C10-3) foram a mesma: no Caso 3 da Seção 3.2 a Ana parafraseou o modelo do portal com "não consegui confirmar a cobertura" e "pela agenda online". A primeira compressão tinha levado a proibição de narrar a verificação para a regra geral de tom. A regra voltou para dentro da 3.2, a v7.1 foi publicada de novo (sha `7f8fbf5dfd34`) e a bateria rodou do zero.

## Carimbo

| Momento | Prompt vivo | Tamanho | sha |
|---|---|---|---|
| Antes de tudo (export) | v7.0 com `set_labels` | 63.657 | `fdfadc07ff6e` |
| Tentativa v71a | primeira compressão | 43.907 | `43852814aca1` |
| Bateria v71, R1 a R3 | v7.1 | 44.243 | `7f8fbf5dfd34` |

Conferido depois da rodada 2: o prompt vivo seguia o `7f8fbf5dfd34`, `updatedAt` 07:21:13Z (a publicação desta sessão). Nenhum `e2e.py` de outra sessão rodou nas janelas.

## Tabela

| Cenário | v159 R1 R2 R3 | v71 R1 | R2 | R3 | Classe | Causa em uma linha |
|---|---|---|---|---|---|---|
| C10-2 Item fora da tabela | falhou ok falhou | falhou | ok | ok | intermitente (melhorou de 2 para 1 em 3) | Ana: "Posso encaminhar?" e `handoff_to_human` no mesmo turno, puxado pelo fora do horário. |
| C08-2 Estimativa de cirurgia | falhou ok falhou | ok | ok | ok | melhorou | A oferta da Seção 6 espera o sim. |
| C10-1 Item fora da tabela | ok falhou ok | ok | ok | ok | melhorou | Idem. |
| C13-1 Achar o cadastro | ok falhou ok | ok | ok | ok | melhorou | A mensagem de prazo não antecipa mais a escalada (Seção 10). |
| C14-1 Horários reais | falhou (runner) ok ok | ok | ok | ok | passa | |
| Outros 24 cenários | ok ok ok | ok | ok | ok | passa | |

Por tipo de falha: **Ana 1** (C10-2 R1), runner 0, cenário 0, infra 0. Falha por Global Health lenta: **0**.

## Evidências

### C10-2, rodada 1 (bateria v71)

- Turno 1, paciente: "quanto custa a ressonância magnética?"
- Veio: "Não encontrei o valor da ressonância magnética na tabela oficial. Posso encaminhar sua solicitação à equipe para confirmar o valor e a disponibilidade?"
- Esperado: a oferta, sem handoff.
- Ferramentas: `consultar_exames`, `kanban_move_card`, `get_current_time`, `set_labels` (`fora-horario`), `handoff_to_human`.
- Leitura: a oferta saiu certa, mas o modelo conferiu o horário, aplicou o `fora-horario` e escalou junto, contra a regra nova da Seção 6 ("no turno da oferta, nenhum `handoff_to_human`, nem fora do horário comercial"). Caiu de duas em três (v159) para uma em três. "Tabela oficial" na frase também é termo interno.

### C09-1 e C10-3, tentativa v71a (corrigido antes da bateria)

- C09-1, paciente: "meu convênio é a Unimed, vocês cobrem cardiologia?" Veio: "A Unimed é aceita no hospital, mas não consegui confirmar a cobertura de cardiologia agora. Você já pode tentar agendar pelo portal..." Ferramentas: `consultar_especialidades_agenda`, `consultar_convenios_agenda`, `search_knowledge`, `set_labels`, `kanban_move_card`.
- C10-3, paciente: "meu plano é a Porto Seguro Saúde, vocês cobrem dermatologia?" Veio: "...mas não consegui confirmar a cobertura de dermatologia pela agenda online. Você pode tentar agendar pelo portal..."
- Esperado: o modelo do Caso 3 sem narrar a verificação. As chamadas estavam certas; só a frase falhou.
- Leitura: a regra "Proibido em todos os casos: narrar a verificação ou citar termos internos" saiu da 3.2 na compressão. Voltou, com "não consegui confirmar" e "agenda online" na lista.

## Custo e mensagens

Média das 87 conversas da bateria (o C22-1 não roda sem `--com-escrita`; a cópia dele na pasta é antiga e ficou de fora). A referência da v7.0 é a bateria `v159-checagem` da #54, na mesma plataforma, com a mesma checagem de fatos ligada (`ana/plataforma/checagem-fatos.md`).

| Medida | v7.0 | v7.1 |
|---|---|---|
| Caracteres do prompt | 63.657 | 44.243 (menos 30%) |
| Tokens do prompt (estimativa, uns 3,7 caracteres por token) | uns 17 mil | uns 12 mil |
| Placar (três rodadas) | 26, 27, 27 | 28, 29, 29 |
| OpenAI por conversa | US$ 0,0060 | US$ 0,0034 |
| Mensagens da Ana por conversa | 1,2 | 1,24 |
| Meta por conversa | R$ 0,042 | R$ 0,043 |

Por cenário, a contagem de mensagens da Ana é igual à da v70 em todos, menos o C29-1 (a despedida não sai, efeito do card ganho da 1.59 já descrito no diagnóstico da v159). Os cenários têm de um a três turnos: o alvo de no máximo 8 mensagens numa conversa de agendamento completa não tem cenário que o meça.

## Pacote de mudanças (proposta, nada aplicado)

1. **C10-2, Seção 6 do prompt:** a regra nova reduziu a falha mas não matou. Proposta: na 6.B, trocar "Sem o valor: a oferta acima." por "Sem o valor: a oferta acima, e o turno termina na pergunta (sem `get_current_time`, `fora-horario` nem escalada)." E tirar "tabela oficial" da fala: somar "tabela" à lista de termos proibidos da Seção 6.
2. **Cenário de conversa longa:** criar um cenário de agendamento completo (preço, aceite, nome e CPF, horário, escalada) para medir o alvo de 8 mensagens da #25.

## Riscos para os cenários que passam

- A proposta 1 mexe só na 6.B. Risco: o C06-x (valor de exame com a tabela) não muda, porque a frase vale só para o caso sem valor.
- A v7.1 juntou os cinco avisos "fora do horário: aplicar a Seção 10" numa frase só na Seção 10. Nesta bateria, de madrugada, nenhum cenário de escalada perdeu o prazo; uma bateria em horário comercial ainda não rodou com a v7.1.
