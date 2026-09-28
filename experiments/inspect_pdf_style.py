import sys

from pypdf import PdfReader


def inspect_pdf_text_style(pdf_path):
    reader = PdfReader(pdf_path)

    for page_number, page in enumerate(reader.pages, start=1):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        print(f"--- Page {page_number} ({page_width:.0f} x {page_height:.0f}) ---")

        state = {"fill_color": None}
        fragments = []

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
                    "text": text.strip(),
                    "size": font_size,
                    "color": state["fill_color"],
                    "x": x,
                    "y": y,
                }
            )

        page.extract_text(
            visitor_operand_before=visitor_operand_before,
            visitor_text=visitor_text,
        )

        for f in fragments:
            off_page = (
                f["x"] < 0
                or f["y"] < 0
                or f["x"] > page_width
                or f["y"] > page_height
            )
            print(
                f"size={f['size']!s:>5} | color={f['color']!s:<22} | "
                f"x={f['x']:7.1f} y={f['y']:7.1f} | off_page={off_page!s:<5} | "
                f"{f['text'][:50]}"
            )


if __name__ == "__main__":
    inspect_pdf_text_style(sys.argv[1])