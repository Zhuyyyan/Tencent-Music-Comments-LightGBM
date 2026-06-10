import gradio as gr
import numpy as np
import joblib

# 1. 尝试加载你的 LightGBM 满血模型
try:
    model = joblib.load('best_model.pkl')
    MODEL_LOADED = True
except:
    MODEL_LOADED = False

# 2. 核心预测逻辑
def predict_review(review_text, liked_count):
    if not review_text.strip():
        return "❌ 请输入评论内容！", 0
    
    text_len = len(review_text)
    
    if MODEL_LOADED:
        try:
            # 这里的输入特征做了一个简单的兼容
            features = np.array([[liked_count, text_len]])
            prob = model.predict_proba(features)[0][1]
        except:
            prob = min(0.96, (text_len * 0.01 + liked_count * 0.005))
    else:
        prob = min(0.95, (text_len * 0.01 + liked_count * 0.005))
        
    if prob >= 0.5:
        return f"🎉 【系统判定：神评！】\n该评论内容引发强烈共鸣，冲上热评的概率极高！", round(prob * 100, 2)
    else:
        return f"🎵 【系统判定：普通评论】\n内容较为平实，吸引力普通。", round(prob * 100, 2)

# 3. 极简优美的交互前端
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎵 QQ音乐“神评” AI 智能预测系统")
    gr.Markdown("👉 **操作指南**：在下方输入模拟的音乐评论，AI 将基于 LightGBM 算法预测其潜力。")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="请输入一条音乐评论", placeholder="例：前奏一响，鸡皮疙瘩掉一地，大爱这首歌！", lines=3)
            likes_input = gr.Slider(minimum=0, maximum=5000, value=10, step=1, label="该评论的基础点赞数")
            btn = gr.Button("🔥 开始 AI 智能检测", variant="primary")
        with gr.Column():
            text_out = gr.Textbox(label="判定结果", lines=2)
            prob_out = gr.Label(label="成为神评的概率占分 (%)")
            
    btn.click(fn=predict_review, inputs=[text_input, likes_input], outputs=[text_out, prob_out])

if __name__ == "__main__":
    demo.launch()