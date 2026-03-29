<template>
  <view class="container">
    
    <view class="status-bar">
      <text class="status-text">{{ statusText }}</text>
    </view>

    <view class="result-card">
      <view class="wave-box" v-if="isRecording">
        <view class="wave w1"></view>
        <view class="wave w2"></view>
        <view class="wave w3"></view>
      </view>
      
      <view class="loading-box" v-else-if="isUploading">
        <text class="loading-icon">⏳</text>
        <text>正在分析中...</text>
      </view>

      <view v-else-if="parsedResult.name" class="parsed-content">
        <text class="res-title">识别结果：{{ parsedResult.name }}</text>
        <text v-if="parsedResult.confidence === 'very_low'" class="res-score very-low">⚠️ 置信度低</text>
        <template v-else-if="parsedResult.confidence === 'low'">
          <text class="res-score">置信度：{{ (parsedResult.score * 100).toFixed(1) }}%</text>
          <text class="res-score low">⚠️ 置信度较低</text>
        </template>
        <text v-else-if="parsedResult.name !== '未知'" class="res-score">置信度：{{ (parsedResult.score * 100).toFixed(1) }}%</text>
        <text v-if="parsedResult.desc" class="res-desc">{{ parsedResult.desc }}</text>

        <view class="voiceprint-box" v-if="parsedResult.voiceprint">
          <text class="vp-label">—— 声纹可视化 ——</text>
          <image 
            class="vp-image" 
			mode="widthFix" 
            :src="parsedResult.voiceprint"
            @error="onImageError"
          ></image>
        </view>
      </view>
      
      <textarea 
        v-else
        class="result-area" 
        v-model="content" 
        placeholder="识别结果将显示在这里..." 
        maxlength="-1"
      />
    </view>

    <view class="btn-group">
      <text class="tip-text" v-if="isUploading">正在处理上一个请求，请稍候...</text>
      <text class="tip-text" v-else>{{ isRecording ? '松开结束' : '按住录音 (请保持2秒以上)' }}</text>
      
      <view 
        class="mic-btn" 
        :class="{ 'recording': isRecording, 'disabled': isUploading }"
        @touchstart="startRecord" 
        @touchend="stopRecord"
        @mousedown="startRecord" 
        @mouseup="stopRecord"
      >
        <text class="mic-icon">🎙️</text>
      </view>

      <button class="save-btn" @click="saveToStore" :disabled="!content && !parsedResult.name">保存到仓库</button>
    </view>

  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { CONFIG } from '@/config.js';

// 1. 接口地址配置
const BASE_URL = CONFIG.AI_BASE_URL;
const API_URL = CONFIG.AI_AUDIO_URL;

// FastAPI 后端上传接口 (8000端口)
const FASTAPI_UPLOAD_URL = CONFIG.FASTAPI_UPLOAD_URL;

const content = ref('');
const parsedResult = ref({}); 
const statusText = ref('准备就绪');
const isRecording = ref(false);
const isUploading = ref(false); 
const startTime = ref(0);       
const recorderManager = uni.getRecorderManager();

onMounted(() => {
  recorderManager.onStart(() => {
    if (isUploading.value) {
      recorderManager.stop();
      return;
    }
    
    startTime.value = Date.now(); 
    statusText.value = '正在录音...';
    isRecording.value = true;
    parsedResult.value = {}; 
    content.value = '';
  });

  recorderManager.onStop((res) => {
    if (!isRecording.value) return; 
    
    isRecording.value = false;
    
    const duration = Date.now() - startTime.value;
    console.log('录音时长:', duration, 'ms');

    if (duration < 2000) {
      statusText.value = '时间太短';
      uni.showToast({ title: '录音太短，请重试', icon: 'none' });
      return; 
    }

    isUploading.value = true; 
    statusText.value = '正在上传分析...';
    
    uploadAudio(res.tempFilePath);
  });

  recorderManager.onError((err) => {
    console.error(err);
    isRecording.value = false;
    statusText.value = '设备异常';
  });
});

const startRecord = () => {
  if (isUploading.value) return; 
  
  // 优化录音参数，提高识别准确率
  recorderManager.start({ 
    format: 'wav',           // 无损 wav 格式
    sampleRate: 22050,       // 优化：降低采样率减少噪音，鸟类叫声主要在11kHz以下
    numberOfChannels: 1,     // 单声道
    encodeBitRate: 64000,    // 优化：提高比特率保证音质
    frameSize: 1024          // 优化：设置合适的帧大小
  });
};

const stopRecord = () => {
  if (isUploading.value) return;
  recorderManager.stop();
};

const uploadAudio = (filePath) => {
  uni.uploadFile({
    url: API_URL, 
    filePath: filePath,
    name: 'file',
    header: { 'ngrok-skip-browser-warning': 'true' },
    success: (uploadFileRes) => {
      
      try {
        const resJson = JSON.parse(uploadFileRes.data);
        
        if (resJson.code === 200 && resJson.data) {
          parsedResult.value = {
            name: resJson.data.name,   
            desc: resJson.data.desc || '',   
            score: resJson.data.score,
            voiceprint: resJson.data.voiceprint,
            confidence: resJson.data.confidence  // 新增：添加置信度等级
          };

          statusText.value = '识别成功';
          content.value = `[声音] ${resJson.data.name}`;
        } 
        else if (resJson.code === 500 || resJson.code === 400) {
           statusText.value = '识别失败';
           uni.showToast({ title: resJson.msg || '服务器内部错误', icon: 'none' });
        }
        else {
          content.value = JSON.stringify(resJson);
          statusText.value = '识别完成';
        }
      } catch (e) {
        console.error('解析失败', e);
        statusText.value = '服务器繁忙';
        uni.showToast({ title: '服务器开小差了，请稍后再试', icon: 'none' });
      }
    },
    fail: () => {
      statusText.value = '网络错误';
      uni.showToast({ title: '无法连接服务器', icon: 'none' });
    },
    complete: () => {
      isUploading.value = false;
    }
  });
};

const onImageError = (e) => {
  console.error("图片加载失败", e);
}

// 终极辅助函数：完美兼容 App、H5、小程序的图片转换器
const getUploadFilePath = (imageSrc) => {
  return new Promise((resolve, reject) => {
    if (!imageSrc) return resolve('');

    // 1. 如果是网络链接，直接下载
    if (imageSrc.startsWith('http://') || imageSrc.startsWith('https://')) {
      uni.downloadFile({
        url: imageSrc,
        success: (res) => {
          if (res.statusCode === 200) resolve(res.tempFilePath);
          else reject(`下载图片失败, 状态码: ${res.statusCode}`);
        },
        fail: (err) => reject(`网络图片下载异常: ${JSON.stringify(err)}`)
      });
      return;
    } 

    // 2. 确保 Base64 带有前缀 (App端的 Bitmap 需要前缀)
    let fullBase64 = imageSrc;
    if (!fullBase64.startsWith('data:image')) {
      const pureBase64 = fullBase64.split(',')[1] || fullBase64;
      fullBase64 = 'data:image/png;base64,' + pureBase64;
    }

    // ==============================================
    // 🌍 环境 1: APP 环境 (Android / iOS)
    // ==============================================
    // #ifdef APP-PLUS
    try {
      const bitmap = new plus.nativeObj.Bitmap("vp_bitmap");
      bitmap.loadBase64Data(fullBase64, () => {
        // 加载成功后，保存为本地文件
        const relativePath = `_doc/vp_${Date.now()}.png`;
        bitmap.save(relativePath, { overwrite: true }, (saveRes) => {
          bitmap.clear(); // 清理内存
          // 转换成绝对路径供 uploadFile 使用
          const absolutePath = plus.io.convertLocalFileSystemURL(relativePath);
          resolve(absolutePath);
        }, (err) => {
          bitmap.clear();
          reject(`App保存图片失败: ${JSON.stringify(err)}`);
        });
      }, (err) => {
        bitmap.clear();
        reject(`App解析Base64失败: ${JSON.stringify(err)}`);
      });
    } catch (e) {
      reject(`APP环境报错: ${e.message}`);
    }
    // #endif

    // ==============================================
    // 🌍 环境 2: 微信小程序等环境
    // ==============================================
    // #ifdef MP
    try {
      const fs = uni.getFileSystemManager();
      const pureBase64 = fullBase64.split(',')[1];
      const filePath = `${uni.env.USER_DATA_PATH}/vp_${Date.now()}.png`;
      fs.writeFile({
        filePath: filePath,
        data: pureBase64,
        encoding: 'base64',
        success: () => resolve(filePath),
        fail: (err) => reject(`小程序写入文件失败: ${JSON.stringify(err)}`)
      });
    } catch (e) {
      reject(`小程序环境报错: ${e.message}`);
    }
    // #endif

    // ==============================================
    // 🌍 环境 3: H5 浏览器环境
    // ==============================================
    // #ifdef H5
    try {
      const pureBase64 = fullBase64.split(',')[1];
      const bstr = atob(pureBase64);
      let n = bstr.length;
      const u8arr = new Uint8Array(n);
      while (n--) { u8arr[n] = bstr.charCodeAt(n); }
      const blob = new Blob([u8arr], { type: 'image/png' });
      resolve(URL.createObjectURL(blob));
    } catch (e) { 
      reject(`H5环境转换失败: ${e.message}`); 
    }
    // #endif

  });
};

//   保存到 FastAPI 后端
const saveToStore = async () => {
  const user = uni.getStorageSync('current_user');
  if (!user || !user.username) {
    return uni.showToast({ title: '请先登录', icon: 'none' });
  }

  // 获取声纹图片源数据
  const vpSrc = parsedResult.value.voiceprint;
  if (!vpSrc) {
    return uni.showToast({ title: '缺少声纹图片，无法保存', icon: 'none' });
  }

  uni.showLoading({ title: '正在存入云端...' });

  try {
    // 1. 将声纹图片转化为真实的本地文件路径
    const localFilePath = await getUploadFilePath(vpSrc);

    if (!localFilePath) {
      uni.hideLoading();
      return uni.showToast({ title: '处理图片失败', icon: 'none' });
    }

    // 2. 调用 uni.uploadFile 上传给 FastAPI 
    uni.uploadFile({
      url: FASTAPI_UPLOAD_URL,         // 8000端口
      filePath: localFilePath,         // 转化后的本地路径
      name: 'file',                    // 对应后端 UploadFile
      formData: {
        username: user.username,
        title: `[声纹识别] ${parsedResult.value.name || '未知鸟类'}`,
        content: parsedResult.value.desc || content.value
      },
      success: (res) => {
        uni.hideLoading();
        if (res.statusCode === 200) {
          const data = JSON.parse(res.data);
          if (data.code === 200) {
            uni.showToast({ title: '已同步至云仓库', icon: 'success' });
          } else {
            uni.showToast({ title: data.msg || '保存失败', icon: 'none' });
          }
        } else {
          // 如果后端报错，立刻在前端打印出真实的错误原因
          console.error("后端报错:", res.data);
          uni.showModal({
            title: '后端报错了',
            content: `状态码: ${res.statusCode}\n详情: ${res.data}`,
            showCancel: false
          });
        }
      },
      fail: (err) => {
        console.error('上传失败:', err);
        uni.hideLoading();
        uni.showToast({ title: '网络连接失败', icon: 'none' });
      }
    });

} catch (error) {
    console.error("转换声纹图片失败的真实原因:", error);
    uni.hideLoading();
    uni.showModal({
      title: '转换图片失败',
      content: typeof error === 'string' ? error : JSON.stringify(error),
      showCancel: false
    });
  }
};
</script>
<style>
.container { display: flex; flex-direction: column; min-height: 100vh; background-color: #F5F7FA; align-items: center; padding-top: 40px; padding-bottom: 40px; box-sizing: border-box; }
.status-bar { margin-bottom: 20px; }
.status-text { color: #2B9939; font-size: 16px; font-weight: bold; background: rgba(43, 153, 57, 0.1); padding: 6px 16px; border-radius: 20px; }

.result-card { 
  width: 90%; 
  min-height: 35vh; 
  height: auto; 
  background: #fff; 
  border-radius: 24px; 
  box-shadow: 0 10px 30px rgba(0,0,0,0.05); 
  padding: 30px 20px; 
  box-sizing: border-box; 
  margin-bottom: 30px; 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  justify-content: center; 
  position: relative; 
  overflow: hidden; 
  transition: all 0.3s; 
  flex-shrink: 0; 
}

.result-area { width: 100%; height: 200px; font-size: 16px; color: #333; }

.parsed-content { display: flex; flex-direction: column; align-items: center; text-align: center; width: 100%; }
.res-title { font-size: 24px; font-weight: bold; color: #333; margin-bottom: 5px; }
.res-score { font-size: 14px; color: #007AFF; margin-bottom: 15px; font-weight: bold; background: #e0f2ff; padding: 2px 8px; border-radius: 4px; }
.res-score.low { color: #ff9500; background: #fff3e0; }
.res-score.very-low { color: #ff3b30; background: #ffe5e3; }
.res-desc { font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 15px; }

.voiceprint-box { width: 100%; margin-top: 15px; margin-bottom: 5px; display: flex; flex-direction: column; align-items: center; animation: fadeIn 0.5s ease; }
.vp-label { font-size: 12px; color: #aaa; margin-bottom: 10px; letter-spacing: 1px; }

.vp-image { 
  width: 100%; 
  background-color: #000; 
  border-radius: 12px; 
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.wave-box { display: flex; align-items: center; justify-content: center; gap: 8px; }
.wave { width: 6px; height: 20px; background-color: #2B9939; border-radius: 3px; animation: waveAnim 1s infinite ease-in-out; }
.w1 { animation-delay: 0s; } .w2 { animation-delay: 0.2s; } .w3 { animation-delay: 0.4s; }
@keyframes waveAnim { 0%, 100% { height: 20px; opacity: 0.5; } 50% { height: 60px; opacity: 1; } }

.loading-box { display: flex; flex-direction: column; align-items: center; color: #999; font-size: 14px; }
.loading-icon { font-size: 30px; margin-bottom: 10px; animation: spin 1s infinite linear; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.btn-group { display: flex; flex-direction: column; align-items: center; width: 100%; }
.tip-text { color: #999; font-size: 14px; margin-bottom: 20px; }

.mic-btn { 
  width: 70px; 
  height: 70px; 
  border-radius: 50%; 
  background: linear-gradient(135deg, #ffffff, #f0f0f0); 
  box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  margin-bottom: 30px; 
  transition: all 0.2s; 
  border: 4px solid #fff; 
}
.mic-icon { font-size: 30px; }
.mic-btn.recording { transform: scale(1.1); background: #2B9939; box-shadow: 0 0 40px rgba(43, 153, 57, 0.4); }
.mic-btn.recording .mic-icon { filter: brightness(10); }

/* 禁用状态 */
.mic-btn.disabled { opacity: 0.6; pointer-events: none; background: #ddd; }

.save-btn { width: 80%; border-radius: 30px; background: linear-gradient(90deg, #2B9939, #4CAF50); font-weight: bold; color: #fff; box-shadow: 0 6px 15px rgba(43, 153, 57, 0.3); }
</style>