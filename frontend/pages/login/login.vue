<template>
	<view class="container">
		<image class="logo" src="/static/logo.png"></image>
		<view class="title">欢迎回来</view>
		
		<input class="input" v-model="username" placeholder="请输入用户名" />
		<input class="input" v-model="password" type="password" placeholder="请输入密码" />
		
		<button type="primary" class="btn" @click="handleLogin">登录</button>
		<view class="link" @click="goRegister">没有账号？去注册</view>
	</view>
</template>

<script setup>
import { ref } from 'vue';
import { CONFIG } from '@/config.js';

const username = ref('');
const password = ref('');

const handleLogin = async () => {
	// 1. 基础校验
	if(!username.value || !password.value) {
		return uni.showToast({ title: '请输入账号密码', icon: 'none' });
	}

	uni.showLoading({ title: '登录中...' });

	try {
		// 2. 调用 FastAPI 后端接口
		const res = await uni.request({
			url: `${CONFIG.FASTAPI_BASE_URL}/auth/login`,
			method: 'POST',
			header: {
				'Content-Type': 'application/json'
			},
			data: {
				username: username.value,
				password: password.value
			}
		});

		const result = res.data;

		// 3. 处理返回结果
		if(result.code === 200) {
			uni.setStorageSync('current_user', result.data);
			uni.showToast({ title: '登录成功', icon: 'success' });
			
			setTimeout(() => {
				uni.switchTab({ url: '/pages/profile/profile' });
			}, 500);
		} else {
			uni.showToast({ title: result.msg || result.detail, icon: 'none' });
		}
	} catch (e) {
		uni.showToast({ title: '请求失败，请检查网络', icon: 'none' });
	} finally {
		uni.hideLoading();
	}
};

const goRegister = () => {
	uni.navigateTo({ url: '/pages/register/register' });
};
</script>

<style>
.container { padding: 40px; display: flex; flex-direction: column; }
.logo { width: 80px; height: 80px; align-self: center; margin-bottom: 20px; border-radius: 10px;}
.title { font-size: 24px; font-weight: bold; margin-bottom: 40px; text-align: center; }
.input { background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-size: 16px; }
.btn { margin-top: 20px; border-radius: 25px; width: 100%; }
.link { text-align: center; margin-top: 20px; color: #007AFF; font-size: 14px; }
</style>