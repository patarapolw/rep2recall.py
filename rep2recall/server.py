from flask import Flask, jsonify, redirect
from flask_socketio import SocketIO
from flask_cors import CORS
import sqlite3
import traceback
import os

# https://github.com/miguelgrinberg/python-socketio/issues/35#issuecomment-482350874
from engineio.async_drivers import gevent

from .shared import Config, resource_path
from .api.quiz import api_quiz
from .api.editor import api_editor
from .api.io import api_io, r_import_progress
from .api.media import api_media

app = Flask(__name__, static_folder=resource_path("www"), static_url_path="")
io = SocketIO(app, logger=True, engineio_logger=True)
CORS(app)

app.register_blueprint(api_quiz)
app.register_blueprint(api_editor)
app.register_blueprint(api_io)
app.register_blueprint(api_media)


@app.route("/")
def r_index():
    return redirect("/index.html")


@app.route("/api/reset", methods=["DELETE"])
def r_reset():
    Config.DB.close()
    os.unlink(Config.COLLECTION)
    return jsonify({"error": None}), 201


@app.errorhandler(sqlite3.Error)
def r_sqlite_error(e):
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


@io.on("message")
def io_anki_progress(message):
    r_import_progress(message)


def run_server():
    io.run(app, port=Config.PORT, log_output=True)
