"""Gera o relatório HTML de um lote (resultado do analyze_folder).

É uma página única, sem arquivos externos, para abrir no navegador. Todo texto
que vem de currículo ou da IA passa por html.escape: o texto de um currículo
é dado não confiável e não pode virar HTML da página.
"""
from datetime import datetime
from html import escape

STATUS_LABELS = {
    "ok": "OK",
    "attention": "Atenção",
    "not_analyzed": "Não analisado",
    "error": "Erro",
}

# Status que ninguém leu de verdade. No Python eles seguem separados
# (not_analyzed = a IA falhou; error = o PDF não abriu), mas na página os dois
# aparecem juntos, na pilha "Não analisados".
UNREAD_STATUSES = ("not_analyzed", "error")

REASON_LABELS = {
    "tiny_font": "fonte minúscula",
    "near_white_text": "texto quase branco",
    "off_page": "fora da página",
}

CATEGORY_LABELS = {
    "instruction_override": "tentativa de sobrescrever instruções",
    "hiring_manipulation": "manipulação da avaliação",
}

RISK_LABELS = {
    "none": "nenhum",
    "low": "baixo",
    "medium": "médio",
    "high": "alto",
    "not_reviewed": "IA não leu",
    "unknown": "IA falhou",
}

CSS = """
:root { --bg:#f6f7f9; --card:#fff; --text:#1d2330; --muted:#5d6678;
  --line:#dfe3ea; --ok:#1c7a3d; --attention:#b45309; --error:#b42318;
  --na:#3f5273;
  --ok-bg:#e6f4ea; --attention-bg:#fdf0dc; --error-bg:#fde8e6;
  --na-bg:#e6ebf4; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#14171d; --card:#1d222b; --text:#e8ebf1; --muted:#9aa4b5;
    --line:#2f3643; --ok:#5fcf86; --attention:#f2b25c; --error:#f08a80;
    --na:#a9b8d4;
    --ok-bg:#183425; --attention-bg:#3a2b12; --error-bg:#3d1c19;
    --na-bg:#262e3d; } }
* { box-sizing:border-box; }
body { margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--text);
  font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:960px; margin:0 auto; }
h1 { font-size:1.6rem; margin:0 0 4px; }
h2 { font-size:1.15rem; margin:32px 0 12px; }
.muted { color:var(--muted); font-size:.9rem; }
.summary { display:flex; flex-wrap:wrap; gap:12px; margin:20px 0; }
.stat { background:var(--card); border:1px solid var(--line); border-radius:10px;
  padding:12px 18px; min-width:120px; }
.stat b { display:block; font-size:1.7rem; line-height:1.2; }
.table-wrap { overflow-x:auto; background:var(--card); border:1px solid var(--line);
  border-radius:10px; }
table { border-collapse:collapse; width:100%; }
th, td { text-align:left; padding:10px 14px; border-bottom:1px solid var(--line);
  vertical-align:top; }
th { font-size:.8rem; text-transform:uppercase; letter-spacing:.04em;
  color:var(--muted); }
tr:last-child td { border-bottom:0; }
.badge { display:inline-block; padding:2px 10px; border-radius:999px;
  font-size:.85rem; font-weight:600; }
.badge.ok { color:var(--ok); background:var(--ok-bg); }
.badge.attention { color:var(--attention); background:var(--attention-bg); }
.badge.error { color:var(--error); background:var(--error-bg); }
.badge.not_analyzed { color:var(--na); background:var(--na-bg); }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px;
  padding:16px 18px; margin-bottom:16px; }
.card h3 { margin:0 0 4px; font-size:1.05rem; overflow-wrap:anywhere; }
.card h4 { margin:16px 0 6px; font-size:.85rem; text-transform:uppercase;
  letter-spacing:.04em; color:var(--muted); }
blockquote { margin:6px 0; padding:8px 12px; border-left:4px solid var(--attention);
  background:var(--attention-bg); overflow-wrap:anywhere; white-space:pre-wrap; }
.warn { color:var(--error); font-weight:600; }
ul { margin:6px 0; padding-left:20px; }
li { overflow-wrap:anywhere; }
.reason { overflow-wrap:anywhere; }
.note { margin-top:32px; }
"""


def esc(value):
    """Escapa qualquer valor para ir dentro do HTML."""
    return escape("" if value is None else str(value), quote=True)


def badge(status):
    label = STATUS_LABELS.get(status, status)
    return f'<span class="badge {esc(status)}">{esc(label)}</span>'


def risk_text(risk_level):
    if risk_level is None:
        return "—"
    return RISK_LABELS.get(risk_level, str(risk_level))


def unread_count(summary):
    """Quantos PDFs ninguém leu: not_analyzed (IA falhou) + error (PDF quebrado).

    Usa .get para aceitar um resumo antigo, sem o contador not_analyzed.
    """
    return summary.get("not_analyzed", 0) + summary.get("error", 0)


def render_summary(summary):
    # OK + Atenção + Não analisados = Total, para a soma fechar.
    stats = [
        ("Total", summary["total"]),
        ("OK", summary["ok"]),
        ("Atenção", summary["attention"]),
        ("Não analisados", unread_count(summary)),
    ]
    cells = "".join(
        f'<div class="stat"><b>{esc(number)}</b>{esc(label)}</div>'
        for label, number in stats
    )
    return f'<div class="summary">{cells}</div>'


def render_table(results):
    if not results:
        return '<p class="muted">Nenhum PDF encontrado na pasta.</p>'

    rows = []
    for row in results:
        if row["status"] == "error":
            findings, risk = "—", "—"
        else:
            findings = esc(row["finding_count"])
            risk = esc(risk_text(row.get("risk_level")))
        rows.append(
            f"<tr><td>{esc(row['file'])}</td><td>{badge(row['status'])}</td>"
            f"<td>{findings}</td><td>{risk}</td></tr>"
        )

    return (
        '<div class="table-wrap"><table><thead><tr>'
        "<th>Arquivo</th><th>Status</th><th>Achados</th><th>Risco (IA)</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def collect_hidden_text(findings):
    """Junta os trechos escondidos de todos os achados hidden_text.

    O mesmo trecho costuma cair em mais de um motivo (fonte minúscula e texto
    quase branco, por exemplo). Para a pessoa ler a mensagem uma vez só, o
    trecho aparece uma vez, com todos os motivos juntos.
    """
    merged = {}
    total_not_listed = 0

    for finding in findings:
        if finding.get("category") != "hidden_text":
            continue
        reason = REASON_LABELS.get(finding.get("pattern"), finding.get("pattern"))
        listed = finding.get("fragments", [])
        total_not_listed += max(finding.get("fragment_count", 0) - len(listed), 0)

        for fragment in listed:
            key = (finding.get("page"), fragment["text"], fragment["x"], fragment["y"])
            entry = merged.setdefault(
                key, {"page": finding.get("page"), "fragment": fragment, "reasons": []}
            )
            if reason not in entry["reasons"]:
                entry["reasons"].append(reason)

    return list(merged.values()), total_not_listed


def render_hidden_text(findings):
    entries, not_listed = collect_hidden_text(findings)
    if not entries:
        return ""

    items = []
    for entry in entries:
        reasons = ", ".join(entry["reasons"])
        items.append(
            f"<li>{esc(entry['fragment']['text'])}"
            f'<br><span class="muted">página {esc(entry["page"])} · {esc(reasons)}'
            f"</span></li>"
        )

    extra = ""
    if not_listed > 0:
        extra = (
            f'<p class="muted">Há mais trechos além dos listados '
            f"(o relatório guarda no máximo 20 por grupo); abra o PDF para ver todos.</p>"
        )

    return f"<h4>Texto escondido no PDF</h4><ul>{''.join(items)}</ul>{extra}"


def render_phrase_findings(findings):
    items = []
    for finding in findings:
        if finding.get("category") == "hidden_text":
            continue
        category = CATEGORY_LABELS.get(finding.get("category"), finding.get("category"))
        items.append(f"<li>{esc(finding.get('pattern'))} <span class=\"muted\">({esc(category)})</span></li>")

    if not items:
        return ""
    return f"<h4>Frases suspeitas encontradas</h4><ul>{''.join(items)}</ul>"


def render_ai(ai_assessment):
    if not ai_assessment:
        return ""

    parts = [
        "<h4>Parecer da IA</h4>",
        f"<p><b>Risco:</b> {esc(risk_text(ai_assessment.get('risk_level')))}</p>",
    ]

    phrase = ai_assessment.get("suspicious_text")
    if phrase:
        parts.append(f"<p><b>Frase suspeita apontada pela IA:</b></p><blockquote>{esc(phrase)}</blockquote>")
        if ai_assessment.get("suspicious_text_found") is False:
            parts.append(
                '<p class="warn">Atenção: a IA citou uma frase que não foi '
                "encontrada no texto do PDF. Confira o currículo antes de "
                "confiar nela.</p>"
            )

    if ai_assessment.get("reasoning"):
        parts.append(f"<p>{esc(ai_assessment['reasoning'])}</p>")
    if ai_assessment.get("recommendation"):
        parts.append(f"<p><b>Sugestão:</b> {esc(ai_assessment['recommendation'])}</p>")
    if ai_assessment.get("text_truncated"):
        parts.append(
            '<p class="muted">O currículo era longo: a IA leu só o começo do texto.</p>'
        )

    return "".join(parts)


def render_attention_card(row):
    report = row["report"]
    body = (
        render_phrase_findings(report["findings"])
        + render_hidden_text(report["findings"])
        + render_ai(report.get("ai_assessment"))
    )
    return (
        f'<section class="card"><h3>{esc(row["file"])} {badge("attention")}</h3>'
        f'<span class="muted">{esc(row["finding_count"])} achado(s) dos detectores</span>'
        f"{body}</section>"
    )


def render_not_analyzed_card(row):
    """Cartão de um currículo que ninguém leu porque a IA falhou.

    O motivo é o "reasoning" que o ai_analysis.py guarda quando a IA falha
    (hoje vem em inglês). É texto não confiável: passa pelo esc.
    """
    ai_assessment = (row.get("report") or {}).get("ai_assessment") or {}
    reason = ai_assessment.get("reasoning") or "Nenhum motivo foi registrado."
    return (
        f'<section class="card"><h3>{esc(row["file"])} {badge("not_analyzed")}</h3>'
        "<p>Os detectores locais não acharam nada neste currículo, mas a IA "
        "não conseguiu lê-lo. Por isso ninguém analisou o conteúdo: abra o "
        "PDF e confira antes de considerar que está sem sinais.</p>"
        f'<p class="reason"><b>Motivo registrado:</b> {esc(reason)}</p>'
        "</section>"
    )


def render_error_card(row):
    return (
        f'<section class="card"><h3>{esc(row["file"])} {badge("error")}</h3>'
        f'<p>Não foi possível analisar este PDF: {esc(row["error"])}</p></section>'
    )


def render_unread_card(row):
    if row["status"] == "not_analyzed":
        return render_not_analyzed_card(row)
    return render_error_card(row)


def render_html(batch, generated_at=None):
    """Monta a página HTML completa de um lote."""
    generated_at = generated_at or datetime.now()
    results = batch["results"]
    summary = batch["summary"]

    attention = [r for r in results if r["status"] == "attention"]
    unread = [r for r in results if r["status"] in UNREAD_STATUSES]

    details = ""
    if attention:
        details += "<h2>Currículos que merecem atenção</h2>"
        details += "".join(render_attention_card(r) for r in attention)
    if unread:
        details += "<h2>Não analisados</h2>"
        details += "".join(render_unread_card(r) for r in unread)

    # "recebidos" e não "analisados": o total inclui PDFs que ninguém leu.
    headline = f"{summary['total']} recebidos, {summary['attention']} sinalizados"
    unread_total = unread_count(summary)
    if unread_total:
        plural = "s" if unread_total > 1 else ""
        headline += f", {unread_total} não analisado{plural}"

    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>CV Shield — relatório do lote</title>"
        f"<style>{CSS}</style></head><body><main>"
        "<h1>CV Shield — relatório do lote</h1>"
        f'<p class="muted">Pasta: {esc(batch["folder"])} · '
        f'gerado em {esc(generated_at.strftime("%d/%m/%Y %H:%M"))}</p>'
        f"<p><b>{esc(headline)}</b></p>"
        f"{render_summary(summary)}"
        "<h2>Todos os currículos</h2>"
        f"{render_table(results)}"
        f"{details}"
        '<p class="muted note">Esta ferramenta aponta sinais para uma pessoa '
        "conferir; ela não decide nada sobre o candidato. “OK” não prova que o "
        "currículo está limpo.</p>"
        "</main></body></html>"
    )


def save_html(batch, output_path):
    """Grava o relatório em um arquivo .html (UTF-8)."""
    with open(output_path, "w", encoding="utf-8") as html_file:
        html_file.write(render_html(batch))
