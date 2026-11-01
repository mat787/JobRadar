from openai import OpenAI
import numpy as np
from numpy.linalg import norm

client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")

query = "Python, SQL, analiza danych, Docker"
offers = [
    "Junior Python Developer: Django, PostgreSQL, Docker",
    "Data Analyst: SQL, Power BI, Excel",
    "Frontend Developer: React, TypeScript",
    "Księgowa: rozliczenia VAT, Symfonia",
    "Data Engineer (EN): Python, Spark, SQL pipelines",
    "Tralalero Tralala: skibidi, Pythom, SQL, Analiza danych, Docker, miau"
]

response = client.embeddings.create(
    model="text-embedding-bge-m3",
    input=[query] + offers,
)

query_vector = response.data[0].embedding
offer_vectors = [item.embedding for item in response.data[1:]]

results = []
for offer, offer_vector in zip(offers, offer_vectors):
    similarity = np.dot(query_vector, offer_vector) / (norm(query_vector) * norm(offer_vector))
    results.append((similarity, offer))

results = sorted(results, reverse=True)[:2]
print(results)

