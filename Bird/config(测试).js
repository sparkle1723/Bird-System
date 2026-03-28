// 服务器配置文件
// 修改此文件即可统一修改所有页面的服务器地址

// const BASE_URL = 'http://8.136.201.70';
const BASE_URL = 'https://unshadily-subphrenic-malcom.ngrok-free.dev';

export const CONFIG = {
	// FastAPI 后端服务 - 暂时禁用（ngrok 只能映射一个端口）
	FASTAPI_BASE_URL: '',
	FASTAPI_UPLOAD_URL: '',
	
	// AI 识别服务（ngrok 已映射到 5000 端口，不需要再加端口号）
	AI_BASE_URL: BASE_URL,
	AI_IMAGE_URL: `${BASE_URL}/predict_image`,
	AI_AUDIO_URL: `${BASE_URL}/predict_audio`,
	AI_CHAT_URL: `${BASE_URL}/chat_about_bird`
};
