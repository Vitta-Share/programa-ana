#!/usr/bin/env python3
"""Mapa da Global Health (HOMOLOGACAO): o que o contrato promete e o que responde hoje.

Uso (saida sempre em JSON):
  python3 ana/api-mv/scripts/mapa-gh.py mapa                  # catalogo + ultimo estado + Historico
  python3 ana/api-mv/scripts/mapa-gh.py testar <capacidade>   # uma leitura ao vivo, resumida
  python3 ana/api-mv/scripts/mapa-gh.py rodada [--quem botao]  # todas as leituras, grava uma Execucao

O catalogo curado mora em ana/api-mv/mapa-gh.json. O Historico mora no estado local do
PedroOS (${PEDROOS_GLOBAL_HEALTH:-~/.pedroos/global-health/ana.jsonl}), uma Execucao por linha.
Le GH_TOKEN_HOMOLOG do .env da raiz do repo, como o smoke-gh.py. Escrita (agendar, reagendar,
cancelar, cadastrar, carteiras) nunca roda daqui. Producao e recusada.
"""
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CATALOGO = Path(__file__).resolve().parent.parent / "mapa-gh.json"
HOMOLOG = "https://dem.agenda.globalhealth.mv/rest/whatsapp"
HOST_PRODUCAO = "whatsapp.agenda.globalhealth.mv"
LOCAIS = ("127.0.0.1", "localhost")  # so a Global Health falsa dos testes
CPF_SONDA = "66301102770"  # paciente-sonda da homologacao (smoke-gh.py); nunca sai na resposta

CORES = {"ok": "verde", "vazio": "amarelo", "erro": "vermelho", "fora_do_ar": "vermelho",
         "bloqueado": "cinza", "sem_registro": "cinza"}
MESES = {m: i for i, ms in enumerate(
    [("jan",), ("feb", "fev"), ("mar",), ("apr", "abr"), ("may", "mai"), ("jun",), ("jul",),
     ("aug", "ago"), ("sep", "set"), ("oct", "out"), ("nov",), ("dec", "dez")], 1) for m in ms}


class Recusa(Exception):
    pass


def emitir(dados, codigo=0):
    print(json.dumps(limpar(dados), ensure_ascii=False, indent=2))
    sys.exit(codigo)


SEGREDOS = []  # nome e telefone da sonda, aprendidos na busca por CPF, mais o token


def limpar(obj):
    """Ultima trava: CPF, nome de paciente, telefone e token nunca saem, nem em mensagem de erro."""
    if isinstance(obj, dict):
        return {k: limpar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [limpar(v) for v in obj]
    if isinstance(obj, str):
        for segredo in [os.environ.get("GH_TOKEN_HOMOLOG"), *SEGREDOS]:
            if segredo:
                obj = re.sub(re.escape(segredo), "***", obj, flags=re.IGNORECASE)
        obj = re.sub(r"\d{3}\.\d{3}\.\d{3}-\d{2}", "***", obj)
        return re.sub(r"\d{10,}", "***", obj)
    return obj


# Catalogo e Historico


def catalogo():
    return json.loads(CATALOGO.read_text(encoding="utf-8"))


def arquivo_historico():
    padrao = Path.home() / ".pedroos" / "global-health" / "ana.jsonl"
    return Path(os.environ.get("PEDROOS_GLOBAL_HEALTH") or padrao)


def ler_historico(cat):
    arq = arquivo_historico()
    if not arq.is_file() or not arq.read_text(encoding="utf-8").strip():
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in cat["semente"]),
                       encoding="utf-8")
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]


def ultimo_estado(cap_id, historico):
    for execucao in reversed(historico):
        res = execucao.get("resultados", {}).get(cap_id)
        if res:
            return {**res, "cor": CORES.get(res["estado"], "cinza"), "data": res.get("data") or execucao["data"],
                    "execucao": execucao["id"], "quem": execucao["quem"],
                    "registro_de_sessao": execucao.get("registro_de_sessao", False)}
    return {"estado": "sem_registro", "cor": "cinza", "data": None}


def escritas_registradas(cat, historico):
    """Ultimo resultado registrado de cada escrita, com a data: as escritas nunca rodam daqui."""
    escritas = {}
    for c in cat["capacidades"]:
        if c["tipo"] != "escrita":
            continue
        ultimo = ultimo_estado(c["id"], historico)
        if ultimo["estado"] != "sem_registro":
            escritas[c["id"]] = {"status": ultimo.get("status"), "mensagem": ultimo.get("faltou"),
                                 "data": ultimo["data"]}
    return escritas


def diferenca(antes, depois):
    """O que mudou de uma Execucao para a seguinte: numeros e estado de cada capacidade."""
    if antes is None:
        return None
    numeros = {k: {"antes": antes["numeros"].get(k), "depois": depois["numeros"].get(k)}
               for k in dict.fromkeys([*antes["numeros"], *depois["numeros"]])
               if antes["numeros"].get(k) != depois["numeros"].get(k)}
    ra, rd = antes.get("resultados", {}), depois.get("resultados", {})
    estados = {c: {"antes": ra[c]["estado"], "depois": rd[c]["estado"]}
               for c in rd if c in ra and ra[c]["estado"] != rd[c]["estado"]}
    return {"numeros": numeros, "estados": estados}


def completar(cat, historico):
    """Cada Execucao com as escritas registradas ate ela (a semente nao as traz escritas)."""
    completas = []
    for i, execucao in enumerate(historico):
        numeros = {**execucao["numeros"]}
        numeros.setdefault("escritas", escritas_registradas(cat, historico[:i + 1]))
        completas.append({**execucao, "numeros": numeros})
    return completas


def resumo_historico(cat, historico):
    completas = completar(cat, historico)
    return [{k: e.get(k) for k in ("id", "data", "quem", "registro_de_sessao", "duracao_ms", "nota")}
            | {"numeros": e["numeros"], "diferenca": diferenca(completas[i - 1] if i else None, e)}
            for i, e in enumerate(completas)]


# Global Health


def base_homolog():
    base = os.environ.get("GH_MAPA_BASE") or HOMOLOG
    host = urllib.parse.urlparse(base).hostname or ""
    if HOST_PRODUCAO in host:
        raise Recusa("endereço de produção recusado: o Mapa só fala com a Global Health de teste")
    if base != HOMOLOG and host not in LOCAIS:
        raise Recusa(f"endereço recusado: o Mapa só fala com {HOMOLOG}")
    return base.rstrip("/")


def token():
    if os.environ.get("GH_TOKEN_HOMOLOG"):
        return os.environ["GH_TOKEN_HOMOLOG"]
    for parent in Path(__file__).resolve().parents:
        env = parent / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                if line.strip().startswith("GH_TOKEN_HOMOLOG="):
                    valor = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["GH_TOKEN_HOMOLOG"] = valor  # para a trava de saida mascarar
                    return valor
    raise Recusa("GH_TOKEN_HOMOLOG ausente do .env")


class GH:
    def __init__(self):
        self.base = base_homolog()
        self.token = token()
        self.timeout = float(os.environ.get("GH_MAPA_TIMEOUT") or 20)
        self.fim = time.monotonic() + float(os.environ.get("GH_MAPA_PRAZO") or 120)
        self.ctx = ssl.create_default_context()

    def chamar(self, metodo, caminho, params=None, body=None):
        """(status, corpo, ms). status None = fora do ar (sem resposta no tempo limite)."""
        restante = self.fim - time.monotonic()
        if restante <= 0:
            return None, "prazo da rodada esgotado", 0
        url = self.base + caminho + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(
            url, method=metodo, data=json.dumps(body).encode() if body is not None else None,
            headers={"Token": self.token, "Accept": "application/json", "Content-Type": "application/json"})
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=min(self.timeout, restante), context=self.ctx) as r:
                status, raw = r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            return None, type(e).__name__, int((time.monotonic() - t0) * 1000)
        ms = int((time.monotonic() - t0) * 1000)
        try:
            return status, json.loads(raw) if raw.strip() else None, ms
        except ValueError:
            return status, raw, ms


def mensagem_erro(corpo):
    if isinstance(corpo, dict):
        msgs = [m.get("texto") for m in corpo.get("mensagens") or [] if isinstance(m, dict) and m.get("texto")]
        if msgs:
            return "; ".join(msgs)
        if corpo.get("mensagemErro"):
            return corpo["mensagemErro"]
    return str(corpo)[:120] if corpo else "sem corpo"


def itens(corpo):
    if isinstance(corpo, dict) and "conteudo" in corpo:
        return corpo["conteudo"] or []
    return corpo if isinstance(corpo, list) else []


def resultado(estado, status=None, ms=None, contagem=None, nomes=(), faltou=None, **extra):
    return {"estado": estado, "status": status, "tempo_ms": ms, "contagem": contagem,
            "nomes": list(nomes)[:5], "faltou": faltou, **extra}


def resumir(resposta, lista=itens, nome=lambda i: i.get("nome"), vazio="a lista veio vazia"):
    """Resume uma resposta: fora do ar, erro com a mensagem da GH, vazio ou ok com ate 5 nomes."""
    status, corpo, ms = resposta
    if status is None:
        return resultado("fora_do_ar", None, ms, faltou=f"fora do ar ({corpo})")
    if status != 200:
        return resultado("erro", status, ms, faltou=mensagem_erro(corpo))
    achados = lista(corpo)
    if not achados:
        return resultado("vazio", status, ms, 0, faltou=vazio)
    return resultado("ok", status, ms, len(achados), [nome(i) for i in achados if nome(i)])


def bloqueado(motivo):
    return resultado("bloqueado", faltou=motivo)


# As leituras, na ordem do caminho. Cada uma recebe o contexto da cadeia (ids montados ao vivo
# pelas anteriores) e devolve o resultado resumido. Dados da sonda ficam so no contexto.


def l_pessoa_por_cpf(gh, ctx):
    status, corpo, ms = gh.chamar("GET", "/pessoas", {"cpf": CPF_SONDA})
    if status == 200 and isinstance(corpo, dict) and corpo.get("id"):
        ctx["sonda"], ctx["telefone"] = True, corpo.get("telefone")
        SEGREDOS.extend(s for s in (corpo.get("nome"), corpo.get("telefone"), corpo.get("email")) if s)
        return resultado("ok", status, ms, 1, faltou=None, resumo="encontrado")
    if status == 200:
        return resultado("vazio", status, ms, 0, faltou="paciente-sonda não encontrado", resumo="não encontrado")
    return resumir((status, corpo, ms))


SEM_SONDA = "sem o paciente-sonda identificado (a busca por CPF não achou)"


def l_pessoa_por_telefone(gh, ctx):
    if not ctx.get("telefone"):
        return bloqueado("sem o telefone da sonda (a busca por CPF não achou)")
    status, corpo, ms = gh.chamar("GET", "/pessoas", {"telefone": ctx["telefone"]})
    if status == 200 and isinstance(corpo, dict) and corpo.get("id"):
        return resultado("ok", status, ms, 1, faltou=None, resumo="encontrado")
    if status == 200:
        return resultado("vazio", status, ms, 0, faltou="paciente-sonda não encontrado", resumo="não encontrado")
    return resumir((status, corpo, ms))


def l_carteiras(gh, ctx):
    if not ctx.get("sonda"):
        return bloqueado(SEM_SONDA)
    return resumir(gh.chamar("GET", "/carteiras", {"cpf": CPF_SONDA}),
                   nome=lambda i: i.get("nomeConvenio"), vazio="a sonda não tem carteira")


def l_especialidades(gh, ctx):
    resp = gh.chamar("GET", "/consultas", {"size": 100})
    ctx["especialidades"] = [i for i in itens(resp[1]) if resp[0] == 200 and not i.get("bloqueado")]
    return resumir(resp, vazio="nenhuma consulta publicada")


def l_prestadores(gh, ctx):
    if not ctx.get("especialidades"):
        return bloqueado("sem especialidade publicada")
    medicos, escolhida, nomes, ms = {}, None, [], 0
    for esp in ctx["especialidades"]:
        res = resumir(gh.chamar("GET", "/prestadores", {"idItemAgendamento": esp["id"], "size": 100}),
                      vazio="nenhum médico publicado")
        if res["estado"] in ("erro", "fora_do_ar"):
            return res
        ms += res["tempo_ms"]
        medicos[esp["nome"]] = res["contagem"]
        if escolhida is None and res["contagem"]:
            escolhida, nomes = esp, res["nomes"]
    # a cadeia segue pela primeira especialidade que tem medico publicado
    escolhida = escolhida or ctx["especialidades"][0]
    ctx.update(medicos_por_especialidade=medicos, idItemAgendamento=escolhida["id"],
               especialidade_da_cadeia=escolhida["nome"])
    total = sum(medicos.values())
    return resultado("ok" if total else "vazio", 200, ms, total, nomes,
                     None if total else "nenhum médico publicado", por_especialidade=medicos,
                     especialidade_da_cadeia=escolhida["nome"])


def escolher_convenio(convenios):
    for c in convenios:
        if (c.get("nome") or "").strip().lower() == "particular":
            return c
    return next((c for c in convenios if c.get("particular")), convenios[0])


def l_convenios(gh, ctx):
    if not ctx.get("idItemAgendamento"):
        return bloqueado("sem especialidade publicada")
    resp = gh.chamar("GET", "/convenios", {"idItemAgendamento": ctx["idItemAgendamento"], "size": 100})
    res = resumir(resp, vazio="nenhum convênio para a especialidade")
    if res["estado"] == "ok":
        ctx["idConvenio"] = escolher_convenio(itens(resp[1]))["id"]
    return res


def l_planos(gh, ctx):
    if not ctx.get("idConvenio"):
        return bloqueado("sem convênio")
    resp = gh.chamar("GET", f"/convenios/{ctx['idConvenio']}/planos",
                     {"idItemAgendamento": ctx["idItemAgendamento"], "size": 100})
    res = resumir(resp, vazio="nenhum plano no convênio")
    if res["estado"] == "ok":
        ctx["idPlano"] = sorted(itens(resp[1]), key=lambda p: p.get("ordem") or 0)[0]["id"]
    return res


def l_subplanos(gh, ctx):
    if not ctx.get("idPlano"):
        return bloqueado("sem plano")
    return resumir(gh.chamar("GET", f"/convenios/{ctx['idConvenio']}/planos/{ctx['idPlano']}/subPlanos"),
                   vazio="nenhum subplano")


def dia_mes(descricao):
    m = re.match(r"(\d{1,2})/([A-Za-z]{3})", descricao or "")
    if m and m.group(2).lower() in MESES:
        return f"{int(m.group(1)):02d}/{MESES[m.group(2).lower()]:02d}"
    m = re.match(r"(\d{1,2})/(\d{1,2})", descricao or "")
    return f"{int(m.group(1)):02d}/{int(m.group(2)):02d}" if m else descricao


def horarios_da_agenda(corpo):
    achados = []
    for agenda in (corpo or {}).get("agendas") or [] if isinstance(corpo, dict) else []:
        for p in agenda.get("prestadores") or []:
            for h in p.get("horarios") or []:
                achados.append({**h, "medico": p.get("nomePrestadorRecurso")})
    return achados


def ultimo_dia(corpo, achados):
    """A data mais distante entre todos os horarios (a resposta vem por unidade e prestador, nao
    por data). O ano sai do dataInicial: um dia/mes antes dele ja e do ano seguinte."""
    inicio = re.match(r"\d{4}-(\d{2})-(\d{2})", (corpo or {}).get("dataInicial") or "")
    comeco = (int(inicio.group(1)), int(inicio.group(2))) if inicio else (1, 1)
    datas = []
    for h in achados:
        m = re.fullmatch(r"(\d{2})/(\d{2})", dia_mes(h.get("descricaoHorario")) or "")
        if m:
            mes_dia = (int(m.group(2)), int(m.group(1)))
            datas.append((mes_dia < comeco, mes_dia))
    if not datas:
        return None
    _, (mes, dia) = max(datas)
    return f"{dia:02d}/{mes:02d}"


def l_horarios(gh, ctx):
    if not ctx.get("idPlano"):
        return bloqueado("sem especialidade, convênio e plano montados ao vivo")
    resp = gh.chamar("GET", "/agendas/v2", {"idItemAgendamento": ctx["idItemAgendamento"],
                                            "idConvenio": ctx["idConvenio"], "idPlano": ctx["idPlano"]})
    res = resumir(resp, lista=horarios_da_agenda,
                  nome=lambda h: f"{h['medico']} {dia_mes(h.get('descricaoHorario'))} "
                                 f"{(h.get('descricaoHorario') or '').split(' ')[-1]}".strip(),
                  vazio="nenhum horário livre nos próximos 14 dias")
    achados = horarios_da_agenda(resp[1]) if resp[0] == 200 else []
    if achados:
        ctx["idHorario"], ctx["idAgenda"] = achados[0]["idHorario"], achados[0]["idAgenda"]
        ctx["ultimo_horario"] = ultimo_dia(resp[1], achados)
    return res


def l_tipos_consulta(gh, ctx):
    if not ctx.get("idAgenda"):
        return bloqueado("sem horário livre (falta o idAgenda)")
    return resumir(gh.chamar("GET", "/consultas/tipos", {"idAgenda": ctx["idAgenda"]}),
                   vazio="nenhum tipo de consulta na agenda")


def l_instrucoes_horario(gh, ctx):
    if not ctx.get("idHorario"):
        return bloqueado("sem horário livre (falta o idHorario)")
    return resumir(gh.chamar("GET", f"/horarios/{ctx['idHorario']}/instrucoes",
                             {"idItemAgendamento": ctx["idItemAgendamento"], "idConvenio": ctx["idConvenio"]}),
                   lista=lambda c: [c] if isinstance(c, dict) and c.get("instrucoes") else [],
                   nome=lambda c: None, vazio="sem instrução cadastrada")


def l_anexos_exigidos(gh, ctx):
    if not ctx.get("idHorario"):
        return bloqueado("sem horário livre (falta o idHorario)")
    return resumir(gh.chamar("POST", "/anexos/agendamento", body={
        "idItemAgendamento": ctx["idItemAgendamento"], "idConvenio": ctx["idConvenio"],
        "idPlano": ctx["idPlano"], "idHorario": ctx["idHorario"]}), vazio="nenhum anexo exigido")


def l_exames(gh, ctx):
    resp = gh.chamar("GET", "/exames", {"size": 100})
    ctx["exames"] = [i for i in itens(resp[1]) if resp[0] == 200 and not i.get("bloqueado")]
    return resumir(resp, vazio="nenhum exame publicado")


def l_perguntas_exame(gh, ctx):
    if not ctx.get("exames"):
        return bloqueado("sem exame publicado")
    if not ctx.get("sonda"):
        return bloqueado(SEM_SONDA)
    return resumir(gh.chamar("GET", "/exames/perguntas",
                             {"idItemAgendamento": ctx["exames"][0]["id"], "cpf": CPF_SONDA}),
                   nome=lambda i: i.get("descricao"), vazio="nenhuma pergunta de triagem")


def l_instrucao_geral_exame(gh, ctx):
    if not ctx.get("exames"):
        return bloqueado("sem exame publicado")
    return resumir(gh.chamar("GET", "/exames/instrucaoGeral", {"idItemAgendamento": ctx["exames"][0]["id"]}),
                   lista=lambda c: [c] if isinstance(c, dict) and c.get("instrucoes") else [],
                   nome=lambda c: None, vazio="sem instrução cadastrada")


def l_listar_agendamentos(gh, ctx):
    if not ctx.get("sonda"):
        return bloqueado(SEM_SONDA)
    resp = gh.chamar("GET", "/agendamentos", {"cpf": CPF_SONDA, "tipoAgendamento": "CONSULTA"})
    achados = itens(resp[1]) if resp[0] == 200 else []
    if achados:
        ctx["idAgendamento"] = achados[0]["id"]
    return resumir(resp, nome=lambda i: i.get("especialidadeExame"), vazio="nenhum agendamento")


def l_detalhe_agendamento(gh, ctx):
    if not ctx.get("idAgendamento"):
        return bloqueado("sem agendamento para detalhar")
    return resumir(gh.chamar("GET", f"/agendamentos/{ctx['idAgendamento']}"),
                   lista=lambda c: [c] if isinstance(c, dict) and c.get("id") else [],
                   nome=lambda c: c.get("especialidadeExame"), vazio="agendamento não encontrado")


LEITURAS = {
    "pessoa_por_cpf": (l_pessoa_por_cpf, []),
    "pessoa_por_telefone": (l_pessoa_por_telefone, ["pessoa_por_cpf"]),
    "carteiras": (l_carteiras, ["pessoa_por_cpf"]),
    "especialidades": (l_especialidades, []),
    "prestadores": (l_prestadores, ["especialidades"]),
    "convenios": (l_convenios, ["prestadores"]),
    "planos": (l_planos, ["convenios"]),
    "subplanos": (l_subplanos, ["planos"]),
    "horarios": (l_horarios, ["planos"]),
    "tipos_consulta": (l_tipos_consulta, ["horarios"]),
    "instrucoes_horario": (l_instrucoes_horario, ["horarios"]),
    "anexos_exigidos": (l_anexos_exigidos, ["horarios"]),
    "exames": (l_exames, []),
    "perguntas_exame": (l_perguntas_exame, ["pessoa_por_cpf", "exames"]),
    "instrucao_geral_exame": (l_instrucao_geral_exame, ["exames"]),
    "listar_agendamentos": (l_listar_agendamentos, ["pessoa_por_cpf"]),
    "detalhe_agendamento": (l_detalhe_agendamento, ["listar_agendamentos"]),
}


def cadeia_ate(alvo):
    """As leituras que montam os ids do alvo, na ordem, terminando nele."""
    ordem = []

    def visitar(cap):
        for dep in LEITURAS[cap][1]:
            visitar(dep)
        if cap not in ordem:
            ordem.append(cap)
    visitar(alvo)
    return ordem


def ids_da_cadeia(ctx):
    return {k: ctx[k] for k in ("idItemAgendamento", "idConvenio", "idPlano", "idHorario", "idAgenda")
            if ctx.get(k) is not None}


def rodar_leituras(gh, caps):
    ctx, resultados = {}, {}
    for cap in caps:
        res = LEITURAS[cap][0](gh, ctx)
        resultados[cap] = {**res, "cor": CORES[res["estado"]]}
    return ctx, resultados


# Os tres usos


def cmd_mapa():
    cat = catalogo()
    historico = ler_historico(cat)
    caminhos = []
    for caminho in cat["caminhos"]:
        caps = sorted((c for c in cat["capacidades"] if c["caminho"] == caminho["id"]), key=lambda c: c["ordem"])
        caminhos.append({**caminho, "capacidades": [{**c, "ultimo_estado": ultimo_estado(c["id"], historico)}
                                                    for c in caps]})
    emitir({"versao_contrato": cat["versao_contrato"], "ambiente": "homologacao",
            "caminhos": caminhos, "historico": resumo_historico(cat, historico)})


def cmd_testar(cap_id):
    cat = catalogo()
    cap = next((c for c in cat["capacidades"] if c["id"] == cap_id), None)
    if cap is None:
        emitir({"erro": f"capacidade desconhecida: {cap_id}",
                "capacidades": [c["id"] for c in cat["capacidades"]]}, 2)
    if cap["tipo"] == "escrita":
        emitir({"capacidade": cap_id, "chamada": cap["chamada"], "recusado": True,
                "motivo": "escrita não roda pelo Mapa; o resultado abaixo é o último registrado numa sessão",
                "ultimo_registro": ultimo_estado(cap_id, ler_historico(cat))})
    gh = GH()
    ctx, resultados = rodar_leituras(gh, cadeia_ate(cap_id))
    emitir({"capacidade": cap_id, "chamada": cap["chamada"], **resultados[cap_id],
            "ids": ids_da_cadeia(ctx)})


def contagem(resultados, cap):
    res = resultados.get(cap) or {}
    return res.get("contagem") if res.get("estado") in ("ok", "vazio") else None


def cmd_rodada(quem):
    cat = catalogo()
    historico = ler_historico(cat)
    gh = GH()
    t0 = time.monotonic()
    leituras = [c["id"] for caminho in cat["caminhos"]
                for c in sorted(cat["capacidades"], key=lambda c: c["ordem"])
                if c["caminho"] == caminho["id"] and c["tipo"] == "leitura"]
    ctx, resultados = rodar_leituras(gh, leituras)
    agora = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")
    erros = [f"{c}: HTTP {r['status']}" if r["estado"] == "erro" else f"{c}: fora do ar"
             for c, r in resultados.items() if r["estado"] in ("erro", "fora_do_ar")]
    execucao = {
        "id": agora, "data": agora, "quem": quem, "registro_de_sessao": False,
        "duracao_ms": int((time.monotonic() - t0) * 1000), "nota": None,
        "numeros": {
            "especialidades_publicadas": contagem(resultados, "especialidades"),
            "exames_publicados": contagem(resultados, "exames"),
            "medicos_por_especialidade": ctx.get("medicos_por_especialidade", {}),
            "especialidade_da_cadeia": ctx.get("especialidade_da_cadeia"),
            "convenios": contagem(resultados, "convenios"),
            "planos": contagem(resultados, "planos"),
            "horarios_14_dias": contagem(resultados, "horarios"),
            "ultimo_horario": ctx.get("ultimo_horario"),
            "escritas": escritas_registradas(cat, historico),
            "erros": erros,
        },
        "ids": ids_da_cadeia(ctx),
        "resultados": resultados,
    }
    execucao = limpar(execucao)
    with arquivo_historico().open("a", encoding="utf-8") as f:
        f.write(json.dumps(execucao, ensure_ascii=False) + "\n")
    anterior = completar(cat, historico)[-1] if historico else None
    emitir({"execucao": execucao, "anterior": anterior and anterior["id"],
            "diferenca": diferenca(anterior, execucao)})


def main(argv):
    try:
        if argv[:1] == ["mapa"]:
            cmd_mapa()
        if argv[:1] == ["testar"] and len(argv) == 2:
            cmd_testar(argv[1])
        if argv[:1] == ["rodada"]:
            quem = argv[argv.index("--quem") + 1] if "--quem" in argv[:-1] else "sessao"
            if quem not in ("botao", "sessao"):
                raise Recusa("--quem aceita botao ou sessao")
            cmd_rodada(quem)
    except Recusa as e:
        emitir({"erro": str(e)}, 2)
    emitir({"erro": "uso: mapa | testar <capacidade> | rodada [--quem botao|sessao]"}, 2)


if __name__ == "__main__":
    main(sys.argv[1:])
