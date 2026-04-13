<template>
  <view class="container">
    <!-- 顶部标题 -->
    <view class="header">
      <view class="header-top">
        <view class="back-btn" @click="goHome">
          <text class="back-icon">‹</text>
        </view>
        <text class="title">🐦 雀灵 - 鸟类AI助手</text>
        <view class="placeholder"></view>
      </view>
      <text class="subtitle">随时问我关于鸟类的任何问题</text>
    </view>

    <!-- 聊天列表 -->
    <scroll-view scroll-y class="chat-list" :scroll-top="scrollTop" :scroll-with-animation="true">
      <view v-for="(msg, index) in chatHistory" :key="index" 
        class="chat-item" 
        :class="msg.role === 'user' ? 'chat-user' : 'chat-ai'">
        
        <image v-if="msg.role === 'ai'" class="chat-avatar ai-avatar" src="/static/1.png" mode="aspectFill"></image>
        
        <view class="bubble">
          <text v-if="msg.role === 'ai' && msg.isMarkdown" class="markdown-content">{{ msg.content }}</text>
          <text v-else>{{ msg.content }}</text>
        </view>
        
        <image v-if="msg.role === 'user'" class="chat-avatar user-avatar" src="/static/logo.png" mode="aspectFill"></image>
      </view>
      
      <!-- 加载中提示 -->
      <view v-if="isLoading" class="loading-tip">
        <text>雀灵助手 正在思考...</text>
      </view>
    </scroll-view>

    <!-- 输入框 -->
    <view class="input-area">
      <view class="input-box">
        <input 
          class="chat-input" 
          v-model="userInput" 
          placeholder="问我关于鸟类的问题，比如：麻雀吃什么？" 
          confirm-type="send"
          :disabled="isLoading"
          @confirm="sendMessage"
        />
        <view class="send-btn" :class="{ 'disabled': isLoading || !userInput.trim() }" @click="sendMessage">
          <text>发送</text>
        </view>
      </view>
      
      <!-- 快捷问题 -->
      <scroll-view scroll-x class="quick-questions">
        <view class="quick-item" @click="askQuick('鹦鹉怎么训练说话？')">鹦鹉训练</view>
        <view class="quick-item" @click="askQuick('如何辨别雄鸟和雌鸟？')">辨别雌雄</view>
        <view class="quick-item" @click="askQuick('候鸟为什么要迁徙？')">候鸟迁徙</view>
        <view class="quick-item" @click="askQuick('什么鸟适合家养？')">家养推荐</view>
        <view class="quick-item" @click="askQuick('鸟类吃什么食物？')">鸟类食物</view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick } from 'vue';

// DeepSeek API 配置 - 请替换为你的 API Key
const DEEPSEEK_API_KEY = 'sk-e042912a9042446c9bb05a503db69f66';
const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

const chatHistory = ref([
  { 
    role: 'ai', 
    content: '你好！我是雀灵🐦\n\n我可以帮你：\n• 识别鸟类品种\n• 解答鸟类习性\n• 推荐养鸟知识\n• 鸟类保护咨询\n\n直接输入问题，或点击下方快捷问题开始吧！',
    isMarkdown: false
  }
]);
const userInput = ref('');
const scrollTop = ref(0);
const isLoading = ref(false);

// 发送消息
const sendMessage = async () => {
  const text = userInput.value.trim();
  if (!text || isLoading.value) return;

  // 添加用户消息
  chatHistory.value.push({ role: 'user', content: text });
  userInput.value = '';
  scrollToBottom();

  isLoading.value = true;

  try {
    const res = await uni.request({
      url: DEEPSEEK_API_URL,
      method: 'POST',
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      data: {
        model: 'deepseek-chat',
        messages: [
          {
            role: 'system',
            content: '你是一位专业的鸟类学专家，擅长解答各种鸟类相关问题。回答要准确、简洁、易懂，适合普通读者阅读。'
          },
          ...chatHistory.value.filter(msg => msg.role !== 'system').map(msg => ({
            role: msg.role === 'ai' ? 'assistant' : 'user',
            content: msg.content
          }))
        ],
        temperature: 0.7,
        max_tokens: 2000
      }
    });

    if (res.statusCode === 200 && res.data.choices && res.data.choices[0]) {
      const answer = res.data.choices[0].message.content;
      chatHistory.value.push({ 
        role: 'ai', 
        content: answer,
        isMarkdown: true
      });
    } else {
      chatHistory.value.push({ 
        role: 'ai', 
        content: '抱歉，我暂时无法回答，请稍后再试。',
        isMarkdown: false
      });
    }
  } catch (e) {
    console.error('请求失败:', e);
    chatHistory.value.push({ 
      role: 'ai', 
      content: '网络连接失败，请检查网络或 API Key 是否正确。',
      isMarkdown: false
    });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};

// 快捷问题
const askQuick = (question) => {
  userInput.value = question;
  sendMessage();
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value += 9999;
  });
};

// 返回主页
const goHome = () => {
  uni.switchTab({
    url: '/pages/index/index'
  });
};
</script>

<style>
.container { 
  min-height: 100vh; 
  background-color: #f5f7fa; 
  display: flex; 
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

/* 头部 */
.header { 
  background: linear-gradient(135deg, #667eea, #764ba2); 
  padding: 40px 20px 20px; 
  text-align: center;
}
.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}
.back-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-left: -5px;
}
.back-icon {
  color: #fff;
  font-size: 36px;
  font-weight: 200;
}
.placeholder {
  width: 40px;
}
.title { 
  color: #fff; 
  font-size: 18px; 
  font-weight: bold;
}
.subtitle { 
  color: rgba(255,255,255,0.8); 
  font-size: 12px; 
  margin-top: 5px; 
  display: block;
}

/* 聊天列表 */
.chat-list { 
  flex: 1; 
  padding: 15px; 
  box-sizing: border-box;
  width: 100%;
}

.chat-item { 
  display: flex; 
  margin-bottom: 15px; 
  align-items: flex-start;
  width: 100%;
  box-sizing: border-box;
}
.chat-user { 
  justify-content: flex-end; 
}
.chat-ai { 
  justify-content: flex-start; 
}

.chat-avatar { 
  width: 40px; 
  height: 40px; 
  border-radius: 50%; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-size: 22px; 
  flex-shrink: 0;
  overflow: hidden;
  box-sizing: border-box;
}
.ai-avatar { 
  margin-right: 10px;
}
.user-avatar { 
  border: 2px solid #4ECDC4;
  margin-left: 10px; 
}

.bubble { 
  max-width: 65%; 
  padding: 12px 15px; 
  border-radius: 18px; 
  font-size: 14px; 
  line-height: 1.6; 
  white-space: pre-wrap;
  word-break: break-all;
}
.chat-user .bubble { 
  background: #007AFF; 
  color: #fff; 
  border-top-right-radius: 4px; 
}
.chat-ai .bubble { 
  background: #fff; 
  color: #333; 
  border: 1px solid #e0e0e0; 
  border-top-left-radius: 4px; 
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.markdown-content {
  font-size: 14px;
  line-height: 1.6;
}

.loading-tip {
  text-align: center;
  color: #999;
  font-size: 12px;
  padding: 10px;
}

/* 输入区域 */
.input-area {
  background: #fff;
  padding: 10px 15px 20px;
  border-top: 1px solid #eee;
}

.input-box { 
  display: flex; 
  align-items: center; 
  gap: 10px;
  margin-bottom: 10px;
}
.chat-input { 
  flex: 1; 
  background: #f0f0f0; 
  height: 44px; 
  border-radius: 22px; 
  padding: 0 18px; 
  font-size: 14px;
}
.send-btn { 
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  padding: 0 20px;
  height: 44px;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
}
.send-btn.disabled {
  background: #ccc;
}

/* 快捷问题 */
.quick-questions {
  white-space: nowrap;
}
.quick-item {
  display: inline-block;
  background: #f0f0f0;
  color: #666;
  padding: 6px 14px;
  border-radius: 15px;
  font-size: 12px;
  margin-right: 8px;
}
</style>
