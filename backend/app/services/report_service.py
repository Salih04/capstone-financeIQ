"""
report_service.py
─────────────────
Generates CSV, JSON, and PDF export files for a completed score run.

External dependencies:
  - reportlab  (PDF)
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.scoring import ScoreRun


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_run_or_404(db: Session, run_id: int) -> ScoreRun:
    run = db.get(ScoreRun, run_id)
    if not run:
        raise ValueError(f"ScoreRun {run_id} not found.")
    return run


def _run_to_dict(run: ScoreRun, db: Session | None = None) -> dict:
    ticker = None
    company_name = None
    if db is not None:
        company = db.get(Company, run.company_id)
        if company:
            ticker = company.ticker
            company_name = company.company_name
    return {
        "score_run_id": run.id,
        "company_id": run.company_id,
        "ticker": ticker,
        "company_name": company_name,
        "period": run.period,
        "model_name": run.model_name,
        "total_score": run.total_score,
        "success_probability": run.success_probability,
        "label_used": getattr(run, "label_used", None),
        "explanation_summary": getattr(run, "explanation_summary", None),
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "details": [
            {
                "metric_name": d.metric_name,
                "metric_value": d.metric_value,
                "normalized_value": getattr(d, "normalized_value", None),
                "weight": d.weight,
                "contribution": d.contribution,
                "comment": d.comment,
            }
            for d in (run.details or [])
        ],
    }


def _generate_ai_commentary(data: dict) -> str:
    """Generate a plain-text AI commentary paragraph based on score run results."""
    lines = []
    score = data.get("total_score") or 0
    prob = data.get("success_probability") or 0
    ticker = data.get("ticker") or f"Company #{data.get('company_id')}"
    period = data.get("period") or "N/A"
    details = data.get("details") or []

    # Overall verdict
    if score >= 75:
        lines.append(
            f"{ticker} achieved a strong score of {score:.1f}/100 for period {period}, "
            "reflecting solid financial fundamentals across the evaluated dimensions."
        )
    elif score >= 50:
        lines.append(
            f"{ticker} recorded a moderate score of {score:.1f}/100 for period {period}. "
            "Results are mixed — some metrics perform well while others require attention."
        )
    else:
        lines.append(
            f"{ticker} scored {score:.1f}/100 for period {period}, indicating significant "
            "financial challenges that may warrant closer monitoring or remediation."
        )

    # Success probability
    if prob >= 0.7:
        lines.append(
            f"The model estimates a high success probability of {prob * 100:.1f}%, "
            "suggesting the company is well-positioned for near-term operational success."
        )
    elif prob < 0.4:
        lines.append(
            f"A low success probability of {prob * 100:.1f}% signals elevated risk. "
            "Key areas such as liquidity and debt coverage should be closely reviewed."
        )

    # Top positive and negative contributors
    if details:
        sorted_details = sorted(details, key=lambda d: d.get("contribution") or 0, reverse=True)
        best = sorted_details[0]
        worst = sorted_details[-1]
        if (best.get("contribution") or 0) > 3:
            lines.append(
                f"The strongest contributor to this score was '{best['metric_name']}' "
                f"(+{best['contribution']:.1f} pts), reflecting a competitive advantage in this area."
            )
        if (worst.get("contribution") or 0) < -2:
            lines.append(
                f"The biggest drag was '{worst['metric_name']}' "
                f"({worst['contribution']:.1f} pts). Improving this metric could meaningfully "
                "boost the overall rating."
            )

    # Explanation summary from engine
    explanation = data.get("explanation_summary")
    if explanation:
        lines.append(explanation)

    return " ".join(lines)


# ── CSV ───────────────────────────────────────────────────────────────────────

def generate_csv(db: Session, run_id: int) -> bytes:
    """
    Return the score run's detail rows as well-structured CSV bytes.

    utf-8-sig is used so Excel opens Turkish characters correctly.
    """
    run = _get_run_or_404(db, run_id)
    data = _run_to_dict(run, db)

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # ── Section 1: Report Header ──────────────────────────────────────────────
    writer.writerow(["STOCK SCORE REPORT"])
    writer.writerow(["Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")])
    writer.writerow([])

    # ── Section 2: Summary ────────────────────────────────────────────────────
    writer.writerow(["Field", "Value"])
    summary_rows = [
        ("Run ID",              data["score_run_id"]),
        ("Company",             data["ticker"] or f"ID:{data['company_id']}"),
        ("Company Name",        data["company_name"] or ""),
        ("Period",              data["period"]),
        ("Scoring Model",       data["model_name"]),
        ("Total Score (/100)",  f"{data['total_score']:.2f}" if data["total_score"] is not None else "N/A"),
        ("Success Probability", f"{data['success_probability'] * 100:.1f}%" if data["success_probability"] is not None else "N/A"),
        ("Scoring Mode",        data["label_used"] or "rule_based"),
        ("Created At",          data["created_at"]),
    ]
    for label, value in summary_rows:
        writer.writerow([label, value])
    writer.writerow([])

    # ── Section 3: AI Commentary ──────────────────────────────────────────────
    commentary = _generate_ai_commentary(data)
    if commentary:
        writer.writerow(["AI Commentary"])
        writer.writerow([commentary])
        writer.writerow([])

    # ── Section 4: Metric Breakdown ───────────────────────────────────────────
    writer.writerow(["METRIC BREAKDOWN"])
    writer.writerow(["Metric Name", "Raw Value", "Normalised Value", "Weight", "Contribution (pts)", "Comment"])
    for d in data["details"]:
        raw   = f"{d['metric_value']:.6f}" if d["metric_value"] is not None else "—"
        norm  = f"{d['normalized_value']:.6f}" if d["normalized_value"] is not None else "—"
        wt    = f"{d['weight']:.4f}" if d["weight"] is not None else "—"
        contr = f"{d['contribution']:+.2f}" if d["contribution"] is not None else "—"
        writer.writerow([
            d["metric_name"],
            raw,
            norm,
            wt,
            contr,
            d["comment"] or "",
        ])

    # Excel compatibility for Turkish chars
    return output.getvalue().encode("utf-8-sig")


# ── JSON ──────────────────────────────────────────────────────────────────────

def generate_json(db: Session, run_id: int) -> bytes:
    """Return the full score run as pretty-printed JSON bytes."""
    run = _get_run_or_404(db, run_id)
    data = _run_to_dict(run, db)
    data["ai_commentary"] = _generate_ai_commentary(data)
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


# ── PDF ───────────────────────────────────────────────────────────────────────

# Built-in ReportLab fonts used — no external TTF files required.
_FONT_NORMAL = "Helvetica"
_FONT_BOLD   = "Helvetica-Bold"


def generate_pdf(db: Session, run_id: int) -> bytes:
    """Return a styled PDF report as bytes (uses reportlab)."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError as exc:
        raise RuntimeError("reportlab is not installed. Add it to requirements.txt.") from exc

    run = _get_run_or_404(db, run_id)
    data = _run_to_dict(run, db)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    styles["Normal"].fontName  = _FONT_NORMAL
    styles["Title"].fontName   = _FONT_BOLD
    styles["Heading2"].fontName = _FONT_BOLD

    normal_style  = styles["Normal"]
    title_style   = styles["Title"]
    heading_style = styles["Heading2"]

    commentary_style = ParagraphStyle(
        "Commentary",
        parent=normal_style,
        fontName=_FONT_NORMAL,
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#1e3a5f"),
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=normal_style,
        fontName=_FONT_NORMAL,
        fontSize=8,
        leading=10,
    )

    story = []

    # Title
    company_label = data.get("ticker") or f"Company #{data['company_id']}"
    if data.get("company_name"):
        company_label = f"{data['ticker']} – {data['company_name']}" if data.get("ticker") else data["company_name"]

    story.append(Paragraph(
        f"<b>Stock Score Report</b> – {company_label}",
        title_style,
    ))
    story.append(Spacer(1, 0.4 * cm))

    # Summary table
    summary_data = [
        [
            Paragraph("<b>Field</b>", table_cell_style),
            Paragraph("<b>Value</b>", table_cell_style),
        ],
        [Paragraph("Company (Ticker)", table_cell_style), Paragraph(str(data.get("ticker") or data["company_id"]), table_cell_style)],
        [Paragraph("Company Name", table_cell_style), Paragraph(str(data.get("company_name") or ""), table_cell_style)],
        [Paragraph("Period", table_cell_style), Paragraph(str(data["period"] or ""), table_cell_style)],
        [Paragraph("Model", table_cell_style), Paragraph(str(data["model_name"] or ""), table_cell_style)],
        [
            Paragraph("Total Score", table_cell_style),
            Paragraph(f"{data['total_score']:.2f} / 100" if data["total_score"] is not None else "N/A", table_cell_style),
        ],
        [
            Paragraph("Success Probability", table_cell_style),
            Paragraph(f"{data['success_probability'] * 100:.1f}%" if data["success_probability"] is not None else "N/A", table_cell_style),
        ],
        [
            Paragraph("Scoring Mode", table_cell_style),
            Paragraph(str(data["label_used"] or "rule_based"), table_cell_style),
        ],
        [
            Paragraph("Generated At", table_cell_style),
            Paragraph(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), table_cell_style),
        ],
    ]

    t = Table(summary_data, colWidths=[5 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), _FONT_BOLD),
        ("FONTNAME",     (0, 1), (-1, -1), _FONT_NORMAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Explanation
    if data["explanation_summary"]:
        story.append(Paragraph(
            f"<b>Analysis:</b> {data['explanation_summary']}",
            normal_style,
        ))
        story.append(Spacer(1, 0.4 * cm))

    # AI Commentary
    commentary = _generate_ai_commentary(data)
    if commentary:
        story.append(Paragraph("<b>AI Commentary</b>", heading_style))
        story.append(Spacer(1, 0.2 * cm))
        # Draw a light blue background box via a single-cell table
        commentary_tbl = Table(
            [[Paragraph(commentary, commentary_style)]],
            colWidths=[17 * cm],
        )
        commentary_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), colors.HexColor("#edf2ff")),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#2563eb")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",(0, 0), (-1, -1), 10),
            ("TOPPADDING",  (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(commentary_tbl)
        story.append(Spacer(1, 0.5 * cm))

    # Detail breakdown
    if data["details"]:
        story.append(Paragraph("<b>Metric Breakdown</b>", heading_style))
        story.append(Spacer(1, 0.2 * cm))

        rows = [[
            Paragraph("<b>Metric</b>", table_cell_style),
            Paragraph("<b>Value</b>", table_cell_style),
            Paragraph("<b>Normalised</b>", table_cell_style),
            Paragraph("<b>Weight</b>", table_cell_style),
            Paragraph("<b>Contribution</b>", table_cell_style),
            Paragraph("<b>Comment</b>", table_cell_style),
        ]]

        for d in data["details"]:
            rows.append([
                Paragraph(str(d["metric_name"] or ""), table_cell_style),
                Paragraph(f"{d['metric_value']:.4f}" if d["metric_value"] is not None else "–", table_cell_style),
                Paragraph(f"{d['normalized_value']:.4f}" if d["normalized_value"] is not None else "–", table_cell_style),
                Paragraph(f"{d['weight']:.2f}" if d["weight"] is not None else "–", table_cell_style),
                Paragraph(f"{d['contribution']:.2f}" if d["contribution"] is not None else "–", table_cell_style),
                Paragraph(str((d["comment"] or "")[:200]), table_cell_style),
            ])

        detail_tbl = Table(
            rows,
            colWidths=[4 * cm, 2 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm, 4.8 * cm],
            repeatRows=1,
        )
        detail_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME",     (0, 1), (-1, -1), _FONT_NORMAL),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf2ff")]),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(detail_tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()