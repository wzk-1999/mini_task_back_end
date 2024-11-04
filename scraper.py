import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import Config
from db import WebsiteEmbedding, SessionLocal, init_db
from volcenginesdkarkruntime import Ark

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter

from utilities.knowledgeBaseUtilities import filter_advertisements, create_knowledge_base, upload_file_in_binary, \
    embedding_file

# Initialize the database
init_db()

client = Ark(api_key=Config().ARK_API_KEY)


def scrape_website(url):
    """Scrape and clean content from the URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract raw text from the page
    content = soup.get_text()

    # Clean content by removing extra whitespace and empty lines
    cleaned_content = '\n'.join(line.strip() for line in content.splitlines() if line.strip())

    # Further filter to eliminate advertisements
    cleaned_content, removed_count = filter_advertisements(cleaned_content)
    print(f"Number of lines removed: {removed_count}")

    return cleaned_content

def save_content_to_file(content, url):
    """Save cleaned content to a .txt file, using URL's domain and path as filename."""
    # Extract hostname and path from URL to use as filename
    parsed_url = urlparse(url)
    # Create a filename based on URL path, replacing special characters
    filename = f"{parsed_url.netloc}{parsed_url.path}".replace('/', '_').replace('.', '_')
    filename = f"{filename}.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Cleaned content saved to {filename}")

def generate_embedding(text):
    """Generate an embedding for the given text content."""
    response = client.embeddings.create(
    model=Config().ARK_MODEL,
    input=text
)
    print("Response:", response)
    return response.data[0].embedding

def save_knowledge_base(url, content, embedding, keywords):
    """Save the scraped content, embedding, and keywords to the database."""
    db = SessionLocal()
    website_embedding = WebsiteEmbedding(
        url=url,
        content=content,
        embedding=embedding,
        keywords=keywords
    )
    db.add(website_embedding)
    db.commit()
    db.close()


def process_website(url):
    """Main function to scrape, embed, and store content."""
    db = SessionLocal()

    # Check if the URL already exists in the database
    existing_entry = db.query(WebsiteEmbedding).filter(WebsiteEmbedding.url == url).first()
    if existing_entry:
        print("Skipped - URL already exists in the database")
        print("Skipped uploading and embedding to knowledge")
        return existing_entry  # Return the existing entry if found

    # URL does not exist, scrape, embed, and save to the database
    content = scrape_website(url)

    # Check or create the knowledge base
    create_knowledge_base("test")

    # Upload the file to the knowledge base
    filename = upload_file_in_binary(content, url)

    # Initiate embedding
    embedding_file(filename)

    # Limit content for testing purposes and saving token consumption; in production, this should be removed
    embedding = generate_embedding('\n'.join(content.splitlines()[:5]))

    top_keywords = extract_keywords(content, num_keywords=5)

    # Save to knowledge base
    save_knowledge_base(url, content, embedding, top_keywords)

    # Retrieve and return the newly created entry
    new_entry = db.query(WebsiteEmbedding).filter(WebsiteEmbedding.url == url).first()
    db.close()
    return new_entry


def extract_keywords(content, num_keywords=5):
    """Extracts the top keywords from content by frequency analysis."""

    # Remove special characters and lowercase the text
    cleaned_text = re.sub(r'[^a-zA-Z\s]', '', content).lower()

    # Tokenize the text into words
    words = word_tokenize(cleaned_text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word not in stop_words]

    # Count word frequency
    word_counts = Counter(filtered_words)

    # Extract the top 'num_keywords' keywords based on frequency
    top_keywords = [word for word, count in word_counts.most_common(num_keywords)]

    return top_keywords

