import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import CrossEncoder
from model2vec import StaticModel
import uuid
from typing import List, Dict, Any, Optional
import re
import random
from app.core.free_llms import llm_prompt

# --- Configuração do Modelo de Embedding ---
embedding_model = StaticModel.from_pretrained(
    "cnmoro/nomic-embed-text-v2-moe-distilled-high-quality"
)


class EmbedDocuments(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return embedding_model.encode(input).tolist()


# --- Conexão com o ChromaDB ---
chroma_client = chromadb.HttpClient(host="localhost", port=8001)
collection = chroma_client.get_or_create_collection(
    name="rpg_nexus_history", embedding_function=EmbedDocuments()
)

# --- Configuração do Reranker ---
# Este modelo ajuda a encontrar os trechos de memória mais relevantes
reranker = CrossEncoder(
    "jinaai/jina-reranker-v2-base-multilingual", trust_remote_code=True
)


def rerank_context(query: str, texts: List[str], top_k=5) -> List[str]:
    """Reordena os textos baseados na relevância para a query."""
    if not texts:
        return []
    rankings = reranker.rank(query, texts, return_documents=True)
    return [r["text"] for r in rankings[:top_k]]


# --- Funções de Interação com a LLM ---

async def generate_initial_narrative(
    character: dict, battle_theme: str, memory: str
) -> str:
    """Gera a primeira narrativa para uma nova batalha."""
    prompt = f"""
    Você é um Mestre de RPG talentoso. Sua tarefa é iniciar uma batalha épica com uma narrativa envolvente e dinâmica, em um único texto contínuo.
    
    Personagem: {character['name']}, um(a) {character['race']} da classe {character['char_class']}.
    Descrição do Personagem: {character.get('description', 'Nenhuma.')}

    Tema da Batalha: "{battle_theme}"

    Memórias de Batalhas Anteriores (use isso para dar continuidade):
    ---
    {memory if memory else "Nenhuma."}
    ---

    Instruções:
    1. Comece descrevendo o cenário de forma vívida.
    2. Em seguida, introduza um inimigo que se encaixe no tema da batalha.
    3. Termine a narrativa em um momento de tensão, preparando o jogador para sua primeira ação.
    4. IMPORTANTE: Sua resposta deve ser APENAS a narrativa em texto puro. NÃO inclua títulos, marcadores ou qualquer texto que não seja parte da história (como "Cenário:", "O Inimigo:", etc.).
    """
    messages = [{"role": "user", "content": prompt}]
    return await llm_prompt(messages)


async def continue_narrative(
    character: dict,
    battle_theme: str,
    history: List[str],
    player_action: str,
    memory: str,
) -> str:
    """Continua a narrativa e retorna um texto simples."""
    history_str = "\n".join(history)

    player_damage = character["attributes"]["strength"] * random.randint(5, 10)
    enemy_damage = random.randint(10, 20)

    # Simula um ataque especial
    if "especial" in player_action.lower() or "habilidade" in player_action.lower():
        player_damage *= 2

    # Simula a chance de esquiva
    player_dodge_chance = character["attributes"]["dexterity"] * 2
    enemy_dodge_chance = 10

    player_dodged = random.randint(1, 100) <= player_dodge_chance
    enemy_dodged = random.randint(1, 100) <= enemy_dodge_chance

    if enemy_dodged:
        player_damage = 0

    if player_dodged:
        enemy_damage = 0

    prompt = f"""
    Você é um mestre de RPG. Sua tarefa é continuar a história de forma clara, dinâmica e que prenda a atenção do jogador.

    Personagem: {character['name']}, um(a) {character['race']} da classe {character['char_class']}.
    Tema da Batalha: "{battle_theme}"

    Memórias de Batalhas Anteriores (para contexto):
    ---
    {memory if memory else "Nenhuma."}
    ---
    
    Histórico da Batalha Atual:
    ---
    {history_str}
    ---

    Ação do Jogador: "{player_action}"

    Cálculo da Rodada:
    - Dano que o Jogador causa: {player_damage}
    - Dano que o Inimigo causa: {enemy_damage}
    - Jogador esquivou do golpe inimigo: {player_dodged}
    - Inimigo esquivou do golpe do jogador: {enemy_dodged}

    Instruções de Resposta:
    1. Descreva o resultado da ação do jogador e, em seguida, a reação e o contra-ataque do inimigo.
    2. A sua resposta deve ser APENAS a narrativa em texto puro.
    3. NÃO inclua títulos como "Resultado da Ação do Jogador" ou "Reação do Inimigo". Apenas o texto corrido.
    4. No final da sua resposta, adicione a seguinte linha especial, sem pular linha: `[DANO_CAUSADO:{player_damage},DANO_RECEBIDO:{enemy_damage}]`
    """
    messages = [{"role": "user", "content": prompt}]
    return await llm_prompt(messages)


async def generate_action_suggestions(battle_theme: str, history: List[str]) -> str:
    """Gera sugestões de ação contextuais para o jogador."""
    history_str = "\n".join(history)
    prompt = f"""
    Você é um Mestre de RPG. Sua tarefa é fornecer 3 sugestões de ações curtas e concisas para o jogador, baseadas no contexto da batalha.
    
    Tema da Batalha: "{battle_theme}"
    Histórico da Batalha Atual:
    ---
    {history_str}
    ---
    
    Instruções:
    1. As sugestões devem ser relevantes para a situação e o tipo de inimigo.
    2. As sugestões devem ser de uma palavra ou frase curta, como "Atacar com Fúria", "Analisar Ponto Fraco", "Fugir para as Sombras".
    3. Separe cada sugestão com um pipe '|'.

    Exemplo de Resposta:
    Atacar o núcleo|Analisar os padrões de ataque|Usar cobertura
    """
    messages = [{"role": "user", "content": prompt}]
    return await llm_prompt(messages)


# --- Funções do Banco de Dados Vetorial (Memória do Personagem) ---


def save_interaction(character_id: str, text: str):
    """Salva uma interação (do jogador ou da LLM) no ChromaDB."""
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[text],
        metadatas=[{"character_id": character_id}],
    )


def retrieve_memory(character_id: str, query: str, top_k=10) -> str:
    """Busca as memórias mais relevantes para um personagem com base em uma query."""
    if not query:
        return ""

    results = collection.query(
        query_texts=[query], n_results=top_k, where={"character_id": character_id}
    )

    documents = results.get("documents")
    if not documents or not documents[0]:
        return "Nenhuma memória relevante encontrada."

    # Refina os resultados com o reranker para obter o melhor contexto
    relevant_memories = reranker.rank(query, documents[0], return_documents=True)[:5]
    return "\n".join([r["text"] for r in relevant_memories])
