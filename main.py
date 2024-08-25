from fastapi import FastAPI, HTTPException, BackgroundTasks
import subprocess

app = FastAPI()

@app.post("/crawl/")
async def crawl_youtube(urls: list[str], background_tasks: BackgroundTasks):
    if len(urls) > 1000000:
        raise HTTPException(status_code=400, detail="Too many URLs. Please provide less than 1000000 at a time.")
    
    # Write the URLs to a file that Scrapy can read
    with open("scrapy_youtube_crawling/input_urls.txt", "w") as f:
        for url in urls:
            f.write(f"{url}\n")

    # Trigger the Scrapy spider via a background task
    background_tasks.add_task(run_spider)
    return {"message": "Crawling started. Data will be processed in the background."}

def run_spider():
    subprocess.run(["scrapy", "crawl", "youtube", "-o", "output.json", "--loglevel=DEBUG"], cwd="scrapy_youtube_crawling")

