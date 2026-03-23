import os
import sys
import yaml
import torch

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接出 pymodel 的路径
pymodel_path = os.path.join(current_dir, 'pymodel')
sys.path.append(pymodel_path)

print(f"正在尝试从这里加载模型: {pymodel_path}")

try:
    # 尝试导入音频预测工具
    from macls.predict import MAClsPredictor
    from macls.utils.utils import dict_to_object
except ImportError as e:
    print("错误：找不到 macls 库。请确认你在 'app' 文件夹下运行此脚本，且 'pymodel' 文件夹存在。")
    print(f"详细错误: {e}")
    sys.exit(1)

def run_recognition():
    # ================= 配置路径 =================
    # 1. 配置文件路径 
    configs_dir = os.path.join(pymodel_path, 'configs')
    config_path = ""
    
    # 自动寻找 yaml 配置文件
    if os.path.exists(configs_dir):
        for file in os.listdir(configs_dir):
            if file.endswith('.yml') or file.endswith('.yaml'):
                config_path = os.path.join(configs_dir, file)
                print(f"找到配置文件: {file}")
                break
    
    if not config_path:
        print("错误：在 pymodel/configs 下找不到 .yml 配置文件！")
        return

    # 2. 模型权重文件路径
    model_path = os.path.join(pymodel_path, 'models', 'model.pth')
    
    if not os.path.exists(model_path):
        print(f"错误：找不到模型文件 {model_path}")
        return

    # ================= 开始识别 =================
    print("正在加载模型，请稍候...")
    
    # 初始化预测器
    predictor = MAClsPredictor(configs=config_path,
                               model_path=model_path,
                               use_gpu=False) # 小白先用 CPU 跑，稳一点
    
    # 测试音频路径
    audio_path = os.path.join(current_dir, 'test.wav')
    
    if not os.path.exists(audio_path):
        print("错误：请在 app 目录下放一个 'test.wav' 音频文件用来测试！")
        return

    print(f"正在识别音频: {audio_path} ...")
    
    # 获取结果
    label, score = predictor.predict(audio_path)
    
    print("\n============= 识别结果 =============")
    # ================= 翻译字典 =================
    bird_dict = {
        "Hirundo": "燕子",
        "Passer": "麻雀",
        "Pica": "喜鹊",
        "Anas": "鸭子",
        "Phasianus": "雉鸡",
        "Streptopelia": "斑鸠",
        "Accipiter": "鹰",
    
    }
    
    chinese_name = bird_dict.get(label, label) 
    
    print("\n============= 识别结果 =============")
    print(f"🐦 鸟类名称: {chinese_name} ({label})")
    print(f"📊 置信度: {score:.2f} (越接近 1 越准)")
    
    if score < 0.5:
        print("⚠️ : 无法准确识别音频，可能是噪音太大或声音太短。")
    print("===================================")

if __name__ == '__main__':
    run_recognition()
