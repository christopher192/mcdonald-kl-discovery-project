CREATE EXTENSION IF NOT EXISTS postgis;

DROP TABLE IF EXISTS mcdonald;

CREATE TABLE mcdonald (
    id SERIAL PRIMARY KEY,
    name TEXT,
    address TEXT,
    telephone TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    categories TEXT,
    geom GEOGRAPHY(POINT, 4326)
);