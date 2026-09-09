import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ai_provider import (
    AIProviderError,
    AnthropicProvider,
    GeminiProvider,
    ResilientProvider,
    create_provider,
)


class GeminiProviderTests(unittest.TestCase):
    def test_requires_api_key_without_injected_client(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AIProviderError):
                GeminiProvider()

    def test_uses_configured_model_and_normalizes_response(self):
        response = SimpleNamespace(
            text="resposta de teste",
            usage_metadata=SimpleNamespace(
                prompt_token_count=12,
                candidates_token_count=8,
            ),
            response_id="request-1",
        )
        client = Mock()
        client.models.generate_content.return_value = response
        provider = GeminiProvider(client=client, model="modelo-de-teste")

        result = provider.generate("pergunta", "instrucao", temperature=0.4)

        self.assertEqual(result.provider, "gemini")
        self.assertEqual(result.model, "modelo-de-teste")
        self.assertEqual(result.text, "resposta de teste")
        self.assertEqual(result.input_tokens, 12)
        client.models.generate_content.assert_called_once()

    def test_normalizes_claude_response(self):
        client = Mock()
        client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="resposta Claude")],
            usage=SimpleNamespace(input_tokens=10, output_tokens=6),
            id="msg-1",
        )
        provider = AnthropicProvider(client=client, model="claude-teste")

        result = provider.generate("pergunta", "instrucao")

        self.assertEqual(result.provider, "claude")
        self.assertEqual(result.text, "resposta Claude")
        self.assertEqual(result.output_tokens, 6)
        client.messages.create.assert_called_once()

    def test_retries_transient_error(self):
        primary = Mock()
        primary.generate.side_effect = [TimeoutError(), "unexpected"]
        provider = ResilientProvider(primary, max_retries=1, backoff_seconds=0)

        result = provider.generate(contents="pergunta")

        self.assertEqual(result, "unexpected")
        self.assertEqual(primary.generate.call_count, 2)

    def test_uses_fallback_after_transient_errors(self):
        primary = Mock()
        primary.generate.side_effect = TimeoutError()
        fallback = Mock()
        fallback.generate.return_value = "resposta fallback"
        provider = ResilientProvider(
            primary,
            fallback=fallback,
            max_retries=1,
            backoff_seconds=0,
        )

        result = provider.generate(contents="pergunta")

        self.assertEqual(result, "resposta fallback")
        self.assertEqual(primary.generate.call_count, 2)
        fallback.generate.assert_called_once_with(contents="pergunta")


if __name__ == "__main__":
    unittest.main()
