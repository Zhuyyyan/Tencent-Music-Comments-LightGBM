import requests
import pandas as pd
import time
import random
from tqdm import tqdm
import urllib3

# 忽略 HTTPS 证书警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_qqmusic_massive_data(max_comment_pages=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://y.qq.com/'
    }
    
    songs_data = []
    comments_data = []
    
    # 💡 建立榜单池，获取更多歌曲
    # 26:热歌榜, 27:新歌榜, 28:网络歌曲榜, 5:内地榜, 4:流行指数榜
    topid_list = [26, 27, 28, 5, 4] 
    song_id_set = set() # 用集合来去重，防止不同榜单有重复歌曲

    print("🚀 [TME数据扩容完美版] 开启多榜单热评+普通评论全量扫街模式...")

    # ================= 阶段一：批量拉取各大榜单 =================
    for topid in topid_list:
        print(f"📊 正在拉取榜单ID [{topid}]...")
        rank_url = f"https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?g_tk=5381&uin=0&format=json&inCharset=utf-8&outCharset=utf-8&notice=0&platform=h5&needNewCode=1&tpl=3&page=detail&type=top&topid={topid}&_=1519963122925"
        
        try:
            res = requests.get(rank_url, headers=headers, timeout=10, verify=False)
            data = res.json()
            song_list = data.get('songlist', [])
            
            for item in song_list:
                song_info = item.get('data', {})
                song_id = str(song_info.get('songid'))
                
                # 过滤掉无效和重复的歌曲
                if not song_id or song_id == 'None' or song_id in song_id_set: 
                    continue
                    
                song_id_set.add(song_id)
                singers = song_info.get('singer', [{'name': '未知歌手'}])
                artist_name = singers[0].get('name', '未知歌手')
                
                # ================= 🚀 核心特征提取 (保留风格与MV，删去发行日期) =================
                # 1. 提取是否有 MV (Boolean 0/1)
                vid = song_info.get('vid', '')
                has_mv = 1 if vid else 0
                
                # 2. 映射歌曲风格标签 (String)
                tag_mapping = {
                    26: '经典/流行',     
                    27: '首发/流行',     
                    28: '网络神曲/下沉', 
                    5:  '内地/华语',     
                    4:  '爆款/上升'      
                }
                song_tags = tag_mapping.get(topid, '流行')
                # ====================================================================
                
                songs_data.append({
                    'song_id': song_id,
                    'song_name': song_info.get('songname', '未知歌曲'),
                    'artist_name': artist_name,
                    'song_tags': song_tags,     # ⭐ 成功保留风格类别
                    'mv_id': has_mv,            # ⭐ 成功保留是否有MV标识
                    'source_list': f'QQMusic_Top_{topid}'
                })
            time.sleep(1) # 榜单之间稍微停顿
        except Exception as e:
            print(f"⚠️ 榜单 {topid} 获取异常跳过: {e}")

    df_songs = pd.DataFrame(songs_data)
    if df_songs.empty:
        print("\n❌ 未能解析到任何歌曲数据。")
        return
        
    df_songs.to_csv("tme_qqmusic_songs_massive.csv", index=False, encoding='utf-8-sig')
    print(f"✅ 阶段一完成：汇聚去重后共获得 {len(df_songs)} 首歌曲，核心维度补齐！")

    # ================= 阶段二：多页评论深度抽取 =================
    print("\n" + "="*50)
    print(f"🚀 阶段二：开始深度抽取 (每首歌兼顾精彩热评，并向下挖掘 {max_comment_pages} 页普通评论)...")
    
    for _, row in tqdm(df_songs.iterrows(), total=len(df_songs), desc="全量抽取进度"):
        song_id = row['song_id']
        
        for page in range(max_comment_pages):
            comment_url = f"https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&cid=205360772&reqtype=2&biztype=1&topid={song_id}&cmd=8&needmusiccrit=0&pagenum={page}&pagesize=25"
            
            try:
                c_res = requests.get(comment_url, headers=headers, timeout=8, verify=False)
                c_data = c_res.json()
                
                # 🌟【修改破局点 1】：如果是第一页(page=0)，主动、强行剥离出独立封装的“精彩热评(hot_comment)”
                if page == 0:
                    hot_comment_list = c_data.get('hot_comment', {}).get('commentlist', [])
                    if hot_comment_list:
                        for c in hot_comment_list:
                            msg = c.get('rootcommentcontent', '').strip()
                            if not msg: continue
                            comments_data.append({
                                'song_id': song_id,
                                'comment_id': str(c.get('commentid', '')),
                                'user_id': str(c.get('uin', '未知ID')),
                                'nickname': c.get('nick', '匿名'),
                                'content': msg,
                                'liked_count': int(c.get('praisenum', 0)),  # 🔥 这里拿到的就是真正的几百上千赞！
                                'comment_time': c.get('time', '')
                            })
                
                # 🌟【修改破局点 2】：无论哪一页，正常抽取最新评论流（提供丰富的低赞长尾对照组样本）
                normal_comment_list = c_data.get('comment', {}).get('commentlist', [])
                
                # 如果当前页没有评论了，直接打断翻页，进入下一首歌
                if not normal_comment_list:
                    break
                
                for c in normal_comment_list:
                    msg = c.get('rootcommentcontent', '').strip()
                    if not msg: continue
                    comments_data.append({
                        'song_id': song_id,
                        'comment_id': str(c.get('commentid', '')),
                        'user_id': str(c.get('uin', '未知ID')), 
                        'nickname': c.get('nick', '匿名'),
                        'content': msg,
                        'liked_count': int(c.get('praisenum', 0)),  # 这里拿到的是自然流点赞
                        'comment_time': c.get('time', '')
                    })
            except Exception:
                break # 单页抓取报错，直接跳过当前歌曲的后续页
            
            # 每翻一页必须休眠，严格控制频率，防止被封 IP
            time.sleep(random.uniform(0.5, 0.9)) 

    if comments_data:
        df_comments = pd.DataFrame(comments_data)
        # 全局去重（防止某热评刚好也是最新评论而被重复记录）
        df_comments.drop_duplicates(subset=['comment_id'], inplace=True) 
        df_comments.to_csv("tme_qqmusic_comments_massive.csv", index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"🎉 【大丰收】全新高质量混合数据集采集完毕！")
        print(f"💾 表1-歌曲数据: tme_qqmusic_songs_massive.csv (共 {len(df_songs)} 首歌曲)")
        print(f"💾 表2-乐评数据: tme_qqmusic_comments_massive.csv (共 {len(df_comments)} 条混合乐评)")
        
        # 实时打印一波点赞数分布，检验修改成果
        print("\n📊 新数据集点赞数区间检验：")
        print(df_comments['liked_count'].describe(percentiles=[0.5, 0.8, 0.9, 0.95, 0.99]))
        print("="*50)

if __name__ == "__main__":
    # 默认单首歌曲挖掘 5 页评论，保证高赞热评的成功覆盖
    fetch_qqmusic_massive_data(max_comment_pages=5)