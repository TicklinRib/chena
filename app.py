"""
app.py – Chess Analyzer Flask backend
Dragon / Komodo UCI engine + python-chess

Install:
pip install flask flask-cors chess

Run:
python app.py

Open:
http://localhost:5000
"""

import atexit
import chess
import chess.engine
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


# ─────────────────────────────────────────────
# Engine configuration
# ─────────────────────────────────────────────

ENGINE_PATH = "engine/dragon-64bit.exe"

# start engine once
engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

# configure engine strength
engine.configure({
    "Threads": 4,      # adjust to CPU cores
    "Hash": 1024       # MB
})


# ─────────────────────────────────────────────
# Flask setup
# ─────────────────────────────────────────────

app = Flask(__name__)
CORS(app)


# ─────────────────────────────────────────────
# Score formatting
# ─────────────────────────────────────────────

def score_str(pov: chess.engine.PovScore) -> str:
    """Return evaluation string from white perspective"""

    w = pov.white()

    if w.is_mate():
        m = w.mate()
        return ('+' if m > 0 else '-') + 'M' + str(abs(m))

    cp = w.score()

    return f"{cp / 100.0:+.2f}" if cp is not None else "?"


def score_cp_relative(pov: chess.engine.PovScore) -> int:
    """Centipawn score from side-to-move perspective"""

    return pov.relative.score(mate_score=10000) or 0


# ─────────────────────────────────────────────
# Analyze endpoint
# ─────────────────────────────────────────────

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json(force=True)

    fen = data.get("fen", chess.STARTING_FEN)
    depth = max(1, min(int(data.get("depth", 15)), 30))

    try:
        board = chess.Board(fen)
    except ValueError as e:
        return jsonify({"error": f"Invalid FEN: {e}"}), 400

    # if game finished
    if board.is_game_over():

        return jsonify({
            "score": "0.00",
            "score_cp": 0,
            "depth": 0,
            "best_move": "",
            "pv": "",
            "top_moves": []
        })

    try:

        info_list = engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
            multipv=3
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


    # sometimes only one move available
    if isinstance(info_list, dict):
        info_list = [info_list]

    top_moves = []

    for info in info_list:

        pv = info.get("pv", [])
        score = info.get("score")

        if not pv:
            continue

        top_moves.append({

            "uci": pv[0].uci(),

            "pv": " ".join(move.uci() for move in pv[:10]),

            "score": score_str(score) if score else "?",

            "score_cp": score_cp_relative(score) if score else 0

        })


    best = top_moves[0] if top_moves else {}

    actual_depth = info_list[0].get("depth", depth)


    return jsonify({

        "score": best.get("score", "?"),

        "score_cp": best.get("score_cp", 0),

        "depth": actual_depth,

        "best_move": best.get("uci", ""),

        "pv": best.get("pv", ""),

        "top_moves": top_moves

    })


# ─────────────────────────────────────────────
# Serve frontend
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────
# Close engine when server stops
# ─────────────────────────────────────────────

@atexit.register
def close_engine():
    engine.quit()
    print("Engine closed.")


# ─────────────────────────────────────────────
# Start server
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\nChess Analyzer Backend")
    print("Engine:", ENGINE_PATH)
    print("Open http://localhost:5000\n")

    app.run(debug=False, port=5000)