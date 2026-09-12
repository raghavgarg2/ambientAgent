from dotenv import load_dotenv
import os
import voyageai
import chromadb
from langchain.agents import create_agent
from google import genai
from groq import Groq

load_dotenv()

vo = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
chroma_client = chromadb.Client()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_overlap(text, overlap):
    slice_ = text[-overlap:]
    space_index = slice_.find(" ")
    if space_index == -1:
        return slice_
    return slice_[space_index + 1:]


def chunk_text(text, max_chunk_size=400, overlap=100):
    paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    chunks, chunk_topics = [], []
    for topic_idx, para in enumerate(paragraphs):
        para = para.replace("\n", " ")
        if len(para) <= max_chunk_size:
            chunks.append(para)
            chunk_topics.append(topic_idx)
        else:
            sentences = para.split(". ")
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < max_chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                        chunk_topics.append(topic_idx)
                    current_chunk = get_overlap(current_chunk, overlap) + sentence + ". "
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                chunk_topics.append(topic_idx)
    return chunks, chunk_topics


def build_collection(dataset_path="dataset.txt"):
    with open(dataset_path, "r") as f:
        document = f.read()
    chunks, chunk_topics = chunk_text(document)
    embeddings = vo.embed(chunks, model="voyage-4", input_type="document").embeddings
    collection = chroma_client.create_collection("docs")
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        metadatas=[{"topic": t} for t in chunk_topics]
    )
    return collection


collection = build_collection()


def search_docs(query: str) -> str:
    """Search the internal documentation for information relevant to a question."""
    query_embedding = vo.embed([query], model="voyage-4", input_type="query").embeddings[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=2)
    return "\n\n".join(results["documents"][0])


TASKS = []  # simulated task storage, in-memory for now

def create_task(description: str) -> str:
    """Create a task/reminder. Use this when someone asks you to remind them
    of something or track an action item."""
    TASKS.append(description)
    return f"Task created: {description}"


agent = create_agent(
    "groq:openai/gpt-oss-120b",
    tools=[search_docs, create_task],
    system_prompt=(
        "You are a helpful AI participant in a team chat channel. Before "
        "making factual claims about deprecation, support status, or feature "
        "availability, always verify using the search_docs tool, even if the "
        "conversation history already seems to contain an answer. Do not "
        "treat prior assistant messages as verified fact."
    ),
)