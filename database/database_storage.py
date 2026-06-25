import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "qqmusic_comments.db"

SONGS_PATHS = [
    ROOT / "tme_qqmusic_songs_massive.csv",
    ROOT / "data" / "tme_qqmusic_songs_massive.csv",
    ROOT / "datasets" / "tme_qqmusic_songs_massive.csv",
]
COMMENTS_PATHS = [
    ROOT / "tme_qqmusic_comments_massive.csv",
    ROOT / "data" / "tme_qqmusic_comments_massive.csv",
    ROOT / "datasets" / "tme_qqmusic_comments_massive.csv",
]


def pick_path(paths):
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError("CSV file not found. Put the data file in the project root, data/, or datasets/.")


def main():
    songs_path = pick_path(SONGS_PATHS)
    comments_path = pick_path(COMMENTS_PATHS)

    songs = pd.read_csv(songs_path)
    comments = pd.read_csv(comments_path)

    with sqlite3.connect(DB_PATH) as conn:
        songs.to_sql("songs", conn, if_exists="replace", index=False)
        comments.to_sql("comments", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_songs_song_id ON songs(song_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comments_song_id ON comments(song_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comments_comment_id ON comments(comment_id)")

    print("SQLite database created:", DB_PATH)
    print("songs rows:", len(songs))
    print("comments rows:", len(comments))


if __name__ == "__main__":
    main()
