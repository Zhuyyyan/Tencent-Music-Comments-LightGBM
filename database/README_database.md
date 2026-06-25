# 数据库存储说明

本文件夹用于补充课程项目中的“数据存储”部分。

项目原始数据以 CSV 文件形式保存，包括歌曲表和评论表。为便于复现和查询，这里提供 SQLite 数据库存储脚本，可将 CSV 数据导入本地数据库 `qqmusic_comments.db`。

## 文件说明

- `create_tables.sql`：数据库表结构文件，包含 `songs` 和 `comments` 两张表的建表语句。
- `database_storage.py`：数据库导入脚本，用于读取 CSV 文件并写入 SQLite 数据库。

## 数据表说明

### songs

用于存储歌曲信息，包括歌曲 ID、歌曲名称、歌手名称、歌曲类型、MV 标识和来源榜单等字段。

### comments

用于存储评论信息，包括歌曲 ID、评论 ID、用户昵称、评论内容、点赞数和评论时间等字段。

## 使用方法

请先确认以下两个 CSV 文件位于项目根目录、`data/` 文件夹或 `datasets/` 文件夹中：

- `tme_qqmusic_songs_massive.csv`
- `tme_qqmusic_comments_massive.csv`

然后运行：

```bash
python database/database_storage.py
```

运行后会在项目根目录生成 SQLite 数据库文件：

```text
qqmusic_comments.db
```

数据库中包含两张表：`songs` 和 `comments`，可用于后续 SQL 查询和结果复现。
