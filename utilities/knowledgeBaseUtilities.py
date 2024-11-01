import re
from ragflow import RAGFlow
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
    rag_object = RAGFlow(api_key=Config().LLM_API_KEY, base_url=Config().LLM_API_URL)
    dataset = rag_object.create_dataset(name=name)

# def upload_file_in_binary():
#     dataset.upload_documents([{"display_name": "1.txt", "blob": "<BINARY_CONTENT_OF_THE_DOC>"}, {"display_name": "2.pdf", "blob": "<BINARY_CONTENT_OF_THE_DOC>"}])

def embedding_file():
    rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
    dataset = rag_object.create_dataset(name="dataset_name")
    documents = [
        {'display_name': 'test1.txt', 'blob': open('./test_data/test1.txt',"rb").read()},
        {'display_name': 'test2.txt', 'blob': open('./test_data/test2.txt',"rb").read()},
        {'display_name': 'test3.txt', 'blob': open('./test_data/test3.txt',"rb").read()}
    ]
    dataset.upload_documents(documents)
    documents = dataset.list_documents(keywords="test")
    ids = []
    for document in documents:
        ids.append(document.id)
    dataset.async_parse_documents(ids)
    print("Async bulk parsing initiated.")