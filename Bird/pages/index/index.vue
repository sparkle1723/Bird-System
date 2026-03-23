<template>
  <view class="home-container">
    
    <!-- 1. 顶部自定义导航/欢迎区 -->
    <view class="top-header">
      <view class="greeting">
        <text class="h1">你好，{{ isLogin ? username : '游客' }}</text>
        <text class="h2">今天想去哪里观测？</text>
      </view>
      <image class="avatar-small" src="/static/logo.png" mode="aspectFill"></image>
    </view>

    <!-- 2. 精致轮播图 -->
    <view class="swiper-box">
      <swiper 
        class="card-swiper" 
        circular 
        autoplay 
        interval="4000" 
        duration="500"
        indicator-dots
        indicator-active-color="#ffffff"
        indicator-color="rgba(255,255,255,0.5)"
      >
        <swiper-item v-for="(item, index) in bannerList" :key="index" class="swiper-item">
          <view class="swiper-content">
            <image class="swiper-img" :src="item.url" mode="aspectFill"></image>
            <view class="img-mask">
              <text class="img-text">{{ item.title }}</text>
            </view>
          </view>
        </swiper-item>
      </swiper>
    </view>

    <!-- 3. 数据概览卡片 -->
    <view class="stats-section">
      <view class="stat-card">
        <view class="stat-left">
          <text class="stat-label">{{ isLogin ? '我的记录' : '请先登录' }}</text>
          <text class="stat-num">{{ count }}</text>
        </view>
        <view class="stat-right">
          <view class="circle-icon">🕊️</view>
        </view>
      </view>
    </view>

    <!-- 4. 快捷功能区 -->
    <view class="section-title">快捷功能</view>
    <view class="grid-menu">
      
      <!-- 第一行：AI 智能功能 -->
      <view class="grid-item" @click="goScan">
        <view class="icon-box red-bg">📷</view>
        <text>拍照识别</text>
      </view>
      
      <view class="grid-item" @click="goDeepSeek">
        <view class="icon-box cyan-bg">🤖</view>
        <text>AI问鸟</text>
      </view>
      
      <view class="grid-item" @click="goVoice">
        <view class="icon-box purple-bg">🎙️</view>
        <text>声纹识别</text>
      </view>
      
      <!-- 第二行：记录管理功能 -->
      <view class="grid-item" @click="goEdit">
        <view class="icon-box orange-bg">✏️</view>
        <text>快速记录</text>
      </view>

      <view class="grid-item" @click="goStore">
        <view class="icon-box blue-bg">📦</view>
        <text>管理库存</text>
      </view>
      
      <view class="grid-item" @click="goMap">
        <view class="icon-box green-bg">🗺️</view>
        <text>查看地图</text>
      </view>

    </view>

  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { CONFIG } from '@/config.js';

const count = ref(0);
const isLogin = ref(false);
const username = ref('');

// 定义后端地址
const FASTAPI_BASE_URL = CONFIG.FASTAPI_BASE_URL;

// 本地图片配置
const bannerList = ref([
  { url: '/static/b1.jpg', title: '' },
  { url: '/static/b2.jpg', title: '' },
  { url: '/static/b3.jpg', title: '' },
  { url: '/static/b4.jpg', title: '' },
  { url: '/static/b5.jpg', title: '' }
]);

onShow(() => {
  const user = uni.getStorageSync('current_user');
  
  if (user && user.username) {
    isLogin.value = true;
    username.value = user.username; 
    
    // ★ 从 FastAPI 拉取记录列表以计算总数 ★
    fetchRecordCount(user.username);
  } else {
    isLogin.value = false;
    username.value = '游客';
    count.value = 0;
  }
});

const fetchRecordCount = (username) => {
  uni.request({
    url: `${FASTAPI_BASE_URL}/records`,
    method: 'GET',
    data: { username: username },
    success: (res) => {
      // 确保后端返回了正确的数据结构
      if (res.statusCode === 200 && res.data && res.data.data) {
        count.value = res.data.data.length; // 记录的长度即为数量
      }
    },
    fail: () => {
      console.error("获取统计数据失败");
    }
  });
};

const checkLogin = (callback) => {
  if (!isLogin.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 500);
  } else {
    callback();
  }
}

const goStore = () => uni.switchTab({ url: '/pages/store/store' });
const goMap = () => uni.switchTab({ url: '/pages/map/map' });
const goEdit = () => checkLogin(() => uni.navigateTo({ url: '/pages/edit/edit' }));
const goVoice = () => checkLogin(() => uni.navigateTo({ url: '/pages/voice/voice' }));

// ★★★ 新增跳转到识别页 ★★★
const goScan = () => checkLogin(() => uni.navigateTo({ url: '/pages/scan/scan' }));

// ★★★ 新增跳转到 DeepSeek AI 对话页 ★★★
const goDeepSeek = () => uni.navigateTo({ url: '/pages/chat/chat' });

</script>

<style>
/* 基础样式 */
.home-container { min-height: 100vh; background-color: #f6f7f9; padding-bottom: 20px; }
.top-header { padding: 53.5px 20px 20px; display: flex; justify-content: space-between; align-items: center; }
.greeting .h1 { font-size: 22px; font-weight: bold; color: #333; display: block; }
.greeting .h2 { font-size: 14px; color: #999; margin-top: 4px; display: block; }
.avatar-small { width: 40px; height: 40px; border-radius: 50%; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }

/* 轮播图样式 */
.swiper-box { padding: 6px 0 10px; display: flex; justify-content: center; }
.card-swiper { width: 92%; height: 480rpx; }
.swiper-content { width: 100%; height: 100%; border-radius: 16px; overflow: hidden; position: relative; box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15); }
.swiper-img { width: 100%; height: 100%; }
.img-mask { position: absolute; bottom: 0; left: 0; right: 0; height: 60px; background: linear-gradient(to top, rgba(0,0,0,0.6), transparent); padding: 0 15px; display: flex; align-items: center; }
.img-text { color: #fff; font-size: 16px; font-weight: 500; letter-spacing: 1px;}

/* 统计卡片样式 */
.stats-section { padding: 20px 4%; }
.stat-card { background: #fff; border-radius: 16px; padding: 25px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.stat-label { font-size: 14px; color: #888; display: block; margin-bottom: 5px; }
.stat-num { font-size: 32px; font-weight: bold; color: #333; }
.circle-icon { width: 50px; height: 50px; background: #eef2ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; }

/* 快捷功能样式 */
.section-title { font-size: 18px; font-weight: bold; padding: 0 4% 15px; color: #333; }
.grid-menu { display: flex; flex-wrap: wrap; padding: 0 2%; }

.grid-item { 
  width: 33.33%;
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  margin-bottom: 40px;
}

.icon-box { 
  width: 50px; height: 50px; 
  border-radius: 15px; 
  display: flex; align-items: center; justify-content: center; 
  font-size: 22px; 
  margin-bottom: 8px; 
  color: #fff; 
  box-shadow: 0 4px 10px rgba(0,0,0,0.1); 
}

.grid-item text { font-size: 12px; color: #666; }

/* 颜色类 */
.blue-bg { background: linear-gradient(135deg, #667eea, #764ba2); }
.green-bg { background: linear-gradient(135deg, #42e695, #3bb2b8); }
.orange-bg { background: linear-gradient(135deg, #f6d365, #fda085); }
.purple-bg { background: linear-gradient(135deg, #a18cd1, #fbc2eb); }
.red-bg { background: linear-gradient(135deg, #ff9a9e, #fecfef); }
.cyan-bg { background: linear-gradient(135deg, #00c6ff, #0072ff); }
</style>