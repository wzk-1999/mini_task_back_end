import re
from urllib.parse import urlparse

from ragflow_sdk import RAGFlow
from config import Config

def filter_advertisements(content):
    """Filter out sections likely to contain ads or irrelevant content."""
    # Define patterns or keywords commonly associated with ads
    ad_patterns = [
        r"(buy now|click here|limited time offer|subscribe|sale|promotion)",
        r"(sponsored|advertisement|ads by)",
        r"(sign up|log in|join now|create an account)"
    ]

    # Count lines before filtering
    original_lines = content.splitlines()

    # Filter lines by removing those matching ad patterns
    filtered_lines = [
        line for line in original_lines
        if not any(re.search(pattern, line, re.IGNORECASE) for pattern in ad_patterns)
    ]

    removed_count = len(original_lines) - len(filtered_lines)
    filtered_content = '\n'.join(filtered_lines)

    return filtered_content, removed_count


def create_knowledge_base(name):
    """Create a knowledge base in RAGFlow if it doesn't exist."""
    rag_object = RAGFlow(api_key=Config().ARK_API_KEY, base_url=Config().ARK_API_LINK)
    datasets = rag_object.list_datasets(name=name)
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
        print(f"Knowledge base '{name}' created.")
    else:
        print(f"Knowledge base '{name}' already exists.")

def upload_file_in_binary(file_content, url):
    """Upload content in binary form to RAGFlow with a unique filename based on the URL."""
    rag_object = RAGFlow(api_key=Config().ARK_API_KEY, base_url=Config().ARK_API_LINK)
    dataset = rag_object.list_datasets(name="test")

    # Create a filename based on URL path, replacing special characters
    parsed_url = urlparse(url)
    filename = f"{parsed_url.netloc}{parsed_url.path}".replace('/', '_').replace('.', '_')

    # Upload the document to the RAGFlow dataset
    dataset.upload_documents([{"display_name": f"{filename}.txt", "blob": file_content}])

    return filename

def embedding_file(filename):
    rag_object = RAGFlow(api_key=Config().ARK_API_KEY, base_url=Config().ARK_API_LINK)
    dataset = rag_object.list_datasets(name="test")
    filename=filename+'.txt'
    document = dataset.list_documents(name=filename)[0]
    dataset.async_parse_documents([document.id])
    print("Async bulk parsing initiated.")