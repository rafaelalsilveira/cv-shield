import unittest
from unittest.mock import MagicMock

from src.ai_analysis import analyze_with_ai


def make_fake_client(response_text):
    """Monta um cliente Groq falso que devolve response_text como se fosse
    a resposta da IA, sem fazer nenhuma chamada de rede de verdade."""
    message = MagicMock()
    message.content = response_text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]

    client = MagicMock()
    client.chat.completions.create.return_value = response
    return client


class TestAiAnalysis(unittest.TestCase):

    def test_skips_api_call_when_there_are_no_findings(self):
        client = make_fake_client("não deveria ser usado")

        result = analyze_with_ai("texto qualquer", [], client=client)

        self.assertEqual(result["risk_level"], "none")
        client.chat.completions.create.assert_not_called()

    def test_returns_parsed_assessment_on_valid_response(self):
        client = make_fake_client(
            '{"risk_level": "high", "reasoning": "motivo", '
            '"recommendation": "ação"}'
        )
        findings = [{"category": "instruction_override", "pattern": "x"}]

        result = analyze_with_ai("texto", findings, client=client)

        self.assertEqual(result["risk_level"], "high")
        self.assertEqual(result["reasoning"], "motivo")
        self.assertEqual(result["recommendation"], "ação")

    def test_handles_non_json_response_gracefully(self):
        client = make_fake_client("isso não é um JSON válido")
        findings = [{"category": "instruction_override", "pattern": "x"}]

        result = analyze_with_ai("texto", findings, client=client)

        self.assertEqual(result["risk_level"], "unknown")
        self.assertIn("recommendation", result)

    def test_handles_api_exceptions_gracefully(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("falha de rede")
        findings = [{"category": "instruction_override", "pattern": "x"}]

        result = analyze_with_ai("texto", findings, client=client)

        self.assertEqual(result["risk_level"], "unknown")
        self.assertIn("falha de rede", result["reasoning"])

    def test_returns_unknown_when_api_key_is_missing(self):
        import os
        old_value = os.environ.pop("GROQ_API_KEY", None)
        try:
            findings = [{"category": "instruction_override", "pattern": "x"}]
            result = analyze_with_ai("texto", findings)

            self.assertEqual(result["risk_level"], "unknown")
            self.assertIn("GROQ_API_KEY", result["reasoning"])
        finally:
            if old_value is not None:
                os.environ["GROQ_API_KEY"] = old_value


if __name__ == "__main__":
    unittest.main()