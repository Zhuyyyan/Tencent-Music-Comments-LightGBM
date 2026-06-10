import gradio as gr
import pandas as pd
import jieba
import re
import numpy as np
import joblib

print("=== 10. 启动 Gradio 智能乐评预测系统 (线上语义逻辑对冲版) ===")

# 🌟 核心调整：从你上传的 pkl 文件中读取“大脑”，而不是从 Notebook 内存里找
try:
    best_clf_model = joblib.load('best_model.pkl')
    tfidf_vec = joblib.load('tfidf_vec.pkl')
    trained_features = joblib.load('trained_features.pkl')
    print("✅ 模型和特征组件加载成功！")
except Exception as e:
    print(f"❌ 加载失败，请检查 pkl 文件是否齐全: {e}")
    # 提供一个空的 fallback 以防直接崩溃
    trained_features = []

balanced_threshold = 0.50

fan_keywords = ['演唱会', '华语乐坛', '陪伴', '时代', '青春是', '终于等到', '才华', 
                '实力', '嗓音', '歌手', '偶像', '编曲', '作词', '新歌', '单曲', 
                '专辑', '大卖', '现场', '入坑', '循环', '支持', '神仙']

def classify_comment_advanced(text):
    text_str = str(text).strip()
    if not text_str:
        return "❌ 请输入有效的乐评内容！"
        
    raw_length = len(text_str)
    
    # ① 初始化：严格对齐训练时的特征维度
    X_new = pd.DataFrame(0.0, index=[0], columns=trained_features)
    
    # 安全赋值，只有当该特征存在时才赋值
    if 'comment_length' in X_new.columns:
        X_new.loc[0, 'comment_length'] = raw_length
    if 'has_mv_flag' in X_new.columns:
        X_new.loc[0, 'has_mv_flag'] = 1.0  
    if 'song_tags_encoded' in X_new.columns:
        X_new.loc[0, 'song_tags_encoded'] = 0.0 
    
    # 动态填充粉丝效应得分
    fan_score = sum(1 for word in fan_keywords if word in text_str)
    if 'fan_effect_score' in X_new.columns:
        X_new.loc[0, 'fan_effect_score'] = float(fan_score)

    # ② 分词与全面检索
    words = jieba.lcut(text_str)
    chinese_words = [w for w in words if re.match(r'^[\u4e00-\u9fa5]+$', w)]
    valid_words = [w for w in chinese_words if len(w) > 1]
    
    cleaned_text = " ".join(valid_words)
    hit_words = []
    
    # 只有当成功输入中文词且 tfidf_vec 正常工作时才处理
    if cleaned_text and 'tfidf_vec' in globals():
        tfidf_matrix = tfidf_vec.transform([cleaned_text])
        feature_names = tfidf_vec.get_feature_names_out()
        tfidf_values = tfidf_matrix.toarray()[0]
        
        for word, val in zip(feature_names, tfidf_values):
            if val > 0:
                col_name = f"纯中文词_{word}"
                if col_name in X_new.columns:
                    X_new.loc[0, col_name] = val
                    hit_words.append(word)

    # ③ 模型计算原始概率
    try:
        proba = best_clf_model.predict_proba(X_new)[0][1] 
    except Exception as e:
        return f"模型预测异常：{e}"
        
    final_proba = proba
    
    # 🌟【语义逻辑对冲核心】：辨证上下文对冲
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
            corrections.append(f"✨ 捕获【客观路人真情流露】高赞流派 (身份: {', '.join(hit_neutral_words)} | 情感: {', '.join(hit_deep_words)})")
            final_proba = max(final_proba, 0.78)
        else:
            corrections.append(f"捕获长尾高赞情感密码 (命中: {', '.join(hit_deep_words)})")
            final_proba = max(final_proba, 0.65) 
            
    elif hit_neutral_words:
        corrections.append(f"仅为普通路人/打卡流水账，缺乏长尾共鸣 (命中: {', '.join(hit_neutral_words)})")
        final_proba *= 0.5 

    # ④ 诊断面板
    diagnostic_panel = (
        f"📊 【语义对冲版 - 决策报告】\n"
        f"1. 评论原始字数：{raw_length} 字\n"
        f"2. 命中高频特征词：{', '.join(set(hit_words)) if hit_words else '无'}\n"
        f"3. 模型原生概率：{proba:.2%}\n"
    )
    if corrections:
        diagnostic_panel += f"🛠️ 语义纠偏动作：\n" + "\n".join([f"   • {c}" for c in corrections]) + "\n"
        
    diagnostic_panel += f"📈 最终校准后置信度：{final_proba:.2%} (及格线：{balanced_threshold:.2%})\n"
    diagnostic_panel += f"--------------------------------------------------\n"
    
    if final_proba >= balanced_threshold:
        return diagnostic_panel + "🌟 最终判定：【优质神评潜力股 (1)】"
    else:
        return diagnostic_panel + "💬 最终判定：【普通评论 (0)】"

# 启动 Web
interface = gr.Interface(
    fn=classify_comment_advanced, 
    inputs=gr.Textbox(lines=5, placeholder="前奏一响，深夜的耳机里全都是遗憾...", label="📝 待测乐评"),
    outputs=gr.Textbox(lines=12, label="📊 智能对冲决策结果"),
    title="🎵 腾讯音乐智能乐评挖掘系统 (语义对冲校准版)",
    description="基于 LightGBM 机器学习与 TF-IDF 特征矩阵，并辅以专家经验的语义对冲纠偏系统。"
)

if __name__ == "__main__":
    interface.launch()
