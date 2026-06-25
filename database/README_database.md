# 数据库存储说明

本文件夹用于对应课程项目中的“数据存储”要求，展示如何将 QQ 音乐歌曲数据和评论数据从 CSV 文件导入数据库，便于后续查询、复现和展示。

## 存储方案

本项目采用 MongoDB 作为主要数据库存储方案，与期末项目报告中的数据存储部分保持一致。MongoDB 属于文档型数据库，适合保存歌曲信息和评论文本这类字段较直观、后续可按文档扩展的数据。

运行 `python database/mongodb_storage.py` 后，会在本地 MongoDB 中生成数据库：

```text
qqmusic_project
```

数据库中包含两个集合：

- `songs`：存储歌曲 ID、歌曲名、歌手、榜单来源、MV 标识等歌曲信息；
- `comments`：存储评论 ID、歌曲 ID、评论内容、点赞数、评论时间等评论信息。

## 文件说明

- `mongodb_storage.py`：MongoDB 入库脚本，读取项目 CSV 数据并写入本地 MongoDB。
- `mongo_collection_schema.md`：MongoDB 集合字段说明，列出 `songs` 和 `comments` 两个集合的主要字段。
- `README_database.md`：数据库存储说明文件。
- `database_storage.py`：SQLite 版本入库脚本，作为可选补充保留，不作为本项目课程报告对应的主流程。
- `create_tables.sql`：SQLite 表结构文件，作为可选补充保留。

## CSV 文件位置

请先确认以下两个 CSV 文件位于项目根目录、`data/` 文件夹或 `datasets/` 文件夹中：

- `tme_qqmusic_songs_massive.csv`
- `tme_qqmusic_comments_massive.csv`

`mongodb_storage.py` 会自动在上述三个位置查找 CSV 文件。

## 运行方法

请先确保本地 MongoDB 服务已经启动，连接地址为：

```text
mongodb://localhost:27017/
```

然后在项目根目录运行：

```bash
python database/mongodb_storage.py
```

脚本会执行以下操作：

1. 读取歌曲数据 `tme_qqmusic_songs_massive.csv`；
2. 读取评论数据 `tme_qqmusic_comments_massive.csv`；
3. 连接本地 MongoDB；
4. 创建或使用数据库 `qqmusic_project`；
5. 导入歌曲数据到 `songs` 集合；
6. 导入评论数据到 `comments` 集合；
7. 导入前清空原有集合，避免重复插入；
8. 为 `songs.song_id`、`comments.song_id`、`comments.comment_id` 创建索引；
9. 在终端输出导入完成信息和两个集合的记录数。

## 集合说明

### songs

`songs` 集合用于存储歌曲信息，包括歌曲 ID、歌曲名称、歌手名称、歌曲标签、MV 标识和来源榜单等字段。

### comments

`comments` 集合用于存储评论信息，包括评论 ID、歌曲 ID、用户昵称、评论内容、点赞数和评论时间等字段。

更详细的字段说明见：`mongo_collection_schema.md`。
