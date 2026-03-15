import json
import requests
from typing import Optional, List

OLLAMA_BASE = "http://localhost:11434"
MODEL = "llama3.2"

RATING_LABELS = {
    "nao_observado": "Não observado",
    "insuficiente": "Insuficiente",
    "adequado": "Adequado",
    "muito_bom": "Muito Bom",
    None: "Não informado",
}

RATING_SCORE = {
    "nao_observado": 0,
    "insuficiente": 33,
    "adequado": 67,
    "muito_bom": 100,
    None: 0,
}

# ─── PEC sections ───────────────────────────────────────────────────────────
SECTION_CRITERIA = {
    "s1": [
        ("s1_c1", "Plano de aula alinhado ao Currículo Paulista e materiais oficiais da SEDUC"),
        ("s1_c2", "Objetivos de aprendizagem explícitos e claros para os alunos"),
        ("s1_c3", "Habilidades da BNCC/Currículo Paulista adequadas ao ano/série"),
        ("s1_c4", "Atividades coerentes com os objetivos da aula"),
    ],
    "s2": [
        ("s2_c1", "Aula inicia nos primeiros 5 minutos"),
        ("s2_c2", "Retomada de conhecimentos prévios ou da aula anterior"),
        ("s2_c3", "Explicação do conteúdo clara com exemplos adequados"),
        ("s2_c4", "Variedade metodológica"),
        ("s2_c5", "Perguntas para verificar compreensão durante a aula"),
        ("s2_c6", "Fechamento/síntese do que foi aprendido"),
    ],
    "s3": [
        ("s3_c1", "Alunos demonstram engajamento e participação ativa"),
        ("s3_c2", "Professor identifica e atende alunos com dificuldades"),
        ("s3_c3", "Diferenciação pedagógica para diferentes níveis"),
        ("s3_c4", "Estratégias de avaliação formativa durante a aula"),
        ("s3_c5", "Professor dá feedback aos alunos sobre suas produções"),
    ],
    "s4": [
        ("s4_c1", "Utiliza materiais oficiais da SEDUC"),
        ("s4_c2", "Uso adequado de recursos disponíveis na escola"),
        ("s4_c3", "Tempo da aula bem distribuído entre atividades"),
        ("s4_c4", "Registros (quadro, projeção) claros e organizados"),
    ],
    "s5": [
        ("s5_c1", "Ambiente de respeito mútuo e segurança para participação"),
        ("s5_c2", "Boa relação com os alunos (escuta, abertura a dúvidas)"),
        ("s5_c3", "Manejo adequado de situações de indisciplina ou conflitos"),
        ("s5_c4", "Professor demonstra preparo prévio e organização"),
        ("s5_c5", "Postura profissional adequada"),
    ],
}

SECTION_NAMES = {
    "s1": "Planejamento e Alinhamento Curricular",
    "s2": "Condução Didática da Aula",
    "s3": "Gestão da Aprendizagem dos Alunos",
    "s4": "Uso de Materiais, Recursos e Tempo",
    "s5": "Clima, Relações e Postura Profissional",
}

# ─── EF I domains ────────────────────────────────────────────────────────────
EF1_SECTION_CRITERIA = {
    "dc": [
        ("ef1_dc_c1", "Professor demonstra conhecimento sólido e preciso do conteúdo ensinado"),
        ("ef1_dc_c2", "Explicações são adequadas à faixa etária (linguagem, exemplos, nível de abstração)"),
        ("ef1_dc_c3", "Estabelece relações entre o conteúdo e o cotidiano/vivência das crianças"),
    ],
    "es": [
        ("ef1_es_c1", "Crianças demonstram interesse, curiosidade e participação ativa"),
        ("ef1_es_c2", "Professor valoriza e aproveita as falas e produções das crianças"),
        ("ef1_es_c3", "Há clima de ludicidade, descoberta e pertencimento"),
    ],
    "me": [
        ("ef1_me_c1", "Utiliza abordagens variadas e adequadas para EF I (jogos, contação de histórias, brincadeiras dirigidas)"),
        ("ef1_me_c2", "Propõe atividades que estimulam o pensamento, a autonomia e a criatividade"),
        ("ef1_me_c3", "Equilibra momentos coletivos, em duplas/grupos e individuais"),
    ],
    "md": [
        ("ef1_md_c1", "Materiais concretos, manipuláveis ou visuais são utilizados intencionalmente"),
        ("ef1_md_c2", "Os recursos são adequados à faixa etária e ao objetivo da aula"),
        ("ef1_md_c3", "Utiliza de forma intencional os materiais oficiais (livro didático, cadernos SEDUC)"),
    ],
    "gs": [
        ("ef1_gs_c1", "Organização do espaço físico favorece a aprendizagem e a interação"),
        ("ef1_gs_c2", "Rotinas e transições entre atividades são claras e bem gerenciadas"),
        ("ef1_gs_c3", "Tempo da aula é aproveitado de forma produtiva, minimizando tempos ociosos"),
    ],
    "mc": [
        ("ef1_mc_c1", "Professor identifica e intervém em situações de conflito com calma e assertividade"),
        ("ef1_mc_c2", "Utiliza estratégias restaurativas, dialógicas e não punitivas"),
        ("ef1_mc_c3", "Mantém ambiente acolhedor e seguro mesmo diante de comportamentos desafiadores"),
    ],
}

EF1_DOMAIN_NAMES = {
    "dc": "Domínio de Conteúdo",
    "es": "Engajamento dos Estudantes",
    "me": "Metodologias e Estratégias",
    "md": "Material Didático",
    "gs": "Gestão de Sala",
    "mc": "Manejo de Conflitos",
}

PEDRO_DEMO_REFS = """
Referências bibliográficas que embasam esta análise:
- DEMO, Pedro. Ser professor é qualidade. Porto Alegre: Artmed, 2011.
- DEMO, Pedro. Avaliação qualitativa. 7ª ed. São Paulo: Cortez, 2002.
- DEMO, Pedro. Educar pela pesquisa. 9ª ed. Campinas: Autores Associados, 2011.
- BNCC – Base Nacional Comum Curricular, MEC/2017.
- Currículo Paulista – SEDUC-SP, 2019.
"""


# ─── Score computation ────────────────────────────────────────────────────────
def compute_section_scores(obs) -> dict:
    scores = {}
    for sec, criteria in SECTION_CRITERIA.items():
        vals = [RATING_SCORE[getattr(obs, field, None)] for field, _ in criteria]
        scores[sec] = round(sum(vals) / len(vals)) if vals else 0
    scores["total"] = round(sum(scores[s] for s in ["s1", "s2", "s3", "s4", "s5"]) / 5)
    return scores


def compute_ef1_scores(obs) -> dict:
    scores = {}
    any_filled = False
    for dom, criteria in EF1_SECTION_CRITERIA.items():
        vals = [RATING_SCORE[getattr(obs, field, None)] for field, _ in criteria]
        filled = [v for field, _ in criteria if getattr(obs, field, None) is not None]
        if filled:
            any_filled = True
        scores[dom] = round(sum(vals) / len(vals)) if vals else 0
    if any_filled:
        scores["ef1_total"] = round(sum(scores[d] for d in EF1_SECTION_CRITERIA) / len(EF1_SECTION_CRITERIA))
    else:
        scores["ef1_total"] = None
    return scores


def infer_grade_band(grade: str) -> str:
    if not grade:
        return "ef2"
    g = grade.lower()
    if any(x in g for x in ["1º", "2º", "3º", "4º", "5º", "1o", "2o", "3o", "4o", "5o",
                              "1°", "2°", "3°", "4°", "5°"]):
        return "ef1"
    if any(x in g for x in ["6º", "7º", "8º", "9º", "6o", "7o", "8o", "9o"]):
        return "ef2"
    if "médio" in g or "em" in g:
        return "em"
    return "ef2"


# ─── RAG context helpers ──────────────────────────────────────────────────────
def _build_history_context(history_obs: List) -> str:
    if not history_obs:
        return ""
    lines = ["\n=== HISTÓRICO DAS ÚLTIMAS OBSERVAÇÕES DO PROFESSOR ==="]
    for h in history_obs:
        scores = compute_section_scores(h)
        ef1 = compute_ef1_scores(h)
        lines.append(f"\nObservação de {h.observed_at.strftime('%d/%m/%Y')}:")
        lines.append(f"  Scores PEC: S1={scores['s1']} S2={scores['s2']} S3={scores['s3']} S4={scores['s4']} S5={scores['s5']} Total={scores['total']}")
        if ef1.get("ef1_total") is not None:
            lines.append(f"  Scores EF I: DC={ef1['dc']} ES={ef1['es']} ME={ef1['me']} MD={ef1['md']} GS={ef1['gs']} MC={ef1['mc']}")
        if h.feedback_raw:
            try:
                fb = json.loads(h.feedback_raw)
                if fb.get("pontos_fortes"):
                    lines.append(f"  Pontos fortes: {'; '.join(str(p) for p in fb['pontos_fortes'][:2])}")
                if fb.get("areas_desenvolvimento"):
                    areas = [a.get("area", "") for a in fb["areas_desenvolvimento"][:2]]
                    lines.append(f"  Áreas de desenvolvimento: {'; '.join(areas)}")
                if fb.get("padroes_identificados"):
                    lines.append(f"  Padrões: {'; '.join(str(p) for p in fb['padroes_identificados'][:2])}")
            except Exception:
                pass
    return "\n".join(lines)


def _build_action_plan_context(action_results: List) -> str:
    if not action_results:
        return ""
    lines = ["\n=== COMBINADOS EXECUTADOS E RESULTADOS ==="]
    for ar in action_results:
        status_label = {"realizado": "✓ Realizado", "parcial": "◑ Parcial", "pendente": "○ Pendente"}.get(ar.status, ar.status)
        line = f"- Ação: \"{ar.action_text}\" | {status_label}"
        if ar.score_before is not None and ar.score_after is not None:
            delta = ar.delta_score or (ar.score_after - ar.score_before)
            sign = "+" if delta >= 0 else ""
            line += f" | Score: {ar.score_before} → {ar.score_after} ({sign}{delta}pts)"
        if ar.result_notes:
            line += f"\n  Resultado: {ar.result_notes}"
        lines.append(line)
    return "\n".join(lines)


def _build_best_practices_context(best_practices: List) -> str:
    if not best_practices:
        return ""
    lines = ["\n=== PRÁTICAS EFICAZES DE PROFESSORES COM PERFIL SIMILAR ==="]
    for bp in best_practices[:5]:
        lines.append(f"▸ {bp.content} (score: {bp.score_at_time})")
    return "\n".join(lines)


# ─── PEC Feedback ─────────────────────────────────────────────────────────────
FEEDBACK_SYSTEM = """Você é um Professor Especialista em Currículo (PEC) da Secretaria da Educação do Estado de São Paulo.
Sua função é fornecer devolutivas formativas construtivas e detalhadas baseadas nas observações de aula registradas,
seguindo as diretrizes do Currículo Paulista e da BNCC. Você deve referenciar o histórico do professor para
identificar padrões, reconhecer avanços e personalizar as recomendações.
Quando disponíveis, incorpore as melhores práticas de professores com perfil similar que obtiveram bons resultados.
Responda APENAS com JSON válido, sem texto adicional, sem markdown."""

FEEDBACK_RESPONSE_FORMAT = """{
  "resumo_geral": "Parágrafo síntese da observação (4-6 frases)",
  "pontos_fortes": ["ponto forte 1", "ponto forte 2", "ponto forte 3"],
  "areas_desenvolvimento": [
    {"area": "nome da área", "descricao": "descrição detalhada", "sugestao_concreta": "ação específica para próxima aula"}
  ],
  "secoes": {
    "s1": {"analise": "análise da seção 1", "recomendacao": "recomendação específica"},
    "s2": {"analise": "análise da seção 2", "recomendacao": "recomendação específica"},
    "s3": {"analise": "análise da seção 3", "recomendacao": "recomendação específica"},
    "s4": {"analise": "análise da seção 4", "recomendacao": "recomendação específica"},
    "s5": {"analise": "análise da seção 5", "recomendacao": "recomendação específica"}
  },
  "proximos_passos": ["ação 1", "ação 2", "ação 3"],
  "score_estimado": {"s1": 75, "s2": 80, "s3": 65, "s4": 70, "s5": 85, "total": 75},
  "analise_historica": "Parágrafo referenciando evolução em relação às observações anteriores",
  "reconhecimento_avancos": ["progresso identificado 1", "progresso identificado 2"],
  "padroes_identificados": ["padrão recorrente 1", "padrão recorrente 2"],
  "alinhamento_bncc": "Análise do alinhamento com as habilidades BNCC informadas"
}"""


def _build_observation_prompt(obs, teacher, history_obs, transcript_excerpt,
                               action_results=None, best_practices=None) -> str:
    sections_text = []
    for sec, criteria in SECTION_CRITERIA.items():
        sec_lines = [f"\n{SECTION_NAMES[sec]}:"]
        for field, label in criteria:
            val = getattr(obs, field, None)
            sec_lines.append(f"  - {label}: {RATING_LABELS.get(val, 'Não informado')}")
        sections_text.append("\n".join(sec_lines))

    methodologies = ""
    if obs.s2_methodologies:
        try:
            mets = json.loads(obs.s2_methodologies)
            if mets:
                methodologies = f"\nMetodologias observadas: {', '.join(mets)}"
        except Exception:
            pass

    bncc = ""
    if obs.bncc_skills:
        try:
            skills = json.loads(obs.bncc_skills)
            bncc = f"\nHabilidades BNCC trabalhadas: {', '.join(skills)}"
        except Exception:
            bncc = f"\nHabilidades BNCC: {obs.bncc_skills}"

    teacher_section = ""
    if any([obs.teacher_feeling, obs.teacher_comments, obs.teacher_expectations, obs.teacher_commitment]):
        teacher_section = "\n\n=== RESPOSTAS DO PROFESSOR ==="
        if obs.teacher_feeling:
            teacher_section += f"\nComo se sentiu: {obs.teacher_feeling}"
        if obs.teacher_comments:
            teacher_section += f"\nComentários: {obs.teacher_comments}"
        if obs.teacher_expectations:
            teacher_section += f"\nExpectativas/objetivos: {obs.teacher_expectations}"
        if obs.teacher_commitment:
            teacher_section += f"\nCompromisso: {obs.teacher_commitment}"

    transcript_section = ""
    if transcript_excerpt:
        transcript_section = f"\n\n=== TRECHO DA TRANSCRIÇÃO DA AULA ===\n{transcript_excerpt[:3000]}"

    history_section = _build_history_context(history_obs)
    action_section = _build_action_plan_context(action_results or [])
    practices_section = _build_best_practices_context(best_practices or [])

    pontos = ""
    if obs.pontos_fortes:
        try:
            p = json.loads(obs.pontos_fortes)
            pontos = f"\nPontos fortes identificados pelo PEC: {'; '.join(p)}"
        except Exception:
            pontos = f"\nPontos fortes: {obs.pontos_fortes}"

    focos = ""
    if obs.focos_desenvolvimento:
        try:
            f_ = json.loads(obs.focos_desenvolvimento)
            focos = f"\nFocos de desenvolvimento: {'; '.join(f_)}"
        except Exception:
            focos = f"\nFocos: {obs.focos_desenvolvimento}"

    return f"""=== DADOS DA OBSERVAÇÃO ===
Professor(a): {teacher.name}
Escola: {teacher.school or 'Não informado'}
Componente Curricular: {teacher.subject or 'Não informado'} | Ano/Série: {teacher.grade or 'Não informado'}
Data da observação: {obs.observed_at.strftime('%d/%m/%Y') if obs.observed_at else 'Não informado'}
PEC responsável: {obs.pec_name or 'Não informado'}
Foco curricular: {obs.focus_area or 'Não informado'}
{bncc}

=== AVALIAÇÃO POR SEÇÃO (FICHA PEC) ===
{"".join(sections_text)}
{methodologies}

=== NARRATIVA DO PEC ===
{pontos}
{focos}
Sugestões do PEC: {obs.sugestoes or 'Não informado'}
{teacher_section}
{transcript_section}
{history_section}
{action_section}
{practices_section}

Gere o feedback completo em JSON com TODOS os campos solicitados, em português, no contexto da educação pública do Estado de São Paulo.

Formato esperado de resposta:
{FEEDBACK_RESPONSE_FORMAT}"""


def generate_feedback(obs, teacher, history_obs: List,
                      action_results=None, best_practices=None) -> dict:
    transcript_excerpt = None
    if obs.transcript:
        transcript_excerpt = obs.transcript[:3000]

    prompt = _build_observation_prompt(obs, teacher, history_obs, transcript_excerpt,
                                       action_results, best_practices)

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "system": FEEDBACK_SYSTEM,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "num_ctx": 8192},
        },
        timeout=180,
    )
    response.raise_for_status()
    raw = response.json().get("response", "{}")
    return json.loads(raw)


# ─── EF I Feedback ────────────────────────────────────────────────────────────
EF1_FEEDBACK_SYSTEM = f"""Você é um formador pedagógico especializado no Ensino Fundamental I (anos 1–5),
com profundo conhecimento das teorias de Pedro Demo sobre qualidade do ensino,
avaliação formativa e pesquisa como princípio educativo.
Sua função é gerar devolutivas formativas embasadas, contextualizadas e propositivas
para professores da infância e dos anos iniciais.

{PEDRO_DEMO_REFS}

Responda APENAS com JSON válido, sem texto adicional, sem markdown."""

EF1_RESPONSE_FORMAT = """{
  "resumo_geral": "Parágrafo síntese da observação EF I (4-6 frases)",
  "pontos_fortes": ["ponto forte 1", "ponto forte 2", "ponto forte 3"],
  "areas_desenvolvimento": [
    {"area": "nome do domínio", "descricao": "descrição detalhada", "sugestao_concreta": "ação para próxima aula"}
  ],
  "dominios": {
    "dc": {"analise": "...", "recomendacao": "...", "referencia_pedro_demo": "citação ou conceito de Pedro Demo"},
    "es": {"analise": "...", "recomendacao": "...", "referencia_pedro_demo": "..."},
    "me": {"analise": "...", "recomendacao": "...", "referencia_pedro_demo": "..."},
    "md": {"analise": "...", "recomendacao": "..."},
    "gs": {"analise": "...", "recomendacao": "..."},
    "mc": {"analise": "...", "recomendacao": "..."}
  },
  "sugestoes_formativas": ["sugestão 1 embasada em literatura", "sugestão 2"],
  "encaminhamentos": ["encaminhamento 1 concreto", "encaminhamento 2"],
  "proximos_passos": ["ação 1", "ação 2", "ação 3"],
  "score_estimado": {"dc": 75, "es": 80, "me": 65, "md": 70, "gs": 85, "mc": 70, "total": 74},
  "analise_historica": "Referência à evolução em observações anteriores (vazio se primeira observação)",
  "reconhecimento_avancos": ["progresso 1", "progresso 2"],
  "padroes_identificados": ["padrão recorrente 1", "padrão recorrente 2"]
}"""


def generate_ef1_feedback(obs, teacher, history_obs: List,
                           action_results=None, best_practices=None) -> dict:
    ef1_sections_text = []
    for dom, criteria in EF1_SECTION_CRITERIA.items():
        dom_lines = [f"\n{EF1_DOMAIN_NAMES[dom]}:"]
        for field, label in criteria:
            val = getattr(obs, field, None)
            dom_lines.append(f"  - {label}: {RATING_LABELS.get(val, 'Não informado')}")
        ef1_sections_text.append("\n".join(dom_lines))

    sugestoes_section = ""
    if obs.ef1_sugestoes:
        sugestoes_section = f"\nSugestões do PEC: {obs.ef1_sugestoes}"

    enc_section = ""
    if obs.ef1_encaminhamentos:
        try:
            encs = json.loads(obs.ef1_encaminhamentos)
            if encs:
                enc_text = "\n".join(
                    f"  - {e.get('encaminhamento', '')} [{e.get('responsible', '')}] até {e.get('deadline', 'sem prazo')}"
                    for e in encs
                )
                enc_section = f"\nEncaminhamentos registrados:\n{enc_text}"
        except Exception:
            enc_section = f"\nEncaminhamentos: {obs.ef1_encaminhamentos}"

    teacher_section = ""
    if obs.teacher_feeling or obs.teacher_commitment:
        teacher_section = "\n\n=== PERSPECTIVA DO PROFESSOR ==="
        if obs.teacher_feeling:
            teacher_section += f"\nComo se sentiu: {obs.teacher_feeling}"
        if obs.teacher_commitment:
            teacher_section += f"\nCompromisso: {obs.teacher_commitment}"

    history_section = _build_history_context(history_obs)
    action_section = _build_action_plan_context(action_results or [])
    practices_section = _build_best_practices_context(best_practices or [])

    transcript_section = ""
    if obs.transcript:
        transcript_section = f"\n\n=== TRECHO DA TRANSCRIÇÃO DA AULA ===\n{obs.transcript[:3000]}"

    prompt = f"""=== DADOS DA OBSERVAÇÃO – ENSINO FUNDAMENTAL I ===
Professor(a): {teacher.name}
Escola: {teacher.school or 'Não informado'}
Componente Curricular: {teacher.subject or 'Não informado'} | Ano/Série: {teacher.grade or 'Não informado'}
Data da observação: {obs.observed_at.strftime('%d/%m/%Y') if obs.observed_at else 'Não informado'}
PEC responsável: {obs.pec_name or 'Não informado'}

=== AVALIAÇÃO POR DOMÍNIO (FICHA EF I) ===
{"".join(ef1_sections_text)}
{sugestoes_section}
{enc_section}
{teacher_section}
{transcript_section}
{history_section}
{action_section}
{practices_section}

Gere o feedback completo em JSON para professor do Ensino Fundamental I,
embasado nas referências de Pedro Demo e nas diretrizes da BNCC e Currículo Paulista.

Formato esperado de resposta:
{EF1_RESPONSE_FORMAT}"""

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "system": EF1_FEEDBACK_SYSTEM,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "num_ctx": 8192},
        },
        timeout=180,
    )
    response.raise_for_status()
    raw = response.json().get("response", "{}")
    return json.loads(raw)


# ─── CNV ─────────────────────────────────────────────────────────────────────
CNV_SYSTEM = """Você é especialista em Comunicação Não-Violenta (CNV) aplicada à formação docente,
seguindo o modelo de Marshall Rosenberg. Para cada pergunta do PEC, gere um roteiro de feedback
rigorosamente estruturado nos 4 componentes CNV:
1. OBSERVAÇÃO: O que foi visto objetivamente, sem julgamento ou interpretação
2. SENTIMENTO: Como o PEC se sente em relação ao observado
3. NECESSIDADE: Qual necessidade pedagógica está por trás
4. PEDIDO: Ação específica, realizável e positiva para o professor tentar na próxima aula
Tom: empático, respeitoso, formativo. Responda APENAS com JSON válido."""

CNV_RESPONSE_FORMAT = """{
  "cnv_script": [
    {
      "pergunta": "pergunta do PEC",
      "observacao": "Durante a aula de [data], observei que...",
      "sentimento": "Sinto-me [sentimento] quando...",
      "necessidade": "Porque para mim é importante que... / Porque acredito que os alunos precisam de...",
      "pedido": "Você estaria disposto a, na próxima aula, [ação específica]?"
    }
  ],
  "opening_script": "Texto de abertura da conversa (2-3 frases, acolhedor e respeitoso)",
  "closing_script": "Texto de encerramento com reconhecimento e encorajamento (2-3 frases)"
}"""


def generate_cnv(obs, teacher, questions: List[str]) -> dict:
    context = f"""Contexto da observação:
Professor(a): {teacher.name} | Componente: {teacher.subject} | Ano/Série: {teacher.grade}
Data: {obs.observed_at.strftime('%d/%m/%Y') if obs.observed_at else 'N/A'}

Pontos fortes observados: {obs.pontos_fortes or 'Não informado'}
Focos de desenvolvimento: {obs.focos_desenvolvimento or 'Não informado'}

Respostas do professor:
Como se sentiu: {obs.teacher_feeling or 'Não informado'}
Expectativas: {obs.teacher_expectations or 'Não informado'}

Perguntas que o PEC precisa responder na devolutiva:
{chr(10).join(f"- {q}" for q in questions)}

Formato esperado:
{CNV_RESPONSE_FORMAT}"""

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": MODEL,
            "prompt": context,
            "system": CNV_SYSTEM,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.4, "num_ctx": 4096},
        },
        timeout=120,
    )
    response.raise_for_status()
    raw = response.json().get("response", "{}")
    return json.loads(raw)


def check_ollama_status() -> dict:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return {"status": "ok", "models": models}
    except Exception as e:
        return {"status": "error", "message": str(e), "models": []}
