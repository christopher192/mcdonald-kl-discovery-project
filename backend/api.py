import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import logging
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from geopy.distance import geodesic

load_dotenv()

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client_qdrant = QdrantClient("http://localhost:6333")
collection_name = "mcd_outlet"

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname='postgis',
            user='postgres',
            password='admin',
            host='localhost',
            port='5432'
        )
        return conn
    except psycopg2.Error as e:
        app.logger.error('Database connection error: %s', e)
        return None

@app.route('/get_outlets', methods=['GET'])
def get_outlets():
    conn = get_db_connection()
    if conn is None:
        return jsonify(status='error', message='Database connection failed.'), 500
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
        return jsonify(data=outlet_list, status='success')
    except Exception as e:
        app.logger.error('Error retrieving outlets: %s', e)
        return jsonify(status='error', message=str(e)), 500
    finally:
        conn.close()

@app.route('/get_outlets_geodesic', methods=['GET'])
def get_outlets_geodesic():
    conn = get_db_connection()
    if conn is None:
        return jsonify(status='error', message='Database connection failed.'), 500
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('''
                    SELECT 
                        id, name, address, latitude, longitude
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
                    if distance_km <= 10: # 5km + 5km
                        intersects = 1
                        break
            outlet['intersects_5km'] = intersects

        return jsonify(data=outlet_list, status='success')

    except Exception as e:
        app.logger.error('Error retrieving outlets: %s', e)
        return jsonify(status='error', message=str(e)), 500

    finally:
        conn.close()

@app.route("/rag_query", methods=["POST"])
def handle_rag_query():
    data = request.get_json()
    user_query = data.get("query")
    if not user_query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

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

        return jsonify({"answer": answer})
    except Exception as e:
        app.logger.error('Error in rag_query: %s', e)
        return jsonify(status='error', message=str(e)), 500

@app.route("/non_rag_query", methods=["POST"])
def non_rag_query():
    data = request.get_json()
    messages = data.get("messages")
    if not messages:
        return jsonify({"error": "Missing 'messages' in request body"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify(status='error', message='Database connection failed.'), 500

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

        return jsonify({"answer": answer})
    
    except Exception as e:
        app.logger.error('Error in non_rag_query: %s', e)
        return jsonify(status='error', message=str(e)), 500

    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)