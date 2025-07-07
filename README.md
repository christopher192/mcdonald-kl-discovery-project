# McDonald’s Kuala Lumpur Discovery Project

## <ins>Introduction</ins>
This project is an extended version of the Subway Discovery Project, it aims to visualize McDonald’s outlets in Kuala Lumpur. Through web scraping, geocoding retrieval, API development, and front-end development, this project provides an interactive map interface for exploring McDonald’s locations across Kuala Lumpur. An LLM (Large Language Model) is implemented to assist users in answering specific questions, such as:
- Which outlets in KL operate 24 hours?
- Which outlet allows birthday parties?

## <ins>Implementation/ Technology</ins>
Technologies Used:

- Database: PostgreSQL with PostGIS
- Web Scraping: Selenium, BeautifulSoup4
- Backend Development: Flask
- Frontend Development: React.js (Velzon template)
- LLM: OpenAI
- RAG Vector Database: Qdrant (running with Docker)

## <ins>Methodology/ Approach</ins>
In the past, the Subway Discovery project use `Haversine` formula to calculate the radius of locations in order to determine if they intersect. This project will use either the `Geodesic` method (via geopy) for more accurate distance calculation and `PostGIS` for native geospatial indexing and spatial queries.

| Method               | Description                                                                                                                                                                      |
|-----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Haversine formula** | Calculates distance assuming Earth is a perfect sphere. Minor inaccuracies for large distances or high precision.                               |
| **Geodesic (geopy)**  | Uses Vincenty or WGS-84 ellipsoid models for geodesic distances on an ellipsoid. More accurate than Haversine.                 |
| **PostGIS**           | Extends PostgreSQL with native geospatial capabilities for spatial indexing, proximity searches, polygon operations, radius searches, and intersections.

## <ins>Instruction</ins>
Kindly ensure PostgreSQL is installed with the PostGIS extension enabled for geospatial capabilities  and Docker installed for running Qdrant vector database. Also remember to create a `.env` file to store your OpenAI API key with the variable name `OPENAI_API_KEY`.

Follow these steps to run the project.

<ins>Step 1: Setup Environment</ins>
<br>
Set up your Conda environment and install the necessary libraries, execute the following command in your command prompt:
<br>
`conda create --name yourenv python=3.10`
<br>
`conda activate yourenv`
<br>
`pip install -r requirements.txt`

<ins>Step 2: Database Creation</ins>
<br>
Refer `creating_database.ipynb` for the database setup process. Please note that running this code will remove any existing table and create a new one.

<ins>Step 3: Web Scrapping & Data Population</ins>
<br>
For the web scraping process and data population, please refer to `scraping.ipynb`.

<ins>Step 4: RAG (Qdrant) + LLM</ins>
<br>
For RAG, vector database storage and LLM integration, please refer to `rag.ipynb`.

Run the following command to start Qdrant using Docker

```
docker pull qdrant/qdrant

docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

<ins>Step 5: Backend Implementation</ins>
<br>
To execute the API, refer to the `backend/api.py` file. Once running, the data can be accessed locally at:
- http://127.0.0.1:5000/get_outlets for outlet data.
- http://127.0.0.1:5000/non_rag_query for the non-RAG chat API.
- http://127.0.0.1:5000/rag_query for the RAG chat API.

This project will be using the non_rag_query endpoint.

Run the following command to start Flask API, replace `yourenv`.

```
conda activate yourenv
python backend/api.py
```

<ins>Step 6: Frontend Implementation</ins>
<br>
To launch the user interface, navigate to the `frontend/react` directory. Use `yarn install` followed by `yarn start` for setup and launch. Please avoid using `npm install` as it may lead to significant errors. Kindly using `Node v18.x.x` for successful package installation and build.

## <ins>Result</ins>
Here is a look at the user interface for the map visualization of outlets.
![alt text](images/ui-web.png)

Below is the full visual representation of the geolocation of MCDonald`s outlets, including their radius and intersections.
![alt text](images/map-visualization.png)