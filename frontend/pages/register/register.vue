<template>
	<view class="container">
		<view class="title">注册新账号</view>
		
		<input class="input" v-model="form.username" placeholder="请输入用户名" />
		<input class="input" v-model="form.password" type="password" placeholder="请输入密码" />
		<input class="input" v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" />
		
		<button type="primary" class="btn" @click="handleRegister">立即注册</button>
		<view class="link" @click="goLogin">已有账号？去登录</view>
	</view>
</template>

<script setup>
import { ref } from 'vue';
import { CONFIG } from '@/config.js';

const form = ref({
	username: '',
	password: '',
	confirmPassword: ''
});

const handleRegister = async () => {
	// 1. 校验输入
	if(!form.value.username || !form.value.password) {
		return uni.showToast({ title: '账号密码不能为空', icon: 'none' });
	}
	if(form.value.password !== form.value.confirmPassword) {
		return uni.showToast({ title: '两次密码不一致', icon: 'none' });
	}

	uni.showLoading({ title: '注册中...' });

	try {
		// 2. 调用 FastAPI 后端接口
		const res = await uni.request({
			url: `${CONFIG.FASTAPI_BASE_URL}/auth/register`,
			method: 'POST',
			header: {
				'Content-Type': 'application/json'
			},
			data: {
				username: form.value.username,
				password: form.value.password
			}
		});

		const result = res.data;

		// 3. 处理结果
		if(result.code === 200) {
			uni.showToast({ title: '注册成功' });
			setTimeout(() => {
				uni.navigateBack(); 
			}, 1000);
		} else {
			uni.showToast({ title: result.msg || result.detail, icon: 'none' });
		}
	} catch (e) {
		uni.showToast({ title: '连接服务器失败', icon: 'none' });
	} finally {
		uni.hideLoading();
	}
};

const goLogin = () => {
	uni.navigateBack();
};
</script>

<style>
.container { padding: 30px; }
.title { font-size: 24px; font-weight: bold; margin-bottom: 30px; text-align: center; }
.input { border-bottom: 1px solid #ddd; padding: 15px 0; margin-bottom: 15px; font-size: 16px; }
.btn { margin-top: 30px; border-radius: 25px; }
.link { text-align: center; margin-top: 20px; color: #007AFF; font-size: 14px; }
</style>