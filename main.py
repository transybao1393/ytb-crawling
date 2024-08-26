from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
import subprocess
from starlette.middleware.cors import CORSMiddleware
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

@app.post("/crawl/", summary="Youtube videos crawling api", tags=["Youtube videos"])
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

@app.get("/", summary="Socket test connection", tags=["Socket"])
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

