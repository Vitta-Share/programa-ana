# Checagem de fatos da Ana em modo só registrar (issue #54)

Desde 16/nov/2026 a plataforma revisa cada resposta da Ana antes de enviar: um segundo modelo compara o que ela escreveu com o que as ferramentas trouxeram e com a base de conhecimento, e anota no log o que não bate. Por enquanto ele só anota. Nenhuma resposta é bloqueada, trocada ou reescrita.

## O que foi ligado

| Onde | Valor | Versão da plataforma |
| --- | --- | --- |
| `settings.guardrails.enabled` | `true` (chave geral; a checagem não roda sem ela) | 1.57 |
| `settings.guardrails.input.enabled` e `output.enabled` | `false` (a moderação de entrada e saída vinha salva ligada e trocaria respostas pelo template) | |
| `settings.guardrails.factualGrounding.action` | `observe` ("Só registrar" no console) | 1.57 |
| `settings.guardrails.factualGrounding.sourceTools` | preço (`consultar_precos_consultas`, `consultar_cirurgias_estimativas`), exame (`consultar_exames`), agenda (`consultar_especialidades_agenda`, `consultar_prestadores_agenda`, `consultar_convenios_agenda`, `consultar_planos_convenio`, `consultar_horarios_livres`), protocolo (`registrar_ouvidoria`, `consultar_protocolo_ouvidoria`) e `search_knowledge` | 1.57 |
| `settings.guardrails.factualGrounding.referenceKnowledgeBaseIds` | `["1"]`, a Base Hospital São Matheus (5 documentos, 4.026 caracteres), lida inteira em toda revisão | 1.58 |
| revisor | `gpt-6-luna` com a chave da própria Ana (`vault:2`); os guardrails não têm chave própria | |

No console: agente Ana, aba Guardrails, seção da checagem factual.

## A bateria

Bateria `v159-checagem`: três rodadas de `cenarios/capacidades.json` (29 cenários) de 04:20Z a 05:55Z de 16/nov, plataforma 1.59.0, prompt vivo de 63.657 caracteres (o mesmo da #51), sem mudança no agente nem nas ferramentas durante as três rodadas. Só homologação da Global Health e API do Hospital.

Placar: **26/29, 27/29 e 28/29**, contra 26, 27 e 27 da bateria v159 da #51 (`ana/bancada/diagnosticos/diagnostico-bateria-2026-11-16-v159.md`). Em modo só registrar a checagem não muda nenhuma resposta, então a diferença é variação do modelo. As falhas: C02-1 nas rodadas 1 e 2 (`kanban_move_card` na saudação), C10-2 nas rodadas 1 e 2 (pergunta "posso encaminhar?" e escala no mesmo turno, a mesma falha da #51) e C26-1 nas rodadas 1 e 3 (o segundo turno não repete o e-mail do prontuário). Nenhuma falha por Global Health lenta.

## Tabela

| Medida | Bateria inteira |
| --- | --- |
| Conversas | 87 |
| Respostas da Ana | 105 |
| Respostas revisadas | 88 (as 17 que saíram junto com `handoff_to_human` não passam pela checagem: a plataforma não revisa depois de uma transferência) |
| Respostas marcadas | **36 de 88 (41%)** |
| Acertos (fato errado ou ação inventada) | **2** |
| Discutíveis | 5 |
| **Falsos alarmes** | **29 de 36 (81%)** |
| Revisões que falharam | 0 |
| Custo extra por conversa | **US$ 0,00023 (R$ 0,0013)** |
| Custo médio da conversa na mesma bateria, para comparar | OpenAI US$ 0,0060 (R$ 0,034) mais Meta R$ 0,042: a checagem é menos de 2% disso |
| Tempo a mais antes de cada resposta | mediana 3,1 s, máximo 12,5 s |
| Tokens por revisão | mediana 3.480 de entrada (2.952 em cache) e 160 de saída |

O custo vem dos tokens que a própria plataforma grava em cada linha da checagem, com os preços de `ana/bancada/precos.json`. Na mesma janela, outras duas sessões (#55 e #56) passaram 42 revisões pela inbox de teste; elas ficaram fora da conta.

### Os 2 acertos

As duas respostas dizem "Registrei sua solicitação e nosso time vai te contatar" sem nenhuma ferramenta ter registrado nada (nem `handoff_to_human`, nem fila):

- C06-3, rodada 1 (tabela de exames, com os preços certos, mais a frase de fora do horário).
- C08-2, rodada 2 (estimativa da apendicectomia certa, depois "Quer que eu encaminhe?" e "Registrei sua solicitação" na mesma mensagem).

São as duas únicas respostas da bateria com essa frase sem transferência, e a checagem pegou as duas. A bancada aprovou os dois cenários. É a mesma raiz que o diagnóstico da #51 achou (a frase de fora do horário puxada antes da hora).

### Os 5 discutíveis

- C26-1 (rodadas 1, 2 com dois turnos, e 3): o e-mail do prontuário está certo, mas a Ana diz que "a equipe vai orientar quais documentos são obrigatórios", e a base lista os documentos (nome, RG, CPF, data de nascimento e período). Não é dado errado, é a Ana deixando de dizer o que a base já diz.
- C10-2, rodada 3: "Posso encaminhar?" seguido de "vai retornar no próximo expediente", sem encaminhamento feito. Lido como promessa condicional, passa; lido ao pé da letra, promete um retorno que ninguém agendou.

### Os 29 falsos alarmes

Todos com a resposta certa pelas fontes ou pelo prompt:

| Cenário | Vezes | O que a Ana disse |
| --- | --- | --- |
| C13-1, C14-1, C16-1 | 8 | "Me passa seu nome completo e CPF? Assim já deixo tudo pronto para o agendamento." |
| C08-1, C08-2 | 5 | estimativa de cirurgia com valor, o que inclui e o aviso, iguais à API do Hospital |
| C09-1, C09-2, C10-3, C20-1 | 7 | convênio da lista da base e o portal de agendamento (Caso 3 da Seção 3.2) |
| C04-1 | 3 | "Sou a Ana, assistente virtual... a qualquer hora do dia" |
| C21-1 | 3 | acolhimento da reclamação, "vou registrar seu relato" antes de coletar |
| C02-1, C03-1, C10-1 | 3 | saudação; não vende plano de saúde; reumatologia fora da tabela (está mesmo fora) |

O padrão é um só: o revisor não lê o prompt da Ana (de propósito, pela documentação da plataforma), então tudo o que é regra da casa e só mora no prompt (como funciona o agendamento, o Caso 3 dos convênios, o que a Ana é, o fluxo da ouvidoria) sai como afirmação sem fonte. As marcações com preço e estimativa certos são o revisor lendo "incluindo honorários e internação" ou "em torno de" como algo que a ferramenta não diz com essas palavras.

## Recomendação: ajustar

Deixar a checagem ligada em Só registrar e **não** ligar o bloqueio (trocar por template, reescrever ou passar para a equipe) agora. Com 81% de falso alarme, o bloqueio mexeria em uma de cada três respostas da Ana, quase sempre certas. Os dois acertos são reais e valem o custo, que é desprezível (menos de 2% da conversa).

Antes de pensar em bloqueio:

1. Pôr na Base Hospital São Matheus um documento curto com as regras de atendimento que hoje só moram no prompt: o que a Ana é e quando atende, a coleta de nome e CPF antes da agenda, o Caso 3 dos convênios (convênio da lista vai para o portal), o acolhimento da ouvidoria. A plataforma lê a base inteira em toda revisão; é para isso que ela existe. Isso deve matar 21 dos 29 falsos alarmes.
2. Corrigir no prompt a frase de fora do horário, que é a raiz dos 2 acertos (proposta 2 do diagnóstico da #51).
3. Rodar a bateria de novo com `checagem-fatos.py medir` e só discutir bloqueio quando o falso alarme ficar abaixo de 10%.
4. Pesar os 3 segundos a mais antes de cada resposta: no WhatsApp passa, mas soma com o tempo das ferramentas.

## Como repetir

```bash
python3 ana/plataforma/scripts/checagem-fatos.py exportar   # guarda o estado antes de mudar
python3 ana/plataforma/scripts/checagem-fatos.py aplicar    # para se outra sessão mudou as settings desde o export
python3 ana/bancada/e2e.py cenarios/capacidades.json --bateria <nome> --rodada 1   # e 2, e 3
python3 ana/plataforma/scripts/checagem-fatos.py medir --bateria <nome>
```

O `aplicar` manda o saco de settings inteiro (o PATCH da plataforma substitui, não mescla) com `expectedUpdatedAt`, então a plataforma recusa com 409 se outra sessão gravou o agente entre a leitura e a escrita. O `medir` lê as linhas `check: factual_grounding` dos logs, fica só com as conversas que a bancada gravou e imprime a tabela e a lista das marcadas, para julgar uma a uma na conversa do Chatwoot.

O motivo de cada marcação (as afirmações e a evidência) só vai para o log com `observability.logToolValues` ligado, que segue desligado no agente 1 porque gravaria CPF e nome do paciente. Por isso o falso alarme foi julgado lendo a resposta e conferindo com a API do Hospital e com a base, e não pelo texto do revisor.

## Como voltar atrás

O estado anterior está em `ana/plataforma/export-ana-pre-checagem-fatos.json` (sem o prompt, que mora em `ana/prompt/`). Para desligar: no console, aba Guardrails, desligar a checagem factual e a chave geral dos guardrails. Pela API, o mesmo PATCH com `guardrails.enabled: false` e `guardrails.factualGrounding.enabled: false`.
