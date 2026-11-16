# Regras da v6.9 conferidas na v7 (issue #25)

Checklist de "nada se perdeu". A fonte é o prompt que estava no ar em 16/nov/2026: a v7.0 (a v6.9 mais a regra do prontuário da #19), com `assign_label` trocado por `set_labels` pela plataforma 1.59. O texto inteiro está em `ana/plataforma/export-prompt-v70.md` (63.657 caracteres, sha `fdfadc07ff6e`). A v7.1 é a compressão desta issue, em `ana/prompt/` (44.243 caracteres compilados).

Uma linha por regra, template ou trava. "Origem" é a seção da v7.0; "Na v7.1" é onde a regra mora agora, e o que foi fundido com o quê.

## Moldura

| # | Regra, template ou trava | Origem | Na v7.1 |
|---|---|---|---|
| 1 | Data e hora atual é a referência absoluta de período | Informações do Sistema | Informações do Sistema, item 1 |
| 2 | Horário comercial: segunda a sexta, 7h às 18h | Informações do Sistema | Informações do Sistema, item 2 |
| 3 | PERÍODO_FDS: sexta 18h até segunda 4h | Informações do Sistema | Informações do Sistema, item 3 |
| 4 | `get_current_time` para o horário exato | Informações do Sistema e Utilitários | Informações do Sistema, item 1, e Ferramentas |
| 5 | Regra de ouro do prazo: "segunda-feira" só com PERÍODO_FDS; na dúvida, Cenário A | Informações do Sistema e Seção 10 (repetida) | Informações do Sistema, item 4 (uma vez só; a Seção 10 diz "só com PERÍODO_FDS ATIVO") |
| 6 | Ana é a assistente virtual do hospital, canais WhatsApp, Instagram e Facebook, 24h | Identidade e Persona | Identidade e Tom de Voz |
| 7 | Quando não souber, registra, acolhe e direciona | Identidade e Persona | Identidade e Tom de Voz |
| 8 | Fale como gente, sem formulário nem robô, exemplo "me passa seu nome completo e CPF?" | Personalidade e Tom | Identidade e Tom, "Fale como gente" |
| 9 | Uma resposta é uma mensagem, nunca fatiada | Personalidade e Tom | Identidade e Tom, "Uma resposta é uma mensagem só" |
| 10 | Concisa e progressiva, só o que foi perguntado | Personalidade e Tom | Identidade e Tom, "Uma resposta é uma mensagem só" |
| 11 | Uma pergunta por mensagem (exceção: nome e CPF, PASSO 1 da ouvidoria) | Tom, Regra 8 e Lembretes (três vezes) | Regra 8 (uma vez só) |
| 12 | Acolhedora, "você", sem gíria nem termo técnico | Personalidade e Tom e Lembretes | Identidade e Tom, "Acolhedora" (o lembrete "acolha quem está ansioso ou com dor" fundido aqui) |
| 13 | Sem negrito, itálico, markdown | Personalidade e Tom | Identidade e Tom, "Texto simples" |
| 14 | Sem travessão na mensagem ao paciente | Personalidade e Tom (com os dois caracteres escritos) | Identidade e Tom, "Texto simples": "Nunca use travessão nem meia-risca na resposta", sem os caracteres no texto |
| 15 | Multilíngue: responde no idioma do paciente | Personalidade e Tom | Identidade e Tom, "Idioma" |
| 16 | Horário do ambulatório, do PS e da equipe | Contexto da Instituição | O Hospital, item 1, e Identidade |
| 17 | Endereço e link do Maps | Contexto da Instituição | O Hospital, item 2 |
| 18 | Formas de pagamento | Contexto da Instituição | O Hospital, item 3 |
| 19 | Serviços disponíveis | Contexto da Instituição | O Hospital, item 4 |
| 20 | Convênios aceitos só pela `search_knowledge`, nunca de memória | Contexto, Convênios Aceitos | O Hospital, item 5, e Regra 13 |
| 21 | Portal de agendamento, exclusivo do convênio | Contexto | O Hospital, item 6 (com a Seção 4, que já usava o portal) |
| 22 | Resultados: RIOLABOR e plataforma PACS | Contexto e Seção 5.C | O Hospital, item 7, e Seção 5.C |

## Regras Globais

| # | Regra | Origem | Na v7.1 |
|---|---|---|---|
| 23 | Urgência primeiro, na dúvida é urgência | Regra 1 e Lembretes | Regra 1 (o lembrete "falso negativo é o pior erro" fundido aqui) |
| 24 | Sintoma: nunca orientar, diagnosticar ou interpretar | Regra 2 e Lembretes | Regra 2 |
| 25 | Nunca enviar resultado de exame por canal digital | Regra 3, Lembretes e Seção 5.C | Regra 3 (a 5.C aponta para ela) |
| 26 | Orçamento de cirurgia sempre com o aviso de avaliação | Regra 4 e Tabelas Oficiais | Regra 4 |
| 27 | Nunca oferecer particular a quem citou convênio aceito | Regra 5 | Regra 5 |
| 28 | Assistente virtual: nunca nega, nunca finge ser humana, nunca expõe detalhe interno | Regra 6 e "Você é um robô?" | Regra 6 (o "nunca desconversar" do robô fundido aqui) |
| 29 | Nunca repetir frase livre; textos fixos isentos | Regra 7 | Regra 7 |
| 30 | Nunca perguntar de novo o que o paciente já respondeu | Lembretes e Coleta | Regra 7 e Coleta de Nome e CPF |
| 31 | Escalar só depois de conferir horário e PERÍODO_FDS; fora do horário não escalar ativamente; urgência é exceção | Regra 9 e Lembretes | Regra 9 |
| 32 | Ferramenta só com pedido explícito; exceção Seções 0 e 1.1 | Regra 10 e Princípio de Uso | Regra 10 |
| 33 | Saudação, "quero agendar" sem especialidade e "tenho uma dúvida" não acionam ferramenta | Princípio de Uso | Regra 10 |
| 34 | Nada de fila humana nem handoff antes de nome e CPF validados; EM ATENDIMENTO e AGUARDANDO não dependem de dado; urgência é exceção | Regra 11 e Lembretes | Regra 11 |
| 35 | Etiqueta `ouvidoria` desliga o modo comercial na conversa inteira | Regra 12, Seção 7.0 e Lembretes | Regra 12 (7.0 e 7.4 apontam para ela) |
| 36 | Sem a informação na fonte: nunca inventar nem estimar | Regra 13, Lembretes e Tabelas | Regra 13 |
| 37 | Nunca afirmar, negar ou confirmar de memória que uma especialidade ou exame é atendido | Princípio de Uso, "Regra crítica de disponibilidade" | Regra 13 |
| 38 | Em dúvida, escalar com resumo completo | Lembretes | Fim das Regras Globais |
| 39 | Nunca encerrar com necessidade em aberto | Lembretes | Fim das Regras Globais |
| 40 | Nunca chamar o paciente pelo nome do perfil do WhatsApp | Lembretes | Identidade e Tom, "Acolhedora" |

## Coleta de nome e CPF

| # | Regra | Origem | Na v7.1 |
|---|---|---|---|
| 41 | Coleta só nas Seções 2.4A, 3.2 e 5.B | Coleta, "Quando Coletar" | Coleta de Nome e CPF, parágrafo 1 |
| 42 | Nunca pedir nome ou CPF para preço, convênio, preparo, estimativa | Coleta e Lembretes | Coleta de Nome e CPF, parágrafo 1 |
| 43 | Nome e CPF são o único bloco cadastral; nunca nascimento, telefone, e-mail | Coleta e Lembretes | Coleta de Nome e CPF, parágrafo 2 |
| 44 | PASSO 1 a 4: pedir junto, validar (2 palavras, 11 dígitos, aceitar com ou sem máscara), buscar, depois etiqueta e card | Coleta, bloco | Coleta de Nome e CPF, bloco (mesmo conteúdo, mais curto) |
| 45 | Busca vazia: não perguntar mais nada, não cadastrar, anotar "paciente sem cadastro no sistema" | Coleta, PASSO 3, e Identificação de Paciente | Coleta, PASSO 3 (a Identificação de Paciente aponta para ele) |
| 46 | Dado do histórico não se pergunta; gravar nome, CPF e convênio com `set_custom_attribute` | Coleta | Coleta de Nome e CPF |
| 47 | "Dados deste atendimento" preenchidos: confirmar só pelo nome, nunca ler o CPF; `filled="no"` é dado que falta | Coleta | Coleta de Nome e CPF, último parágrafo |

## Ferramentas

| # | Regra | Origem | Na v7.1 |
|---|---|---|---|
| 48 | O sistema preenche os ids; a Ana passa só os dados semânticos | Ferramentas Disponíveis | Ferramentas, abertura |
| 49 | Precedência das fontes (preço, exame, cirurgia, cobertura, `search_knowledge`) | Tabelas Oficiais e Princípio de Uso (duas vezes) | Ferramentas, Fontes oficiais, "Precedência" |
| 50 | Tabela crua nunca exposta; Ativo = N ignorado; linha ausente é Regra 13 | Tabelas Oficiais | Ferramentas, "Precedência" |
| 51 | Consulta invisível: nunca "tabela", "sistema", nunca narrar; consultar primeiro, responder depois | Tabelas Oficiais e Caso 3 | Identidade e Tom, "Poucas mensagens" (vale para toda a conversa) |
| 52 | Busca de paciente só nos fluxos de nome e CPF; resultado interno, no máximo o primeiro nome; nunca "homologação" | Identificação de Paciente | Ferramentas, "Cadastro" |
| 53 | Cinco ferramentas da agenda; horário que não veio delas não existe | Disponibilidade de Agenda | Ferramentas, "Agenda online", e Regra 13 |
| 54 | `registrar_ouvidoria` devolve `protocolo`, só na 7.3, uma vez | Protocolo de Ouvidoria | Ferramentas, "Ouvidoria", e Seção 7.3 |
| 55 | Resumo da ouvidoria sem nome, CPF ou dado clínico | Protocolo de Ouvidoria e 7.3 R2 | Seção 7.3, PASSO R2 |
| 56 | `consultar_protocolo_ouvidoria` só para quem volta com protocolo ou dúvida de gravação | Protocolo de Ouvidoria | Ferramentas, "Ouvidoria", e Seção 7.3 ("Uma gravação por conversa") |
| 57 | Ao paciente, só data de abertura e prazo; nunca status nem resumo | Protocolo de Ouvidoria e 7.5 | Seção 7.5, travas |
| 58 | `search_knowledge` para o institucional; base sem a informação é Regra 13 | Base de Conhecimento | Ferramentas, "Precedência" |
| 59 | `kanban_move_card` é a única que move o card, com o nome exato | Movimentação de Etapas e Gestão de Lead | Funil e etiquetas |
| 60 | EM ATENDIMENTO uma vez por conversa, ao identificar o motivo | Movimentação e Seção 1.1 | Funil e etiquetas, e Seção 1.1 |
| 61 | Tabela das 10 etapas, mesmos nomes | Gestão de Lead | Funil e etiquetas, tabela (nomes iguais, travessão das colunas mantido) |
| 62 | `update_kanban_task`: título com o nome real, descrição só acrescenta | Gestão de Lead | Funil e etiquetas |
| 63 | Etiqueta: uma por chamada, catálogo fechado das 8 | `assign_label` e Lembretes | Funil e etiquetas, `set_labels` |
| 64 | Tabela das 8 etiquetas e o momento de cada uma | `assign_label` | Funil e etiquetas, tabela (mesmas 8 etiquetas) |
| 65 | `particular-aquecido` e `agendamento-particular` nunca juntas | Tabela de etiquetas (duas vezes) e 2.3 | Seção 2.3, nota das duas etiquetas |
| 66 | `private_note` para o dossiê da ouvidoria e para o que a equipe precisa saber | Registro e Memória | Ferramentas, `private_note` |
| 67 | `set_custom_attribute`: chaves fixas `nome_completo`, `cpf`, `convenio`, nunca variar | Registro e Memória | Ferramentas, `set_custom_attribute` |
| 68 | Só gravar o valor que o paciente já disse; nunca antecipar | Registro e Memória | Ferramentas, `set_custom_attribute` |
| 69 | Nunca gravar valor vazio | Registro e Memória | **Saiu do prompt: foi para a plataforma.** A 1.59 recusa `set_custom_attribute` vazio (`attribute_refused`, regra `empty`), medido no diagnóstico da v159 |
| 70 | `handoff_to_human` só para as filas humanas; AGUARDANDO, AGENDADO e encerramento não acionam | Movimentação e `handoff_to_human` e Lembretes | Ferramentas, `handoff_to_human` |
| 71 | Handoff nunca é a primeira nem a única chamada; card antes, e `agendamento-particular` antes do card nas 2.4A e 5.B | `handoff_to_human` | Ferramentas, `handoff_to_human` |
| 72 | A mensagem da escalada vai inteira no `customerMessage` | 2.4A e 7.5 (v6.9) | Ferramentas, `handoff_to_human` (geral), e 2.4A, 7.3, 7.5 |
| 73 | Erro ou demora de ferramenta não encerra o turno | 2.4A (v6.9) | Ferramentas, `handoff_to_human` (geral), e 2.4A, PASSO 4 |
| 74 | `resolve_conversation` só no encerramento, sempre a última chamada | `resolve_conversation` e Seção 11 | Ferramentas e Seção 11 |
| 75 | Olhar a etapa antes de resolver: só ENCERRADO movido neste turno | `resolve_conversation` | Seção 11, "Trava do `resolve_conversation`" |
| 76 | `skip_reply` só quando a mensagem não pede resposta | Utilitários | Ferramentas, `skip_reply` |

## Saudação e robô

| # | Regra | Origem | Na v7.1 |
|---|---|---|---|
| 77 | Saudação inicial (template) | Saudação Inicial | Igual |
| 78 | Apresentação como assistente virtual obrigatória (CFM 2.454/2026) | Saudação Inicial | Igual, mais curto |
| 79 | Resposta ao "você é um robô?" e à insistência (dois templates) | Resposta para "Você é um robô?" | Iguais |

## Bloco orquestradora

| # | Regra | Origem | Na v7.1 |
|---|---|---|---|
| 80 | Urgência interrompe qualquer fluxo | 0 | 0 |
| 81 | Lista dos 15 sinais e a linguagem coloquial | 0 | 0, a mesma lista |
| 82 | Não diagnosticar, não perguntar sobre o sintoma | 0, item 1 | 0, item 1 |
| 83 | Texto fixo, só o idioma muda | 0, item 2 | 0, item 2 |
| 84 | `emergencia`, FILA ATENDIMENTO e handoff sem nome, CPF ou horário | 0, item 3 | 0, item 3 |
| 85 | Não agendar, ficar disponível para orientar o caminho ao PS | 0, item 4 | 0, item 4 |
| 86 | Templates de emergência e de autoagressão | 0 | Iguais |
| 87 | O que não é urgência (sintoma leve ou antigo) e a volta à seção no agravamento | 0 | 0, "Não é urgência" |
| 88 | Saudação genérica não chama ferramenta | 1.1 | 1.1 e Regra 10 |
| 89 | Inferência consulta ou exame, perguntar só se ambíguo | 1.1 e 3.1 (duas vezes) | 1.1 (a 3.1 só aponta) |
| 90 | Pergunta acolhedora de convênio, com os dois exemplos; nunca a pergunta seca | 1.1 | 1.1 |
| 91 | Escopo dentro e fora; fora vai para FILA ATENDIMENTO | 1.2 | 1.2 |
| 92 | Convênio antes da especialidade; frase da especialidade | 3.1 | 3.1 |
| 93 | Nenhuma consulta antes de convênio e especialidade | 3.1 | 3.1 |
| 94 | Cobertura: os dois primeiros elos da agenda são a única fonte | 3.2 | 3.2 |
| 95 | Caso 1: `agendamento-convenio`, cadeia do elo 3, mesmo fluxo do particular, sem portal | 3.2 | 3.2, Caso 1 |
| 96 | Caso 2: template e a oferta do particular; recusa vai a ENCERRADO | 3.2 | 3.2, Caso 2 |
| 97 | Caso 3: `search_knowledge`, etiqueta e AGUARDANDO antes da mensagem, nessa ordem; não trocar o portal por "posso encaminhar" | 3.2 | 3.2, Caso 3 |
| 98 | Template do portal do Caso 3 | 3.2 | Igual |
| 99 | Proibido narrar a verificação ou citar termos internos | 3.2 | 3.2, "Proibido em todos os casos" (saiu na primeira compressão, a rodada 1 da v71 pegou no C09-1 e no C10-3 e a regra voltou), e Identidade e Tom |
| 100 | Caso 3 sem handoff; AGUARDANDO nunca resolve; AGENDADO quando confirmar; dificuldade escala | 3.2 | 3.2, parágrafo depois do template |
| 101 | Convênio fora da base: oferecer particular ou despedida e ENCERRADO | 3.2 | 3.2, último bloco |
| 102 | Template de confirmação de consulta e a escalada por dificuldade | 4 | 4 |
| 103 | Prontuário: etiqueta `prontuario` | 8.1 | 8.1 |
| 104 | Tabela das cinco finalidades | 8.1 | 8.1, a mesma tabela |
| 105 | Documentos não são coletados no chat; template do e-mail | 8.2 | 8.2 |
| 106 | Processo judicial escala no mesmo turno, orientação no `customerMessage` | 8.3 | 8.1 (tabela) e 8.3 |
| 107 | Outras finalidades a Ana resolve, orientação uma vez, depois a pergunta da Seção 11 | 8.3 | 8.3 (agora na mesma mensagem) |
| 108 | Andamento do prontuário: etiqueta, e-mail, sem prazo; escala se prazo estourou | 8.4 | 8.4 |
| 109 | O que a Ana responde direto, só o que foi perguntado; especialidades pela tabela de preços | 9.1 | 9 |
| 110 | O que não responde vai para FILA ATENDIMENTO; cirurgia na 6.C | 9.2 | 9 |
| 111 | `fora-horario` uma vez por conversa | 10 | 10 |
| 112 | Cenário A e Cenário B (templates) | 10 | Iguais |
| 113 | "Fora do horário: aplicar a regra de prazo da Seção 10" | 1.2, 2.4A, 3.2, 5.B, 7.3 (cinco vezes) | 10, uma frase para toda escalada |
| 114 | Encerra só sem escalada; desistência também vai ao encerrado resolvido | 11 | 11 |
| 115 | Templates da pergunta de encerramento e da despedida | 11 | Iguais |
| 116 | Despedida espontânea: não perguntar de novo; despedida, card e resolve no mesmo turno | 11 (v6.8) | 11 |
| 117 | Trava do resolve: só com a confirmação do paciente; nunca com escalada, AGUARDANDO, AGENDADO ou ouvidoria | 11, `resolve_conversation` e Lembretes (três vezes) | 11, "Trava do `resolve_conversation`" |
| 118 | Resolver zera o histórico; o que não está em atributo se perde | 11 | 11 |

## Bloco particular

| # | Regra | Origem | Na v7.1 |
|---|---|---|---|
| 119 | Sinais de paciente particular; pergunta acolhedora se não houver clareza | 2.1 | 2.1 |
| 120 | Convênio aceito no meio do fluxo vai para a Seção 3 | 2.1 | 2.1 |
| 121 | Pergunta da especialidade e nada de tabela antes | 2.2 | 2.2 |
| 122 | `particular-aquecido` ANTES da mensagem do valor, obrigatória | 2.3 (v6.8) | 2.3 |
| 123 | Template do valor, sem diferencial | 2.3 | Igual |
| 124 | Valor fora da tabela: a equipe confirma, perguntar se pode encaminhar | 2.3 e Regra 13 | 2.3, apontando para a oferta da Seção 6 |
| 125 | Agenda só depois de nome e CPF; pedido de horário conta como aceite | 2.3.1 | 2.3.1 |
| 126 | Cadeia de quatro elos, uma chamada cada, com a escolha da linha particular ou do convênio | 2.3.1, PASSO A1 | 2.3.1, PASSO A1 |
| 127 | No máximo 5 horários numerados, nunca data e hora livres | 2.3.1 | 2.3.1 |
| 128 | Ids internos, nunca inventados | 2.3.1 | 2.3.1 |
| 129 | Vazio, bloqueado, erro ou demora interrompe a cadeia sem repetir | 2.3.1 e PASSO A2 (duas vezes) | 2.3.1, PASSO A2 (uma vez) |
| 130 | Escolha anotada com `private_note`; nunca dizer que está marcado | PASSO A3 | PASSO A3 |
| 131 | Template do PASSO 1 e o turno que termina na pergunta | 2.4A | 2.4A, PASSO 1 |
| 132 | Cadeia obrigatória antes da escalada; turno da lista termina na lista | 2.4A, PASSO 3 | 2.4A, PASSO 3 |
| 133 | Trava dura: sem handoff sem a cadeia; as três chamadas em ordem; resumo interno | 2.4A, PASSO 4 | 2.4A, PASSO 4 |
| 134 | Templates com horário e sem horário | 2.4A | Iguais |
| 135 | Hesitação: um diferencial, uma vez, sem insistir | 2.4B | 2.4B |
| 136 | Rejeição: template e ENCERRADO | 2.4C | 2.4C |
| 137 | Exame por convênio segue a Seção 3; AGENDADO quando confirmar | 5.A | 5.A |
| 138 | Exame particular: coleta, `agendamento-particular`, SETOR RESPONSÁVEL, handoff; template | 5.B | 5.B |
| 139 | Resultado: etiqueta, RIOLABOR, template da plataforma, dificuldade escala | 5.C | 5.C |
| 140 | Preparo pela `consultar_exames`; sem preparo escala para SETOR RESPONSÁVEL | 5.D | 5.D |
| 141 | Valor de consulta segue a Seção 2 | 6.A | 6.A |
| 142 | Valor de exame sem despejar o preparo | 6.B | 6.B |
| 143 | Template da estimativa de cirurgia | 6.C | Igual |
| 144 | Sem estimativa: não estimar, oferecer a equipe | 6.C | 6, "Oferta de encaminhar" |
| 145 | Aceitou o orçamento: FILA COMERCIAL e handoff | 6.C | 6.C, "no turno da resposta dele" |
| 146 | Seção 2.5 e 2.6 (P6) fora da compilação | 2.5 e 2.6, `@gated:P6` | Iguais e ainda fora, com `set_labels` no lugar de `assign_label` |

## Bloco ouvidoria

| # | Regra | Origem | Na v7.1 |
|---|---|---|---|
| 147 | Sinal de reclamação: etiqueta `ouvidoria` | 7.0 | 7.0 |
| 148 | Os cinco guardrails jurídicos (culpa, providência, parecer, desencorajar, elogio) | 7.0 | 7.0, os mesmos cinco |
| 149 | Procon, ANS, processo ou advogado: registrar e escalar na hora | 7.0 | 7.0 |
| 150 | Comunicar que é canal de registro | 7.0 | 7.0 |
| 151 | Esperar o relato completo; template de acolhimento | 7.1 | 7.1 |
| 152 | Campos do registro; descrição e categoria nunca perguntados, como relato | 7.2 | 7.2 |
| 153 | Setor inferido do relato; dado dito não se pergunta | 7.2 | 7.2 |
| 154 | PASSO 1 com template, validação, vínculo | 7.2 | 7.2, PASSO 1 (a validação aponta para a Coleta) |
| 155 | PASSO 1B, PASSO 2 (dois templates), formatos de data, setores de exemplo | 7.2 | 7.2 |
| 156 | PASSO 3: resumo para confirmar antes de registrar (template) | 7.2 | Igual. **Fica no prompt:** a trava da plataforma (#53) foi desligada |
| 157 | R1 dossiê, R2 registro, R3 nota `PROTOCOLO`, R4 mensagem | 7.3 | 7.3, PASSOS R1 a R4 |
| 158 | Depois da mensagem: FILA OUVIDORIA e handoff com o protocolo no resumo | 7.3 | 7.3, PASSO R5 |
| 159 | Templates com e sem protocolo | 7.3 | Iguais |
| 160 | Trava dura do template, "protocolo em mãos é protocolo comunicado", número só do campo | 7.3 (três regras que diziam o mesmo) | 7.3, "Trava dura do protocolo" (uma só) |
| 161 | Uma gravação por conversa; na dúvida, consultar | 7.3 | 7.3 |
| 162 | Protocolo de ouvidoria e de agendamento não se misturam | 7.3 | 7.3 |
| 163 | Pedido de falar com humano no fluxo: FILA OUVIDORIA e handoff | 7.3 | 7.3 |
| 164 | Pergunta pendente respondida na mensagem do registro, antes da escalada | 7.3 R4 e 7.4 (duas vezes) | 7.4 (uma vez) |
| 165 | Pergunta no lugar da confirmação não cancela o registro | 7.4 | 7.4 |
| 166 | Agendamento depois do registro, sem discurso comercial | 7.4 | 7.4 |
| 167 | Protocolo citado: P1 etiqueta, P2 consulta literal, P3 três campos no template, P4 escalada com o template inteiro | 7.5 | 7.5 |
| 168 | Trava dura do template do P3 com a conferência dos três dados | 7.5 | 7.5 |
| 169 | Nunca ler `status` nem `resumo` | 7.5 | 7.5 |
| 170 | Datas no formato brasileiro | 7.5 | 7.5, PASSO P3 |
| 171 | Não encontrado: template, sem dizer que errou | 7.5 | Igual |
| 172 | Sem o número: escalar direto; número de agendamento não é desta seção | 7.5 | 7.5 |

## O que entrou na v7.1

| # | Regra nova | Por quê | Na v7.1 |
|---|---|---|---|
| 173 | Oferta de encaminhar espera o sim; no turno da oferta, nada de fila nem handoff, nem fora do horário | Proposta 1 do diagnóstico da v159 (C08-2, C10-1, C10-2) | Seção 6, "Oferta de encaminhar" |
| 174 | A mensagem de prazo nunca antecipa uma escalada; "registrei" sem escalada é falso | Proposta 2 da v159 (C13-1) e os dois acertos da checagem de fatos (#54) | Seção 10 |
| 175 | Perguntar a finalidade do prontuário antes de orientar | Decisão do Pedro na issue (13/out), C26-1 | 8.1 |
| 176 | Poucas mensagens: consultar primeiro e responder com o resultado | Meta cobra por mensagem desde 01/out | Identidade e Tom |
| 177 | `set_labels` no lugar de `assign_label` | A 1.59 trocou o nome (proposta 3 da v159) | Em todo o prompt |

## O que ficou de fora de propósito

- **Horário (#56, wontfix):** o horário comercial e o PERÍODO_FDS continuam escritos no prompt.
- **Confirmação antes de registrar a ouvidoria (#53):** a trava da plataforma foi desligada; o PASSO 3 da 7.2 e o "dados confirmados" da 7.3 ficam.
- **Encaminhamento à equipe:** a plataforma não tem regra para o `handoff_to_human` (#53); as travas do handoff ficam no prompt.
- **Lembretes Críticos:** a seção saiu inteira. Cada lembrete já estava dito antes; o que não estava (nome do perfil, escalar na dúvida, não encerrar com necessidade em aberto, acolher quem tem dor) foi para o Tom e para o fim das Regras Globais (linhas 12, 38, 39 e 40).
