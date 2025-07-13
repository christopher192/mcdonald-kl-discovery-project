#!/usr/bin/env python
# coding: utf-8

# In[2]:


import os
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams


# In[3]:


load_dotenv()

# building connection to qdrant
client_qdrant = QdrantClient("http://localhost:6333")
collection_name = "mcd_outlet"

# building connection to OpenAI
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# In[4]:


def get_all_outlet():
    conn = psycopg2.connect(
        dbname='postgis',
        user='postgres',
        password='admin',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, address, telephone, latitude, longitude, categories FROM mcdonald")
    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(column_names, row)) for row in rows]

def rag_query(user_query):
    response = client_openai.embeddings.create(
        model="text-embedding-3-small",
        input=user_query
    )
    query_embedding = response.data[0].embedding

    search_results = client_qdrant.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=5
    )
    
    retrieved = [hit.payload for hit in search_results]

    context_text = "\n".join([f"{o['name']} - {o['address']}" for o in retrieved])

    prompt = f"""
    You are a helpful assistant for McDonald's outlet search.

    User Query: {user_query}

    Matching Outlets:
    {context_text}

    Answer the user clearly and concisely based only on the outlets above.
    """

    response = client_openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    return response.choices[0].message.content


# In[5]:


# check if collection exists
if client_qdrant.collection_exists(collection_name):
    client_qdrant.delete_collection(collection_name)

# create collection with correct vector size
client_qdrant.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=1536, distance="Cosine")
)


# In[6]:


# embed and upload each outlet
outlets = get_all_outlet()

points = []
for idx, o in enumerate(outlets):
    text = (
        f"Name: {o['name']}. "
        f"Address: {o['address']}. "
        f"Latitude: {o.get('latitude')}. "
        f"Longitude: {o.get('longitude')}. "
        f"Categories: {o.get('categories','')}."
        f"geom: {o.get('geom','')}."
    )
    response = client_openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    embedding = response.data[0].embedding
    points.append(PointStruct(id=idx, vector=embedding, payload=o))

# Upsert all at once
client_qdrant.upsert(
    collection_name=collection_name,
    points=points
)


# In[7]:


# answer = rag_query("Which outlets in KL operate 24 hours?")
answer = rag_query("Which outlet allows birthday parties?")
print(answer)

