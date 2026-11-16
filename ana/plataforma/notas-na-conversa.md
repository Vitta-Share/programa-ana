# Notas da Ana no Chatwoot (issue #57)

Desde 15/nov/2026 o agente 1 (Ana) escreve, em cada conversa do Chatwoot, uma nota privada com as ferramentas que chamou no turno e outra com os erros que contornou. O paciente não vê nota privada. A equipe vê, logo abaixo da resposta da Ana.

## O que foi ligado

| Onde | Valor | Versão da plataforma |
| --- | --- | --- |
| `settings.conversationNotes.toolsUsed` | `note` (nota privada) | 1.55 |
| `settings.conversationNotes.errors` | `note` (nota privada) | 1.55 |
| `settings.observability.fullDetailRetentionDays` | `14` | 1.59 |

No console: agente Ana, aba Comportamento, "Notas na conversa"; e aba Logs, "Guardar o detalhe completo de cada turno".

O formato `note` foi escolhido em vez de `activity` porque a issue pede nota privada e porque a linha de atividade, até o fork do Chatwoot mudar, sai atribuída ao contato e mexe no "última atividade" dele.

## Por que 14 dias de guarda

- Cobre duas semanas entre uma bateria da bancada e a seguinte, e o intervalo até a demo para o diretor: dá para abrir um turno estranho dias depois.
- Fica abaixo dos 30 dias em que os logs da plataforma somem (`FLOWLOG_RETENTION_DAYS`); acima disso o detalhe ficaria pendurado numa linha que não existe mais.
- É o padrão que a própria plataforma sugere, e guardar menos é o lado certo enquanto a Ana não atende paciente de verdade.

**O que a guarda pega hoje:** só o prompt auditado de cada turno. O resultado inteiro das ferramentas só é guardado quando o agente registra valores (`observability.logToolValues`), que segue desligado no agente 1, porque gravaria CPF e nome do paciente nos logs. Ligar isso é decisão à parte, antes do WhatsApp real.

## Conferência na conversa de teste

Conversa 608 da inbox de API "Ana E2E", em modo teste, com o paciente de teste da homologação (nome e CPF dele na mensagem). Trecho, com o CPF fora do texto:

```
paciente: Quero marcar uma consulta de cardiologia particular. Meu nome é <nome de teste> e meu CPF é <CPF de teste>
Ana:      Perfeito, Teste! A consulta de cardiologia é R$ 380. Nossa equipe vai entrar em contato no próximo expediente para confirmar os horários disponíveis.
nota:     Ferramentas usadas pelo agente neste turno: kanban_move_card (2x), set_custom_attribute (2x), consultar_precos_consultas, set_labels (2x), buscar_paciente_por_cpf, consultar_especialidades_agenda, consultar_convenios_agenda.
nota:     Erros neste turno do agente:
          - Ferramenta consultar_convenios_agenda: falhou (erro). Não se recuperou: o agente seguiu sem ela.
          Detalhes do turno: https://agents.hospitalsaomatheus.cloud/logs?turnId=10f1a3bb-e8a2-4f16-8fe7-c5a485f7a857&switchTenant=1
```

A varredura do script não achou CPF inteiro (com ou sem máscara) nem o nome que o paciente disse em nenhuma das duas notas. A nota de ferramentas traz só os nomes; a de erros traz o motivo numa palavra de lista fechada da plataforma e o link para os Logs, onde fica o detalhe.

A própria nota já mostrou serviço: `consultar_convenios_agenda` falhou nesse turno e a Ana seguiu sem ela.

## Como repetir

```bash
python3 ana/plataforma/scripts/notas-na-conversa.py exportar            # guarda o estado antes de mudar
python3 ana/plataforma/scripts/notas-na-conversa.py aplicar --dias 14   # para se outra sessão mudou as settings desde o export
python3 ana/plataforma/scripts/notas-na-conversa.py conferir --conversa <id> --proibido "<nome que o paciente disse>"
```

O `aplicar` manda o saco de settings inteiro (o PATCH da plataforma substitui, não mescla) com `expectedUpdatedAt`, então a plataforma recusa com 409 se outra sessão gravou o agente entre a leitura e a escrita.

## Como voltar atrás

O estado anterior está em `ana/plataforma/export-ana-pre-notas-na-conversa.json` (sem o prompt, que mora em `ana/prompt/`; vão o hash e o tamanho dele). Para desligar: no console, as duas opções de "Notas na conversa" em Desligado e a guarda do detalhe desligada. O que já foi guardado sai sozinho quando vencem os 14 dias.
