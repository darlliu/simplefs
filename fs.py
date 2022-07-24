from flask import Flask, jsonify, render_template, send_file, g, request
import os
import json
import time
import cutlet
import pinyin
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve

app = Flask(__name__)
app.secret_key = open("key.key", "r").read()
#app.use_x_sendfile = True
app.wsgi_app = ProxyFix(app.wsgi_app)

CONFIG = json.load(open("config.json"))

DIRS = CONFIG.get("dirs", [])

katsu = cutlet.Cutlet()


def to_kanji(ss):
    return katsu.romaji(ss)


def to_pinyin(ss):
    return pinyin.get(ss, format="strip", delimiter="")


def process_fname(fname):
    fname = fname.rstrip(".mp4").rstrip(".mkv").rstrip(".avi")
    return fname, to_kanji(fname), to_pinyin(fname)


def check_key(ss, v):
    ss = ss.lower()
    return (ss in v[0].lower()) or (ss in v[1].lower()) or (ss in v[2].lower())


@app.route("/")
def render_main():
    ts = time.time()
    if g.get("ts") is None or g.ts - ts > 300:
        g.ts = ts
        g.res = refresh()
    sstr = request.args.get("sstr", "")
    if sstr:
        fnames = [k for k in g.res.keys() if check_key(sstr, g.res[k])]
    else:
        fnames = []
    return render_template("index.html", fnames=fnames)


@app.route("/serve")
def serve_file(fname=""):
    fname = request.args.get("fname")
    if ".mp4" in fname:
        return send_file(fname, mimetype="video/mp4")
    elif ".avi" in fname:
        return send_file(fname, mimetype="video/x-msvideo")
    elif ".mkv" in fname:
        return send_file(fname, mimetype="video/x-matroska")
    return f"<p>Empty: {fname}</p>"


def refresh():
    res = {}
    for dp in DIRS:
        for root, dirs, files in os.walk(dp, True):
            files = filter(
                lambda x: ".mkv" in x or ".avi" in x or ".mp4" in x, files)
            fps = {f"{root}/{fname}": process_fname(fname) for fname in files}
            res.update(fps)
    return res


if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=3037, threads=2)
