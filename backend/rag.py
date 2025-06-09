from together import Together

client = Together()

import requests
from bs4 import BeautifulSoup

def scrape_pg_essay():

    url = 'https://paulgraham.com/foundermode.html'

    try:
        # Send GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Paul Graham's essays typically have the main content in a font tag
        # You might need to adjust this selector based on the actual HTML structure
        content = soup.find('font')

        if content:
            # Extract and clean the text
            text = content.get_text()
            # Remove extra whitespace and normalize line breaks
            text = ' '.join(text.split())
            return text
        else:
            return "Could not find the main content of the essay."

    except requests.RequestException as e:
        return f"Error fetching the webpage: {e}"

# Scrape the essay
pg_essay = scrape_pg_essay()

# Naive fixed sized chunking with overlaps

def create_chunks(document, chunk_size=300, overlap=50):
    return [document[i : i + chunk_size] for i in range(0, len(document), chunk_size - overlap)]
  
  
chunks = create_chunks(pg_essay, chunk_size=250, overlap=30)

from typing import List
import numpy as np

def generate_embeddings(input_texts: List[str], model_api_string: str) -> np.ndarray:
    """Generate embeddings from Together python library.

    Args:
        input_texts: a list of string input texts.
        model_api_string: str. An API string for a specific embedding model of your choice.

    Returns:
        embeddings_list: a list of embeddings. Each element corresponds to the each input text.
    """
    outputs = client.embeddings.create(
        input=input_texts,
        model=model_api_string,
    )
    return np.array([x.embedding for x in outputs.data])
  
embeddings = generate_embeddings(chunks, "BAAI/bge-large-en-v1.5")


def vector_retreival(query: str, top_k: int = 5, vector_index: np.ndarray = None) -> List[int]:
    """
    Retrieve the top-k most similar items from an index based on a query.
    Args:
        query (str): The query string to search for.
        top_k (int, optional): The number of top similar items to retrieve. Defaults to 5.
        index (np.ndarray, optional): The index array containing embeddings to search against. Defaults to None.
    Returns:
        List[int]: A list of indices corresponding to the top-k most similar items in the index.
    """

    query_embedding = np.array(generate_embeddings([query], 'BAAI/bge-large-en-v1.5')[0])

    similarity_scores = np.dot(query_embedding, vector_index.T)

    return list(np.argsort(-similarity_scores)[:top_k])
  
top_k_indices = vector_retreival(query =  "What are 'skip-level' meetings?", top_k = 5, vector_index = embeddings)
top_k_chunks = [chunks[i] for i in top_k_indices]

def rerank(query: str, chunks: List[str], top_k = 3) -> List[int]:
    response = client.rerank.create(
    model = "Salesforce/Llama-Rank-V1",
    query = query,
    documents = chunks,
    top_n = top_k
    )

    return [result.index for result in response.results]

rerank_indices = rerank("What are 'skip-level' meetings?", chunks = top_k_chunks, top_k=3)

reranked_chunks = ''

for index in rerank_indices:
    reranked_chunks += top_k_chunks[index] + '\n\n'

print(reranked_chunks)

query = "What are 'skip-level' meetings?"

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    messages=[
      {"role": "system", "content": "You are a helpful chatbot."},
      {"role": "user", "content": f"Answer the question: {query}. Use only information provided here: {reranked_chunks}"},
    ],
)

response.choices[0].message.content