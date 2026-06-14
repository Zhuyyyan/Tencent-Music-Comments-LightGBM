import os
import gradio as gr
import pandas as pd
import numpy as np
import jieba
import re
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

print("=== 启动 Gradio 智能乐评预测系统 (1:1 旗舰复刻版) ===")

# ==========================================
# 1. 环境与模型加载
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def project_path(filename):
    return os.path.join(BASE_DIR, filename)

# 设置画图支持中文（兼容云端环境）
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 读取 NLP 模型与特征大脑
try:
    best_clf_model = joblib.load(project_path('best_model.pkl'))
    tfidf_vec = joblib.load(project_path('tfidf_vec.pkl'))
    trained_features = list(joblib.load(project_path('trained_features.pkl')))
    MODEL_LOADED = True
    MODEL_ERROR = ""
    print("✅ 模型和特征组件加载成功！")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    MODEL_LOADED = False
    MODEL_ERROR = str(e)
    best_clf_model = None
    tfidf_vec = None
    trained_features = []

# 读取本地大屏数据
SONGS_FILE = project_path('tme_qqmusic_songs_massive.csv')
COMMENTS_FILE = project_path('tme_qqmusic_comments_massive.csv')
try:
    df_songs = pd.read_csv(SONGS_FILE)
    df_comments = pd.read_csv(COMMENTS_FILE, usecols=['song_id'])
    DATA_LOADED = True
except Exception as e:
    print(f"❌ 数据文件加载失败: {e}")
    df_songs = None
    df_comments = None
    DATA_LOADED = False

balanced_threshold = 0.50
fan_keywords = ['演唱会', '华语乐坛', '陪伴', '时代', '青春是', '终于等到', '才华', 
                '实力', '嗓音', '歌手', '偶像', '编曲', '作词', '新歌', '单曲', 
                '专辑', '大卖', '现场', '入坑', '循环', '支持', '神仙']

# ==========================================
# 2. 核心预测逻辑 (你的语义逻辑对冲版)
# ==========================================
def classify_comment_advanced(text):
    if not MODEL_LOADED:
        return f"❌ 模型组件加载失败：{MODEL_ERROR}"
        
    text_str = str(text or "").strip()
    if not text_str:
        return "❌ 请输入有效的乐评内容！"
        
    raw_length = len(text_str)
    X_new = pd.DataFrame(0.0, index=[0], columns=trained_features)
    
    if 'comment_length' in X_new.columns:
        X_new.loc[0, 'comment_length'] = raw_length
    if 'has_mv_flag' in X_new.columns:
        X_new.loc[0, 'has_mv_flag'] = 1.0  
    if 'song_tags_encoded' in X_new.columns:
        X_new.loc[0, 'song_tags_encoded'] = 0.0 
    
    fan_score = sum(1 for word in fan_keywords if word in text_str)
    if 'fan_effect_score' in X_new.columns:
        X_new.loc[0, 'fan_effect_score'] = float(fan_score)

    words = jieba.lcut(text_str)
    chinese_words = [w for w in words if re.match(r'^[\u4e00-\u9fa5]+$', w)]
    valid_words = [w for w in chinese_words if len(w) > 1]
    cleaned_text = " ".join(valid_words)
    hit_words = []
    
    if cleaned_text:
        tfidf_matrix = tfidf_vec.transform([cleaned_text])
        feature_names = tfidf_vec.get_feature_names_out()
        tfidf_values = tfidf_matrix.toarray()[0]
        for word, val in zip(feature_names, tfidf_values):
            if val > 0:
                col_name = f"纯中文词_{word}"
                if col_name in X_new.columns:
                    X_new.loc[0, col_name] = val
                    hit_words.append(word)

    try:
        proba = best_clf_model.predict_proba(X_new)[0][1] 
    except Exception as e:
        return f"模型维度匹配异常：{e}"
        
    final_proba = proba
    corrections = []
    
    敷衍批判词 = {'一般般', '一般', '随便听听', '凑热闹', '切', '难听'}
    身份中性词 = {'纯路人', '路人', '打卡', '支持'}
    深情长尾词 = {'深夜', '眼泪', '耳机', '哭', '憋不住', '回忆', '遗憾', '错过的', '再也', '前奏', '惊艳', '沦陷'}
    
    hit_bad_words = [w for w in chinese_words if w in 敷衍批判词]
    hit_neutral_words = [w for w in chinese_words if w in 身份中性词]
    hit_deep_words = [w for w in chinese_words if w in 深情长尾词]
    
    if hit_bad_words:
        corrections.append(f"触发敷衍/批评词一票否决 (命中: {', '.join(hit_bad_words)})")
        final_proba *= 0.2
    elif hit_deep_words:
        if hit_neutral_words:
            corrections.append(f"✨ 捕获【客观路人真情流露】高赞流派 (命中: {', '.join(hit_deep_words)})")
            final_proba = max(final_proba, 0.78)
        else:
            corrections.append(f"捕获长尾高赞情感密码 (命中: {', '.join(hit_deep_words)})")
            final_proba = max(final_proba, 0.65) 
    elif hit_neutral_words:
        corrections.append(f"仅为普通路人打卡流水账 (命中: {', '.join(hit_neutral_words)})")
        final_proba *= 0.5 

    diagnostic_panel = (
        f"📊 【语义对冲版 - 决策报告】\n"
        f"1. 评论原始字数：{raw_length} 字\n"
        f"2. 命中高频特征词：{', '.join(set(hit_words)) if hit_words else '无'}\n"
        f"3. 模型原生概率：{proba:.2%}\n"
    )
    if corrections:
        diagnostic_panel += f"🛠️ 语义纠偏动作：\n" + "\n".join([f"   • {c}" for c in corrections]) + "\n"
        
    final_proba = float(np.clip(final_proba, 0.0, 1.0))
    diagnostic_panel += f"📈 规则调整后潜在共鸣得分：{final_proba:.2%} (及格线：{balanced_threshold:.2%})\n"
    diagnostic_panel += f"--------------------------------------------------\n"
    
    if final_proba >= balanced_threshold:
        return diagnostic_panel + "🌟 最终判定：【优质神评潜力股 (1)】\n\n说明：该得分用于课程展示，不代表评论一定会成为平台真实热评。"
    else:
        return diagnostic_panel + "💬 最终判定：【普通评论 (0)】\n\n说明：该得分用于课程展示，不代表评论一定会成为平台真实热评。"

# ==========================================
# 3. 数据大屏画图逻辑
# ==========================================
def show_chart(chart_name):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    if chart_name == "📊 爬取歌曲热度排行 TOP 10":
        required_columns = {'song_id', 'song_name'}
        if DATA_LOADED and required_columns.issubset(df_songs.columns):
            song_names = df_songs[['song_id', 'song_name']].copy()
            song_names['song_id'] = song_names['song_id'].astype(str)
            comment_counts = (
                df_comments.assign(song_id=df_comments['song_id'].astype(str))
                .groupby('song_id')
                .size()
                .rename('sample_comment_count')
                .reset_index()
            )
            top_10 = (
                song_names.merge(comment_counts, on='song_id', how='left')
                .fillna({'sample_comment_count': 0})
                .nlargest(10, 'sample_comment_count')
            )
            sns.barplot(
                data=top_10,
                x='sample_comment_count',
                y='song_name',
                ax=ax,
                hue='song_name',
                palette="plasma",
                legend=False
            )
            ax.set_title("QQ音乐当前采集样本评论量 TOP 10")
            ax.set_xlabel("本次数据集收录评论数")
            ax.set_ylabel("歌曲名称")
        else:
            ax.text(0.5, 0.5, "💡 提示：云端尚未上传 CSV 数据集\n请将 massive.csv 上传至 Hugging Face 以点亮大屏！", ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            
    elif chart_name == "🎯 LightGBM 特征重要性排行榜":
        if MODEL_LOADED and hasattr(best_clf_model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                '特征名称': trained_features,
                '权重值': best_clf_model.feature_importances_
            }).nlargest(20, '权重值')
            sns.barplot(
                data=feature_importance,
                x='权重值',
                y='特征名称',
                ax=ax,
                hue='特征名称',
                palette="viridis",
                legend=False
            )
            ax.set_title("LightGBM 判断“神评”的真实特征重要性 TOP 20")
        else:
            ax.text(0.5, 0.5, "模型未加载，暂时无法展示特征重要性", ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
        
    elif chart_name == "📈 模型训练混淆矩阵":
        # 来自 analysis.ipynb 中 LightGBM 对同一测试集的真实输出。
        cm = [[3721, 2366], [1584, 2384]]
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                    xticklabels=['预测普通', '预测神评'], yticklabels=['真实普通', '真实神评'])
        ax.set_title("LightGBM 测试集真实混淆矩阵")
        
    plt.tight_layout()
    return fig

# ==========================================
# 4. Gradio 前端页面搭建 (双 Tab 旗舰版)
# ==========================================
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎵 QQ音乐榜单数据挖掘与“神评”AI智能预测系统")
    gr.Markdown("包含基于 TF-IDF 语义逻辑对冲的 NLP 模型与数据看板 1:1 云端复刻。")
    
    with gr.Tabs():
        # Tab 1：智能对冲预测
        with gr.TabItem("🚀 AI 语义对冲预测"):
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(lines=5, placeholder="前奏一响，深夜的耳机里全都是遗憾...", label="📝 请输入一条音乐评论")
                    btn = gr.Button("🔍 启动智能诊断", variant="primary")
                with gr.Column():
                    text_out = gr.Textbox(lines=12, label="📊 智能对冲决策结果")
            btn.click(fn=classify_comment_advanced, inputs=[text_input], outputs=[text_out])
            
        # Tab 2：数据看板大屏
        with gr.TabItem("📊 数据大屏看板"):
            selector = gr.Radio(["📊 爬取歌曲热度排行 TOP 10", "🎯 LightGBM 特征重要性排行榜", "📈 模型训练混淆矩阵"], 
                                label="选择图表面板：", value="📊 爬取歌曲热度排行 TOP 10")
            plot_out = gr.Plot()
            selector.change(fn=show_chart, inputs=selector, outputs=plot_out)
            demo.load(fn=show_chart, inputs=selector, outputs=plot_out)

if __name__ == "__main__":
    demo.launch()
