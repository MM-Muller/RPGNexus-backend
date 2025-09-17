# rpgnexus-backend/app/core/free_llms.py

import os
import json
import aiohttp
from google import genai
from google.genai import types
from app.core.log_util import log_exception

# --- Variáveis Globais para Clientes (iniciadas como None) ---
_google_client = None
_cerebras_headers = None
_groq_headers = None
# ... adicione outros clientes aqui se precisar

# --- Funções de Inicialização (Lazy Getters) ---


def get_google_client():
    """Cria e retorna o cliente do Google AI Studio, apenas uma vez."""
    global _google_client
    if _google_client is None:
        api_key = os.environ.get("GOOGLE_AISTUDIO_KEY")
        if not api_key:
            print("AVISO: GOOGLE_AISTUDIO_KEY não encontrada no ambiente.")
            return None
        _google_client = genai.Client(api_key=api_key)
    return _google_client


def get_cerebras_headers():
    """Cria e retorna os headers para a API Cerebras, apenas uma vez."""
    global _cerebras_headers
    if _cerebras_headers is None:
        api_key = os.environ.get("CEREBRAS_KEY")
        if not api_key:
            print("AVISO: CEREBRAS_KEY não encontrada no ambiente.")
            return None
        _cerebras_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    return _cerebras_headers


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
GOOGLE_AISTUDIO_MODELS = os.environ.get(
    "GOOGLE_AISTUDIO_MODELS_PRIORITY", "gemini-1.5-flash-latest;gemma-2-9b-it"
).split(";")
CEREBRAS_MODELS = os.environ.get("CEREBRAS_MODELS_PRIORITY", "btlm-3b-8k-base").split(
    ";"
)
GROQ_MODELS = os.environ.get("GROQ_MODELS_PRIORITY", "llama3-8b-8192").split(";")

timeout = aiohttp.ClientTimeout(total=90)

# --- Funções de Requisição (Agora usam os Getters) ---


async def google_aistudio_request(messages):
    google_client = get_google_client()
    if not google_client:
        return None

    model_name = GOOGLE_AISTUDIO_MODELS[0]  # Usando o primeiro da lista de prioridade
    try:
        model = google_client.get_model(f"models/{model_name}")
        response = await model.generate_content_async(messages)
        return response.text.strip()
    except Exception:
        log_exception()
        return None


async def cerebras_request(messages):
    headers = get_cerebras_headers()
    if not headers:
        return None

    model = CEREBRAS_MODELS[0]
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(
                "https://api.cerebras.ai/v1/chat/completions",
                json={"model": model, "messages": messages},
            ) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return json_response["choices"][0]["message"]["content"].strip()
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
    # Defina a ordem de preferência aqui
    providers = [
        ("GOOGLE AISTUDIO", google_aistudio_request),
        ("GROQ", groq_request),
        ("CEREBRAS", cerebras_request),
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
    return "O mestre da masmorra está momentaneamente sem palavras."
