import os
from huggingface_hub import snapshot_download

# 1. 强制开启国内镜像加速
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

print("🚀 正在启动多线程断点续传...")
print("目标目录: raw_data")

# 2. 直接调用库函数下载 (这和命令行工具是一模一样的)
snapshot_download(
    repo_id="sakei/Bird_audio_in_China",
    repo_type="dataset",
    local_dir="raw_data",    # 下载到 raw_data 文件夹
    max_workers=8,           # 开启8线程加速
    resume_download=True     # 确保断点续传
)

print("✅ 下载完成！请继续运行解压脚本。")