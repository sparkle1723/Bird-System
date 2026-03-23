<template>
  <view class="map-wrap">
    
    <!-- 地图组件 -->
    <map 
      id="myMap"
      class="map"
      :latitude="latitude" 
      :longitude="longitude" 
      :markers="markers"
      :scale="scale"
      show-location
      enable-traffic
      @markertap="onMarkerTap"
    ></map>

    <!-- 中心红图钉 -->
    <cover-image 
      class="center-marker" 
      src="https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png"
    ></cover-image>

    <!-- 顶部状态提示 (display隐藏法，不破坏DOM) -->
    <cover-view 
      class="top-pill-box" 
      :style="{ display: statusMsg ? 'flex' : 'none' }"
    >
      <cover-view class="pill-content">
        <cover-view class="status-text">{{ statusMsg }}</cover-view>
      </cover-view>
    </cover-view>

    <!-- 右下角悬浮按钮组 -->
    <cover-view class="fab-group">
      
      <!-- 按钮 1：定位 -->
      <cover-view class="fab-btn white-btn">
        <!-- 视觉层：纯粹只负责好看，不绑定任何事件 -->
        <cover-view class="css-target-outer">
          <cover-view class="css-target-inner-white">
            <cover-view class="css-target-dot"></cover-view>
          </cover-view>
        </cover-view>
        <cover-view class="btn-text btn-text-blue">定位</cover-view>
        
        <!-- ★ 交互层：隐形透明的点击遮罩，铺满整个58x58的按钮，拦截所有点击！ ★ -->
        <cover-view class="click-mask" @click="moveToMyLocation"></cover-view>
      </cover-view>

      <!-- 按钮 2：标记 -->
      <cover-view class="fab-btn solid-blue-btn">
        <!-- 视觉层 -->
        <cover-view class="css-plus-icon">
          <cover-view class="css-plus-v"></cover-view>
          <cover-view class="css-plus-h"></cover-view>
        </cover-view>
        <cover-view class="btn-text btn-text-white">标记</cover-view>
        
        <!-- ★ 交互层：隐形透明遮罩，接管一切点击 ★ -->
        <cover-view class="click-mask" @click="markCenterLocation"></cover-view>
      </cover-view>

    </cover-view>

  </view>
</template>

<script setup>
import { ref, getCurrentInstance } from 'vue';
import { onShow, onReady } from '@dcloudio/uni-app';

const latitude = ref(32.0415); 
const longitude = ref(118.7823);
const scale = ref(16);
const markers = ref([]);
const mapContext = ref(null);
const statusMsg = ref(''); 
const currentUser = ref(null);

let msgTimer = null; 

const { proxy } = getCurrentInstance();

onReady(() => {
  setTimeout(() => {
    mapContext.value = uni.createMapContext('myMap', proxy);
    initData();
  }, 200);
});

onShow(() => {
  if (mapContext.value) {
    initData();
  }
});

const showTempMessage = (text, keepTime = 2000) => {
  statusMsg.value = text;
  if (msgTimer) clearTimeout(msgTimer);
  
  msgTimer = setTimeout(() => {
    statusMsg.value = ''; 
  }, keepTime);
};

const initData = () => {
  const user = uni.getStorageSync('current_user');
  if (user) {
    currentUser.value = user;
    loadUserMarkers();
    uni.getLocation({
      type: 'gcj02',
      success: (res) => {
        latitude.value = res.latitude;
        longitude.value = res.longitude;
        mapContext.value?.moveToLocation({ latitude: res.latitude, longitude: res.longitude });
      }
    });
  } else {
    currentUser.value = null;
    markers.value = [];
    showTempMessage('访客模式 - 请先登录', 3000);
  }
};

const loadUserMarkers = () => {
  if (!currentUser.value) return;
  const markerKey = 'markers_' + currentUser.value.username;
  const allList = uni.getStorageSync(markerKey) || [];
  
  markers.value = allList.map(item => ({
    id: item.id,
    latitude: item.latitude,
    longitude: item.longitude,
    width: 25, 
    height: 34,
    iconPath: 'https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-default.png', 
    callout: {
      content: ` ${item.title} `,
      color: '#007AFF', 
      fontSize: 13,
      borderRadius: 8,
      bgColor: '#ffffff',
      padding: 8,
      display: 'ALWAYS',
      textAlign: 'center'
    },
    anchor: { x: 0.5, y: 1 }
  }));
};

const markCenterLocation = () => {
  if (!currentUser.value) return uni.showToast({ title: '请先登录', icon: 'none' });
  if (!mapContext.value) return;

  mapContext.value.getCenterLocation({
    success: (res) => {
      const lat = Number(res.latitude);
      const lng = Number(res.longitude);

      uni.showModal({
        title: '在此处打卡',
        editable: true,
        placeholderText: '请输入标记名称...',
        success: (modalRes) => {
          if (modalRes.confirm) {
            const title = modalRes.content?.trim() || '新标记点';
            saveMarkerToMapOnly(title, lat, lng);
          }
        }
      });
    },
    fail: () => uni.showToast({ title: '获取中心点失败', icon: 'none' })
  });
};

const saveMarkerToMapOnly = (title, lat, lng) => {
  const markerKey = 'markers_' + currentUser.value.username;
  const allList = uni.getStorageSync(markerKey) || [];
  
  allList.push({
    id: Date.now(),
    title: title,
    latitude: lat,
    longitude: lng,
    time: new Date().toLocaleString()
  });

  uni.setStorageSync(markerKey, allList);
  showTempMessage(`已标记: ${title}`);
  loadUserMarkers();
};

const moveToMyLocation = () => {
  showTempMessage('定位中...', 1000);

  uni.getLocation({
    type: 'gcj02', 
    isHighAccuracy: true,
    success: (res) => {
      latitude.value = res.latitude;
      longitude.value = res.longitude;
      
      if (mapContext.value) {
        mapContext.value.moveToLocation({ 
          latitude: res.latitude, 
          longitude: res.longitude 
        });
      }
      showTempMessage('已回到当前位置'); 
    },
    fail: () => {
      showTempMessage('定位失败，请检查定位权限', 3000);
    }
  });
};

const onMarkerTap = (e) => {
  const markerId = e.markerId || e.detail?.markerId; 
  const target = markers.value.find(m => m.id === markerId);
  if (!target) return;

  const title = target.callout?.content?.trim() || '未知点';
  uni.showActionSheet({
    itemList: [`查看详情: ${title}`, '删除此标记'],
    itemColor: "#e53935", 
    success: (res) => {
      if (res.tapIndex === 1) deleteMarker(markerId);
    }
  });
};

const deleteMarker = (id) => {
  uni.showModal({
    title: '删除确认',
    content: '确定要移除这个标记吗？',
    success: (res) => {
      if (res.confirm) {
        const markerKey = 'markers_' + currentUser.value.username;
        const allList = uni.getStorageSync(markerKey) || [];
        const newList = allList.filter(item => item.id !== id);
        uni.setStorageSync(markerKey, newList);
        loadUserMarkers();
        showTempMessage('已删除标记');
      }
    }
  });
};
</script>

<style scoped>
.map-wrap { 
  width: 100%; 
  height: 100vh; 
  position: relative; 
  background-color: #f5f5f5; 
}
.map { 
  width: 100%; 
  height: 100%; 
}

.center-marker {
  position: absolute; 
  top: 50%; 
  left: 50%;
  width: 25px; 
  height: 34px;
  margin-left: -12.5px;
  margin-top: -34px; 
  z-index: 9999;
}

.top-pill-box {
  position: fixed; 
  top: 60px; 
  left: 0; 
  right: 0;
  justify-content: center; 
  z-index: 9999; 
}
.pill-content {
  background-color: rgba(255, 255, 255, 0.95);
  padding: 8px 20px;
  border-radius: 20px;
  text-align: center;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.status-text { 
  font-size: 14px; 
  color: #333; 
  font-weight: bold; 
}

.fab-group {
  position: fixed; 
  bottom: 110px; 
  right: 15px;
  display: flex; 
  flex-direction: column; 
  align-items: flex-end;
  z-index: 9999; 
}

/* ★ 关键修复1：为容器加上 position: relative，让膜能盖住它自己 ★ */
.fab-btn {
  position: relative; 
  width: 58px; 
  height: 58px;
  border-radius: 50%;
  margin-top: 20px;
  text-align: center;
  padding-top: 10px;
  box-sizing: border-box;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.white-btn { background-color: #ffffff; }
.solid-blue-btn { background-color: #007AFF; }

/* ★ 关键修复2：隐形点击膜，100%长宽覆盖按钮的所有角落 ★ */
.click-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: transparent; /* 完全透明 */
  z-index: 99; /* 保证这层膜永远浮在图标和文字的最上面！ */
}

/* 以下是纯展示视觉的文字和图标层，它们在膜的下方，不会再干扰点击 */
.btn-text {
  font-size: 11px;
  font-weight: bold;
  margin-top: 5px;
  text-align: center;
}
.btn-text-blue { color: #007AFF; }
.btn-text-white { color: #ffffff; }

.css-target-outer {
  width: 20px; height: 20px;
  background-color: #007AFF;
  border-radius: 50%;
  margin: 0 auto;
  display: flex; 
  justify-content: center; 
  align-items: center;
}
.css-target-inner-white {
  width: 15px; height: 15px;
  background-color: #ffffff;
  border-radius: 50%;
  display: flex; 
  justify-content: center; 
  align-items: center;
}
.css-target-dot {
  width: 7px; height: 7px;
  background-color: #007AFF;
  border-radius: 50%;
}

.css-plus-icon {
  position: relative;
  width: 20px; height: 20px;
  margin: 0 auto;
}
.css-plus-v {
  position: absolute;
  width: 2.5px; height: 20px;
  background-color: #ffffff;
  left: 8.75px; top: 0;
}
.css-plus-h {
  position: absolute;
  width: 20px; height: 2.5px;
  background-color: #ffffff;
  left: 0; top: 8.75px;
}
</style>