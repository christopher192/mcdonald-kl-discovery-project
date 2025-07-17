#!/usr/bin/env python3
# coding: utf-8

import os
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_DOCKER_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_DOCKER_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_DOCKER_PORT")

collection_name = "mcd_outlet"

client_qdrant = QdrantClient(QDRANT_URL)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

def get_all_outlet():
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, address, telephone, latitude, longitude, categories FROM mcdonald")
    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(column_names, row)) for row in rows]

def main():
    if client_qdrant.collection_exists(collection_name):
        client_qdrant.delete_collection(collection_name)

    client_qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance="Cosine")
    )

    outlets = get_all_outlet()
    points = []
    for idx, o in enumerate(outlets):
        text = (
            f"Name: {o['name']}. "
            f"Address: {o['address']}. "
            f"Latitude: {o.get('latitude')}. "
            f"Longitude: {o.get('longitude')}. "
            f"Categories: {o.get('categories', '')}."
        )
        response = client_openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding = response.data[0].embedding
        points.append(PointStruct(id=idx, vector=embedding, payload=o))

    client_qdrant.upsert(
        collection_name=collection_name,
        points=points
    )

if __name__ == "__main__":
    main()
