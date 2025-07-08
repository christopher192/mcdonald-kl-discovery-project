# McDonald’s Kuala Lumpur Discovery Project

## <ins>Introduction</ins>
This project is an extended version of the Subway Discovery Project, it aims to visualize McDonald’s outlets in Kuala Lumpur. Through web scraping, geocoding retrieval, API development, and front-end development, this project provides an interactive map interface for exploring McDonald’s locations across Kuala Lumpur. An LLM (Large Language Model) is implemented to assist users in answering specific questions, such as:
- Which outlets in KL operate 24 hours?
- Which outlet allows birthday parties?

## <ins>Implementation/ Technology</ins>
Technologies Used:

- Database: PostgreSQL with PostGIS
- Web Scraping: Selenium, BeautifulSoup4
- Backend Development: Flask, FastAPI
- Frontend Development: React.js (Velzon template)
- LLM: OpenAI
- RAG Vector Database: Qdrant (running with Docker)

## <ins>Methodology/ Approach</ins>
In the past, the Subway Discovery project use `Haversine` formula to calculate the radius of locations in order to determine if they intersect. This project will use `Geodesic` method (via geopy) for more accurate distance calculation and `PostGIS` for native geospatial indexing and spatial queries.

| Method               | Description                                                                                                                                                                      |
|-----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Haversine formula** | Calculates distance assuming Earth is a perfect sphere. Minor inaccuracies for large distances or high precision.                               |
| **Geodesic (geopy)**  | Uses Vincenty or WGS-84 ellipsoid models for geodesic distances on an ellipsoid. More accurate than Haversine.                 |
| **PostGIS**           | Extends PostgreSQL with native geospatial capabilities for spatial indexing, proximity searches, polygon operations, radius searches, and intersections.

Using `ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY` stores location data in a way that PostGIS understands as real earth locations, enabling accurate geospatial queries. Without this, PostGIS treats the data as flat geometry, resulting in inaccurate calculations for latitude and longitude. For more information, see [https://postgis.net/docs/ST_MakePoint.html](https://postgis.net/docs/ST_MakePoint.html).

```
INSERT INTO mcdonald (
    name,
    address,
    telephone,
    latitude,
    longitude,
    categories,
    geom
)
VALUES (
    %s,  -- name
    %s,  -- address
    %s,  -- telephone
    %s,  -- latitude
    %s,  -- longitude
    %s,  -- categories
    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY  -- geom
```

This query selects each McDonald's outlet and checks if there is any other outlet within 10 km (to determine if their 5 km catchments intersect). It adds a column `intersects_5km`:
- `1` → if at least one other outlet is within 10 km
- `0` → if none are within 10 km

```
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
```

Using `geopy’s geodesic (Vincenty)`
Here is the code to check if two outlets' 5 km radius catchments intersect. It calculates the geodesic distance between two geographic coordinates using the WGS-84 ellipsoid model, which is more accurate than the Haversine formula (which assumes Earth is a perfect sphere).

```
from geopy.distance import geodesic

point1 = (lat1, lon1)
point2 = (lat2, lon2)

distance_km = geodesic(point1, point2).km

# check if their 5 km radius catchments intersect
if distance_km <= 10: # 5km + 5km
    print("The outlets' 5 km catchments intersect.")
else:
    print("The outlets' 5 km catchments do not intersect.")
```

On the chatbot page, short-term memory is implemented so the bot remembers all previous messages within the current chat session. Here`s the key implementation. 
1. `React`: Maintain messages array in React state.
```
const [messages, setMessages] = useState([
  { role: "assistant", content: "Hello, how can I help you?" },
  { role: "user", content: "What time does McDonald's Bukit Bintang open?" },
  { role: "assistant", content: "McDonald's Bukit Bintang operates 24 hours daily." },
  { role: "user", content: "Which outlets have birthday party facilities?" },
  { role: "assistant", content: "Several outlets offer birthday party facilities, including McDonald's Bukit Bintang, Bangsar, and Alpha Angle." }
]);
```
2. Pass the full conversation history, including both user and assistant messages, to the API with each request.
3. Other methods might be 
    - Backend session store (Redis)
    - Database storage with user ID
    - OpenAI function calling (Structured Memory)
    - Stateful frameworks
        - LangChain memory module (ConversationBufferMemory, etc..)
        - LLM orchestration tools (Built-in Session Memory, etc..)

## <ins>Instruction</ins>
Kindly ensure PostgreSQL is installed with the PostGIS extension enabled for geospatial capabilities  and Docker installed for running Qdrant vector database. Also remember to create a `.env` file to store your OpenAI API key with the variable name `OPENAI_API_KEY`.

Follow these steps to run the project.

<ins>Step 1: Setup Environment</ins>
<br>
Set up your Conda environment and install the necessary libraries, execute the following command in your command prompt.

```
conda create --name yourenv python=3.10
conda activate yourenv
pip install -r requirements.txt
```

<ins>Step 2: Database Creation</ins>
<br>
Refer `creating_database.ipynb` for the database setup process. Please note that running this code will remove any existing table and create a new one.

<ins>Step 3: Web Scrapping & Data Population</ins>
<br>
For the web scraping process and data population, please refer to `scraping.ipynb`.

<ins>Step 4: RAG (Qdrant) + LLM</ins>
<br>
For RAG, vector database storage and LLM integration, please refer to `rag.ipynb`.

Run the following command to start Qdrant using Docker.

```
docker pull qdrant/qdrant

docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

<ins>Step 5: Backend Implementation</ins>
<br>
To execute the API, refer to the `backend/api.py` file. Once running, the data can be accessed locally at:
- http://127.0.0.1:5000/get_outlets_geodesic for outlet data (Geodesic).
- http://127.0.0.1:5000/get_outlets for outlet data (PostGIS).
- http://127.0.0.1:5000/non_rag_query for the non-RAG chat API.
- http://127.0.0.1:5000/rag_query for the RAG chat API.

This project will be using the non_rag_query endpoint.

To start the Flask API, run the following commands, replacing `yourenv` with your environment name.

```
conda activate yourenv
python backend/flask/api.py
```

```
uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

<ins>Step 6: Frontend Implementation</ins>
<br>
To launch the user interface, navigate to the `frontend/react` directory. Use `yarn install` followed by `yarn start` for setup and launch. Please avoid using `npm install` as it may lead to significant errors. Kindly using `Node v18.x.x` for successful package installation and build.

## <ins>Result</ins>
Here is a look at the user interface for the map visualization of outlets.
![alt text](images/ui-web.png)

Below is a complete visual representation of McDonald's outlets generated using PostGIS, showing their locations, 5 km radius coverage, and any intersections within that distance.
![alt text](images/map-visualization.png)

Other visualization based on Geodesic.
![alt text](images/map-visualization2.png)

Here is the UI for interacting with the McDonald's chatbot, where can ask questions and receive answers.
![alt text](images/chat.png)