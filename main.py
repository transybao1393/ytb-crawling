from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
import subprocess
import threading
import socket
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
SOCKET_PORT = 9006
SOCKET_HOST = 'localhost'

# A flag to stop the server
shutdown_event = threading.Event()

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

def start_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((SOCKET_HOST, SOCKET_PORT))
        server_socket.listen(5)
        print(f"Socket server listening on {SOCKET_HOST}:{SOCKET_PORT}")
        
        server_socket.settimeout(1.0) # Set a timeout to periodically check for shutdown

        while not shutdown_event.is_set():
            try:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Connected by {addr}")

                    # sending acknowledge message
                    acknowledgment = "Connection successful"
                    conn.sendall(acknowledgment.encode('utf-8'))

                    # actively receiving data from client
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        print(f"Received message: {data.decode('utf-8')}")

                        # broadcast message
                        conn.sendall((data.decode('utf-8')).encode('utf-8')) # sending status to all
            except socket.timeout:
                continue  # Continue loop to check shutdown flag
            except Exception as e:
                print(f"Error in socket server: {e}")
                break # Optionally break the loop on other exceptions

# Start the socket server in a separate thread
socket_thread = threading.Thread(target=start_socket_server, daemon=True)
socket_thread.start()

@app.get("/")
def read_root():
    return {"message": "FastAPI server with socket running"}

@app.get("/status")
def status():
    return {"status": f"Socket server running on port {SOCKET_PORT}"}

# Shutdown event for FastAPI
@app.on_event("shutdown")
def shutdown():
    print("FastAPI shutdown initiated. Shutting down socket server...")
    shutdown_event.set()  # Signal the socket server to shut down
    socket_thread.join()  # Wait for the socket server to close