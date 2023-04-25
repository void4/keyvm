from gevent import monkey

monkey.patch_all()

from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

from instructions import *


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string='%%',  # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_end_string='%%',
    ))


app = CustomFlask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(cors_allowed_origins="*")

socketio.init_app(
    app,
    message_queue="redis://127.0.0.1:6379/0"
)


@app.route("/")
def r_index():
    return render_template("index.html", INSTRUCTIONNAMES=INSTRUCTIONNAMES)


socketio.run(app, port=8001, debug=False, use_reloader=False)
