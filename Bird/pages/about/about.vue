<template>
  <view class="container">
    <!-- 头部 Logo -->
    <view class="header">
      <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      <text class="app-name">鸟了么</text>
      <text class="version">版本 1.1.0</text>
    </view>

    <!-- 应用介绍 -->
    <view class="section">
      <view class="section-title">关于应用</view>
      <view class="content">
        <text class="desc">
          鸟了么 是一款专为鸟类爱好者打造的智能识别与记录应用。通过 AI 技术，帮助用户识别鸟类、记录观测数据、学习鸟类知识。
        </text>
      </view>
    </view>

    <!-- 核心功能 -->
    <view class="section">
      <view class="section-title">核心功能</view>
      <view class="feature-list">
        <view class="feature-item">
          <text class="icon">📷</text>
          <view class="feature-text">
            <text class="feature-name">拍照识别</text>
            <text class="feature-desc">上传鸟类照片，AI 智能识别</text>
          </view>
        </view>
        <view class="feature-item">
          <text class="icon">🎙️</text>
          <view class="feature-text">
            <text class="feature-name">声纹识别</text>
            <text class="feature-desc">录制鸟鸣声音，辨别鸟类</text>
          </view>
        </view>
        <view class="feature-item">
          <text class="icon">🐦</text>
          <view class="feature-text">
            <text class="feature-name">雀灵助手</text>
            <text class="feature-desc">AI 鸟类专家，随时解答疑问</text>
          </view>
        </view>
        <view class="feature-item">
          <text class="icon">📦</text>
          <view class="feature-text">
            <text class="feature-name">观测记录</text>
            <text class="feature-desc">记录每次观测，建立个人数据库</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 技术栈 -->
    <view class="section">
      <view class="section-title">技术栈</view>
      <view class="tech-list">
        <text class="tech-item">• 前端：uni-app + Vue3</text>
        <text class="tech-item">• 后端：FastAPI + Flask</text>
        <text class="tech-item">• 数据库：SQLite</text>
      </view>
    </view>

    <!-- AI 技术详情 -->
    <view class="section">
  <view class="section-title">AI 技术架构</view>
  <view class="tech-detail">
    <view class="tech-block">
      <text class="tech-name">🐦 雀灵助手</text>
      <text class="tech-desc">基于 DeepSeek V3 大语言模型，结合专业鸟类知识库进行微调训练，提供精准的自然语言问答服务。</text>
    </view>
    <view class="tech-block">
      <text class="tech-name">📷 图像识别</text>
      <text class="tech-desc">基于 ResNet50 卷积神经网络，融合 CUB-200 等大规模鸟类数据集训练，支持多达 499 种常见鸟类识别。</text>
    </view>
    <view class="tech-block">
      <text class="tech-name">🎙️ 声纹识别</text>
      <text class="tech-desc">基于 CAM++ 声纹识别模型，通过提取 80 维梅尔频谱（Mel）特征，支持 162 种鸟类叫声的智能辨识。</text>
    </view>
  </view>
</view>

    <!-- 联系我们 -->
    <view class="section contact-section">
      <text class="contact-name">潘羿丞 李亦晨 何泽宇 潘启政</text>
      <text class="contact-company">金陵科技学院</text>
    </view>

    <!-- 版权信息 -->
    <view class="footer">
      <text class="copyright">© 2026 Bird Watcher. All rights reserved.</text>
    </view>
  </view>
</template>

<script setup>
// 关于我们页面
</script>

<style>
.container {
  min-height: 100vh;
  background-color: #f6f7f9;
  padding-bottom: 30px;
}

/* 头部 */
.header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: #fff;
  margin-bottom: 15px;
}

.app-name {
  color: #fff;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.version {
  color: rgba(255,255,255,0.8);
  font-size: 14px;
}

/* 区块 */
.section {
  background: #fff;
  margin: 15px;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 15px;
  padding-left: 10px;
  border-left: 4px solid #667eea;
}

/* 应用介绍 */
.desc {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
}

/* 功能列表 */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.feature-item {
  display: flex;
  align-items: center;
}

.icon {
  font-size: 28px;
  margin-right: 15px;
  width: 40px;
  text-align: center;
}

.feature-text {
  display: flex;
  flex-direction: column;
}

.feature-name {
  font-size: 15px;
  font-weight: bold;
  color: #333;
  margin-bottom: 3px;
}

.feature-desc {
  font-size: 12px;
  color: #999;
}

/* 技术栈 */
.tech-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tech-item {
  font-size: 14px;
  color: #666;
}

/* AI 技术详情 */
.tech-detail {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.tech-block {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 10px;
}

.tech-name {
  font-size: 15px;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 8px;
}

.tech-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

/* 联系我们 */
.contact-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contact-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px;
}

.contact-name {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.contact-company {
  font-size: 14px;
  color: #999;
}

/* 底部 */
.footer {
  margin-top: 30px;
  text-align: center;
  padding: 20px;
}

.copyright {
  font-size: 12px;
  color: #999;
}
</style>
