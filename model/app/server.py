from flask import Flask, request, jsonify
import os
import sys
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import requests
import io
import base64

#核心绘图库
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np

# ================= 1. 全局配置与字典 =================

app = Flask(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

#DeepSeek API Key
DEEPSEEK_API_KEY = "sk-e042912a9042446c9bb05a503db69f66" 
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

#鸟类拉丁名 -> 中文名
BIRD_TRANSLATOR = {
    # === 常见鸟类 ===
    "Passer": "麻雀",
    "Hirundo": "燕子",
    "Pica": "喜鹊",
    "Streptopelia": "斑鸠",
    "Garrulax": "噪鹛",
    "Pycnonotus": "鹎 (白头翁)",
    "Acridotheres": "八哥",
    "Cuculus": "布谷鸟",
    "Francolinus": "鹧鸪",
    "Phasianus": "雉鸡 (野鸡)",
    "Garrulus": "松鸦",
    "Cyanopica": "灰喜鹊",
    "Lanius": "伯劳",
    "Parus": "山雀",
    "Sitta": "鳾",
    
    # === 鸭鹅雁类 ===
    "Anas": "鸭子 (绿头鸭)",
    "Anser": "雁 (大雁)",
    "Aythya": "潜鸭",
    "Aix": "鸳鸯",
    "Cygnus": "天鹅",
    "Tadorna": "麻鸭",
    "Mergus": "秋沙鸭",
    "Dendrocygna": "树鸭",
    
    # === 鸡形目 (野鸡/鹌鹑) ===
    "Gallus": "原鸡",
    "Coturnix": "鹌鹑",
    "Bambusicola": "竹鸡",
    "Chrysolophus": "锦鸡 (红腹锦鸡)",
    "Lophura": "鹇 (白鹇)",
    "Pavo": "孔雀",
    "Tragopan": "角雉",
    "Lophophorus": "虹雉",
    "Crossoptilon": "马鸡",
    "Syrmaticus": "长尾雉",
    "Ithaginis": "血雉",
    "Pucrasia": "勺鸡",
    "Alectoris": "石鸡",
    "Perdix": "斑翅山鹑",
    "Tetraogallus": "雪鸡",
    
    # === 杜鹃 (布谷鸟类) ===
    "Hierococcyx": "鹰鹃",
    "Cacomantis": "八声杜鹃",
    "Eudynamys": "噪鹃",
    "Chrysococcyx": "金鹃",
    "Centropus": "鸦鹃",
    
    # === 柳莺/苇莺 ===
    "Phylloscopus": "柳莺",
    "Acrocephalus": "苇莺",
    "Cettia": "树莺",
    "Horornis": "短翅莺",
    "Locustella": "蝗莺",
    "Bradypterus": "短翅莺",
    "Prinia": "山鹪莺",
    "Orthotomus": "缝叶莺",
    
    # === 画眉/噪鹛 ===
    "Trochalopteron": "噪鹛",
    "Ianthocincla": "噪鹛",
    "Pterorhinus": "噪鹛",
    "Leioptila": "相思鸟",
    "Liocichla": "薮鹛",
    "Heterophasia": "奇鹛",
    "Minla": "希鹛",
    "Yuhina": "凤鹛",
    
    # === 鸫类 ===
    "Turdus": "鸫 (乌鸫)",
    "Zoothera": "地鸫",
    "Myophonus": "啸鸫",
    "Larvivora": "鸲 (红尾歌鸲)",
    "Luscinia": "歌鸲 (夜莺)",
    "Tarsiger": "林鸲",
    "Copsychus": "鹊鸲",
    "Phoenicurus": "红尾鸲",
    "Enicurus": "燕尾",
    
    # === 其他常见 ===
    "Zosterops": "绣眼鸟",
    "Aegithalos": "长尾山雀",
    "Alauda": "云雀",
    "Motacilla": "鹡鸰",
    "Anthus": "鹨",
    "Chloropsis": "叶鹎",
    "Sturnus": "椋鸟",
    "Spodiopsar": "灰椋鸟",
    "Gracupica": "椋鸟",
    
    # === 猛禽/夜鸟 ===
    "Caprimulgus": "夜鹰",
    "Otus": "角印",
    "Ninox": "鹰鸮",
    "Strix": "林鸮",
    
    # === 鸽鸠类 ===
    "Columba": "鸽子",
    "Spilopelia": "珠颈斑鸠",
    "Treron": "绿鸠",
    "Chalcophaps": "绿翅金鸠",
    
    # === 其他属 ===
    "Abroscopus": "鹟莺",
    "Actinodura": "斑翅鹛",
    "Aerodramus": "金丝燕",
    "Agropsar": "椋鸟",
    "Alcippe": "雀鹛",
    "Anthipes": "鹟",
    "Apus": "雨燕",
    "Arborophila": "山鹧鸪",
    "Arundinax": "大苇莺",
    "Batrachostomus": "蛙口夜鹰",
    "Brachypteryx": "短翅鸫",
    "Calamornis": "苇莺",
    "Cecropis": "金腰燕",
    "Cercotrichas": "棕尾鸲",
    "Certhia": "旋木雀",
    "Charadrius": "鸻",
    "Cholornis": "鹦嘴雀",
    "Cisticola": "扇尾莺",
    "Clamator": "凤头鹃",
    "Conostoma": "鹦嘴雀",
    "Coturnicops": "田鸡",
    "Curruca": "白喉林莺",
    "Cutia": "斑胁希鹛",
    "Cyanoderma": "雅鹛",
    "Cyanoptila": "白腹蓝鹟",
    "Cyornis": "蓝鹟",
    "Cypsiurus": "棕雨燕",
    "Delichon": "毛脚燕",
    "Ducula": "皇鸠",
    "Elachura": "丽星鹩鹛",
    "Erythrogenys": "钩嘴鹛",
    "Eumyias": "铜蓝鹟",
    "Fulica": "骨顶鸡",
    "Fulvetta": "雀鹛",
    "Gallicrex": "董鸡",
    "Gallinula": "黑水鸡",
    "Geokichla": "地鸫",
    "Graminicola": "大草莺",
    "Grammatoptila": "纹背噪鹛",
    "Grandala": "蓝大翅鸲",
    "Gypsophila": "鹪鹛",
    "Helopsaltes": "苍眉蝗莺",
    "Iduna": "篱莺",
    "Leioptila": "火尾希鹛",
    "Leptopoecile": "凤头雀莺",
    "Lerwa": "雪鹧鸪",
    "Lewinia": "灰胸秧鸡",
    "Lioparus": "金胸雀鹛",
    "Macropygia": "鹃鸠",
    "Mareca": "赤颈鸭",
    "Megalurus": "大尾莺",
    "Mixornis": "纹胸鹛",
    "Moupinia": "宝兴鹛雀",
    "Muscicapa": "鹟",
    "Myzornis": "火尾绿鹛",
    "Napothera": "短尾鹛",
    "Neosuthora": "短尾鹦嘴雀",
    "Nettapus": "棉凫",
    "Niltava": "仙鹟",
    "Paradoxornis": "鹦嘴雀",
    "Parayuhina": "凤鹛",
    "Pellorneum": "幽鹛",
    "Phaenicophaeus": "地鹃",
    "Phyllergates": "金头缝叶莺",
    "Pnoepyga": "鳞鹩",
    "Polyplectron": "孔雀雉",
    "Pomatorhinus": "钩嘴鹛",
    "Porphyrio": "紫水鸡",
    "Psittiparus": "鹦嘴雀",
    "Ptyonoprogne": "岩燕",
    "Rallina": "斑秧鸡",
    "Rallus": "秧鸡",
    "Regulus": "戴菊",
    "Rhopophilus": "山鹛",
    "Riparia": "沙燕",
    "Schoeniparus": "雀鹛",
    "Sinosuthora": "鹦嘴雀",
    "Spatula": "琵嘴鸭",
    "Spelaeornis": "鹪鹛",
    "Stachyris": "穗鹛",
    "Staphida": "凤鹛",
    "Sturnia": "椋鸟",
    "Surniculus": "乌鹃",
    "Suthora": "鹦嘴雀",
    "Syrrhaptes": "毛腿沙鸡",
    "Tesia": "短翅莺",
    "Tetraophasis": "雉鹑",
    "Tetrastes": "榛鸡",
    "Tichodroma": "红翅旋壁雀",
    "Tickellia": "宽嘴鹟莺",
    "Timalia": "红顶鹛",
    "Troglodytes": "鹪鹩",
    "Tropicoperdix": "山鹧鸪",
    "Urosphena": "小短翅莺",
    "Zapornia": "小秧鸡",
}

# 视觉模型英文鸟类名称 -> 中文名
VISION_BIRD_TRANSLATOR = {
    # 信天翁
    "Black_footed_Albatross": "黑脚信天翁",
    "Laysan_Albatross": "莱桑信天翁",
    "Sooty_Albatross": "乌信天翁",
    # 杜鹃/犀鹃
    "Groove_billed_Ani": "沟嘴犀鹃",
    # 海雀
    "Crested_Auklet": "冠小海雀",
    "Least_Auklet": "小海雀",
    "Parakeet_Auklet": "鹦鹉海雀",
    "Rhinoceros_Auklet": "犀海雀",
    # 黑鸟
    "Brewer_Blackbird": "蓝头黑鹂",
    "Red_winged_Blackbird": "红翅黑鹂",
    "Rusty_Blackbird": "锈色黑鹂",
    "Yellow_headed_Blackbird": "黄头黑鹂",
    # 其他
    "Bobolink": "刺歌雀",
    "Indigo_Bunting": "靛蓝彩鹀",
    "Lazuli_Bunting": "琉璃彩鹀",
    "Painted_Bunting": "丽彩鹀",
    "Cardinal": "主红雀",
    "Spotted_Catbird": "斑猫鸟",
    "Gray_Catbird": "灰猫鸟",
    "Yellow_breasted_Chat": "黄胸大鵖",
    "Eastern_Towhee": "棕胁唧鹀",
    "Chuck_will_Widow": "卡氏夜鹰",
    # 鸬鹚
    "Brandt_Cormorant": "加州鸬鹚",
    "Red_faced_Cormorant": "红脸鸬鹚",
    "Pelagic_Cormorant": "海鸬鹚",
    # 牛鹂
    "Bronzed_Cowbird": "铜色牛鹂",
    "Shiny_Cowbird": "辉牛鹂",
    # 旋木雀
    "Brown_Creeper": "美洲旋木雀",
    # 乌鸦
    "American_Crow": "美洲乌鸦",
    "Fish_Crow": "鱼鸦",
    # 杜鹃
    "Black_billed_Cuckoo": "黑嘴美洲鹃",
    "Mangrove_Cuckoo": "红树美洲鹃",
    "Yellow_billed_Cuckoo": "黄嘴美洲鹃",
    # 雀
    "Gray_crowned_Rosy_Finch": "灰头岭雀",
    "Purple_Finch": "紫朱雀",
    "Northern_Flicker": "北扑翅鴷",
    # 鹟
    "Acadian_Flycatcher": "绿纹霸鹟",
    "Great_Crested_Flycatcher": "大冠蝇霸鹟",
    "Least_Flycatcher": "小纹霸鹟",
    "Olive_sided_Flycatcher": "绿胁绿霸鹟",
    "Scissor_tailed_Flycatcher": "剪尾王霸鹟",
    "Vermilion_Flycatcher": "朱红霸鹟",
    "Yellow_bellied_Flycatcher": "黄腹纹霸鹟",
    # 军舰鸟
    "Frigatebird": "军舰鸟",
    "Northern_Fulmar": "暴风鹱",
    "Gadwall": "赤膀鸭",
    # 金翅雀
    "American_Goldfinch": "美洲金翅雀",
    "European_Goldfinch": "红额金翅雀",
    # 鹩哥
    "Boat_tailed_Grackle": "宽尾拟八哥",
    # 䴙䴘
    "Eared_Grebe": "角䴙䴘",
    "Horned_Grebe": "黑颈䴙䴘",
    "Pied_billed_Grebe": "斑嘴巨䴙䴘",
    "Western_Grebe": "北美䴙䴘",
    # 蜡嘴雀
    "Blue_Grosbeak": "蓝蜡嘴雀",
    "Evening_Grosbeak": "黄昏蜡嘴雀",
    "Pine_Grosbeak": "松雀",
    "Rose_breasted_Grosbeak": "玫胸白翅斑雀",
    # 海鸽/鸥
    "Pigeon_Guillemot": "海鸽",
    "California_Gull": "加州鸥",
    "Glaucous_winged_Gull": "灰翅鸥",
    "Heermann_Gull": "红嘴灰鸥",
    "Herring_Gull": "银鸥",
    "Ivory_Gull": "象牙鸥",
    "Ring_billed_Gull": "环嘴鸥",
    "Slaty_backed_Gull": "灰背鸥",
    "Western_Gull": "西美鸥",
    # 蜂鸟
    "Anna_Hummingbird": "安氏蜂鸟",
    "Ruby_throated_Hummingbird": "红喉北蜂鸟",
    "Rufous_Hummingbird": "棕煌蜂鸟",
    "Green_Violetear": "辉紫耳蜂鸟",
    # 贼鸥
    "Long_tailed_Jaeger": "长尾贼鸥",
    "Pomarine_Jaeger": "中贼鸥",
    # 松鸦
    "Blue_Jay": "冠蓝鸦",
    "Florida_Jay": "佛罗里达丛鸦",
    "Green_Jay": "绿鸦",
    # 灯草鹀
    "Dark_eyed_Junco": "暗眼灯草鹀",
    # 王霸鹟
    "Tropical_Kingbird": "热带王霸鹟",
    "Gray_Kingbird": "灰王霸鹟",
    # 翠鸟
    "Belted_Kingfisher": "白腹鱼狗",
    "Green_Kingfisher": "绿鱼狗",
    "Pied_Kingfisher": "斑鱼狗",
    "Ringed_Kingfisher": "棕腹鱼狗",
    "White_breasted_Kingfisher": "白胸翡翠",
    # 鸥
    "Red_legged_Kittiwake": "红腿三趾鸥",
    # 百灵
    "Horned_Lark": "角百灵",
    "Pacific_Loon": "太平洋潜鸟",
    "Mallard": "绿头鸭",
    "Western_Meadowlark": "西草地鹨",
    # 秋沙鸭
    "Hooded_Merganser": "棕胁秋沙鸭",
    "Red_breasted_Merganser": "红胸秋沙鸭",
    "Mockingbird": "嘲鸫",
    "Nighthawk": "夜鹰",
    "Clark_Nutcracker": "北美星鸦",
    "White_breasted_Nuthatch": "白胸鳾",
    # 拟黄鹂
    "Baltimore_Oriole": "橙腹拟黄鹂",
    "Hooded_Oriole": "巾冠拟黄鹂",
    "Orchard_Oriole": "圃拟黄鹂",
    "Scott_Oriole": "斯氏拟黄鹂",
    "Ovenbird": "橙顶灶莺",
    # 鹈鹕
    "Brown_Pelican": "褐鹈鹕",
    "White_Pelican": "美洲白鹈鹕",
    "Western_Wood_Pewee": "西绿霸鹟",
    "Sayornis": "菲比霸鹟",
    "American_Pipit": "黄腹鹨",
    "Whip_poor_Will": "三声夜鹰",
    # 渡鸦
    "Common_Raven": "渡鸦",
    "White_necked_Raven": "白颈渡鸦",
    "American_Redstart": "橙尾鸲莺",
    "Geococcyx": "走鹃",
    # 伯劳
    "Loggerhead_Shrike": "呆头伯劳",
    "Great_Grey_Shrike": "灰伯劳",
    # 麻雀
    "Baird_Sparrow": "贝氏草鹀",
    "Black_throated_Sparrow": "黑喉漠鹀",
    "Brewer_Sparrow": "布氏草鹀",
    "Chipping_Sparrow": "棕顶雀鹀",
    "Clay_colored_Sparrow": "泥色麻雀",
    "House_Sparrow": "家麻雀",
    "Field_Sparrow": "田雀鹀",
    "Fox_Sparrow": "狐色雀鹀",
    "Grasshopper_Sparrow": "黄胸草鹀",
    "Harris_Sparrow": "赫氏带鹀",
    "Henslow_Sparrow": "亨氏草鹀",
    "Le_Conte_Sparrow": "莱氏沙鹀",
    "Lincoln_Sparrow": "林氏带鹀",
    "Nelson_Sharp_tailed_Sparrow": "纳氏沙鹀",
    "Savannah_Sparrow": "稀树草鹀",
    "Seaside_Sparrow": "海滨沙鹀",
    "Song_Sparrow": "歌带鹀",
    "Tree_Sparrow": "美洲树雀鹀",
    "Vesper_Sparrow": "黄昏雀鹀",
    "White_crowned_Sparrow": "白冠带鹀",
    "White_throated_Sparrow": "白喉带鹀",
    "Cape_Glossy_Starling": "南非辉椋鸟",
    # 燕
    "Bank_Swallow": "灰沙燕",
    "Barn_Swallow": "家燕",
    "Cliff_Swallow": "美洲燕",
    "Tree_Swallow": "双色树燕",
    # 唐纳雀
    "Scarlet_Tanager": "猩红丽唐纳雀",
    "Summer_Tanager": "玫红丽唐纳雀",
    # 燕鸥
    "Artic_Tern": "北极燕鸥",
    "Black_Tern": "黑浮鸥",
    "Caspian_Tern": "红嘴巨鸥",
    "Common_Tern": "普通燕鸥",
    "Elegant_Tern": "丽色凤头燕鸥",
    "Forsters_Tern": "弗氏燕鸥",
    "Least_Tern": "小白额燕鸥",
    "Green_tailed_Towhee": "绿尾唧鹀",
    # 嘲鸫
    "Brown_Thrasher": "褐弯嘴嘲鸫",
    "Sage_Thrasher": "高山弯嘴嘲鸫",
    # 莺雀
    "Black_capped_Vireo": "黑顶莺雀",
    "Blue_headed_Vireo": "蓝头莺雀",
    "Philadelphia_Vireo": "费城莺雀",
    "Red_eyed_Vireo": "红眼莺雀",
    "Warbling_Vireo": "歌莺雀",
    "White_eyed_Vireo": "白眼莺雀",
    "Yellow_throated_Vireo": "黄喉莺雀",
    # 林莺
    "Bay_breasted_Warbler": "栗胸林莺",
    "Black_and_white_Warbler": "黑白森莺",
    "Black_throated_Blue_Warbler": "黑喉蓝林莺",
    "Blue_winged_Warbler": "蓝翅黄森莺",
    "Canada_Warbler": "加拿大林莺",
    "Cape_May_Warbler": "栗颊林莺",
    "Cerulean_Warbler": "天蓝林莺",
    "Chestnut_sided_Warbler": "栗胁林莺",
    "Golden_winged_Warbler": "金翅虫森莺",
    "Hooded_Warbler": "黑枕威森莺",
    "Kentucky_Warbler": "黄腹地莺",
    "Magnolia_Warbler": "玉兰林莺",
    "Mourning_Warbler": "黑胸地莺",
    "Myrtle_Warbler": "黄腰白喉林莺",
    "Nashville_Warbler": "灰冠虫森莺",
    "Orange_crowned_Warbler": "橙冠虫森莺",
    "Palm_Warbler": "棕榈林莺",
    "Pine_Warbler": "松莺",
    "Prairie_Warbler": "草原林莺",
    "Prothonotary_Warbler": "蓝翅黄森莺",
    "Swainson_Warbler": "斯氏虫森莺",
    "Tennessee_Warbler": "灰冠虫森莺",
    "Wilson_Warbler": "黑头威森莺",
    "Worm_eating_Warbler": "食虫森莺",
    "Yellow_Warbler": "黄林莺",
    "Northern_Waterthrush": "黄眉灶莺",
    "Louisiana_Waterthrush": "白眉灶莺",
    # 太平鸟
    "Bohemian_Waxwing": "太平鸟",
    "Cedar_Waxwing": "雪松太平鸟",
    # 啄木鸟
    "American_Three_toed_Woodpecker": "美洲三趾啄木鸟",
    "Pileated_Woodpecker": "北美黑啄木鸟",
    "Red_bellied_Woodpecker": "红腹啄木鸟",
    "Red_cockaded_Woodpecker": "红顶啄木鸟",
    "Red_headed_Woodpecker": "红头啄木鸟",
    "Downy_Woodpecker": "绒啄木鸟",
    # 鹪鹩
    "Bewick_Wren": "比氏苇鹪鹩",
    "Cactus_Wren": "棕曲嘴鹪鹩",
    "Carolina_Wren": "卡罗苇鹪鹩",
    "House_Wren": "莺鹪鹩",
    "Marsh_Wren": "长嘴沼泽鹪鹩",
    "Rock_Wren": "岩鹪鹩",
    "Winter_Wren": "冬鹪鹩",
    "Common_Yellowthroat": "黄喉地莺",
}

def translate_bird_name(name):
    """
    翻译鸟类名称：支持拉丁学名和英文名称
    """
    # 先尝试从拉丁名字典查找
    if name in BIRD_TRANSLATOR:
        return BIRD_TRANSLATOR[name]
    # 再尝试从英文名字典查找
    if name in VISION_BIRD_TRANSLATOR:
        return VISION_BIRD_TRANSLATOR[name]
    # 都找不到则返回原名
    return name


# ================= 2. 功能函数 =================

def generate_spectrogram_base64(audio_path):
    """
    把声音变成 Base64 图片
    """
    try:
        # 1. 读取音频 (延长至5秒，捕捉更多特征)
        y, sr = librosa.load(audio_path, duration=5)
        
        # 2. 音频预处理 - 降噪和归一化
        # 归一化音频
        y = librosa.util.normalize(y)
        
        # 3. 计算梅尔频谱 (增加细节)
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=256, fmax=8000, hop_length=512)
        S_dB = librosa.power_to_db(S, ref=np.max)
        
        # 3. 设置画布
        plt.figure(figsize=(10, 4))
        
        # 4. 绘制热力图
        librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', 
                               fmax=8000, cmap='magma')
        
        # 5. 美化
        plt.axis('off')         # 关掉坐标轴
        plt.tight_layout(pad=0) # 去掉白边
        
        # 6. 保存到内存
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
        buffer.seek(0)
        
        # 7. 转 Base64
        img_str = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return "data:image/png;base64," + img_str
    except Exception as e:
        print(f"画图失败: {e} (请尝试运行: pip install soundfile)")
        return ""

def ask_deepseek_about_bird(bird_name):
    """
    问 AI：获取鸟类科普
    """
    if not DEEPSEEK_API_KEY or "sk-" not in DEEPSEEK_API_KEY:
        print("错误：DeepSeek Key 未配置或格式不对！")
        return "（DeepSeek 密钥未配置）"
    try:
        print(f"[雀灵] 正在回答关于：{bird_name}...")
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是雀灵，一位幽默的生物学家。请用生动简练的语言（80字左右）介绍这种鸟。注意：如果用户给你的是拉丁学名，请先自动翻译成中文再介绍。"},
                {"role": "user", "content": f"请介绍一下【{bird_name}】。"}
            ],
            "stream": False
        }
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        
        response = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"[雀灵] DeepSeek 报错！状态码: {response.status_code}")
            print(f"[雀灵] 错误信息: {response.text}")
            return f"（雀灵暂时无法回答: {response.status_code}）"
            
        return response.json()['choices'][0]['message']['content']
        
    except Exception as e:
        print(f"[雀灵] 网络请求异常: {e}")
        return "（雀灵网络连接错误）"


# ================= 3. 加载模型 =================
print("正在加载声纹模型...")
try:
    pymodel_path = os.path.join(current_dir, 'pymodel')
    sys.path.append(pymodel_path)
    from macls.predict import MAClsPredictor
    audio_configs = os.path.join(pymodel_path, 'configs', 'cam++.yml')
    audio_model_path = os.path.join(pymodel_path, 'models', 'model.pth')
    # 切换到 pymodel 目录以解决相对路径问题
    original_cwd = os.getcwd()
    os.chdir(pymodel_path)
    audio_predictor = MAClsPredictor(configs=audio_configs, model_path=audio_model_path, use_gpu=False)
    os.chdir(original_cwd)
    print("✅ 声纹模型就绪！")
except Exception as e:
    print(f"❌ 声纹模型加载失败: {e}")

print("👁️ 正在加载视觉模型...")
vision_model = None
vision_classes = []
vision_transform = None
try:
    class_path = os.path.join(current_dir, 'bird_classes.txt')
    if os.path.exists(class_path):
        with open(class_path, 'r') as f:
            vision_classes = [line.strip() for line in f.readlines()]
    vision_model = models.resnet18(pretrained=False)
    num_ftrs = vision_model.fc.in_features
    vision_model.fc = nn.Linear(num_ftrs, len(vision_classes))
    model_path = os.path.join(current_dir, 'bird_visual_model.pth')
    if os.path.exists(model_path):
        vision_model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        vision_model.eval()
        vision_transform = transforms.Compose([
            transforms.Resize((224, 224)), transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        print("✅ 视觉模型就绪！")
    else:
        print("❌ 找不到 bird_visual_model.pth，视觉功能无法使用")
except Exception as e:
    print(f"❌ 视觉模型加载失败: {e}")

# ================= 4. 接口定义 =================

# --- 接口 A: 听音识鸟
@app.route('/predict_audio', methods=['POST'])
def predict_audio():
    if 'file' not in request.files: 
        return jsonify({'code': 400, 'msg': '无文件'}), 400
    
    # 检查模型是否加载成功
    if 'audio_predictor' not in globals() or audio_predictor is None:
        print("[声纹识别] 错误：模型未加载")
        return jsonify({'code': 500, 'msg': '声纹模型未加载，请检查模型文件'}), 500
    
    file = request.files['file']
    save_path = os.path.join(current_dir, 'temp_audio.wav')
    file.save(save_path)
    
    try:
        # 1. 识别
        print(f"[声纹识别] 正在分析音频: {file.filename}")
        label, score = audio_predictor.predict(save_path)
        
        # 翻译为中文
        cn_name = translate_bird_name(label)
        score_float = float(score)
        
        print(f"[声纹识别] 识别结果: {cn_name} (置信度: {score_float:.2%})")
        
        # 2. 根据置信度返回不同结果 (阈值 40%)
        ai_desc = ""
        if score_float < 0.4:
            cn_name = "未知"
            ai_desc = "哎呀，雀灵没听出来这是什么鸟呢🤔\n\n建议：\n• 找个安静的环境重新录制\n• 尽量靠近鸟类，录制清晰的叫声\n• 避免风声或其他噪音干扰"
        else:
            # 置信度 >= 40%，调用 AI 给出详细介绍
            ai_desc = ask_deepseek_about_bird(cn_name)
        
        # 3. 绘制声纹图
        spectrogram_base64 = generate_spectrogram_base64(save_path)
        
        # 4. 返回结果
        return jsonify({
            'code': 200,
            'msg': '识别成功',
            'data': {
                'name': cn_name,
                'score': score_float,
                'type': 'audio',
                'desc': ai_desc,
                'voiceprint': spectrogram_base64,
                'confidence': 'high' if score_float > 0.6 else 'low'
            }
        })
    except Exception as e:
        print(f"[声纹识别] 处理异常: {e}")
        return jsonify({'code': 500, 'msg': f'识别失败: {str(e)}'}), 500
    finally:
        # 清理临时文件
        if os.path.exists(save_path):
            os.remove(save_path)

# --- 接口 B: 拍照识鸟 ---
@app.route('/predict_image', methods=['POST'])
def predict_image():
    if 'file' not in request.files: 
        return jsonify({'code': 400, 'msg': '无图片'}), 400
    
    # 检查模型是否加载成功
    if vision_model is None or vision_transform is None:
        print("[图像识别] 错误：视觉模型未加载")
        return jsonify({'code': 500, 'msg': '视觉模型未加载，请检查模型文件'}), 500
    
    file = request.files['file']
    print(f"[图像识别] 正在分析图片: {file.filename}")
    
    try:
        image = Image.open(file.stream).convert('RGB')
        image_tensor = vision_transform(image).unsqueeze(0)
        
        with torch.no_grad():
            outputs = vision_model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            score, index = torch.max(probabilities, 0)
        
        score_float = score.item()
        raw_name = vision_classes[index.item()]
        clean_name = raw_name.split('.')[-1]
        
        # 翻译
        cn_name = translate_bird_name(clean_name)
        print(f"[图像识别] 识别结果: {cn_name} (置信度: {score_float:.2%})")
        
        # 根据置信度返回不同结果 (阈值 40%)
        if score_float < 0.4:
            cn_name = "未知"
            ai_desc = "哎呀，雀灵没认出这是什么鸟呢🤔\n\n建议：\n• 拍摄更清晰的鸟类照片\n• 尽量让鸟占据画面主要位置\n• 避免逆光或光线不足"
        else:
            # 置信度 >= 40%，调用 AI 给出详细介绍
            ai_desc = ask_deepseek_about_bird(cn_name)
        
        return jsonify({
            'code': 200, 
            'msg': '识别成功',
            'data': {
                'name': cn_name,
                'score': score_float,
                'type': 'visual',
                'desc': ai_desc,
                'confidence': 'high' if score_float > 0.5 else 'low'
            }
        })
    except Exception as e:
        print(f"[图像识别] 处理异常: {e}")
        return jsonify({'code': 500, 'msg': f'识别失败: {str(e)}'}), 500

# --- 接口 C: 聊天 (保持不变) ---
@app.route('/chat_about_bird', methods=['POST'])
def chat_about_bird():
    data = request.json
    bird_name = data.get('bird_name', '这种鸟')
    question = data.get('question')

    if not DEEPSEEK_API_KEY: return jsonify({'data': {'answer': '未配置 Key'}})
    
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "system", "content": "你是雀灵，鸟类专家助手"}, {"role": "user", "content": f"关于{bird_name}：{question}"}]
        }
        res = requests.post(DEEPSEEK_URL, json=payload, headers=headers).json()
        return jsonify({'code': 200, 'data': {'answer': res['choices'][0]['message']['content']}})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500

@app.route('/')
def hello():
    return "Flask 服务正常运行中！"

if __name__ == '__main__':
    # 允许所有 IP 访问，方便手机调试
    app.run(host='0.0.0.0', port=5000)