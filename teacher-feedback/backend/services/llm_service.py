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


def compute_section_scores(obs) -> dict:
    scores = {}
    for sec, criteria in SECTION_CRITERIA.items():
        vals = [RATING_SCORE[getattr(obs, field, None)] for field, _ in criteria]
        scores[sec] = round(sum(vals) / len(vals)) if vals else 0
    scores["total"] = round(sum(scores[s] for s in ["s1", "s2", "s3", "s4", "s5"]) / 5)
    return scores


def _build_history_context(history_obs: List) -> str:
    if not history_obs:
        return ""
    lines = ["\n=== HISTÓRICO DAS ÚLTIMAS OBSERVAÇÕES ==="]
    for h in history_obs:
        scores = compute_section_scores(h)
        lines.append(f"\nObservação de {h.observed_at.strftime('%d/%m/%Y')}:")
        lines.append(f"  Scores: S1={scores['s1']} S2={scores['s2']} S3={scores['s3']} S4={scores['s4']} S5={scores['s5']} Total={scores['total']}")
        if h.feedback_raw:
            try:
                fb = json.loads(h.feedback_raw)
                if fb.get("pontos_fortes"):
                    lines.append(f"  Pontos fortes anteriores: {'; '.join(fb['pontos_fortes'][:2])}")
                if fb.get("areas_desenvolvimento"):
                    areas = [a.get("area", "") for a in fb["areas_desenvolvimento"][:2]]
                    lines.append(f"  Áreas de desenvolvimento anteriores: {'; '.join(areas)}")
            except Exception:
                pass
        if h.combined_actions:
            try:
                actions = json.loads(h.combined_actions)
                if actions:
                    lines.append(f"  Combinados anteriores: {'; '.join(str(a) for a in actions[:2])}")
            except Exception:
                pass
    return "\n".join(lines)


def _build_observation_prompt(obs, teacher, history_obs: List, transcript_excerpt: Optional[str]) -> str:
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

=== AVALIAÇÃO POR SEÇÃO ===
{"".join(sections_text)}
{methodologies}

=== NARRATIVA DO PEC ===
{pontos}
{focos}
Sugestões do PEC: {obs.sugestoes or 'Não informado'}
{teacher_section}
{transcript_section}
{history_section}

Gere o feedback completo em JSON com TODOS os campos solicitados, em português, no contexto da educação pública do Estado de São Paulo."""


FEEDBACK_SYSTEM = """Você é um Professor Especialista em Currículo (PEC) da Secretaria da Educação do Estado de São Paulo.
Sua função é fornecer devolutivas formativas construtivas e detalhadas baseadas nas observações de aula registradas,
seguindo as diretrizes do Currículo Paulista e da BNCC. Você deve referenciar o histórico do professor para
identificar padrões, reconhecer avanços e personalizar as recomendações.
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
  "analise_historica": "Parágrafo referenciando evolução em relação às observações anteriores (ou vazio se primeira observação)",
  "reconhecimento_avancos": ["progresso identificado 1", "progresso identificado 2"],
  "padroes_identificados": ["padrão recorrente 1", "padrão recorrente 2"],
  "alinhamento_bncc": "Análise do alinhamento com as habilidades BNCC informadas"
}"""


def generate_feedback(obs, teacher, history_obs: List) -> dict:
    transcript_excerpt = None
    if obs.transcript:
        transcript_excerpt = obs.transcript[:3000]
    elif obs.media_file_id:
        # transcript may be on media file - caller should pass it
        pass

    prompt = _build_observation_prompt(obs, teacher, history_obs, transcript_excerpt)
    full_prompt = f"{prompt}\n\nFormato esperado de resposta:\n{FEEDBACK_RESPONSE_FORMAT}"

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": MODEL,
            "prompt": full_prompt,
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


CNV_SYSTEM = """Você é especialista em Comunicação Não-Violenta (CNV) aplicada à formação docente,
seguindo o modelo de Marshall Rosenberg. Para cada pergunta do PEC, gere um roteiro de feedback
rigorosamente estruturado nos 4 componentes CNV:
1. OBSERVAÇÃO: O que foi visto objetivamente, sem julgamento ou interpretação
2. SENTIMENTO: Como o PEC se sente em relação ao observado (ex: preocupado, esperançoso, admirado)
3. NECESSIDADE: Qual necessidade pedagógica está por trás (ex: aprendizagem dos alunos, clareza curricular)
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
