import sys
import asyncio
import webbrowser
import importlib.resources as resources

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from buelon.hub import WorkerClient

app = FastAPI()
worker_client: WorkerClient | None = None


def get_static_file(filename: str) -> str:
    # Opens the file as text
    with resources.files("buelon.static").joinpath(filename).open("r", encoding="utf-8") as f:
        return f.read()


def get_static_path(filename: str) -> str:
    # Gets the actual filesystem path (works even if installed in venv)
    return str(resources.files("buelon.static").joinpath(filename))


@app.get("/", response_class=HTMLResponse)
async def index():
    return get_static_file("index.html")


@app.get("/static/{path:path}")
async def static_file(path: str):
    return FileResponse(get_static_path(path))


@app.post("/data")
async def get_data():
    assert worker_client is not None
    data = await worker_client.get_web_info(True)
    return JSONResponse(content=data)


async def start_app(open_browser: bool = False):
    global worker_client
    port = 11011
    host = "localhost"

    if open_browser:
        webbrowser.open(f"http://{host}:{port}")

    async with WorkerClient() as client:
        worker_client = client
        # Start FastAPI with uvicorn
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


def run(open_browser: bool = False):
    asyncio.run(start_app(open_browser=open_browser))


if __name__ == "__main__":
    asyncio.run(start_app(open_browser=True))





# import sys
# import asyncio
# import webbrowser
# import importlib.resources as resources
#
# from unsync import unsync
# from flask import Flask, request, jsonify, send_file, render_template_string
# from buelon.hub import WorkerClient
#
# app = Flask(__name__)
# worker_client = WorkerClient()
#
#
# def get_static_file(filename: str) -> str:
#     # Opens the file as text
#     with resources.files("buelon.static").joinpath(filename).open("r", encoding="utf-8") as f:
#         return f.read()
#
#
# def get_static_path(filename: str) -> str:
#     # Gets the actual filesystem path (works even if installed in venv)
#     return str(resources.files("buelon.static").joinpath(filename))
#
#
# @app.route("/")
# def index():
#     return render_template_string(get_static_file("index.html"))
#
#
# @app.route("/static/<path:path>")
# def static_file(path):
#     return send_file(get_static_path(path))
#
#
# @app.route('/data', methods=['POST'])
# def get_data():
#     @unsync
#     async def get_data_sync():
#         return await worker_client.get_web_info(True)
#
#     return jsonify(get_data_sync().result())
#
#
# def run(open_browser: bool = False):
#     _run(open_browser).result()
#
#
# @unsync
# async def _run(open_browser: bool = False):
#     global worker_client
#     port = 11011
#     host = 'localhost'
#
#     if open_browser:  # ('-y' in sys.argv and '-n' not in sys.argv) or f'{input("Open Browser? (y/n)")}'.lower().startswith('y'):
#         webbrowser.open(f'http://{host}:{port}')
#
#     async with WorkerClient() as client:
#         worker_client = client
#         app.run(port=port, host=host)
#
#
# if __name__ == '__main__':
#     run()
#
#
#
#
