import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import CrossEncoder
from model2vec import StaticModel
import uuid
from typing import List

# Importe a função de LLM do seu novo arquivo
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
    Você é um Mestre de RPG talentoso. Sua tarefa é iniciar uma batalha épica.
    
    Personagem: {character['name']}, um(a) {character['race']} da classe {character['char_class']}.
    Descrição do Personagem: {character.get('description', 'Nenhuma.')}

    Tema da Batalha: "{battle_theme}"

    Memórias de Batalhas Anteriores (use isso para dar continuidade):
    ---
    {memory if memory else "Nenhuma."}
    ---

    Instruções:
    1. Descreva o cenário de forma vívida e imersiva.
    2. Introduza um inimigo que se encaixe no tema da batalha.
    3. A narrativa deve terminar em um momento de tensão, preparando o jogador para agir.
    4. Seja criativo! Se o personagem já enfrentou inimigos parecidos, faça uma referência sutil.
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
    """Continua a narrativa com base na ação do jogador."""
    history_str = "\n".join(history)
    prompt = f"""
    Você é um Mestre de RPG talentoso. Continue a narrativa da batalha com base na ação do jogador.

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

    Instruções:
    1. Descreva o resultado da ação do jogador de forma dramática.
    2. Narre a reação ou o contra-ataque do inimigo.
    3. Mantenha a história fluindo. Não termine a batalha a menos que a ação do jogador seja claramente final.
    4. A narrativa deve ser apenas a continuação da história, sem saudações ou comentários para o jogador.
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
    relevant_memories = rerank_context(query, documents[0])
    return "\n".join(relevant_memories)
