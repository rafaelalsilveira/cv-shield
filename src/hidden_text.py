from pypdf import PdfReader

# Abaixo desse tamanho (em pontos) o texto é ilegível para um humano.
MIN_VISIBLE_FONT_SIZE = 3.0

# Cada canal RGB igual ou acima disso é considerado "quase branco".
NEAR_WHITE_THRESHOLD = 0.95


def extract_text_fragments(pdf_path):
    """Extrai cada trecho de texto do PDF com tamanho, cor e posição."""
    reader = PdfReader(pdf_path)
    fragments = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        state = {"fill_color": None}

        def visitor_operand_before(operator, operands, cm, tm):
            # Guarda a última cor de preenchimento definida antes do texto.
            if operator == b"rg":
                state["fill_color"] = tuple(round(float(v), 3) for v in operands)
            elif operator == b"g":
                gray = round(float(operands[0]), 3)
                state["fill_color"] = (gray, gray, gray)
            elif operator == b"k":
                state["fill_color"] = ("cmyk",) + tuple(
                    round(float(v), 3) for v in operands
                )

        def visitor_text(text, cm, tm, font_dict, font_size):
            if not text.strip():
                return
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            fragments.append(
                {
                    "page": page_number,
                    "text": text.strip(),
                    "size": font_size,
                    "color": state["fill_color"],
                    "x": x,
                    "y": y,
                    "page_width": page_width,
                    "page_height": page_height,
                }
            )

        page.extract_text(
            visitor_operand_before=visitor_operand_before,
            visitor_text=visitor_text,
        )

    return fragments


def is_tiny_font(fragment):
    size = fragment.get("size")
    return size is not None and 0 < size < MIN_VISIBLE_FONT_SIZE


def is_near_white(fragment):
    color = fragment.get("color")
    if color is None:
        return False  # Nenhuma cor definida: o PDF usa preto por padrão.
    if color[0] == "cmyk":
        return all(value <= 1 - NEAR_WHITE_THRESHOLD for value in color[1:])
    return all(value >= NEAR_WHITE_THRESHOLD for value in color)


def is_off_page(fragment):
    return (
        fragment["x"] < 0
        or fragment["y"] < 0
        or fragment["x"] > fragment["page_width"]
        or fragment["y"] > fragment["page_height"]
    )


HIDDEN_TEXT_CHECKS = {
    "tiny_font": is_tiny_font,
    "near_white_text": is_near_white,
    "off_page": is_off_page,
}


def find_hidden_text(fragments):
    """Agrupa os achados por (página, motivo) para o relatório não ficar
    com uma linha para cada trecho do mesmo bloco escondido."""
    grouped = {}

    for fragment in fragments:
        for reason, check in HIDDEN_TEXT_CHECKS.items():
            if check(fragment):
                key = (fragment["page"], reason)
                if key not in grouped:
                    grouped[key] = {
                        "category": "hidden_text",
                        "pattern": reason,
                        "page": fragment["page"],
                        "fragment_count": 0,
                        "text_preview": fragment["text"][:60],
                    }
                grouped[key]["fragment_count"] += 1

    return list(grouped.values())