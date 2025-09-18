import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import CrossEncoder
from model2vec import StaticModel
import uuid
from typing import List
import re

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
    Você é um Mestre de RPG talentoso. Sua tarefa é iniciar uma batalha épica com uma narrativa envolvente e dinâmica.
    
    Personagem: {character['name']}, um(a) {character['race']} da classe {character['char_class']}.
    Descrição do Personagem: {character.get('description', 'Nenhuma.')}

    Tema da Batalha: "{battle_theme}"

    Memórias de Batalhas Anteriores (use isso para dar continuidade):
    ---
    {memory if memory else "Nenhuma."}
    ---

    Instruções:
    1. Descreva o cenário de forma vívida, em um parágrafo conciso de 2 a 3 frases de tamanho médio.
    2. Introduza um inimigo que se encaixe perfeitamente no tema da batalha.
    3. A narrativa deve terminar em um momento de tensão, preparando o jogador para a sua primeira ação.
    4. Cada parágrafo deve começar com um recuo de doze espaços.
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

    Instruções de Resposta:
    1. Descreva o resultado da ação do jogador em um parágrafo curto e impactante (2-3 frases de tamanho médio).
    2. Em seguida, descreva a reação e o contra-ataque do inimigo em outro parágrafo igualmente dinâmico (2-3 frases de tamanho médio). O inimigo deve sempre atacar de volta.
    3. Cada parágrafo deve começar em uma nova linha com um recuo de doze espaços.
    4. No final da narrativa, adicione uma linha especial no formato: `[DANO_CAUSADO:X,DANO_RECEBIDO:Y,VITORIA:Z]`
        - `DANO_CAUSADO` (X): É o dano que o JOGADOR causou ao INIMIGO.
        - `DANO_RECEBIDO` (Y): É o dano que o INIMIGO causou ao JOGADOR.
        - `VITORIA` (Z): É 'true' se o inimigo foi derrotado, ou 'false' caso contrário.

    Exemplo de Resposta:
            Com um movimento rápido e preciso, você avança pelas sombras e crava sua adaga profundamente nas costas do sentinela, que emite um som metálico de dor. A lâmina encontra resistência, mas perfura a armadura.
            O sentinela, embora ferido, reage instantaneamente. Ele gira sobre seus calcanhares com uma velocidade surpreendente e desfere um golpe poderoso com seu bastão de energia que atinge seu ombro.
    [DANO_CAUSADO:80,DANO_RECEBIDO:25,VITORIA:false]
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
