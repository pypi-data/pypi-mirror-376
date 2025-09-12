import sys
import asyncio
import webbrowser
import importlib.resources as resources

from unsync import unsync
from flask import Flask, request, jsonify, send_file, render_template_string
from buelon.hub import WorkerClient

app = Flask(__name__)


def get_static_file(filename: str) -> str:
    # Opens the file as text
    with resources.files("buelon.static").joinpath(filename).open("r", encoding="utf-8") as f:
        return f.read()


def get_static_path(filename: str) -> str:
    # Gets the actual filesystem path (works even if installed in venv)
    return str(resources.files("buelon.static").joinpath(filename))


@app.route("/")
def index():
    return render_template_string(get_static_file("index.html"))


@app.route("/static/<path:path>")
def static_file(path):
    return send_file(get_static_path(path))


@app.route('/data', methods=['POST'])
def get_data():
    @unsync
    async def get_data_sync():
        async with WorkerClient() as client:
            return await client.get_web_info(True)

    return jsonify(get_data_sync().result())


def run(open_browser: bool = False):
    port = 11011
    host = 'localhost'

    if open_browser:  # ('-y' in sys.argv and '-n' not in sys.argv) or f'{input("Open Browser? (y/n)")}'.lower().startswith('y'):
        webbrowser.open(f'http://{host}:{port}')

    app.run(port=port, host=host)


if __name__ == '__main__':
    run()




