from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from starlette.middleware.cors import CORSMiddleware
from typing import List
import subprocess
import asyncio
import json
import os
from fastapi.responses import HTMLResponse

app = FastAPI()

# List of allowed origins
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Simulate updating the crawling status every 5 seconds
        await asyncio.sleep(1)
        # Check if the file exists before reading it
        file_path = "scrapy_youtube_crawling/scrapy_youtube_crawling/progress.txt"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read().strip()
        else:
            content = '0'  # Default value if the file is not found
        await websocket.send_text(content)


@app.post("/crawl/")
async def crawl_youtube(urls: list[str], background_tasks: BackgroundTasks):
    if len(urls) > 1000000:
        raise HTTPException(status_code=400, detail="Too many URLs. Please provide less than 1000000 at a time.")
    
    # Write the URLs to a file that Scrapy can read
    with open("scrapy_youtube_crawling/input_urls.txt", "w") as f:
        for url in urls:
            f.write(f"{url}\n")
    with open("scrapy_youtube_crawling/scrapy_youtube_crawling/progress.txt", "w") as f:
        f.write(f"0\n")

    # Trigger the Scrapy spider via a background task
    background_tasks.add_task(run_spider)
    return {"message": "Crawling started. Data will be processed in the background."}

def run_spider():
    subprocess.run(["scrapy", "crawl", "youtube", "-o", "output.json", "--loglevel=DEBUG"], cwd="scrapy_youtube_crawling")


# for socket connections
# HTML for testing WebSocket connection
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <textarea id="messages" cols="100" rows="20"></textarea><br>
        <input id="messageInput" type="text" size="100"><button id="sendMessage">Send</button>

        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            const messageInput = document.getElementById("messageInput");
            const sendMessageButton = document.getElementById("sendMessage");
            const messages = document.getElementById("messages");

            ws.onmessage = function(event) {
                messages.value += event.data + "\\n";
            };

            sendMessageButton.onclick = function() {
                const message = messageInput.value;
                ws.send(message);
                messageInput.value = "";
            };
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

