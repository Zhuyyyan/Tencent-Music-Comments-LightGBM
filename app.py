import os
import re

import gradio as gr
import jieba
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC",
    "SimHei",
    "Arial Unicode MS",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False

MODEL_FILE = "best_model.pkl"
TFIDF_FILE = "tfidf_vec.pkl"
FEATURES_FILE = "trained_features.pkl"
SONGS_FILE = "tme_qqmusic_songs_massive.csv"

TEST_METRICS = {
    "Accuracy": "60.72%",
    "F1-Score": "54.69%",
    "ROC-AUC": "0.656",
}

try:
    best_clf_model = joblib.load(MODEL_FILE)
    tfidf_vec = joblib.load(TFIDF_FILE)
    trained_features = list(joblib.load(FEATURES_FILE))
    MODEL_LOADED = True
    MODEL_ERROR = ""
except Exception as exc:
    best_clf_model = None
    tfidf_vec = None
    trained_features = []
    MODEL_LOADED = False
    MODEL_ERROR = str(exc)

try:
    df_songs = pd.read_csv(SONGS_FILE) if os.path.exists(SONGS_FILE) else None
except Exception:
    df_songs = None

decision_threshold = 0.50

fan_keywords = [
    "演唱会", "华语乐坛", "陪伴", "时代", "青春是", "终于等到", "才华",
    "实力", "嗓音", "歌手", "偶像", "编曲", "作词", "新歌", "单曲",
    "专辑", "大卖", "现场", "入坑", "循环", "支持", "神仙",
]

negative_words = {"一般般", "一般", "随便听听", "凑热闹", "切", "难听"}
identity_words = {"纯路人", "路人", "打卡", "支持"}
emotional_words = {
    "深夜", "眼泪", "耳机", "哭", "憋不住", "回忆", "遗憾",
    "错过的", "再也", "前奏", "惊艳", "沦陷",
}


def find_hits(words, candidates):
    return sorted({word for word in words if word in candidates})


def classify_comment(text):
    if not MODEL_LOADED:
        return f"模型组件加载失败：{MODEL_ERROR}"

    text_str = str(text or "").strip()
    if not text_str:
        return "请输入有效的音乐评论。"

    raw_length = len(text_str)
    x_new = pd.DataFrame(0.0, index=[0], columns=trained_features)

    if "comment_length" in x_new.columns:
        x_new.loc[0, "comment_length"] = raw_length
    if "has_mv_flag" in x_new.columns:
        x_new.loc[0, "has_mv_flag"] = 1.0
    if "song_tags_encoded" in x_new.columns:
        x_new.loc[0, "song_tags_encoded"] = 0.0
    if "fan_effect_score" in x_new.columns:
        x_new.loc[0, "fan_effect_score"] = float(
            sum(word in text_str for word in fan_keywords)
        )

    words = jieba.lcut(text_str)
    chinese_words = [
        word for word in words
        if len(word) > 1 and re.fullmatch(r"[\u4e00-\u9fa5]+", word)
    ]
    cleaned_text = " ".join(chinese_words)

    hit_features = []
    tfidf_matrix = tfidf_vec.transform([cleaned_text])
    for word, value in zip(
        tfidf_vec.get_feature_names_out(),
        tfidf_matrix.toarray()[0],
    ):
        column = f"纯中文词_{word}"
        if value > 0 and column in x_new.columns:
            x_new.loc[0, column] = value
            hit_features.append(word)

    try:
        model_score = float(best_clf_model.predict_proba(x_new)[0][1])
    except Exception as exc:
        return f"模型预测失败：{exc}"

    adjusted_score = model_score
    adjustments = []

    bad_hits = find_hits(chinese_words, negative_words)
    identity_hits = find_hits(chinese_words, identity_words)
    emotional_hits = find_hits(chinese_words, emotional_words)

    if bad_hits:
        adjusted_score *= 0.2
        adjustments.append(
            f"低共鸣或批评词降权：{', '.join(bad_hits)}"
        )
    elif emotional_hits:
        if identity_hits:
            adjusted_score = max(adjusted_score, 0.78)
            adjustments.append(
                "识别到路人身份与情绪表达组合："
                f"{', '.join(identity_hits + emotional_hits)}"
            )
        else:
            adjusted_score = max(adjusted_score, 0.65)
            adjustments.append(
                f"识别到情绪共鸣词：{', '.join(emotional_hits)}"
            )
    elif identity_hits:
        adjusted_score *= 0.5
        adjustments.append(
            f"仅识别到身份或打卡表达：{', '.join(identity_hits)}"
        )

    adjusted_score = float(np.clip(adjusted_score, 0.0, 1.0))
    result = (
        "潜在共鸣评论"
        if adjusted_score >= decision_threshold
        else "普通评论"
    )

    lines = [
        "【评论文本分析结果】",
        f"评论长度：{raw_length}字",
        f"命中的TF-IDF词：{', '.join(sorted(set(hit_features))) or '无'}",
        f"模型原始输出：{model_score:.2%}",
    ]

    if adjustments:
        lines.append("规则调整：" + "；".join(adjustments))
    else:
        lines.append("规则调整：未触发")

    lines.extend([
        f"规则调整后的潜在共鸣得分：{adjusted_score:.2%}",
        f"展示判定：{result}",
        "",
        "说明：该得分用于课程展示，不是经过概率校准的真实热评概率。",
        "评论热度还会受到发布时间、曝光位置、歌曲热度和粉丝群体等因素影响。",
    ])
    return "\n".join(lines)


def empty_chart(message):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.text(
        0.5, 0.5, message,
        ha="center", va="center", color="gray", fontsize=12,
    )
    ax.axis("off")
    plt.tight_layout()
    return fig


def show_chart(chart_name):
    if chart_name == "歌曲评论量 TOP 10":
        if df_songs is None or "song_name" not in df_songs.columns:
            return empty_chart("未读取到歌曲数据文件")

        value_column = (
            "comment_num"
            if "comment_num" in df_songs.columns
            else None
        )
        if value_column is None:
            return empty_chart("歌曲数据中没有 comment_num 字段")

        top_10 = df_songs.nlargest(10, value_column)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        sns.barplot(
            data=top_10,
            x=value_column,
            y="song_name",
            ax=ax,
            color="#5B8FF9",
        )
        ax.set_title("样本歌曲评论量 TOP 10")
        ax.set_xlabel("评论量")
        ax.set_ylabel("歌曲")
        plt.tight_layout()
        return fig

    if chart_name == "LightGBM真实特征重要性":
        if not MODEL_LOADED or not hasattr(
            best_clf_model, "feature_importances_"
        ):
            return empty_chart("当前模型不支持特征重要性展示")

        importance = pd.DataFrame({
            "feature": trained_features,
            "importance": best_clf_model.feature_importances_,
        }).nlargest(20, "importance")

        fig, ax = plt.subplots(figsize=(8, 5.5))
        sns.barplot(
            data=importance,
            x="importance",
            y="feature",
            ax=ax,
            color="#61DDAA",
        )
        ax.set_title("LightGBM真实特征重要性 TOP 20")
        ax.set_xlabel("模型特征重要性")
        ax.set_ylabel("特征")
        plt.tight_layout()
        return fig

    return empty_chart(
        "测试集结果\n"
        f"Accuracy：{TEST_METRICS['Accuracy']}\n"
        f"F1-Score：{TEST_METRICS['F1-Score']}\n"
        f"ROC-AUC：{TEST_METRICS['ROC-AUC']}\n\n"
        "以上指标来自 analysis.ipynb 的测试集结果。"
    )


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# QQ音乐评论数据分析与潜在共鸣评论识别")
    gr.Markdown(
        "本页面用于展示评论文本的获赞倾向与情感共鸣特征。"
        "结果不代表评论一定会成为QQ音乐平台真实热评。"
    )

    with gr.Tabs():
        with gr.TabItem("评论文本分析"):
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        lines=5,
                        placeholder="请输入一条音乐评论……",
                        label="音乐评论",
                    )
                    predict_button = gr.Button(
                        "开始分析",
                        variant="primary",
                    )
                with gr.Column():
                    text_output = gr.Textbox(
                        lines=13,
                        label="分析结果",
                    )

            predict_button.click(
                fn=classify_comment,
                inputs=text_input,
                outputs=text_output,
            )

        with gr.TabItem("数据与模型展示"):
            selector = gr.Radio(
                [
                    "歌曲评论量 TOP 10",
                    "LightGBM真实特征重要性",
                    "模型测试集指标",
                ],
                value="歌曲评论量 TOP 10",
                label="选择展示内容",
            )
            plot_output = gr.Plot()
            selector.change(
                fn=show_chart,
                inputs=selector,
                outputs=plot_output,
            )
            demo.load(
                fn=show_chart,
                inputs=selector,
                outputs=plot_output,
            )


if __name__ == "__main__":
    demo.launch()
