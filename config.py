import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "Falta la variable de entorno OPENAI_API_KEY. "
        "Configúrala en Vercel o en el entorno local."
    )

OPENAI_MODEL = "gpt-4o-mini"
