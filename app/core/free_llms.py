import os
import json
import aiohttp
import google.generativeai as genai
from app.core.log_util import log_exception

# --- Clientes Globais (Inicializados como None) ---
_google_model = None
_groq_headers = None


# --- Funções de Inicialização (Lazy Getters) ---
def get_google_model():
    """Configura e retorna o modelo generativo do Google, apenas uma vez."""
    global _google_model
    if _google_model is None:
        api_key = os.environ.get("GOOGLE_AISTUDIO_KEY")
        if not api_key:
            print("AVISO: GOOGLE_AISTUDIO_KEY não encontrada no ambiente.")
            return None
        genai.configure(api_key=api_key)
        model_name = os.environ.get(
            "GOOGLE_AISTUDIO_MODELS_PRIORITY", "gemini-1.5-flash-latest"
        ).split(";")[0]
        _google_model = genai.GenerativeModel(model_name)
    return _google_model


def get_groq_headers():
    """Cria e retorna os headers para a API Groq, apenas uma vez."""
    global _groq_headers
    if _groq_headers is None:
        api_key = os.environ.get("GROQ_KEY")
        if not api_key:
            print("AVISO: GROQ_KEY não encontrada no ambiente.")
            return None
        _groq_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    return _groq_headers


# --- Modelos e Configurações ---
GROQ_MODELS = os.environ.get("GROQ_MODELS_PRIORITY", "llama3-8b-8192").split(";")
timeout = aiohttp.ClientTimeout(total=90)


# --- Funções de Requisição ---
async def google_aistudio_request(messages):
    model = get_google_model()
    if not model:
        return None
    try:
        google_formatted_messages = [
            {"role": msg["role"], "parts": [msg["content"]]} for msg in messages
        ]

        generation_config = genai.types.GenerationConfig()

        response = await model.generate_content_async(
            google_formatted_messages,
            generation_config=generation_config,
        )
        return response.text.strip()
    except Exception:
        log_exception()
        return None


async def groq_request(messages):
    headers = get_groq_headers()
    if not headers:
        return None
    model = GROQ_MODELS[0]
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={"model": model, "messages": messages},
            ) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return json_response["choices"][0]["message"]["content"].strip()
    except Exception:
        log_exception()
    return None


async def llm_prompt(messages):
    """Tenta provedores de LLM em ordem de prioridade."""
    providers = [
        ("GOOGLE AISTUDIO", google_aistudio_request),
        ("GROQ", groq_request),
    ]

    for name, func in providers:
        try:
            response = await func(messages)
            if response:
                print(f"Usado com sucesso: {name}")
                return response
        except Exception:
            log_exception()

    print("AVISO: Todos os provedores de LLM falharam.")
    return json.dumps(
        {
            "narrativa": "O mestre da masmorra está momentaneamente sem palavras. Um silêncio ecoa pelo vazio...",
            "evento": {
                "tipo": "dialogo",
                "danoRecebido": 0,
                "danoCausado": 0,
                "vitoria": False,
            },
        }
    )
