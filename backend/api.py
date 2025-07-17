import os
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from openai import OpenAI
from qdrant_client import QdrantClient
from geopy.distance import geodesic

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client_qdrant = QdrantClient(os.getenv("QDRANT_URL"))
collection_name = "mcd_outlet"

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT")
        )
        return conn
    except psycopg2.Error as e:
        logging.error(f'Database connection error: {e}')
        return None

class QueryRequest(BaseModel):
    query: Optional[str] = None

class MessagesRequest(BaseModel):
    messages: List[Dict[str, str]]

@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}

@app.get("/get_outlets")
def get_outlets():
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('''
                    SELECT 
                        a.id,
                        a.name,
                        a.address,
                        a.latitude,
                        a.longitude,
                        CASE 
                            WHEN EXISTS (
                                SELECT 1 
                                FROM mcdonald b
                                WHERE a.id != b.id
                                AND ST_DWithin(a.geom, b.geom, 10000)
                            )
                            THEN 1
                            ELSE 0
                        END AS intersects_5km
                    FROM mcdonald a;
                ''')
                outlets = cursor.fetchall()
                outlet_list = [dict(outlet) for outlet in outlets]
        return {"data": outlet_list, "status": "success"}
    except Exception as e:
        logging.error(f'Error retrieving outlets: {e}')
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/get_outlets_geodesic")
def get_outlets_geodesic():
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('''
                    SELECT id, name, address, latitude, longitude
                    FROM mcdonald;
                ''')
                outlets = cursor.fetchall()
                outlet_list = [dict(outlet) for outlet in outlets]

        for outlet in outlet_list:
            outlet_coord = (outlet['latitude'], outlet['longitude'])
            intersects = 0
            for other in outlet_list:
                if outlet['id'] != other['id']:
                    other_coord = (other['latitude'], other['longitude'])
                    distance_km = geodesic(outlet_coord, other_coord).kilometers
                    if distance_km <= 10:  # 5km + 5km
                        intersects = 1
                        break
            outlet['intersects_5km'] = intersects

        return {"data": outlet_list, "status": "success"}
    except Exception as e:
        logging.error(f'Error retrieving outlets: {e}')
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/rag_query")
def handle_rag_query(request: QueryRequest):
    user_query = request.query
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")

    try:
        response = client_openai.embeddings.create(
            model="text-embedding-3-small",
            input=user_query
        )
        query_embedding = response.data[0].embedding

        search_results = client_qdrant.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=30
        )
        retrieved = [hit.payload for hit in search_results]

        context_text = "\n".join([f"{o['name']} - {o['address']}" for o in retrieved])

        prompt = f"""
        You are a helpful assistant for McDonald's outlet search.

        User Query: {user_query}

        Matching Outlets:
        {context_text}

        Answer the user clearly and concisely based only on the outlets above. Do not use numbered lists. Instead, list items separated by commas for readability.
        """

        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )

        answer = response.choices[0].message.content

        return {"answer": answer}

    except Exception as e:
        logging.error(f'Error in rag_query: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/non_rag_query")
def non_rag_query(request: MessagesRequest):
    messages = request.messages
    if not messages:
        raise HTTPException(status_code=400, detail="Missing 'messages' in request body")

    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")

    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('''
                    SELECT id, name, address, telephone, latitude, longitude, categories
                    FROM mcdonald;
                ''')
                outlets = cursor.fetchall()
                outlet_list = [dict(outlet) for outlet in outlets]

        context_text = "\n".join([
            f"{o['name']} - {o['address']} - {o.get('categories','')}" for o in outlet_list
        ])

        system_prompt = {
            "role": "system",
            "content": f"""
You are a helpful assistant for McDonald's outlet search.

All Outlets:
{context_text}

Use the above outlets data to answer user questions clearly and concisely. Do not use numbered lists. Instead, list items separated by commas for readability.
"""
        }

        full_messages = [system_prompt] + messages

        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=full_messages
        )
        answer = response.choices[0].message.content

        return {"answer": answer}

    except Exception as e:
        logging.error(f'Error in non_rag_query: {e}')
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()