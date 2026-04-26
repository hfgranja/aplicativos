"""ReportLab PDF generator for PEC observation feedback reports."""
import hashlib
import io
from datetime import datetime
from typing import Optional


def _safe(val, default="—") -> str:
    if val is None:
        return default
    return str(val)


def generate_feedback_pdf(
    observation_id: str,
    school_name: str,
    teacher_name: str,
    subject: str,
    grade: str,
    lesson_theme: str,
    observed_at: Optional[str],
    summary: Optional[str],
    strengths: Optional[list],
    improvement_points: Optional[list],
    evidence: Optional[list],
    action_plan: Optional[list],
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=14, spaceAfter=6)
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"], fontSize=11,
                                   textColor=colors.HexColor("#1a365d"), spaceAfter=4)
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, spaceAfter=4)
    label_style = ParagraphStyle("label", parent=styles["Normal"], fontSize=8,
                                  textColor=colors.grey)

    story = []

    # Header
    story.append(Paragraph("SECRETARIA DA EDUCAÇÃO DO ESTADO DE SÃO PAULO", label_style))
    story.append(Paragraph("Relatório de Observação Pedagógica", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a365d")))
    story.append(Spacer(1, 0.3 * cm))

    # Observation details table
    details = [
        ["Escola:", _safe(school_name), "Data:", _safe(observed_at, datetime.utcnow().strftime("%d/%m/%Y"))],
        ["Professor(a):", _safe(teacher_name), "Componente:", _safe(subject)],
        ["Série/Ano:", _safe(grade), "Tema da Aula:", _safe(lesson_theme)],
        ["ID Observação:", observation_id, "", ""],
    ]
    t = Table(details, colWidths=[3 * cm, 7 * cm, 3 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    # Summary
    if summary:
        story.append(Paragraph("Síntese da Observação", heading_style))
        story.append(Paragraph(_safe(summary), body_style))
        story.append(Spacer(1, 0.3 * cm))

    # Strengths
    if strengths:
        story.append(Paragraph("Pontos Fortes", heading_style))
        for item in strengths:
            if isinstance(item, dict):
                story.append(Paragraph(f"<b>{_safe(item.get('title'))}</b>: {_safe(item.get('description'))}", body_style))
                if item.get("evidence"):
                    story.append(Paragraph(f"<i>Evidência: \"{_safe(item.get('evidence'))}\"</i>", label_style))
            else:
                story.append(Paragraph(f"• {_safe(item)}", body_style))
        story.append(Spacer(1, 0.3 * cm))

    # Improvement points
    if improvement_points:
        story.append(Paragraph("Pontos de Desenvolvimento", heading_style))
        for item in improvement_points:
            if isinstance(item, dict):
                story.append(Paragraph(f"<b>{_safe(item.get('title'))}</b>: {_safe(item.get('description'))}", body_style))
                if item.get("evidence"):
                    story.append(Paragraph(f"<i>Evidência: \"{_safe(item.get('evidence'))}\"</i>", label_style))
            else:
                story.append(Paragraph(f"• {_safe(item)}", body_style))
        story.append(Spacer(1, 0.3 * cm))

    # Action plan
    if action_plan:
        story.append(Paragraph("Plano de Ação — Combinados", heading_style))
        ap_data = [["Ação", "Responsável", "Prazo", "Evidência Esperada"]]
        for ap in action_plan:
            if isinstance(ap, dict):
                ap_data.append([
                    _safe(ap.get("action") or ap.get("description")),
                    _safe(ap.get("owner")),
                    _safe(ap.get("due_date") or ap.get("due_date_suggestion")),
                    _safe(ap.get("expected_evidence")),
                ])
        if len(ap_data) > 1:
            at = Table(ap_data, colWidths=[7 * cm, 3 * cm, 2.5 * cm, 4.5 * cm])
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(at)

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        f"Documento gerado em {datetime.utcnow().strftime('%d/%m/%Y às %H:%M UTC')} | "
        f"ID: {observation_id}",
        label_style,
    ))

    doc.build(story)
    return buf.getvalue()


def compute_hash(pdf_bytes: bytes) -> str:
    return hashlib.sha256(pdf_bytes).hexdigest()
