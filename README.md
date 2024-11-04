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

  deploy the embedding and large language two models

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

### embedding parsing config

knowledgeBaseUtilities.py

currently hardcode like this, you can adjust it to get better effect

```python
if not datasets:
    rag_object.create_dataset(
        name=name,
        avatar="",
        description="test for English text",
        embedding_model="BAAI/bge-large-en-v1.5",
        language="English",
        permission="me",
        chunk_method="naive",
        parser_config=None
    )



