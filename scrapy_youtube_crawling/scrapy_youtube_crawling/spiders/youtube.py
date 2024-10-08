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
import json
import yt_dlp as youtube_dl
from urllib.parse import urlparse, parse_qs
import socket
import websocket
import threading

class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    allowed_domains = ["youtube.com"]

    def __init__(self, *args, **kwargs):

        # FIXME: Should getting from env file
        self.SOCKET_PORT = 9002
        self.SOCKET_HOST = 'localhost'

        self.driver = None
        self.crawled_urls = set()  # To track crawled URLs

        # websocket define
        self.websocket_url = "ws://localhost:8000/ws/2"  # WebSocket server URL with client id is 2
        self.ws = None
        self.ws_thread = None

    def open_websocket(self):
        # Start the WebSocket connection in a separate thread to avoid blocking
        self.ws = websocket.WebSocketApp(
            self.websocket_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def init_driver(self):

        # Open WebSocket connection before making requests
        self.open_websocket()

        if self.driver:
            self.driver.quit()
        
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

    def closed(self, reason):
        # Method called when the spider is closed
        # self.notify_completion(reason) # reason might be one of: finished, close_spider, cancelled, shutdown
        print(f'Spider closed: {reason}')
        # close websocket when closed
        if self.ws:
            self.ws.close()
            print("WebSocket connection closed after spider completion")
        if self.ws_thread:
            self.ws_thread.join()

    def parse(self, response):
        # Add the crawled URL to the set
        self.crawled_urls.add(response.url)
        # Initialize the driver for each request
        self.init_driver()
        item = ScrapyYoutubeCrawlingItem()

        # Parse video title
        item['title'] = response.xpath('//meta[@property="og:title"]/@content').get()

        # Parse video description
        item['description'] = response.xpath('//meta[@property="og:description"]/@content').get()

        # Parse video duration (in seconds)
        duration = response.xpath('//meta[@itemprop="duration"]/@content').get()
        item['duration'] = self.parse_duration(duration)

        # call another function to get youtube comments
        item['comments'] = self.scrape_youtube_comments(response)
        item['subtitles'] = self.download_subtitles(response.url)

        
        yield item

        # nofity 
        video_id = parse_qs(urlparse(response.url).query).get('v', [None])[0]
        self.notify_via_websocket(video_id)

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

    def download_subtitles(self, video_url):
        # Extract video ID more robustly
        video_id = parse_qs(urlparse(video_url).query).get('v', [None])[0]
        
        if not video_id:
            return "Invalid YouTube URL"

        save_as = f'{video_id}.%(ext)s'
        ytdlp_options = {
            'ratelimit': 100 * 1024,  # Limit download speed to 100KB/s
            'writesubtitles': True,  # Download subtitles if available
            'skip_download': True,   # Skip video download
            'subtitleslangs': ['en'],  # Specify language for subtitles
            'outtmpl': save_as,  # Save as video_id.extension
            'listsubs': True,  # List available subtitles
            'writeautomaticsub': True,  # Enable auto-generated subtitles
            'subtitlesformat': 'srt',  # Subtitles in SRT format
        }

        try:
            isDownloaded = False
            with youtube_dl.YoutubeDL(ytdlp_options) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                subtitles = info_dict.get('subtitles', {})

                if subtitles:
                    print("Available subtitles:")

                    for lang, sub_info in subtitles.items():
                        print(f"Language: {lang}, Formats: {sub_info}")

                    # Download subtitles
                    ydl.download([video_url])
                    time.sleep(3)
                    isDownloaded = True
                
            if isDownloaded:
                return video_id
            else:
                return f'No subtitles available for this video id {video_id}.'
        except youtube_dl.utils.DownloadError as e:
            print(f"Download error: {e}")
            return f'No subtitles available for this video id {video_id}, error {e}'
        except Exception as e:
            print(f"Unexpected error: {e}")
            return f'No subtitles available for this video id {video_id}, error {e}'


    # websocket events
    def on_open(self, ws):
        print("WebSocket connection opened")

    def on_message(self, ws, message):
        print(f"Message from server: {message}")

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    def notify_via_websocket(self, video_id: str):
        try:
            message = f"{video_id} crawled"
            self.ws.send(message)
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")