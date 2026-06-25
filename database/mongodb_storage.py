from pathlib import Path

import pandas as pd
from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRS = [PROJECT_ROOT, PROJECT_ROOT / "data", PROJECT_ROOT / "datasets"]
SONGS_FILENAME = "tme_qqmusic_songs_massive.csv"
COMMENTS_FILENAME = "tme_qqmusic_comments_massive.csv"
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "qqmusic_project"


def find_csv(filename):
    for directory in DATA_DIRS:
        csv_path = directory / filename
        if csv_path.exists():
            return csv_path
    searched_paths = ", ".join(str(directory / filename) for directory in DATA_DIRS)
    raise FileNotFoundError(f"Could not find {filename}. Searched: {searched_paths}")


def read_csv_records(csv_path):
    dataframe = pd.read_csv(csv_path, encoding="utf-8-sig")
    dataframe = dataframe.astype(object).where(pd.notna(dataframe), None)
    return dataframe.to_dict(orient="records")


def replace_collection(collection, records):
    collection.delete_many({})
    if records:
        collection.insert_many(records)


def main():
    songs_path = find_csv(SONGS_FILENAME)
    comments_path = find_csv(COMMENTS_FILENAME)

    songs_records = read_csv_records(songs_path)
    comments_records = read_csv_records(comments_path)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    songs_collection = db["songs"]
    comments_collection = db["comments"]

    replace_collection(songs_collection, songs_records)
    replace_collection(comments_collection, comments_records)

    songs_collection.create_index("song_id")
    comments_collection.create_index("song_id")
    comments_collection.create_index("comment_id")

    songs_count = songs_collection.count_documents({})
    comments_count = comments_collection.count_documents({})

    print("MongoDB import completed.")
    print(f"Database: {DB_NAME}")
    print(f"songs records: {songs_count}")
    print(f"comments records: {comments_count}")

    client.close()


if __name__ == "__main__":
    main()
