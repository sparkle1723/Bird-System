# prepare_data.py - 数据集处理脚本
import os
import soundfile as sf
from datasets import load_dataset
from tqdm import tqdm

# 1. 设置路径
dataset_dir = 'dataset'
audio_dir = os.path.join(dataset_dir, 'audio')
os.makedirs(audio_dir, exist_ok=True)

print("🚀 正在从 Hugging Face 下载中国鸟类数据集 (可能会比较慢，请耐心等待)...")
# 加载数据集 (sakei/Bird_audio_in_China)
try:
    ds = load_dataset("sakei/Bird_audio_in_China", split="train")
except Exception as e:
    print(f"❌ 下载失败，请检查网络 (可能需要梯子): {e}")
    exit()

print(f"✅ 下载完成！共找到 {len(ds)} 条音频数据。正在转换格式...")

label_map = {}  # 存储 标签名 -> ID 的映射
train_lines = [] # 存储训练列表

# 2. 遍历数据并保存为 WAV
for i, item in tqdm(enumerate(ds), total=len(ds)):
    # 获取音频数据和标签
    audio_array = item['audio']['array']
    sr = item['audio']['sampling_rate']
    
    # 假设 dataset 里有个字段叫 'label' 或者 'bird_name'
    # 如果报错，我们需要打印 item.keys() 看看具体字段名
    # 这里假设标签字段是 'label' (通常是数字) 或 'name'
    # 为了保险，我们用 label 的索引
    label_idx = item['label'] 
    
    # 如果 dataset 包含真实鸟名，我们尝试获取
    # 注意：具体字段名取决于数据集结构，这里暂用 ID 命名文件夹
    label_name = str(label_idx) 
    
    # 保存路径: dataset/audio/0/123.wav
    save_folder = os.path.join(audio_dir, label_name)
    os.makedirs(save_folder, exist_ok=True)
    
    filename = f"{i}.wav"
    file_path = os.path.join(save_folder, filename)
    
    # 保存音频
    sf.write(file_path, audio_array, sr)
    
    # 记录到列表: 路径 标签ID
    # 注意：Windows路径可能需要转义，这里用相对路径
    rel_path = f"dataset/audio/{label_name}/{filename}"
    train_lines.append(f"{rel_path}\t{label_idx}")

# 3. 生成列表文件
print("📝 正在生成训练列表...")
with open(os.path.join(dataset_dir, 'train_list.txt'), 'w', encoding='utf-8') as f:
    for line in train_lines:
        f.write(line + '\n')

# 生成标签列表 (这里简单生成，后续可能需要根据数据集文档手动完善对应中文名)
unique_labels = sorted(list(set([x.split('\t')[1] for x in train_lines])))
with open(os.path.join(dataset_dir, 'label_list.txt'), 'w', encoding='utf-8') as f:
    for lbl in unique_labels:
        f.write(f"{lbl}\n")

print("🎉 搞定！数据已准备好。")
print(f"1. 音频保存在: {audio_dir}")
print(f"2. 训练列表: {os.path.join(dataset_dir, 'train_list.txt')}")
print("下一步：请运行训练脚本！")