<template>
  <view class="container">
    <view class="form-item">
      <text class="label">图片</text>
      <view class="upload-box" @click="handleChooseImage">
        <!-- 如果 formData 里有 image 的值，就直接展示图片 -->
        <view v-if="formData.image" class="preview-box">
          <image :src="formData.image" mode="aspectFit" class="preview-img"></image>
          <view class="delete-icon" @click.stop="removeImage">×</view>
        </view>
        <view v-else class="add-icon">
          <text class="plus">+</text>
          <text class="tip">点击上传</text>
        </view>
      </view>
    </view>

    <view class="form-item">
      <text class="label">标题</text>
      <input class="input" v-model="formData.title" placeholder="请输入标题" />
    </view>
    
    <view class="form-item">
      <text class="label">详情备注</text>
      <textarea class="textarea" v-model="formData.content" placeholder="请输入详细内容" />
    </view>

    <button type="primary" class="save-btn" @click="saveData">保存记录</button>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { CONFIG } from '@/config.js';

const formData = ref({ _id: null, title: '', content: '', time: '', image: '' });

onLoad((options) => {
  //  核心逻辑：判断是不是点数据卡片跳过来的
  if (options.id) {
    // 从仓库跳转进来，读取缓存数据并回显
    const data = uni.getStorageSync('current_detail_item');
    if (data) {
      formData.value = data; // 直接把图片、标题、详情填入表单
    }
  } else {
    // 点右下角 + 号跳转进来，需要清空表单
    formData.value = { _id: null, title: '', content: '', time: '', image: '' };
    uni.removeStorageSync('current_detail_item');
  }
});

// 选择图片并保存临时路径
const handleChooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    success: (res) => {
      // 直接保存临时文件路径，用于后续上传
      formData.value.image = res.tempFilePaths[0];
      console.log('选择图片路径:', formData.value.image);
    }
  });
};
const removeImage = () => { formData.value.image = ''; };

const saveData = async () => {
  if (!formData.value.title) return uni.showToast({ title: '标题不能为空', icon: 'none' });

  const user = uni.getStorageSync('current_user');
  if (!user || !user.username) {
    return uni.showToast({ title: '请先登录', icon: 'none' });
  }

  uni.showLoading({ title: '保存中...' });
  console.log('开始保存，图片数据:', formData.value.image ? '有图片' : '无图片');

  try {
    // 判断是否有图片需要上传
    // 图片可能是：
    // 1. Base64 格式（data:image 开头）- 需要转换
    // 2. 本地临时文件路径（file://、wxfile://、/storage/ 等）- 直接使用
    // 3. 网络URL（http://、https://）- 表示图片未更改，不需要上传
    let filePath = null;
    let isNewImage = false;
    
    if (formData.value.image) {
      // 网络URL - 图片未更改，不需要上传
      if (formData.value.image.startsWith('http://') || formData.value.image.startsWith('https://')) {
        console.log('图片为网络URL，无需重新上传:', formData.value.image);
        // 编辑模式下，保留原图片URL
        isNewImage = false;
      }
      // Base64 格式需要特殊处理
      else if (formData.value.image.startsWith('data:image')) {
        isNewImage = true;
        // #ifdef APP-PLUS
        try {
          const bitmap = new plus.nativeObj.Bitmap('upload_bitmap');
          const pureBase64 = formData.value.image.split(',')[1] || formData.value.image;
          const fullBase64 = 'data:image/png;base64,' + pureBase64;
          const relativePath = `_doc/temp_${Date.now()}.jpg`;
          filePath = await new Promise((resolve, reject) => {
            bitmap.loadBase64Data(fullBase64, () => {
              bitmap.save(relativePath, { overwrite: true }, (saveRes) => {
                bitmap.clear();
                resolve(plus.io.convertLocalFileSystemURL(relativePath));
              }, (err) => { bitmap.clear(); reject(err); });
            }, (err) => { bitmap.clear(); reject(err); });
          });
          console.log('APP端Base64已转为本地文件:', filePath);
        } catch (e) { console.error('APP端Base64转换失败:', e); }
        // #endif
        // #ifndef APP-PLUS
        try {
          const fs = uni.getFileSystemManager();
          const base64Data = formData.value.image.replace(/^data:image\/\w+;base64,/, '');
          filePath = `${uni.env.USER_DATA_PATH}/temp_image_${Date.now()}.jpg`;
          fs.writeFileSync(filePath, base64Data, 'base64');
          console.log('小程序Base64已保存到临时文件:', filePath);
        } catch (e) { console.error('保存临时文件失败:', e); }
        // #endif
      } else {
        // 本地临时文件路径直接使用（file://、wxfile://、/storage/ 等）
        isNewImage = true;
        filePath = formData.value.image;
        console.log('使用本地文件路径:', filePath);
      }
    }

    // 使用 uploadFile 上传到 FastAPI 后端（仅当有新的本地图片时）
    if (filePath && isNewImage) {
      console.log('使用 uploadFile 上传:', CONFIG.FASTAPI_UPLOAD_URL);
      const uploadFormData = {
        username: user.username,
        title: formData.value.title,
        content: formData.value.content
      };
      // 如果是编辑模式，传递 record_id
      if (formData.value._id) {
        uploadFormData.record_id = formData.value._id;
      }
      uni.uploadFile({
        url: CONFIG.FASTAPI_UPLOAD_URL,
        filePath: filePath,
        name: 'file',
        formData: uploadFormData,
        success: (res) => {
          const data = JSON.parse(res.data);
          if (data.code === 200) {
            uni.showToast({ title: data.msg || '保存成功' });
            setTimeout(() => { uni.switchTab({ url: '/pages/store/store' }); }, 1000);
          } else {
            uni.showToast({ title: data.msg || '保存失败', icon: 'none' });
          }
        },
        fail: () => {
          uni.showToast({ title: '网络请求失败', icon: 'none' });
        },
        complete: () => {
          uni.hideLoading();
        }
      });
    } else {
      // 没有图片 或 图片未更改（网络URL），判断是新建还是更新
      const isEdit = formData.value._id !== null && formData.value._id !== undefined;
      const url = isEdit 
        ? `${CONFIG.FASTAPI_BASE_URL}/records/${formData.value._id}`
        : `${CONFIG.FASTAPI_BASE_URL}/records`;
      const method = isEdit ? 'PUT' : 'POST';
      
      uni.request({
        url: url,
        method: method,
        header: {
          'Content-Type': 'application/json'
        },
        data: {
          username: user.username,
          title: formData.value.title,
          content: formData.value.content
        },
        success: (res) => {
          console.log('保存响应:', res);
          if (res.data && res.data.code === 200) {
            uni.showToast({ title: isEdit ? '更新成功' : '保存成功' });
            setTimeout(() => { uni.switchTab({ url: '/pages/store/store' }); }, 1000);
          } else {
            const msg = res.data && res.data.msg ? res.data.msg : '保存失败';
            uni.showToast({ title: msg, icon: 'none' });
          }
        },
        fail: (err) => {
          console.error('保存失败:', err);
          uni.showToast({ title: '网络请求失败', icon: 'none' });
        },
        complete: () => {
          uni.hideLoading();
        }
      });
    }
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'none' });
    uni.hideLoading();
  }
};
</script>

<style>
/* CSS保持不变 */
.container { padding: 20px; background-color: #fff; min-height: 100vh; }
.form-item { margin-bottom: 25px; }
.label { display: block; margin-bottom: 10px; font-weight: bold; font-size: 16px; color: #333; }
.input { background: #f8f8f8; padding: 12px; border-radius: 8px; font-size: 16px; }
.textarea { background: #f8f8f8; padding: 12px; border-radius: 8px; width: 100%; height: 100px; box-sizing: border-box;}
.upload-box { width: 100%; height: 220px; background-color: #f0f2f5; border-radius: 12px; overflow: hidden; position: relative; border: 1px dashed #ccc; box-sizing: border-box; }
.add-icon { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; }
.plus { font-size: 40px; line-height: 40px; font-weight: 300; }
.tip { font-size: 12px; margin-top: 5px; }
.preview-box { width: 100%; height: 100%; position: relative; background-color: #000; }
.preview-img { width: 100%; height: 100%; }
.delete-icon { position: absolute; top: 0; right: 0; width: 30px; height: 30px; background: rgba(0,0,0,0.5); color: #fff; text-align: center; line-height: 30px; font-size: 18px; border-bottom-left-radius: 8px; z-index: 9; }
.save-btn { margin-top: 40px; background-color: #007AFF; border-radius: 25px; }
</style>