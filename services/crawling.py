from fastapi import BackgroundTasks
from typing import List
import subprocess


class Crawling:
    def __init__(self):
        self.crawl_dir = "scrapy_youtube_crawling"

    def crawl_url(self, urls: list[str], background_tasks: BackgroundTasks):
       
        # Write the URLs to a file that Scrapy can read
        with open(f"{self.crawl_dir}/input_urls.txt", "w") as f:
            for url in urls:
                f.write(f"{url}\n")

        # Trigger the Scrapy spider via a background task
        background_tasks.add_task(self.run_spider)

    def run_spider(self):
        subprocess.run(["scrapy", "crawl", "youtube", "-o", "output.json", "--loglevel=DEBUG"], cwd="scrapy_youtube_crawling")