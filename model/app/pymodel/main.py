"""
 * Original work Copyright 2024 yeyupiaoling
 * Modified work Copyright 2025 Jiachen You & Pengzhe Miao
 * Licensed under Apache License 2.0 (see LICENSE file)
"""
import os
from pydub import AudioSegment, silence
import noisereduce as nr
import numpy as np
import scipy.io.wavfile as wav

import argparse
from datetime import datetime

from macls.predict import MAClsPredictor
from macls.utils.utils import print_arguments

# ------ 音频处理 ------

# --- 配置路径 ---
parser = argparse.ArgumentParser(description='音频处理与分类脚本')
parser.add_argument('--input', type=str, required=True, help='输入音频文件路径')
parser.add_argument('--output', type=str, required=True, help='输出音频文件名')
parser.add_argument('--configs', type=str, default="configs/cam++.yml", help='配置文件')
parser.add_argument('--use_gpu', type=bool, default=False, help='是否使用GPU预测')
parser.add_argument('--model_path', type=str,
                    default="models/",
                    help='导出的预测模型文件路径')
args = parser.parse_args()

# 验证输入文件
if not os.path.exists(args.input):
    raise FileNotFoundError(f"输入文件不存在: {args.input}")

input_path = args.input
denoised_path = "denoised.wav"
output_folder = "output"

# --- 创建输出文件夹 ---
os.makedirs(output_folder, exist_ok=True)

# 生成日期格式的文件名 (YYMMDD.wav)
current_date = datetime.now().strftime("%y%m%d")
merged_output = os.path.join(output_folder, args.output)

print("加载音频...")
try:
    sound = AudioSegment.from_file(args.input)
except Exception as e:
    raise ValueError(f"无法加载音频文件: {e}")

try:
    rate, data = wav.read(args.input)
except Exception as e:
    raise ValueError(f"无法读取WAV文件: {e}")
if len(data.shape) == 2:
    data = data.mean(axis=1)

print("正在降噪...")
reduced_noise = nr.reduce_noise(y=data, sr=rate)
wav.write(denoised_path, rate, reduced_noise.astype(np.int16))

try:
    denoised = AudioSegment.from_file(denoised_path)
except Exception as e:
    raise ValueError(f"无法加载降噪后的音频: {e}")

print("检测非静音片段...")
non_silents = silence.detect_nonsilent(
    denoised,
    min_silence_len=500,
    silence_thresh=denoised.dBFS - 20,
)

print(f"共检测到 {len(non_silents)} 个有声音的片段。")

combined = AudioSegment.empty()
for i, (start, end) in enumerate(non_silents):
    combined += denoised[start:end]

combined.export(merged_output, format="wav")
print(f"已将所有片段合并为: {merged_output}")

# ------ 音频预测 ------
print_arguments(args=args)

predictor = MAClsPredictor(
    configs=args.configs, model_path=args.model_path, use_gpu=args.use_gpu
)

label, score = predictor.predict(audio_data=merged_output)
print(f"合并后的音频预测结果标签为: {label}, 得分: {score}")

# --- 清理临时文件 ---
if os.path.exists(denoised_path):
    os.remove(denoised_path)
    print("清理临时文件: denoised.wav")