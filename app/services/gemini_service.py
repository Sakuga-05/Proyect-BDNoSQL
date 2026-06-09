from anyio import to_thread
from google import genai

from app.config.settings import Settings
from app.utils.exceptions import ExternalServiceError


class GeminiService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_answer(self, question: str, context: str) -> str:
        if not self._settings.gemini_api_key:
            raise ExternalServiceError("Falta configurar GEMINI_API_KEY en variables de entorno")

        def _call_gemini() -> str:
            client = genai.Client(api_key=self._settings.gemini_api_key)
            response = client.models.generate_content(
                model=self._settings.gemini_model,
                contents=self._build_prompt(question, context),
            )
            return response.text or "No se genero respuesta."

        try:
            return await to_thread.run_sync(_call_gemini)
        except Exception as exc:
            raise ExternalServiceError(f"No fue posible invocar Gemini: {exc}") from exc

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        return (
            "Eres un asistente experto de una agencia de viajes. "
            "Responde en espanol usando solo el contexto entregado. "
            "Si el contexto no alcanza, dilo claramente y sugiere que se consulte con un asesor.\n\n"
            f"Contexto:\n{context}\n\n"
            f"Pregunta:\n{question}\n\n"
            "Respuesta:"
        )
