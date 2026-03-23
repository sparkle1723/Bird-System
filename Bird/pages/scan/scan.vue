<template>
  <view class="container">
    
    <view class="image-box" @click="handleScan">
      <image v-if="imageUrl" :src="imageUrl" mode="aspectFit" class="scan-img"></image>
      <view v-else class="placeholder">
        <text class="camera-icon">📷</text>
        <text class="tip">点击拍摄/上传鸟类照片</text>
      </view>
      <view v-if="isScanning" class="scan-line"></view>
    </view>

    <view class="result-card" v-if="result.name">
      
      <view class="result-header">
        <text v-if="result.name !== '未知'" class="match-score">匹配度: {{ result.score }}%</text>
        <text v-if="result.confidence === 'low' && result.score < 40" class="low-confidence-tip">⚠️ 置信度较低</text>
        <text class="tag">雀灵识别</text>
      </view>
      <text class="bird-name">{{ result.name }}</text>
      <text class="bird-desc">{{ result.desc }}</text>
      
      <button type="primary" class="save-btn" @click="saveToStore">保存到我的仓库</button>

      <view class="chat-container">
        <view class="chat-title">💬 雀灵助手</view>
        
        <scroll-view scroll-y class="chat-list" :scroll-top="scrollTop" :scroll-with-animation="true">
          <view v-for="(msg, index) in chatHistory" :key="index" 
            class="chat-item" 
            :class="msg.role === 'user' ? 'chat-user' : 'chat-ai'">
            
            <view v-if="msg.role === 'ai'" class="chat-avatar ai-avatar">🤖</view>
            
            <view class="bubble">{{ msg.content }}</view>
            
            <view v-if="msg.role === 'user'" class="chat-avatar user-avatar">👤</view>
          </view>
        </scroll-view>

        <view class="input-box">
          <input 
            class="chat-input" 
            v-model="userInput" 
            placeholder="问问它吃什么？住哪里？" 
            confirm-type="send" 
            @confirm="sendChat" 
          />
          <view class="send-btn" @click="sendChat">发送</view>
        </view>
      </view>
    </view>

    <view class="start-tip" v-else>
      <text v-if="isScanning">正在上传图片并分析...</text>
      <text v-else>请上传清晰的照片以获取准确结果</text>
    </view>

  </view>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { CONFIG } from '@/config.js';

// 1. 接口地址配置
const AI_BASE_URL = CONFIG.AI_BASE_URL;
const UPLOAD_URL = CONFIG.AI_IMAGE_URL;       // AI识图接口
const CHAT_URL = CONFIG.AI_CHAT_URL;          // 聊天接口

// FastAPI 后端上传接口 (8000端口)
const FASTAPI_UPLOAD_URL = CONFIG.FASTAPI_UPLOAD_URL;

const imageUrl = ref('');
const localFilePath = ref(''); // 新增：用于临时保存相机的本地图片路径，供后续上传后端用
const isScanning = ref(false);
const result = ref({ name: '', desc: '', score: 0 });

// 聊天相关数据
const chatHistory = ref([]);
const userInput = ref('');
const scrollTop = ref(0);

// 1. 识图流程
const handleScan = () => {
  if (isScanning.value) return;
  
  // 重置状态
  result.value = { name: '', desc: '', score: 0 };
  chatHistory.value = [];

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['camera', 'album'], 
    success: (res) => {
      const filePath = res.tempFilePaths[0];
      
      localFilePath.value = filePath; // 存下本地路径，等会儿点“保存”时要传给 FastAPI

      generateBase64(res.tempFiles[0], filePath).then(base64 => { imageUrl.value = base64; });
      uploadImage(filePath);
    }
  });
};

const uploadImage = (filePath) => {
  isScanning.value = true;
  uni.uploadFile({
    url: UPLOAD_URL, 
    filePath: filePath,
    name: 'file',
    header: { 'ngrok-skip-browser-warning': 'true' },
    success: (res) => {
      isScanning.value = false;
      if (res.statusCode === 200) {
        try {
          const responseObj = JSON.parse(res.data);
          const birdData = responseObj.data; 

          if (birdData && birdData.name) {
            result.value = {
              name: birdData.name, 
              desc: birdData.desc || '暂无描述',
              score: Math.floor((birdData.score || 0) * 100),
              confidence: birdData.confidence
            };
            
            // 添加雀灵欢迎语（包括低置信度情况）
            if (birdData.name === '未知') {
              chatHistory.value.push({ 
                role: 'ai', 
                content: '哎呀，雀灵没认出这是什么鸟呢🤔 你可以描述一下它的特征，比如颜色、大小、在哪里看到的，我来帮你分析分析！'
              });
            } else if (birdData.confidence === 'low') {
              chatHistory.value.push({ 
                role: 'ai', 
                content: `雀灵觉得这可能是【${birdData.name}】，但不太确定。你可以问我关于${birdData.name}的问题，或者描述更多特征帮我确认！`
              });
            } else {
              chatHistory.value.push({ 
                role: 'ai', 
                content: `我是雀灵，我认出这是【${birdData.name}】。你可以问我关于它的习性、食物等问题哦！` 
              });
            }
          }
        } catch (e) { 
          console.error("解析数据失败:", e); 
        }
      }
    },
    fail: () => { isScanning.value = false; uni.showToast({ title: '网络错误', icon: 'none' }); }
  });
};

// 2. 发送聊天 (保持不变)
const sendChat = () => {
  const text = userInput.value.trim();
  if (!text) return;

  chatHistory.value.push({ role: 'user', content: text });
  const currentQuestion = text;
  userInput.value = ''; 
  scrollToBottom();

  uni.request({
    url: CHAT_URL,
    method: 'POST',
    header: { 'ngrok-skip-browser-warning': 'true' },
    data: {
      bird_name: result.value.name, 
      question: currentQuestion     
    },
    success: (res) => {
      if (res.statusCode === 200 && res.data && res.data.data && res.data.data.answer) {
        chatHistory.value.push({ role: 'ai', content: res.data.data.answer });
        scrollToBottom();
      }
    },
    fail: () => {
      chatHistory.value.push({ role: 'ai', content: '网络开小差了，请检查服务器。' });
      scrollToBottom();
    }
  });
};

// 辅助：Base64生成 (保持不变)
const generateBase64 = (fileObj, filePath) => {
  return new Promise((resolve) => {
    // #ifdef H5
    const reader = new FileReader();
    reader.readAsDataURL(fileObj);
    reader.onload = (e) => resolve(e.target.result);
    // #endif
    // #ifndef H5
    uni.getFileSystemManager().readFile({
      filePath: filePath, encoding: 'base64',
      success: r => resolve('data:image/jpeg;base64,' + r.data),
      fail: () => resolve(filePath)
    });
    // #endif
  });
};

// 保存到 FastAPI 后端
const saveToStore = () => {
  const user = uni.getStorageSync('current_user');
  if (!user || !user.username) {
    return uni.showToast({ title: '请先登录', icon: 'none' });
  }

  if (!localFilePath.value) {
    return uni.showToast({ title: '没有找到可保存的图片', icon: 'none' });
  }

  uni.showLoading({ title: '正在存入云端...' });

  // 使用 uni.uploadFile 上传文件及附带的表单数据(Form Data)
  uni.uploadFile({
    url: FASTAPI_UPLOAD_URL,         // 对应你后端的 @app.post("/upload")
    filePath: localFilePath.value,   // 刚拍的本地图片路径
    name: 'file',                    // 对应后端参数 file: UploadFile = File(...)
    formData: {                      // 对应后端接收的 Form(...)
      username: user.username,
      title: `[图像识别] ${result.value.name}`,
      content: result.value.desc
    },
    success: (res) => {
      uni.hideLoading();
      if (res.statusCode === 200) {
        // 注意：uni.uploadFile 返回的 res.data 是字符串类型，需要解析
        const data = JSON.parse(res.data);
        if (data.code === 200) {
          uni.showToast({ title: '已同步至云仓库', icon: 'success' });
          setTimeout(() => {
            // 保存成功后跳转到个人中心或记录页
            uni.switchTab({ url: '/pages/profile/profile' });
          }, 1000);
        } else {
          uni.showToast({ title: data.msg || '保存失败', icon: 'none' });
        }
      } else {
        uni.showToast({ title: '服务器开小差了', icon: 'none' });
      }
    },
    fail: (err) => {
      console.error('上传失败:', err);
      uni.hideLoading();
      uni.showToast({ title: '网络连接失败', icon: 'none' });
    }
  });
};

// 辅助：自动滚动到底部 (保持不变)
const scrollToBottom = () => {
  nextTick(() => { scrollTop.value += 500; }); 
};
</script>

<style>
.container { padding: 20px; background-color: #1c1c1e; min-height: 100vh; display: flex; flex-direction: column; align-items: center; }

/* 图片区 */
.image-box { width: 100%; height: 35vh; background-color: #2c2c2e; border-radius: 20px; overflow: hidden; position: relative; display: flex; align-items: center; justify-content: center; border: 2px dashed #444; margin-top: 10px; }
.scan-img { width: 100%; height: 100%; }
.placeholder { display: flex; flex-direction: column; align-items: center; }
.camera-icon { font-size: 50px; color: #666; margin-bottom: 10px; }
.tip { color: #888; font-size: 14px; }
.scan-line { position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(to right, transparent, #00ff00, transparent); animation: scan 2s infinite linear; }
@keyframes scan { 0% { top: 0; } 100% { top: 100%; } }

/* 结果卡片 */
.result-card { width: 100%; background: #fff; border-radius: 20px; padding: 20px; margin-top: -20px; z-index: 10; box-sizing: border-box; display: flex; flex-direction: column; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.match-score { color: #007AFF; font-weight: bold; font-size: 12px; }
.low-confidence-tip { color: #ff9500; font-weight: bold; font-size: 12px; margin-right: 10px; }
.tag { background: #e0f2ff; padding: 2px 8px; border-radius: 4px; font-size: 10px; color: #007AFF; }
.bird-name { font-size: 24px; font-weight: bold; color: #333; display: block; margin-bottom: 5px; }
.bird-desc { font-size: 13px; color: #666; margin-bottom: 15px; display: block; }
.save-btn { border-radius: 25px; background: linear-gradient(90deg, #007AFF, #00c6ff); font-size: 14px; margin-bottom: 15px; height: 40px; line-height: 40px; }

/* 聊天区域 */
.chat-container { border-top: 1px solid #eee; padding-top: 10px; flex: 1; display: flex; flex-direction: column; }
.chat-title { font-size: 14px; font-weight: bold; margin-bottom: 8px; color: #333; }
.chat-list { height: 250px; background: #f5f7fa; border-radius: 12px; padding: 10px; box-sizing: border-box; margin-bottom: 10px; }

.chat-item { display: flex; margin-bottom: 15px; align-items: flex-start; }
.chat-user { justify-content: flex-end; }
.chat-ai { justify-content: flex-start; }

.chat-avatar { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; background: #ddd; flex-shrink: 0; }
.ai-avatar { background: #e0f2ff; margin-right: 8px; }
.user-avatar { background: #007AFF; color: #fff; margin-left: 8px; }

.bubble { max-width: 70%; padding: 8px 12px; border-radius: 12px; font-size: 13px; line-height: 1.4; position: relative; }
.chat-user .bubble { background: #007AFF; color: #fff; border-top-right-radius: 2px; }
.chat-ai .bubble { background: #fff; color: #333; border: 1px solid #eee; border-top-left-radius: 2px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }

.input-box { display: flex; align-items: center; gap: 8px; }
.chat-input { flex: 1; background: #f0f0f0; height: 36px; border-radius: 18px; padding: 0 15px; font-size: 13px; }
.send-btn { color: #007AFF; font-weight: bold; padding: 0 5px; font-size: 14px; }

.start-tip { margin-top: 40px; color: #666; font-size: 14px; }
</style>