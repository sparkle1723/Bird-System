<template>
  <view class="container">
    <view class="header-title">📦 我的仓库</view>

    <view v-if="!isLogin" class="empty-tip">
      <text>请先登录后查看数据</text>
      <button size="mini" type="primary" style="margin-top: 20px;" @click="goLogin">去登录</button>
    </view>

    <view v-else-if="list.length === 0" class="empty-tip">
      <image src="/static/logo.png" style="width: 50px; height: 50px; opacity: 0.5; margin-bottom: 10px;"></image>
      <view>暂无记录，快去添加吧~</view>
    </view>

    <view v-else class="list-box">
      <!-- 列表渲染 -->
      <view v-for="(item, index) in list" :key="item.id" class="card" @click="goEdit(item)">
        
        <!-- 显示后端返回的图片 -->
        <image 
          class="card-img" 
          :src="item.file_url || '/static/bird.png'"
          mode="aspectFit"
        ></image>
        
        <view class="card-content">
          <view class="card-top">
            <text class="type-tag" :class="item.title.includes('声纹') ? 'voice-tag' : 'image-tag'">{{ item.title.includes('声纹') ? '声纹' : '图像' }}</text>
            <text class="card-title">{{ formatTitle(item.title) }}</text>
          </view>
          <text class="card-desc">{{ item.content }}</text>
          <text class="card-time">{{ formatTime(item.created_at) }}</text>
        </view>

        <!-- 删除按钮 -->
        <view class="delete-btn" @click.stop="deleteItem(item, index)">
          <text>🗑️</text> 
        </view>
      </view>
    </view>

    <!-- 右下角加号 -->
    <view v-if="isLogin" class="add-btn" @click="goAdd">
      <text>+</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { CONFIG } from '@/config.js';

const FASTAPI_BASE_URL = CONFIG.FASTAPI_BASE_URL;

const list = ref([]);
const isLogin = ref(false);
const currentUser = ref(null);
// 🔥 新增：根据标题动态判断显示哪张封面图
const getCoverImage = (title) => {
  if (!title) return '/static/bird.png';
  
  // 如果标题里包含"声纹"，就显示语音的封面
  if (title.includes('声纹')) {
    return '/static/voice.png';
  }
  
  // 否则默认显示小鸟的封面
  return '/static/bird.png';
};

// 格式化标题：[声纹识别] 鸟名 → 鸟名
const formatTitle = (title) => {
  if (!title) return '';
  // 只保留鸟名，去掉识别类型前缀
  const match = title.match(/\[(?:声纹|图像)识别\]\s*(.+)/);
  return match ? match[1] : title;
};

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '刚刚';
  
  // 处理后端返回的时间格式
  const date = new Date(timeStr.replace(' ', 'T'));
  if (isNaN(date.getTime())) return '刚刚';
  
  const now = new Date();
  const diff = now - date;
  
  // 小于1分钟
  if (diff < 60000) return '刚刚';
  // 小于1小时
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  // 小于24小时
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  // 小于7天
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
  
  // 显示具体日期
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${month}月${day}日 ${hours}:${minutes}`;
};

onShow(() => {
  refreshData();
});
const refreshData = () => {
  const user = uni.getStorageSync('current_user');
  if (user && user.username) {
    isLogin.value = true;
    currentUser.value = user;
    uni.showLoading({ title: '加载中...' });
    
    uni.request({
      url: `${FASTAPI_BASE_URL}/records`, 
      method: 'GET',
      data: { username: user.username },
      success: (res) => {
        if (res.statusCode === 200 && res.data.code === 200) {
          list.value = res.data.data ||[];
        } else {
          uni.showToast({ title: '拉取数据失败', icon: 'none' });
        }
      },
      complete: () => {
        uni.hideLoading();
      }
    });
  } else {
    isLogin.value = false;
    list.value =[];
  }
};

// 跳转逻辑
const goLogin = () => uni.navigateTo({ url: '/pages/login/login' });

// 点右下角 + 号，新建记录（不传id）
const goAdd = () => uni.navigateTo({ url: '/pages/edit/edit' }); 

// 🔥 核心修改：点列表数据，跳转编辑页并传值
const goEdit = (item) => {
  // 把当前点击的数据存到本地缓存里，供编辑页读取
  uni.setStorageSync('current_detail_item', {
    _id: item.id,
    title: item.title,
    content: item.content,
    image: item.file_url, // ★把后端的 file_url 赋值给前端的 image 字段
    time: item.created_at
  });
  
  // 带着 ID 跳转到编辑页
  uni.navigateTo({ url: `/pages/edit/edit?id=${item.id}` }); 
};

// 删除逻辑
const deleteItem = (item, index) => {
  uni.showModal({
    title: '提示',
    content: '确定要删除这条记录吗？',
    success: function (res) {
      if (res.confirm) {
        uni.showLoading({ title: '删除中...' });
        uni.request({
          url: `${FASTAPI_BASE_URL}/records/${item.id}`,
          method: 'DELETE',
          success: (res) => {
            if (res.statusCode === 200) {
              list.value.splice(index, 1);
              uni.showToast({ title: '已移除', icon: 'success' });
            }
          },
          complete: () => { uni.hideLoading(); }
        });
      }
    }
  });
};
</script>

<style>
/* CSS 样式保持不变 */
.container { padding: 20px; background-color: #f6f7f9; min-height: 100vh; }
.header-title { font-size: 22px; font-weight: bold; margin-bottom: 20px; color: #333; }
.card { background-color: #fff; padding: 15px; margin-bottom: 15px; border-radius: 12px; display: flex; align-items: flex-start; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.card-img { width: 90px; height: 90px; border-radius: 10px; background-color: #eee; flex-shrink: 0; margin-right: 15px; margin-top: 2px; }
.card-content { flex: 1; display: flex; flex-direction: column; justify-content: flex-start; min-height: 90px; padding: 2px 0; overflow: hidden; }
.card-top { display: flex; align-items: center; margin-bottom: 6px; }
.type-tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; color: #fff; font-weight: 500; flex-shrink: 0; margin-right: 6px; }
.voice-tag { background: linear-gradient(135deg, #667eea, #764ba2); }
.image-tag { background: linear-gradient(135deg, #f093fb, #f5576c); }
.card-title { font-size: 17px; font-weight: 600; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-desc { font-size: 13px; color: #666; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }
.card-time { font-size: 12px; color: #999; margin-top: auto; }
.delete-btn { padding: 10px; opacity: 0.6; font-size: 18px; }
.empty-tip { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; margin-top: 100px; }
.add-btn { position: fixed; bottom: 80px; right: 30px; z-index: 99; width: 55px; height: 55px; background: linear-gradient(135deg, #007AFF, #00C6FF); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 32px; box-shadow: 0 4px 15px rgba(0,122,255,0.4); }
</style>