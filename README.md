# Web Scraper for Visitor Classification

## Preparation and Prerequisite: 
- Python 3.x
- pip (Python package installer)

### Deploy RAGFlow: 
reference: https://github.com/infiniflow/ragflow/blob/main/README.md, https://ragflow.io/docs/dev/deploy_local_llm

- CPU >= 4 cores
- RAM >= 16 GB
- Disk >= 50 GB
- Docker >= 24.0.0 & Docker Compose >= v2.26.1

  deploy the embedding and large language two model

register an account for api key generation

### API CONFIGURATION

 Follow the config-example.py to config necessary info

## Set up:

`docker run -d -p 5432:5432 --name pgvector -e POSTGRES_PASSWORD=yourpassword ankane/pgvector`

`docker exec -it pgvector psql -U postgres`

`create database "your db name"`

`python -m venv venv`

`venv\Scripts\activate` for windows

`source venv/bin/activate` for macOS/Linux

`pip install -r requirements.txt`

`flask run`
