"""
Run this ONCE to download all frontend assets locally.
python download_assets.py
"""
import urllib.request, os

os.makedirs("static/js",  exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/img/chesspieces/wikipedia", exist_ok=True)

assets = [
    ("https://code.jquery.com/jquery-3.7.1.min.js",
     "static/js/jquery.min.js"),
    ("https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js",
     "static/js/chess.min.js"),
    ("https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.js",
     "static/js/chessboard.js"),
    ("https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.css",
     "static/css/chessboard.css"),
]

pieces = ["bB","bK","bN","bP","bQ","bR","wB","wK","wN","wP","wQ","wR"]
for p in pieces:
    assets.append((
        f"https://chessboardjs.com/img/chesspieces/wikipedia/{p}.png",
        f"static/img/chesspieces/wikipedia/{p}.png"
    ))

for url, dest in assets:
    print(f"Downloading {dest} ...", end=" ")
    try:
        urllib.request.urlretrieve(url, dest)
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")

print("\nDone. Now run: python app.py")
