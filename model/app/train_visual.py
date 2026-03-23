# train_visual.py - 视觉模型训练
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader, random_split
import os

# === 配置 ===
DATA_DIR = './dataset_vision'
SAVE_PATH = 'bird_visual_model.pth'
CLASSES_PATH = 'bird_classes.txt'
BATCH_SIZE = 32
EPOCHS = 5 

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 开始训练！使用设备: {device}")
    
    # 2.把各种大小的图片变成统一格式
    data_transforms = transforms.Compose([
        transforms.Resize((224, 224)), # ResNet 需要 224x224
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 3. 加载数据集
    if not os.path.exists(DATA_DIR):
        print(f"❌ 错误：找不到 '{DATA_DIR}' 文件夹。请先下载并解压数据集！")
        return

    full_dataset = datasets.ImageFolder(DATA_DIR, transform=data_transforms)
    class_names = full_dataset.classes
    print(f"✅ 找到 {len(full_dataset)} 张图片，共 {len(class_names)} 种鸟类。")

    with open(CLASSES_PATH, "w") as f:
        for c in class_names:
            f.write(c + "\n")
    print(f"📝 类别列表已保存到 {CLASSES_PATH}")

    # 划分训练集和测试集 (80% 训练, 20% 测试)
    train_size = int(0.8 * len(full_dataset))
    test_size = len(full_dataset) - train_size
    train_dataset, test_dataset = random_split(full_dataset, [train_size, test_size])
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

    # 4. 下载预训练模型 (ResNet18)
    print("⬇️ 正在加载 ResNet18 模型...")
    model = models.resnet18(pretrained=True)
    
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    model = model.to(device)

    # 5. 定义优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 6. 开始循环训练
    for epoch in range(EPOCHS):
        print(f"\n🔥 第 {epoch+1}/{EPOCHS} 轮训练开始...")
        model.train()
        running_loss = 0.0
        
        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            
            if (i+1) % 10 == 0:
                print(f"   进度: [{i+1}/{len(train_loader)}] Loss: {loss.item():.4f}")

    # 7. 保存结果
    print("\n🎉 训练完成！正在保存模型...")
    torch.save(model.state_dict(), SAVE_PATH)
    print(f"💾 模型已保存为: {SAVE_PATH}")

if __name__ == '__main__':
    train()