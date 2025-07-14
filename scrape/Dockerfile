FROM python:3.10-slim
WORKDIR /app
COPY scrape_and_insert.py .
RUN pip install psycopg2-binary selenium beautifulsoup4
CMD ["python", "scrape_and_insert.py"]