# 鸟了么 (Bird Watcher)

一款专为鸟类爱好者打造的智能识别与记录应用。通过 AI 技术，帮助用户识别鸟类、记录观测数据、学习鸟类知识。

## 核心功能

### 📷 拍照识别
上传鸟类照片，AI 智能识别鸟类品种

### 🎙️ 声纹识别
录制鸟鸣声音，辨别鸟类种类

### 🤖 雀灵助手
AI 鸟类专家，基于大语言模型，随时解答鸟类相关问题

### 📦 观测记录
记录每次观测，建立个人数据库

## AI 技术架构

### 🤖 雀灵助手
基于 DeepSeek V3 大语言模型，使用鸟类知识库微调训练，支持自然语言问答。

### 📷 图像识别
基于 ResNet18 卷积神经网络，使用 CUB-200 鸟类数据集训练。

### 🎙️ 声纹识别
基于 CAM++ 声纹模型，使用梅尔频谱特征提取，支持鸟类叫声分类识别。

## 技术栈

| 类别 | 技术 |
|------|------|
| 前端 | uni-app + Vue3 |
| 后端 | FastAPI + Flask |
| 数据库 | SQLite |

## 项目结构

```
├── Bird/                # uni-app 前端项目
│   ├── pages/           # 页面文件
│   ├── static/          # 静态资源
│   └── uni_modules/     # uni-app 组件
├── backend/             # Python 后端
│   ├── main.py          # FastAPI 主程序
│   ├── database.py      # 数据库配置
│   └── models.py        # 数据模型
└── model/               # AI 模型服务
    ├── app/
    │   ├── pymodel/     # 模型文件
    │   └── dataset/     # 数据集
    └── server.py        # Flask 模型服务
```

## 快速开始

### 前端运行

```bash
cd Bird
npm install
npm run dev
```

### 后端运行

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### AI 模型服务

```bash
cd model
pip install -r requirements.txt
python server.py
```

## 联系方式

- 作者：@小北
- 公司：洛圣都网络科技有限公司

## 许可证

© 2026 Bird Watcher. All rights reserved.
