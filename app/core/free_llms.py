import os
import json
import aiohttp
import google.generativeai as genai
import uuid
from typing import List, Dict, Any, Optional
from app.core.log_util import log_exception
from app.api.deps import get_chroma_client
from dotenv import load_dotenv

load_dotenv()

# --- Clientes Globais (Inicializados como None) ---
_google_model = None
_groq_headers = None
_cloudflare_headers = None


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
            "GOOGLE_AISTUDIO_MODELS_PRIORITY", "gemini-1.5-flash"
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


def get_cloudflare_headers():
    """Cria e retorna os headers para a API Cloudflare, apenas uma vez."""
    global _cloudflare_headers
    if _cloudflare_headers is None:
        api_key = os.environ.get("CLOUDFLARE_WORKERS_AI_KEY")
        if not api_key:
            print("AVISO: CLOUDFLARE_WORKERS_AI_KEY não encontrada no ambiente.")
            return None
        _cloudflare_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    return _cloudflare_headers


# --- Funções de Requisição ---
async def google_aistudio_request(messages: List[Dict[str, str]]) -> Optional[str]:
    model = get_google_model()
    if not model:
        return None
    try:
        google_formatted_messages = [
            {"role": msg["role"], "parts": [msg["content"]]} for msg in messages
        ]

        response = await model.generate_content_async(google_formatted_messages)
        return response.text.strip()
    except Exception:
        log_exception()
        return None


async def groq_request(messages: List[Dict[str, str]]) -> Optional[str]:
    headers = get_groq_headers()
    if not headers:
        return None

    groq_models = os.environ.get("GROQ_MODELS_PRIORITY", "llama-3.1-8b-instant").split(
        ";"
    )
    model = groq_models[0] if groq_models else "llama-3.1-8b-instant"

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={"model": model, "messages": messages},
            ) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return json_response["choices"][0]["message"]["content"].strip()
                else:
                    print(f"Erro na requisição Groq: {await response.text()}")
                    return None
    except Exception:
        log_exception()
        return None


async def cloudflare_request(messages: List[Dict[str, str]]) -> Optional[str]:
    headers = get_cloudflare_headers()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")

    if not headers or not account_id:
        return None

    model = "@cf/meta/llama-3-8b-instruct"

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}",
                json={"messages": messages},
            ) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return json_response["result"]["response"].strip()
                else:
                    print(f"Erro na requisição Cloudflare: {await response.text()}")
                    return None
    except Exception:
        log_exception()
        return None


async def llm_prompt(messages: List[Dict[str, str]]) -> str:
    """Tenta provedores de LLM em ordem de prioridade."""
    providers = [
        ("GOOGLE AISTUDIO", google_aistudio_request),
        ("GROQ", groq_request),
        ("CLOUDFLARE", cloudflare_request),
    ]

    for name, func in providers:
        try:
            response = await func(messages)
            if response:
                print(f"Usado com sucesso: {name}")
                return response.strip("`").strip()
            else:
                print(f"Falha com o provedor: {name}. Tentando o próximo...")
                continue
        except Exception:
            log_exception()
            print(f"Exceção com o provedor: {name}. Tentando o próximo...")
            continue

    print("Todos os provedores de LLM falharam.")
    return "Ocorreu um erro na geração da narrativa. Tente novamente mais tarde."
