<template>
  <view class="center-container">
    <!-- 头部区域 -->
    <view class="header" @click="checkLogin">
      <!-- 装饰圆圈 -->
      <view class="decor-circle decor-1"></view>
      <view class="decor-circle decor-2"></view>
      
      <!-- 头像 -->
      <view class="avatar-wrapper">
        <image class="avatar" :src="isLogin ? '/static/logo.png' : '/static/logo.png'"></image>
        <view class="avatar-badge" v-if="isLogin">✓</view>
      </view>
      
      <view class="user-info">
        <text class="main-id">{{ isLogin ? userInfo.username : '点击登录' }}</text>
        <text class="sub-text">{{ isLogin ? '已登录' : '登录后解锁更多功能' }}</text>
      </view>
      
    </view>
    
    <!-- 数据统计卡片 -->
    <view class="stats-card" v-if="isLogin">
      <view class="stat-item">
        <text class="stat-num">{{ recordCount }}</text>
        <text class="stat-label">识别记录</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="stat-num">{{ daysCount }}</text>
        <text class="stat-label">使用天数</text>
      </view>
    </view>
    
    <!-- 菜单列表 -->
    <view class="menu-section">
      <view class="section-title">功能</view>
      <view class="menu-list">
        <view class="menu-item" @click="goStore">
          <view class="menu-icon">📦</view>
          <text class="menu-text">我的仓库</text>
          <text class="arrow">›</text>
        </view>
        <view class="menu-item" @click="goAbout">
          <view class="menu-icon">ℹ️</view>
          <text class="menu-text">关于我们</text>
          <text class="arrow">›</text>
        </view>
      </view>
    </view>
    
    <!-- 退出登录 -->
    <view class="logout-section" v-if="isLogin">
      <button class="logout-btn" @click="handleLogout">退出登录</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { CONFIG } from '@/config.js';

const isLogin = ref(false);
const userInfo = ref({});
const recordCount = ref(0);

// 计算使用天数
const daysCount = computed(() => {
  if (!userInfo.value.created_at) return 1;
  const createDate = new Date(userInfo.value.created_at);
  const now = new Date();
  const diff = Math.floor((now - createDate) / (1000 * 60 * 60 * 24)) + 1;
  return diff > 0 ? diff : 1;
});

onShow(() => {
  const user = uni.getStorageSync('current_user');
  if (user) {
    isLogin.value = true;
    userInfo.value = user;
    fetchRecordCount(user.username);
  } else {
    isLogin.value = false;
    userInfo.value = {};
    recordCount.value = 0;
  }
});

// 获取记录数量
const fetchRecordCount = (username) => {
  uni.request({
    url: `${CONFIG.FASTAPI_BASE_URL}/records`,
    method: 'GET',
    data: { username },
    success: (res) => {
      if (res.statusCode === 200 && res.data.code === 200) {
        recordCount.value = res.data.data ? res.data.data.length : 0;
      }
    }
  });
};

const checkLogin = () => {
  if (!isLogin.value) {
    uni.navigateTo({ url: '/pages/login/login' });
  }
};

const goAbout = () => {
  uni.navigateTo({ url: '/pages/about/about' });
};

const goStore = () => {
  uni.switchTab({ url: '/pages/store/store' });
};

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('current_user');
        isLogin.value = false;
        userInfo.value = {};
        uni.showToast({ title: '已退出', icon: 'none' });
      }
    }
  });
};
</script>

<style>
/* 容器背景色 */
.center-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

/* 头部样式 */
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 20px 40px;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* 装饰圆圈 */
.decor-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
}
.decor-1 {
  width: 150px;
  height: 150px;
  top: -50px;
  right: -30px;
}
.decor-2 {
  width: 80px;
  height: 80px;
  bottom: 20px;
  right: 60px;
}

/* 头像包装 */
.avatar-wrapper {
  position: relative;
  margin-right: 15px;
}

.avatar {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid rgba(255,255,255,0.4);
}

.avatar-badge {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  background: #52c41a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #fff;
  border: 2px solid #fff;
}

.user-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
}

.main-id {
  color: #fff;
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 6px;
}

.sub-text {
  color: rgba(255,255,255,0.8);
  font-size: 13px;
}

.header-arrow {
  color: rgba(255,255,255,0.6);
  font-size: 28px;
  margin-left: 10px;
}

/* 统计卡片 */
.stats-card {
  margin: -20px 15px 20px;
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  position: relative;
  z-index: 10;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: #eee;
}

/* 菜单区域 */
.menu-section {
  padding: 0 15px;
}

.section-title {
  font-size: 14px;
  color: #999;
  margin: 20px 0 10px 5px;
}

.menu-list {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.menu-item {
  padding: 16px 18px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f5f5f5;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-item:active {
  background-color: #f9f9f9;
}

.menu-icon {
  font-size: 20px;
  margin-right: 12px;
}

.menu-text {
  flex: 1;
  font-size: 15px;
  color: #333;
}

.arrow {
  color: #ccc;
  font-size: 18px;
}

/* 退出按钮 */
.logout-section {
  padding: 30px 15px;
}

.logout-btn {
  width: 100%;
  height: 46px;
  line-height: 46px;
  background: #fff;
  color: #ff4d4f;
  font-size: 15px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.logout-btn:active {
  background: #fff5f5;
}
</style>