CREATE TABLE songs (
    song_id TEXT,
    song_name TEXT,
    artist_name TEXT,
    song_tags TEXT,
    mv_id TEXT,
    source_list TEXT
);

CREATE TABLE comments (
    song_id TEXT,
    comment_id TEXT,
    nickname TEXT,
    content TEXT,
    liked_count INTEGER,
    comment_time TEXT
);

CREATE INDEX idx_songs_song_id ON songs(song_id);
CREATE INDEX idx_comments_song_id ON comments(song_id);
CREATE INDEX idx_comments_comment_id ON comments(comment_id);
