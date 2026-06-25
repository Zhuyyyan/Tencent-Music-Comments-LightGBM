# MongoDB 集合字段说明

MongoDB 是文档型数据库，本项目在 `qqmusic_project` 数据库中保存的是集合（collection）与文档（document），因此这里提供的是集合字段说明，而不是传统 SQL 表结构。

## songs 集合

`songs` 集合用于存储 QQ 音乐榜单歌曲信息。

| 字段名 | 含义 | 示例/说明 |
|---|---|---|
| `song_id` | 歌曲 ID | 用于关联评论数据 |
| `song_name` | 歌曲名称 | QQ 音乐歌曲名 |
| `artist_name` | 歌手名称 | 歌曲对应歌手 |
| `song_tags` | 歌曲标签/类型 | 如经典、流行等榜单或标签信息 |
| `mv_id` | MV 标识 | 用于表示歌曲是否关联 MV 信息 |
| `source_list` | 榜单来源 | 歌曲采集来源榜单 |

## comments 集合

`comments` 集合用于存储 QQ 音乐用户评论信息。

| 字段名 | 含义 | 示例/说明 |
|---|---|---|
| `song_id` | 歌曲 ID | 与 `songs.song_id` 对应 |
| `comment_id` | 评论 ID | 用于唯一识别评论记录 |
| `user_id` | 用户 ID | 接口返回字段，当前数据中可能为空 |
| `nickname` | 用户昵称 | 评论用户昵称 |
| `content` | 评论内容 | 用户发布的评论文本 |
| `liked_count` | 点赞数 | 评论获得的点赞数量 |
| `comment_time` | 评论时间 | 接口返回的评论发布时间戳 |

## 索引说明

`mongodb_storage.py` 导入数据后会创建以下索引，便于按歌曲和评论 ID 查询：

| 集合 | 索引字段 | 用途 |
|---|---|---|
| `songs` | `song_id` | 按歌曲 ID 查询歌曲信息 |
| `comments` | `song_id` | 按歌曲 ID 查询对应评论 |
| `comments` | `comment_id` | 按评论 ID 查询评论记录 |
