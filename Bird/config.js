// 服务器配置文件
// 修改此文件即可统一修改所有页面的服务器地址

const BASE_URL = 'http://8.136.201.70';

export const CONFIG = {
	
	// FastAPI 后端服务 (端口 8000)
	FASTAPI_BASE_URL: `${BASE_URL}:8000`,
	FASTAPI_UPLOAD_URL: `${BASE_URL}:8000/upload`,
	
	// AI 识别服务 (端口 5000)
	AI_BASE_URL: `${BASE_URL}:5000`,
	AI_IMAGE_URL: `${BASE_URL}:5000/predict_image`,
	AI_AUDIO_URL: `${BASE_URL}:5000/predict_audio`,
	AI_CHAT_URL: `${BASE_URL}:5000/chat_about_bird`

};