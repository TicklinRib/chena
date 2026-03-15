"""
app.py  –  Chess Analyzer Flask backend
Dragon Komodo 1 via UCI  +  python-chess

Install:
    pip install flask flask-cors chess

Run:
    python app.py
Then open  http://localhost:5000  in your browser.
"""

import chess
import chess.engine
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# ── Engine path (already set to your binary) ─────────────────────────────
ENGINE_PATH = "engine/dragon-64bit.exe"

app = Flask(__name__)
CORS(app)   # allow requests from file:// or other origins


# ── Score helper ─────────────────────────────────────────────────────────
def score_str(pov: chess.engine.PovScore) -> str:
    """White-perspective score string:  '+0.45'  '-1.20'  '+M3'  '-M2'"""
    w = pov.white()
    if w.is_mate():
        m = w.mate()
        return ('+' if m > 0 else '-') + 'M' + str(abs(m))
    cp = w.score()
    return f"{cp / 100.0:+.2f}" if cp is not None else "?"


def score_cp_relative(pov: chess.engine.PovScore) -> int:
    """Centipawns from the side-to-move's perspective (used for classification)."""
    return pov.relative.score(mate_score=10000) or 0


# ── Analyze a single position ─────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    data  = request.get_json(force=True)
    fen   = data.get("fen", chess.STARTING_FEN)
    depth = max(1, min(int(data.get("depth", 15)), 30))

    try:
        board = chess.Board(fen)
    except ValueError as e:
        return jsonify({"error": f"Invalid FEN: {e}"}), 400

    if board.is_game_over():
        return jsonify({
            "score": "0.00", "score_cp": 0, "depth": 0,
            "best_move": "", "pv": "", "top_moves": []
        })

    try:
        with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
            # multipv=3 returns a list of InfoDict
            info_list = engine.analyse(
                board,
                chess.engine.Limit(depth=depth),
                multipv=3
            )
    except FileNotFoundError:
        return jsonify({"error": f"Engine not found: {ENGINE_PATH}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Normalise: single-move positions return a dict, not a list
    if isinstance(info_list, dict):
        info_list = [info_list]

    top_moves = []
    for info in info_list:
        pv = info.get("pv", [])
        if not pv:
            continue
        sc = info.get("score")
        top_moves.append({
            "uci":      pv[0].uci(),
            "pv":       " ".join(m.uci() for m in pv[:10]),
            "score":    score_str(sc) if sc else "?",
            "score_cp": score_cp_relative(sc) if sc else 0,
        })

    best = top_moves[0] if top_moves else {}
    actual_depth = info_list[0].get("depth", depth) if info_list else depth

    return jsonify({
        "score":      best.get("score",    "?"),
        "score_cp":   best.get("score_cp", 0),
        "depth":      actual_depth,
        "best_move":  best.get("uci",      ""),
        "pv":         best.get("pv",       ""),
        "top_moves":  top_moves,
    })


# ── Serve frontend ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    print(f"\n  Chess Analyzer  –  engine: {ENGINE_PATH}")
    print("  Open  http://localhost:5000  in your browser.\n")
    app.run(debug=False, port=5000)