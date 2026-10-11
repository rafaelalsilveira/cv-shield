from pypdf import PdfReader

# Abaixo desse tamanho (em pontos) o texto é ilegível para um humano.
MIN_VISIBLE_FONT_SIZE = 3.0

# Cada canal RGB igual ou acima disso é considerado "quase branco".
NEAR_WHITE_THRESHOLD = 0.95

# Contraste mínimo (WCAG, texto grande) entre o texto claro e o fundo para
# considerar que um humano consegue ler. Abaixo disso, o texto é suspeito.
MIN_CONTRAST_RATIO = 3.0

# Estimativa da caixa do texto, usada para checar se ele cabe inteiro dentro
# de um retângulo colorido: largura média de um caractere e altura visível,
# ambas como fração do tamanho da fonte.
AVG_CHAR_WIDTH_EM = 0.5
TEXT_HEIGHT_EM = 0.7

# Limites da lista de trechos de cada achado no relatório: quantos trechos
# aparecem e quantos caracteres de cada um. Um PDF malicioso pode ter
# milhares de trechos; sem limite o relatório (e o pedido à IA) explodiria.
MAX_LISTED_FRAGMENTS = 20
MAX_LISTED_TEXT_LENGTH = 200

# Operadores PDF que preenchem o caminho atual.
FILL_OPERATORS = {b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*"}

# Operadores PDF que terminam o caminho sem preencher.
PATH_END_OPERATORS = {b"n", b"S", b"s"}


def color_to_rgb(color):
    """Converte a cor guardada (RGB, cinza ou CMYK) em uma tupla RGB."""
    if color is None:
        return None
    if color[0] == "cmyk":
        c, m, y, k = color[1:]
        return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
    return tuple(color)


def _linearize(channel):
    channel = min(max(channel, 0.0), 1.0)
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
    r, g, b = (_linearize(value) for value in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb_a, rgb_b):
    """Razão de contraste WCAG entre duas cores RGB (1 a 21)."""
    lum_a = relative_luminance(rgb_a)
    lum_b = relative_luminance(rgb_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _rect_bounds(operands, cm):
    """Retângulo do operador "re" no espaço da página: (esquerda, baixo,
    direita, topo). Aplica a matriz atual aos 4 cantos e normaliza altura
    ou largura negativas."""
    x, y, w, h = (float(v) for v in operands)
    a, b, c, d, e, f = (float(v) for v in cm)
    corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    xs = [cx * a + cy * c + e for cx, cy in corners]
    ys = [cx * b + cy * d + f for cx, cy in corners]
    return (min(xs), min(ys), max(xs), max(ys))


def find_background(rects, x, y, text, font_size):
    """Cor de fundo (RGB) atrás do texto, ou None se não for conhecida.

    "rects" são os retângulos preenchidos ATÉ este ponto do PDF, em ordem de
    desenho. Um retângulo desenhado depois do texto o cobriria, não serviria
    de fundo, então só os anteriores contam. Vale o mais recente (o que está
    por cima) que contém o início do texto, e só se a caixa estimada do texto
    couber inteira nele: um retângulo minúsculo escondido no começo do texto
    não pode servir de fundo para o texto todo.
    """
    size = font_size if font_size and font_size > 0 else 0.0
    box_right = x + len(text) * size * AVG_CHAR_WIDTH_EM
    box_top = y + size * TEXT_HEIGHT_EM

    for left, bottom, right, top, rgb in reversed(rects):
        if left <= x <= right and bottom <= y <= top:
            if box_right <= right and box_top <= top:
                return rgb
            return None
    return None


def extract_text_fragments(pdf_path):
    """Extrai cada trecho de texto do PDF com tamanho, cor, posição e a cor
    do fundo colorido atrás dele (quando houver)."""
    reader = PdfReader(pdf_path)
    fragments = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        state = {
            "fill_color": None,
            "color_stack": [],
            "path_rects": [],
            "filled_rects": [],
        }

        def visitor_operand_before(operator, operands, cm, tm):
            # Guarda a última cor de preenchimento definida antes do texto.
            if operator == b"q":
                state["color_stack"].append(state["fill_color"])
            elif operator == b"Q":
                if state["color_stack"]:
                    state["fill_color"] = state["color_stack"].pop()
            elif operator == b"rg":
                state["fill_color"] = tuple(round(float(v), 3) for v in operands)
            elif operator == b"g":
                gray = round(float(operands[0]), 3)
                state["fill_color"] = (gray, gray, gray)
            elif operator == b"k":
                state["fill_color"] = ("cmyk",) + tuple(
                    round(float(v), 3) for v in operands
                )
            # Registra os retângulos preenchidos (faixas e blocos coloridos).
            elif operator == b"re" and len(operands) == 4:
                state["path_rects"].append(_rect_bounds(operands, cm))
            elif operator in FILL_OPERATORS:
                # Sem cor definida, o PDF preenche com preto.
                rgb = color_to_rgb(state["fill_color"]) or (0.0, 0.0, 0.0)
                for bounds in state["path_rects"]:
                    state["filled_rects"].append(bounds + (rgb,))
                state["path_rects"] = []
            elif operator in PATH_END_OPERATORS:
                state["path_rects"] = []

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
                    "background": find_background(
                        state["filled_rects"], x, y, text.strip(), font_size
                    ),
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
        looks_white = all(value <= 1 - NEAR_WHITE_THRESHOLD for value in color[1:])
    else:
        looks_white = all(value >= NEAR_WHITE_THRESHOLD for value in color)
    if not looks_white:
        return False

    # Texto claro sobre um fundo escuro conhecido (faixa de template) é
    # legível. Sem fundo conhecido, vale a regra antiga: suspeito.
    background = fragment.get("background")
    if background is not None:
        if contrast_ratio(color_to_rgb(color), background) >= MIN_CONTRAST_RATIO:
            return False
    return True


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
    com uma linha para cada trecho do mesmo bloco escondido.

    Cada grupo traz "fragment_count" (quantos trechos caíram nele) e
    "fragments" (o texto e a posição de cada um, para o revisor conferir
    um por um). A lista é limitada para o relatório não crescer sem fim,
    mas "fragment_count" sempre mostra o total real."""
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
                        "fragments": [],
                    }
                group = grouped[key]
                group["fragment_count"] += 1
                if len(group["fragments"]) < MAX_LISTED_FRAGMENTS:
                    group["fragments"].append(
                        {
                            "text": fragment["text"][:MAX_LISTED_TEXT_LENGTH],
                            "x": round(fragment["x"], 1),
                            "y": round(fragment["y"], 1),
                        }
                    )

    return list(grouped.values())
