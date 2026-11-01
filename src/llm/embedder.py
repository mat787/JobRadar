import os

from dotenv import load_dotenv
from openai import OpenAI


class Embedder:
    """Zamienia teksty na wektory przy pomocy modelu embeddingów."""

    def __init__(self, batch_size=32):
        load_dotenv()
        self.client = OpenAI(base_url=os.environ["MODEL_URL"], api_key=os.environ["API_KEY"])
        self.model = os.environ.get("EMBEDDING_MODEL") or os.environ["MODEL_NAME"]
        self.batch_size = batch_size

    def embed(self, texts):
        vectors = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            vectors.extend(self._embed_batch(batch))
        return vectors

    def embed_one(self, text):
        return self.embed([text])[0]

    def _embed_batch(self, texts):
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]
