import unittest
from scraper import scrape_website, process_website, save_content_to_file, extract_keywords

class TestScraper(unittest.TestCase):
    def test_scrape_website_real_url(self):
        test_url = "https://www.vrbo.com/vacation-rentals?msockid=10c55a28d319616f2d1249d6d222601a"

        content = scrape_website(test_url)

        print("count: ",len(content),"content: ",content)

class TestEmBedding(unittest.TestCase):
    def test_embedding_process(self):
        test_url = "https://www.microsoft.com/en-us/"

        result = process_website(test_url)

        print("result: ",result)

class TestCleanAndSave(unittest.TestCase):
    def test_clean_save(self):
        test_url = "https://www.vrbo.com/"

        cleaned_content=scrape_website(test_url)

        save_content_to_file(cleaned_content,test_url)

class TestExtractKeywords(unittest.TestCase):
    def test_ExtractKeywords(self):
        test_url = "https://www.td.com/ca/en/personal-banking"

        cleaned_content=scrape_website(test_url)

        keywords=extract_keywords(cleaned_content,5)
        print(keywords)

if __name__ == "__main__":
    unittest.main()
