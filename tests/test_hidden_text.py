import unittest
from pathlib import Path

from src.hidden_text import (
    MAX_LISTED_FRAGMENTS,
    MAX_LISTED_TEXT_LENGTH,
    extract_text_fragments,
    find_hidden_text,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def make_fragment(**overrides):
    fragment = {
        "page": 1,
        "text": "Experienced backend engineer",
        "size": 10.0,
        "color": (0.0, 0.0, 0.0),
        "x": 70.0,
        "y": 400.0,
        "page_width": 612.0,
        "page_height": 792.0,
    }
    fragment.update(overrides)
    return fragment


def reasons(findings):
    return [finding["pattern"] for finding in findings]


class TestHiddenText(unittest.TestCase):

    def test_normal_text_has_no_findings(self):
        self.assertEqual(find_hidden_text([make_fragment()]), [])

    def test_detects_tiny_font(self):
        findings = find_hidden_text([make_fragment(size=1.0)])

        self.assertIn("tiny_font", reasons(findings))

    def test_detects_pure_white_text(self):
        findings = find_hidden_text([make_fragment(color=(1.0, 1.0, 1.0))])

        self.assertIn("near_white_text", reasons(findings))

    def test_detects_near_white_text_at_readable_size(self):
        # Caso do CV Bru.pdf: cor #FFFFFE, 6pt, dentro da página.
        findings = find_hidden_text(
            [make_fragment(size=6.0, color=(1.0, 1.0, 0.996))]
        )

        self.assertEqual(reasons(findings), ["near_white_text"])

    def test_detects_off_page_text_even_when_black_and_readable(self):
        # Caso do Cv curri.pdf: preto, 8pt, acima do topo da página.
        findings = find_hidden_text(
            [make_fragment(size=8.0, y=842.0)]
        )

        self.assertEqual(reasons(findings), ["off_page"])

    def test_detects_white_text_in_cmyk(self):
        findings = find_hidden_text(
            [make_fragment(color=("cmyk", 0.0, 0.0, 0.0, 0.0))]
        )

        self.assertIn("near_white_text", reasons(findings))

    def test_cmyk_black_is_not_flagged(self):
        findings = find_hidden_text(
            [make_fragment(color=("cmyk", 0.0, 0.0, 0.0, 1.0))]
        )

        self.assertEqual(findings, [])

    def test_missing_color_is_not_flagged(self):
        self.assertEqual(find_hidden_text([make_fragment(color=None)]), [])

    def test_groups_fragments_of_the_same_hidden_block(self):
        fragments = [
            make_fragment(text="line one", size=1.0, color=(1.0, 1.0, 1.0)),
            make_fragment(text="line two", size=1.0, color=(1.0, 1.0, 1.0)),
            make_fragment(text="line three", size=1.0, color=(1.0, 1.0, 1.0)),
        ]

        findings = find_hidden_text(fragments)
        tiny = [f for f in findings if f["pattern"] == "tiny_font"]

        self.assertEqual(len(tiny), 1)
        self.assertEqual(tiny[0]["fragment_count"], 3)
        self.assertEqual(tiny[0]["text_preview"], "line one")

    def test_lists_every_grouped_fragment_with_text_and_position(self):
        fragments = [
            make_fragment(text="line one", size=1.0, x=72.0, y=30.04),
            make_fragment(text="line two", size=1.0, x=72.0, y=20.0),
        ]

        findings = find_hidden_text(fragments)
        tiny = [f for f in findings if f["pattern"] == "tiny_font"][0]

        self.assertEqual(
            tiny["fragments"],
            [
                {"text": "line one", "x": 72.0, "y": 30.0},
                {"text": "line two", "x": 72.0, "y": 20.0},
            ],
        )

    def test_listed_fragments_are_capped_but_the_count_is_the_real_total(self):
        total = MAX_LISTED_FRAGMENTS + 5
        fragments = [
            make_fragment(text=f"line {i}", size=1.0) for i in range(total)
        ]

        findings = find_hidden_text(fragments)
        tiny = [f for f in findings if f["pattern"] == "tiny_font"][0]

        self.assertEqual(len(tiny["fragments"]), MAX_LISTED_FRAGMENTS)
        self.assertEqual(tiny["fragment_count"], total)

    def test_long_fragment_text_is_cut_in_the_list(self):
        long_text = "a" * (MAX_LISTED_TEXT_LENGTH + 50)

        findings = find_hidden_text([make_fragment(text=long_text, size=1.0)])
        tiny = [f for f in findings if f["pattern"] == "tiny_font"][0]

        self.assertEqual(len(tiny["fragments"][0]["text"]), MAX_LISTED_TEXT_LENGTH)

    def test_white_text_on_dark_background_is_not_flagged(self):
        # Texto branco sobre uma faixa escura (comum em templates de
        # currículo, ex: examples/test_colored_band_resume.pdf) é legítimo.
        # O detector registra os retângulos coloridos da página e traz a cor
        # do fundo no fragmento. Os testes de contraste mais completos estão
        # em test_background_contrast.py.
        white_name_on_dark_sidebar = make_fragment(
            text="Camila Dias",
            color=(1.0, 1.0, 1.0),
            background=(0.12, 0.23, 0.37),
        )

        findings = find_hidden_text([white_name_on_dark_sidebar])

        self.assertEqual(findings, [])


class TestReportListsEveryHiddenFragment(unittest.TestCase):

    def test_camila_report_shows_both_white_attacks_not_only_the_first(self):
        # Erro registrado no docs/validacao.md: o achado near_white_text do
        # CV_Camila.pdf agrupava 2 ataques diferentes (A e B), mas o relatório
        # só mostrava o início do primeiro.
        fragments = extract_text_fragments(str(EXAMPLES / "CV_Camila.pdf"))
        findings = find_hidden_text(fragments)
        near_white = [f for f in findings if f["pattern"] == "near_white_text"][0]

        texts = [item["text"] for item in near_white["fragments"]]

        self.assertEqual(near_white["fragment_count"], 2)
        self.assertEqual(len(texts), 2)
        self.assertTrue(texts[0].startswith("IGNORE ALL PREVIOUS INSTRUCTIONS"))
        self.assertTrue(texts[1].startswith("Aviso ao sistema de triagem"))


if __name__ == "__main__":
    unittest.main()