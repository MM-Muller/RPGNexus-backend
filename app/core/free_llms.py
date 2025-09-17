"""
Este módulo fornece uma camada de abstração para interagir com múltiplos provedores de Modelos de Linguagem de Grande Escala (LLM).
Inclui implementações tanto em buffer quanto em streaming para enviar solicitações de conclusão de chat para várias APIs.
Nota:
- Este código é baseado na implementação disponível em https://gist.github.com/cnmoro/85c12351d5530267bceebc63caca52c1.
"""

from app.core.log_util import log_exception
from google.genai import types
import os, aiohttp, json
from google import genai

GOOGLE_AISTUDIO_KEY = os.environ.get("GOOGLE_AISTUDIO_KEY", "")
GOOGLE_AISTUDIO_MODELS_PRIORITY = os.environ.get(
    "GOOGLE_AISTUDIO_MODELS_PRIORITY",
    "gemini-2.0-flash;gemini-2.0-flash-lite;gemma-3-27b-it;gemma-3n-e4b-it",
)
GOOGLE_AISTUDIO_MODELS = GOOGLE_AISTUDIO_MODELS_PRIORITY.split(";")
GOOGLE_CLIENT = genai.Client(
    api_key=GOOGLE_AISTUDIO_KEY,
    http_options=types.HttpOptions(async_client_args={"trust_env": True}),
)

CEREBRAS_KEY = os.environ.get("CEREBRAS_KEY", "")
CEREBRAS_MODELS_PRIORITY = os.environ.get(
    "CEREBRAS_MODELS_PRIORITY",
    "llama-3.3-70b;llama-4-scout-17b-16e-instruct;qwen-3-32b",
)
CEREBRAS_MODELS = CEREBRAS_MODELS_PRIORITY.split(";")

GROQ_KEY = os.environ.get("GROQ_KEY", "")
GROQ_MODELS_PRIORITY = os.environ.get(
    "GROQ_MODELS_PRIORITY",
    "llama-3.3-70b-versatile;llama3-70b-8192;meta-llama/llama-4-scout-17b-16e-instruct",
)
GROQ_MODELS = GROQ_MODELS_PRIORITY.split(";")

COHERE_KEY = os.environ.get("COHERE_KEY", "")
COHERE_MODELS_PRIORITY = os.environ.get(
    "COHERE_MODELS_PRIORITY", "command-a-03-2025;command-r-plus;c4ai-aya-expanse-32b"
)
COHERE_MODELS = COHERE_MODELS_PRIORITY.split(";")

TOGETHER_KEY = os.environ.get("TOGETHER_KEY", "")
TOGETHER_MODELS_PRIORITY = os.environ.get(
    "TOGETHER_MODELS_PRIORITY",
    "deepseek-ai/DeepSeek-V3;meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8;arcee_ai/arcee-spotlight;google/gemma-3n-E4B-it",
)
TOGETHER_MODELS = TOGETHER_MODELS_PRIORITY.split(";")

NVIDIA_NIM_KEY = os.environ.get("NVIDIA_NIM_KEY", "")
NVIDIA_MODELS_PRIORITY = os.environ.get(
    "NVIDIA_MODELS_PRIORITY",
    "meta/llama-3.3-70b-instruct;google/gemma-3-27b-it;qwen/qwen3-235b-a22b;mistralai/mistral-small-3.1-24b-instruct-2503;google/gemma-3n-e4b-it",
)
NVIDIA_MODELS = NVIDIA_MODELS_PRIORITY.split(";")

CLOUDFLARE_WORKERS_AI_KEY = os.environ.get("CLOUDFLARE_WORKERS_AI_KEY", "")
CLOUDFLARE_WORKERS_AI_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_WORKERS_AI_MODELS_PRIORITY = os.environ.get(
    "CLOUDFLARE_WORKERS_AI_MODELS_PRIORITY",
    "meta/llama-3.3-70b-instruct-fp8-fast;meta/llama-3.1-70b-instruct;meta/llama-4-scout-17b-16e-instruct;mistralai/mistral-small-3.1-24b-instruct",
)
CLOUDFLARE_WORKERS_AI_MODELS = CLOUDFLARE_WORKERS_AI_MODELS_PRIORITY.split(";")

OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")
OPENROUTER_BASEMODEL = os.environ.get("OPENROUTER_BASEMODEL", "google/gemma-3n-e4b-it")
OPENROUTER_MODELS_FALLBACK = os.environ.get(
    "OPENROUTER_MODELS_FALLBACK",
    "amazon/nova-micro-v1;google/gemini-flash-1.5-8b;mistralai/mistral-nemo",
)
if ";" in OPENROUTER_MODELS_FALLBACK:
    OPENROUTER_MODELS_FALLBACK = OPENROUTER_MODELS_FALLBACK.split(";")
else:
    OPENROUTER_MODELS_FALLBACK = [OPENROUTER_MODELS_FALLBACK]

timeout = aiohttp.ClientTimeout(total=90)


def convert_messages_to_google_contents(messages):
    """
    Converts a list of dict messages (with 'role' and 'content') to Google GenAI Content objects.
    """
    return [
        types.Content(role=m["role"], parts=[types.Part.from_text(text=m["content"])])
        for m in messages
    ]


async def google_aistudio_request(messages):
    try:
        full_response = ""
        async for chunk in streaming_google_aistudio_request(messages):
            full_response += chunk
        return full_response.strip()
    except Exception:
        log_exception()
    return None


async def cerebras_request(messages):
    headers = {
        "Authorization": f"Bearer {CEREBRAS_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in CEREBRAS_MODELS:
                try:
                    async with session.post(
                        "https://api.cerebras.ai/v1/chat/completions",
                        json={"model": model, "messages": messages},
                    ) as response:
                        json_response = await response.json()
                        if "error" not in json_response:
                            return json_response["choices"][0]["message"][
                                "content"
                            ].strip()
                except Exception:
                    log_exception()
    except Exception:
        log_exception()
    return None


async def groq_request(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in GROQ_MODELS:
                try:
                    async with session.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json={"model": model, "messages": messages},
                    ) as response:
                        json_response = await response.json()
                        if "error" not in json_response:
                            return json_response["choices"][0]["message"][
                                "content"
                            ].strip()
                except Exception:
                    log_exception()
    except Exception:
        log_exception()
    return None


async def cohere_request(messages):
    headers = {
        "Authorization": f"Bearer {COHERE_KEY}",
        "Content-Type": "application/json",
    }

    # Convert messages to cohere format
    for i in range(len(messages)):
        messages[i] = {
            "role": messages[i]["role"],
            "content": [{"type": "text", "text": messages[i]["content"]}],
        }

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in COHERE_MODELS:
                try:
                    async with session.post(
                        "https://api.cohere.com/v2/chat",
                        json={"model": model, "messages": messages},
                    ) as response:
                        json_response = await response.json()
                        raw_response = json_response["message"]["content"][0][
                            "text"
                        ].strip()
                        print(f"Used COHERE successfully, model: {model}")
                        return raw_response
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return None


async def nvidia_nim_request(messages):
    headers = {
        "Authorization": f"Bearer {NVIDIA_NIM_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in NVIDIA_MODELS:
                try:
                    async with session.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        json={
                            "model": model,
                            "messages": messages,
                            "chat_template_kwargs": {"thinking": False},
                        },
                    ) as response:
                        json_response = await response.json()
                        if "error" not in json_response:
                            print(f"Used NVIDIA NIM successfully, model: {model}")
                            return json_response["choices"][0]["message"][
                                "content"
                            ].strip()
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return None


async def together_request(messages):
    headers = {
        "Authorization": f"Bearer {TOGETHER_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in TOGETHER_MODELS:
                try:
                    async with session.post(
                        "https://api.together.xyz/v1/chat/completions",
                        json={"model": model, "messages": messages},
                    ) as response:
                        json_response = await response.json()
                        if "error" not in json_response:
                            print(f"Used TOGETHER successfully, model: {model}")
                            return json_response["choices"][0]["message"][
                                "content"
                            ].strip()
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return None


async def cloudflare_workers_ai_request(messages):
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_WORKERS_AI_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in CLOUDFLARE_WORKERS_AI_MODELS:
                try:
                    async with session.post(
                        f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_WORKERS_AI_ACCOUNT_ID}/ai/run/@cf/{model}",
                        json={"messages": messages},
                    ) as response:
                        json_response = await response.json()
                        if json_response.get("success", False):
                            print(
                                f"Used CLOUDFLARE WORKERS AI successfully, model: {model}"
                            )
                            return json_response["result"]["response"].strip()
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return None


async def openrouter_request(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "stream": False,
        "model": OPENROUTER_BASEMODEL,
        "models": OPENROUTER_MODELS_FALLBACK,
        "messages": messages,
        "reasoning": {"exclude": True},
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions", json=body
            ) as response:
                json_response = await response.json()
                return json_response["choices"][0]["message"]["content"].strip()
    except Exception:
        log_exception()
    return None


async def llm_prompt(messages):
    # Try all available providers in order, BEFORE falling back to OpenRouter (paid)
    providers = [
        ("GOOGLE AISTUDIO", google_aistudio_request),
        ("CEREBRAS", cerebras_request),
        ("GROQ", groq_request),
        ("NVIDIA NIM", nvidia_nim_request),
        ("COHERE", cohere_request),
        ("TOGETHER", together_request),
        ("CLOUDFLARE WORKERS AI", cloudflare_workers_ai_request),
        ("OPENROUTER", openrouter_request),
    ]

    for name, func in providers:
        try:
            response = await func(messages)
            if response:
                print(f"Used {name} successfully")
                return response
        except Exception:
            log_exception()

    return ""


################## Streaming versions below ####


async def streaming_google_aistudio_request(messages):
    contents = convert_messages_to_google_contents(messages)

    # Extract system message if any
    system_message = None
    for i, content in enumerate(contents):
        if content.role == "system":
            system_message = content
            # Remove this item from the list
            contents.pop(i)
            break

    def build_config(system_instruction, include_thinking):
        return types.GenerateContentConfig(
            response_mime_type="text/plain",
            thinking_config=(
                types.ThinkingConfig(include_thoughts=False, thinking_budget=0)
                if include_thinking
                else None
            ),
            system_instruction=system_instruction,
        )

    include_thinking = True
    finished = False

    for model in GOOGLE_AISTUDIO_MODELS:
        if finished:
            break

        while not finished:
            try:
                config = build_config(system_message, include_thinking)
                stream = await GOOGLE_CLIENT.aio.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=config,
                )

                first_chunk = True

                async for chunk in stream:
                    print(chunk)
                    candidates = chunk.candidates
                    if not candidates:
                        continue
                    parts = candidates[0].content.parts
                    if parts is None:
                        if first_chunk:
                            raise ValueError(
                                "First chunk has no parts, invalid response"
                            )
                        else:
                            break  # stop indicator
                    yield parts[0].text
                    first_chunk = False
                print(f"Streaming ended with model: {model}")
                finished = True
                break

            except genai.errors.ClientError as e:
                print(e)
                error_msg = str(e)
                if "Developer instruction is not enabled" in error_msg:
                    if system_message:
                        system_text = system_message.parts[0].text
                        contents = [c for c in contents if c.role != "system"]
                        for c in contents:
                            if c.role == "user":
                                c.parts[0].text = system_text + "\n" + c.parts[0].text
                                break
                        system_message = None
                        continue  # retry same model
                elif "Thinking is not enabled" in error_msg:
                    if include_thinking:
                        include_thinking = False
                        continue  # retry same model
                else:
                    log_exception()
                    break  # move to next model on unrelated ClientError

            except Exception:
                log_exception()
                break  # move to next model on any other Exception


async def streaming_cerebras_request(messages):
    """
    Sends a chat completion request to Cerebras API with streaming enabled.
    Yields generated tokens as they arrive.
    """
    headers = {
        "Authorization": f"Bearer {CEREBRAS_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in CEREBRAS_MODELS:
                try:
                    async with session.post(
                        "https://api.cerebras.ai/v1/chat/completions",
                        json={
                            "model": model,
                            "messages": messages,
                            "stream": True,  # Enable streaming
                        },
                    ) as response:
                        response.raise_for_status()  # Raise an exception for bad status codes
                        async for chunk in response.content.iter_any():
                            decoded_chunk = chunk.decode("utf-8")
                            # Split by newlines to handle multiple SSE events in one chunk
                            for line in decoded_chunk.splitlines():
                                if line.startswith("data: "):
                                    json_str = line[len("data: ") :].strip()
                                    if json_str == "[DONE]":
                                        return  # End of stream
                                    try:
                                        json_response = json.loads(json_str)
                                        content = json_response["choices"][0][
                                            "delta"
                                        ].get("content")
                                        if content:
                                            yield content
                                    except json.JSONDecodeError:
                                        # Handle incomplete JSON objects or other parsing errors
                                        continue
                    return
                except Exception:
                    log_exception()
    except Exception:
        log_exception()
    return


async def streaming_groq_request(messages):
    """
    Sends a chat completion request to Groq API with streaming enabled.
    Yields generated tokens as they arrive.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in GROQ_MODELS:
                try:
                    async with session.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json={
                            "model": model,
                            "messages": messages,
                            "stream": True,  # Enable streaming
                        },
                    ) as response:
                        response.raise_for_status()  # Raise an exception for bad status codes
                        async for chunk in response.content.iter_any():
                            decoded_chunk = chunk.decode("utf-8")
                            for line in decoded_chunk.splitlines():
                                if line.startswith("data: "):
                                    json_str = line[len("data: ") :].strip()
                                    if json_str == "[DONE]":
                                        return  # End of stream
                                    try:
                                        json_response = json.loads(json_str)
                                        content = json_response["choices"][0][
                                            "delta"
                                        ].get("content")
                                        if content:
                                            yield content
                                    except json.JSONDecodeError:
                                        continue
                    return
                except Exception:
                    log_exception()
    except Exception:
        log_exception()
    return


async def streaming_cohere_request(messages):
    """
    Sends a chat request to Cohere API with streaming enabled.
    Yields generated tokens as they arrive.
    """
    headers = {
        "Authorization": f"Bearer {COHERE_KEY}",
        "Content-Type": "application/json",
    }

    # Convert messages to Cohere format for streaming
    cohere_messages = []
    for msg in messages:
        cohere_messages.append(
            {"role": msg["role"], "content": [{"type": "text", "text": msg["content"]}]}
        )

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in COHERE_MODELS:
                try:
                    async with session.post(
                        "https://api.cohere.com/v2/chat",
                        json={
                            "model": model,
                            "messages": cohere_messages,
                            "stream": True,  # Enable streaming
                        },
                    ) as response:
                        response.raise_for_status()  # Raise an exception for bad status codes
                        current_event_type = None
                        async for chunk in response.content.iter_any():
                            decoded_chunk = chunk.decode("utf-8")
                            for line in decoded_chunk.splitlines():
                                if line.startswith("event: "):
                                    current_event_type = line[len("event: ") :].strip()
                                elif line.startswith("data: "):
                                    json_str = line[len("data: ") :].strip()
                                    if json_str == "[DONE]":
                                        return  # End of stream
                                    try:
                                        json_response = json.loads(json_str)
                                        if current_event_type == "content-delta":
                                            # Extract content from the nested structure
                                            content = (
                                                json_response.get("delta", {})
                                                .get("message", {})
                                                .get("content", {})
                                                .get("text")
                                            )
                                            if content:
                                                yield content
                                        current_event_type = (
                                            None  # Reset for the next event
                                        )
                                    except json.JSONDecodeError:
                                        # Handle incomplete JSON objects or other parsing errors
                                        continue
                    return
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return


async def streaming_nvidia_nim_request(messages):
    """
    Sends a chat completion request to NVIDIA NIM API with streaming enabled.
    Yields generated tokens as they arrive.
    """
    headers = {
        "Authorization": f"Bearer {NVIDIA_NIM_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in NVIDIA_MODELS:
                try:
                    async with session.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        json={
                            "model": model,
                            "messages": messages,
                            "chat_template_kwargs": {"thinking": False},
                            "stream": True,  # Enable streaming
                        },
                    ) as response:
                        response.raise_for_status()  # Raise an exception for bad status codes
                        async for chunk in response.content.iter_any():
                            decoded_chunk = chunk.decode("utf-8")
                            for line in decoded_chunk.splitlines():
                                if line.startswith("data: "):
                                    json_str = line[len("data: ") :].strip()
                                    if json_str == "[DONE]":
                                        return  # End of stream
                                    try:
                                        json_response = json.loads(json_str)
                                        content = json_response["choices"][0][
                                            "delta"
                                        ].get("content")
                                        if content:
                                            yield content
                                    except json.JSONDecodeError:
                                        continue
                    return
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return


async def streaming_together_request(messages):
    """
    Sends a chat completion request to Together AI with streaming enabled.
    Yields generated tokens as they arrive.
    """
    headers = {
        "Authorization": f"Bearer {TOGETHER_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in TOGETHER_MODELS:
                try:
                    async with session.post(
                        "https://api.together.xyz/v1/chat/completions",
                        json={
                            "model": model,
                            "messages": messages,
                            "stream": True,  # Enable streaming
                        },
                    ) as response:
                        response.raise_for_status()  # Raise an exception for bad status codes
                        async for chunk in response.content.iter_any():
                            decoded_chunk = chunk.decode("utf-8")
                            for line in decoded_chunk.splitlines():
                                if line.startswith("data: "):
                                    json_str = line[len("data: ") :].strip()
                                    if json_str == "[DONE]":
                                        return  # End of stream
                                    try:
                                        json_response = json.loads(json_str)
                                        content = json_response["choices"][0][
                                            "delta"
                                        ].get("content")
                                        if content:
                                            yield content
                                    except json.JSONDecodeError:
                                        continue
                    return
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return


async def streaming_cloudflare_workers_ai_request(messages):
    """
    Sends a chat completion request to Cloudflare Workers AI with streaming enabled.
    Yields generated tokens as they arrive.
    """
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_WORKERS_AI_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for model in CLOUDFLARE_WORKERS_AI_MODELS:
                try:
                    async with session.post(
                        f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_WORKERS_AI_ACCOUNT_ID}/ai/run/@cf/{model}",
                        json={"messages": messages, "stream": True},  # Enable streaming
                    ) as response:
                        response.raise_for_status()  # Raise an exception for bad status codes
                        async for chunk in response.content.iter_any():
                            decoded_chunk = chunk.decode("utf-8")
                            for line in decoded_chunk.splitlines():
                                if line.startswith(
                                    "data: "
                                ):  # Cloudflare Workers AI uses "data: " prefix
                                    json_str = line[len("data: ") :].strip()
                                    if json_str == "[DONE]":
                                        return  # End of stream
                                    try:
                                        json_response = json.loads(json_str)
                                        # Cloudflare Workers AI streaming returns 'response' directly in the JSON
                                        content = json_response.get("response")
                                        if content:
                                            yield content
                                    except json.JSONDecodeError:
                                        continue
                    return
                except Exception as e:
                    log_exception()
    except Exception as e:
        log_exception()
    return


async def streaming_openrouter_request(messages):
    """
    Sends a chat completion request to OpenRouter API with streaming enabled.
    Yields generated tokens as they arrive.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "stream": True,  # Enable streaming
        "model": OPENROUTER_BASEMODEL,
        "models": OPENROUTER_MODELS_FALLBACK,
        "messages": messages,
        "reasoning": {"exclude": True},
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions", json=body
            ) as response:
                response.raise_for_status()  # Raise an exception for bad status codes
                async for chunk in response.content.iter_any():
                    decoded_chunk = chunk.decode("utf-8")
                    for line in decoded_chunk.splitlines():
                        if line.startswith("data: "):
                            json_str = line[len("data: ") :].strip()
                            if json_str == "[DONE]":
                                return  # End of stream
                            try:
                                json_response = json.loads(json_str)
                                content = json_response["choices"][0]["delta"].get(
                                    "content"
                                )
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
            return
    except Exception:
        log_exception()
    return


async def stream_llm_prompt(messages):
    """
    Attempts to get a streaming response from multiple LLM providers in order,
    yielding tokens as they arrive. Falls back to the next provider if one fails.

    Args:
        messages (list): A list of message dictionaries for the chat completion.

    Yields:
        str: Chunks of the generated content from the LLM.
    """
    providers = [
        ("GOOGLE AISTUDIO", streaming_google_aistudio_request),
        ("CEREBRAS", streaming_cerebras_request),
        ("GROQ", streaming_groq_request),
        ("NVIDIA NIM", streaming_nvidia_nim_request),
        ("COHERE", streaming_cohere_request),
        ("TOGETHER", streaming_together_request),
        ("CLOUDFLARE WORKERS AI", streaming_cloudflare_workers_ai_request),
        ("OPENROUTER", streaming_openrouter_request),
    ]

    for name, func in providers:
        try:
            print(f"Attempting to use {name} for streaming...", flush=True)
            async for token in func(messages):
                yield token
            print(f"Successfully used {name} for streaming.", flush=True)
            return  # Exit after a successful streaming response
        except Exception:
            log_exception()
            print(
                f"Failed to get a streaming response from {name}, trying next provider.",
                flush=True,
            )
            continue  # Try the next provider

    print("All streaming LLM providers failed.", flush=True)
    return  # No content to yield if all providers fail
