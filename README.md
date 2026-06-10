# 🎵 QQ音乐榜单数据挖掘与“神评”AI智能预测系统

🎓 **【上海财经大学 - 数据科学导论期末项目】** | 这是一个基于 Python 爬虫、LightGBM 机器学习算法与 Gradio 云端部署的完整数据科学流水线项目。

---

## 🌟 核心亮点：在线一键体验 (Online Demo)
为了方便查阅与测试模型的实际预测效果，本项目已将训练好的 LightGBM 模型封装为 Web 前端，并部署于 Hugging Face 云端服务器。

**👉 无需配置任何本地环境，老师可以直接点击下方链接，输入评论进行测试：**

🔥 **[点击这里一键在线体验“神评”预测系统](https://huggingface.co/spaces/Zhuyyyan/qqmusic-project-app)** 🔥

*(注：云端首次加载可能需要几秒钟唤醒，请耐心等待网页显示为 Running 状态即可流畅交互)*

---

## 📖 项目简介 (Project Overview)
随着数字音乐平台的快速发展，歌曲评论区已成为用户情感共鸣的重要社区。本项目旨在通过完整的数据科学流程，探索“什么样的评论能成为高赞神评”。

项目包含以下三个核心模块：
1. **自动化数据采集**：编写 Python 爬虫 (`qq_music.py`)，抓取 QQ 音乐各大热门榜单的歌曲信息及海量用户评论（累计约 5 万条真实交互数据）。
2. **数据分析与机器学习**：在 `analysis.ipynb` 中进行数据清洗、文本特征工程构建（如文本长度、互动比例等），并训练高精度的 **LightGBM 二分类模型** 来预测评论潜力。
3. **模型工程化部署**：将训练完毕的核心模型导出为 `.pkl` 文件，利用 Gradio 框架搭建交互式前端 (`app.py`)，实现“离线训练、在线推理”的轻量级 AI 应用落地。

---

## 📂 仓库文件目录 (Repository Structure)
本项目核心代码及文件结构如下：

```text
📦 QQMusic-HotComment-Prediction
 ┣ 📜 qq_music.py           # 爬虫模块：全量抓取热门榜单歌曲与评论数据的自动化脚本
 ┣ 📓 analysis.ipynb        # 核心分析模块：包含数据探索(EDA)、特征提取与 LightGBM 模型训练的全过程
 ┣ 📜 app.py                # 前端部署模块：Gradio 交互式网页的源代码
 ┣ 📄 requirements.txt      # 环境依赖清单：云端部署所需的 Python 核心第三方库
 ┗ 🧠 best_model.pkl        # 序列化模型：在本地训练完成的 LightGBM 满血模型大脑（供云端直接调用）# Tencent-Music-Comments-LightGBM
