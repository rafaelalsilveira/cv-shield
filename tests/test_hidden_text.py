import unittest

from src.hidden_text import find_hidden_text


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


if __name__ == "__main__":
    unittest.main()