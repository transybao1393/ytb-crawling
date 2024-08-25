import scrapy
from scrapy_youtube_crawling.items import ScrapyYoutubeCrawlingItem
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import random

class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    allowed_domains = ["youtube.com"]

    def __init__(self, *args, **kwargs):
        # Specify the custom User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-A526B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-S906E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; OnePlus 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        ]
        user_agent = random.choice(user_agents)

        # Run in headless mode
        self.driver = self.create_chrome_driver(user_agent=user_agent)

    def start_requests(self):
        # Read URLs from the input file
        with open("input_urls.txt", "r") as f:
            urls = f.readlines()

        for url in urls:
            yield scrapy.Request(url=url.strip(), callback=self.parse)

    def parse(self, response):
        item = ScrapyYoutubeCrawlingItem()

        # Parse video title
        item['title'] = response.xpath('//meta[@property="og:title"]/@content').get()

        # Parse video description
        item['description'] = response.xpath('//meta[@property="og:description"]/@content').get()

        # Parse video duration (in seconds)
        duration = response.xpath('//meta[@itemprop="duration"]/@content').get()
        item['duration'] = self.parse_duration(duration)

        # Parse comments (simplified example)
        soup = BeautifulSoup(response.text, 'lxml')

        # call another function to get youtube comments
        item['comments'] = self.scrape_youtube_comments(response)
        
        self.driver.quit()  # Close the Selenium browser after scraping

        # Parse subtitles (if available)
        subtitles = []
        for track in soup.find_all("track"):
            subtitles.append(track.get("src"))
        item['subtitles'] = subtitles

        yield item

    def parse_duration(self, duration_string):
        # Parse ISO 8601 duration format (e.g., PT1H2M3S)
        pattern = re.compile(r'PT(\d+H)?(\d+M)?(\d+S)?')
        match = pattern.match(duration_string)
        if not match:
            return 0

        hours = int(match.group(1)[:-1]) if match.group(1) else 0
        minutes = int(match.group(2)[:-1]) if match.group(2) else 0
        seconds = int(match.group(3)[:-1]) if match.group(3) else 0
        return hours * 3600 + minutes * 60 + seconds

    def create_chrome_driver(self, user_agent):
        # Initialize Selenium WebDriver (Chrome)
        # chrome_options = webdriver.ChromeOptions()
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_argument("--headless")  # Run in headless mode (optional)
        chrome_options.add_argument("--disable-gpu")  # Disable GPU rendering (optional)
        chrome_options.add_argument("--no-sandbox")  # Needed for some Linux environments
        chrome_options.add_argument("--incognito")  # Run in incognito mode to avoid keeping session
        
        # Initialize the Chrome WebDriver with webdriver_manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver
    
    def scrape_youtube_comments(self, response):
        self.driver.get(response.url)
        time.sleep(5)

        # Scroll to load more comments (adjust as needed)
        for _ in range(2):  # Scroll down 2 times
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(5)  # Wait for comments to load

        # Scroll down to load more comments
        comment_list = []
        comments = self.driver.find_elements(By.CSS_SELECTOR, "#contents #content-text")
        authors = self.driver.find_elements(By.CSS_SELECTOR, "#contents #author-text")
        for comment, author in zip(comments, authors):
            comment_list.append({
                author.text: comment.text
            })
        
        return comment_list
