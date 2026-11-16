# INTEGRACOES.md
<!-- gerado por /snapshot; não editar à mão -->

Serviços externos do Programa Ana e o NOME das chaves de ambiente que o código lê
(do `.env` da raiz, fora do git). Nunca o valor. O repositório não tem `.env.example`:
as chaves saem da varredura do código (fora `tools/` e `.claude/`, que são do fluxo de trabalho).

## Global Health
**Pra que serve:** API de agendamento WhatsApp da MV. Os scripts locais chamam só a homologação; produção é proibida neste app.
**Onde aparece no código:** `ana/api-mv/scripts/mapa-gh.py`
**Secret/env primária:** `GH_TOKEN_HOMOLOG`
**Variáveis relacionadas:** `GH_MAPA_BASE`, `GH_MAPA_PRAZO`, `GH_MAPA_TIMEOUT`

## Oracle MV (base TST)
**Pra que serve:** Banco do hospital, base de teste. Só leitura (SELECT/WITH), pelo query-mv.py.
**Onde aparece no código:** `ana/api-mv/scripts/query-mv.py`
**Secret/env primária:** `ORACLE_PASSWORD`
**Variáveis relacionadas:** `ORACLE_CLIENT_DIR`, `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE`, `ORACLE_SID`, `ORACLE_USER`

## fazer.ai agents
**Pra que serve:** A plataforma onde a Ana roda: lista de ferramentas para o Retrato.
**Onde aparece no código:** `ana/bancada/arquivo/divergimetro.py`, `ana/bancada/e2e.py`, `ana/plataforma/scripts/checagem-fatos.py`, `ana/plataforma/scripts/notas-na-conversa.py`, `retrato/gerar.py`
**Secret/env primária:** `AGENTS_API_TOKEN`
**Variáveis relacionadas:** `PLATAFORMA_URL`

## Chatwoot
**Pra que serve:** Inbox do atendimento: a bancada e2e conversa por ele.
**Onde aparece no código:** `ana/bancada/e2e.py`, `ana/plataforma/scripts/fetch-chatwoot-releases.py`, `ana/plataforma/scripts/notas-na-conversa.py`
**Secret/env primária:** `CHATWOOT_API_TOKEN`
**Variáveis relacionadas:** `CHATWOOT_ACCOUNT_ID`, `CHATWOOT_URL`

## Outras chaves
**Pra que serve:** Chaves lidas pelo código sem serviço mapeado no snapshot.py.
**Onde aparece no código:** `ana/api-mv/scripts/mapa-gh.py`
**Secret/env primária:** `PEDROOS_GLOBAL_HEALTH`

---
**Resumo:** 5 serviços com chave no código. Langfuse e a API do Hospital são
configurados na plataforma, sem chave lida por este repositório.
