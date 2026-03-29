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
from functools import lru_cache
import time

# CPU 性能优化
torch.set_num_threads(4)  # 限制 PyTorch 线程数
torch.backends.mkldnn.enabled = True  # 启用 MKL-DNN 加速

# 核心绘图库
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np

# ================= 1. 全局配置与字典 =================

app = Flask(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# DeepSeek API Key (提示：建议实际部署时放在环境变量里更安全哦)
DEEPSEEK_API_KEY = "sk-e042912a9042446c9bb05a503db69f66" 
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# 鸟类拉丁名 -> 中文名 (声纹用)
# 优化说明：统一格式，清理空格，按字母排序
BIRD_TRANSLATOR = {
    # A
    "Abroscopus": "鹟莺", "Acridotheres": "八哥", "Acrocephalus": "苇莺",
    "Actinodura": "斑翅鹛", "Aegithalos": "长尾山雀", "Aerodramus": "金丝燕",
    "Agropsar": "椋鸟", "Alauda": "云雀", "Alcippe": "雀鹛",
    "Anas": "鸭", "Anser": "雁", "Anthipes": "鹟",
    "Anthus": "鹨", "Apus": "雨燕", "Arborophila": "山鹧鸪",
    "Arundinax": "大苇莺", "Aythya": "潜鸭", "Aix": "鸳鸯","Alectoris": "石鸡",
    # B
    "Bambusicola": "竹鸡", "Batrachostomus": "蛙口夜鹰", "Brachypteryx": "短翅鸫",
    "Bradypterus": "短翅莺",
    # C
    "Cacomantis": "八声杜鹃", "Calamornis": "苇莺", "Caprimulgus": "夜鹰",
    "Cecropis": "金腰燕", "Centropus": "鸦鹃", "Certhia": "旋木雀",
    "Cercotrichas": "棕尾鸲", "Charadrius": "鸻", "Chalcophaps": "绿翅金鸠",
    "Chloropsis": "叶鹎", "Cholornis": "鹦嘴雀", "Chrysococcyx": "金鹃",
    "Chrysolophus": "锦鸡", "Cisticola": "扇尾莺", "Clamator": "凤头鹃",
    "Columba": "鸽", "Conostoma": "鹦嘴雀", "Coturnicops": "田鸡",
    "Coturnix": "鹌鹑", "Crossoptilon": "马鸡", "Curruca": "白喉林莺",
    "Cutia": "斑胁希鹛", "Cuculus": "布谷鸟", "Cyanoderma": "雅鹛",
    "Cyanopica": "灰喜鹊", "Cyanoptila": "白腹蓝鹟", "Cyornis": "蓝鹟",
    "Cypsiurus": "棕雨燕", "Cygnus": "天鹅","Cettia": "树莺",
    # D
    "Delichon": "毛脚燕", "Dendrocygna": "树鸭", "Ducula": "皇鸠",
    # E
    "Elachura": "丽星鹩鹛", "Enicurus": "燕尾", "Eudynamys": "噪鹃",
    "Eumyias": "铜蓝鹟", "Erythrogenys": "钩嘴鹛",
    # F
    "Francolinus": "鹧鸪", "Fulica": "骨顶鸡", "Fulvetta": "雀鹛",
    # G
    "Gallicrex": "董鸡", "Gallinula": "黑水鸡", "Gallus": "原鸡",
    "Garrulax": "噪鹛", "Garrulus": "松鸦", "Geokichla": "地鸫",
    "Graminicola": "大草莺", "Grammatoptila": "纹背噪鹛", "Grandala": "蓝大翅鸲",
    "Gypsophila": "鹪鹛","Gracupica": "椋鸟",
    # H
    "Helopsaltes": "苍眉蝗莺", "Heterophasia": "奇鹛", "Hierococcyx": "鹰鹃",
    "Horornis": "短翅莺", "Hirundo": "燕",
    # I
    "Iduna": "篱莺", "Ianthocincla": "噪鹛", "Ithaginis": "血雉",
    # L
    "Lanius": "伯劳", "Larvivora": "鸲", "Leioptila": "相思鸟",
    "Leptopoecile": "凤头雀莺", "Lerwa": "雪鹧鸪", "Lewinia": "灰胸秧鸡",
    "Liocichla": "薮鹛", "Lioparus": "金胸雀鹛", "Locustella": "蝗莺",
    "Lophophorus": "虹雉", "Lophura": "鹇", "Luscinia": "歌鸲",
    # M
    "Macropygia": "鹃鸠", "Mareca": "赤颈鸭", "Megalurus": "大尾莺",
    "Minla": "希鹛", "Mixornis": "纹胸鹛", "Motacilla": "鹡鸰",
    "Moupinia": "宝兴鹛雀", "Muscicapa": "鹟", "Myophonus": "啸鸫",
    "Myzornis": "火尾绿鹛","Mergus": "秋沙鸭",
    # N
    "Napothera": "短尾鹛", "Neosuthora": "短尾鹦嘴雀", "Nettapus": "棉凫",
    "Niltava": "仙鹟", "Ninox": "鹰鸮",
    # O
    "Orthotomus": "缝叶莺", "Otus": "角鸮",
    # P
    "Paradoxornis": "鹦嘴雀", "Parayuhina": "凤鹛", "Parus": "山雀",
    "Passer": "麻雀", "Pavo": "孔雀", "Pellorneum": "幽鹛",
    "Phaenicophaeus": "地鹃", "Phasianus": "雉鸡", "Phoenicurus": "红尾鸲",
    "Phylloscopus": "柳莺", "Phyllergates": "金头缝叶莺", "Pica": "喜鹊",
    "Pnoepyga": "鳞鹩", "Polyplectron": "孔雀雉", "Pomatorhinus": "钩嘴鹛",
    "Porphyrio": "紫水鸡", "Prinia": "山鹪莺", "Psittiparus": "鹦嘴雀",
    "Pterorhinus": "噪鹛", "Ptyonoprogne": "岩燕", "Pycnonotus": "鹎","Perdix": "山鹑","Pucrasia": "勺鸡",
    # R
    "Rallina": "斑秧鸡", "Rallus": "秧鸡", "Regulus": "戴菊",
    "Rhipidura": "扇尾鹟", "Rhopophilus": "山鹛", "Riparia": "沙燕",
    # S
    "Schoeniparus": "雀鹛", "Sinosuthora": "鹦嘴雀", "Spilopelia": "珠颈斑鸠",
    "Spatula": "琵嘴鸭", "Spelaeornis": "鹪鹛", "Stachyris": "穗鹛",
    "Staphida": "凤鹛", "Streptopelia": "斑鸠", "Strix": "林鸮",
    "Sturnia": "椋鸟", "Sturnus": "椋鸟", "Suthora": "鹦嘴雀",
    "Syrmaticus": "长尾雉", "Syrrhaptes": "毛腿沙鸡","Sitta": "鳾","Spodiopsar": "椋鸟","Surniculus": "乌鹃",
    # T
    "Tarsiger": "林鸲", "Tesia": "短翅莺", "Tetraogallus": "雪鸡",
    "Tetrastes": "榛鸡", "Tetraophasis": "雉鹑", "Tickellia": "宽嘴鹟莺",
    "Tichodroma": "红翅旋壁雀", "Timalia": "红顶鹛", "Treron": "绿鸠",
    "Trochalopteron": "噪鹛", "Troglodytes": "鹪鹩", "Tropicoperdix": "山鹧鸪","Tadorna": "麻鸭","Tragopan": "角雉",
    "Turdus": "鸫",
    # U
    "Urosphena": "小短翅莺",
    # Y
    "Yuhina": "凤鹛",
    # Z
    "Zapornia": "小秧鸡", "Zoothera": "地鸫", "Zosterops": "绣眼鸟"
}

# 终极版：525 种全球/中国常见鸟类翻译大字典 (视觉模型专属)
# 优化说明：清理了所有中英文之间的多余空格，统一翻译格式
VISION_BIRD_TRANSLATOR = {
    # A
    "ABBOTTS BABBLER": "阿波特鹛", "ABBOTTS BOOBY": "阿波特鲣鸟", "ABYSSINIAN GROUND HORNBILL": "阿比西尼亚地犀鸟",
    "AFRICAN CROWNED CRANE": "非洲冠鹤", "AFRICAN CROWNED EAGLE": "非洲冠雕", "AFRICAN EMERALD CUCKOO": "非洲翠鹃",
    "AFRICAN FIREFINCH": "非洲红雀", "AFRICAN OYSTER CATCHER": "非洲蛎鹬", "AFRICAN OYSTERCATCHER": "非洲蛎鹬",
    "AFRICAN PIED HORNBILL": "非洲斑犀鸟", "AFRICAN PYGMY GOOSE": "非洲侏儒鹅",
    "ALBATROSS": "信天翁", "ALBERTS TOWHEE": "艾伯氏唧鹀", "ALEXANDRINE PARAKEET": "亚历山大鹦鹉",
    "ALPINE CHOUGH": "黄嘴山鸦", "ALTAMIRA ORIOLE": "阿尔塔米拉拟黄鹂", "ALTAMIRA YELLOWTHROAT": "阿尔塔米拉黄喉莺",
    "AMERICAN AVOCET": "美洲反嘴鹬", "AMERICAN BITTERN": "美洲麻鳽", "AMERICAN COOT": "美洲骨顶鸡",
    "AMERICAN DIPPER": "美洲河乌", "AMERICAN FLAMINGO": "美洲火烈鸟", "AMERICAN GOLDFINCH": "美洲金翅雀",
    "AMERICAN KESTREL": "美洲隼", "AMERICAN PIPIT": "黄腹鹨", "AMERICAN REDSTART": "橙尾鸲莺",
    "AMERICAN ROBIN": "美洲鸫", "AMERICAN WIGEON": "美洲赤颈鸭", "AMETHYST WOODSTAR": "紫晶林星蜂鸟",
    "ANDEAN GOOSE": "安第斯雁", "ANDEAN LAPWING": "安第斯麦鸡", "ANDEAN SISKIN": "安第斯黄雀",
    "ANHINGA": "美洲蛇鹈", "ANIANIAU": "小夏威夷旋蜜雀", "ANNAS HUMMINGBIRD": "安氏蜂鸟",
    "ANTBIRD": "蚁鸟", "ANTILLEAN EUPHONIA": "安的列斯歌雀", "APAPANE": "白腹蜜鸟",
    "APOSTLEBIRD": "灰雷鸟", "ARARIPE MANAKIN": "阿拉里佩侏儒鸟", "ASHY STORM PETREL": "灰叉尾海燕",
    "ASHY THRUSHBIRD": "灰鸫鹛", "ASIAN CRESTED IBIS": "朱鹮", "ASIAN DOLLARD BIRD": "三宝鸟",
    "ASIAN GREEN BEE EATER": "绿喉蜂虎", "ASIAN OPENBILL STORK": "钳嘴鹳", "AUCKLAND SHAQ": "奥克兰鸬鹚",
    "AUSTRAL CANASTERO": "南方卡纳斯特罗雀", "AUSTRALASIAN FIGBIRD": "裸眼无花果鹂",
    "AVADAVAT": "红梅花雀", "AZARAS SPINETAIL": "阿氏针尾雀", "AZURE BREASTED PITTA": "蓝胸八色鸫",
    "AZURE JAY": "天蓝鸦", "AZURE TANAGER": "蓝唐纳雀", "AZURE TIT": "灰蓝山雀",
    # B
    "BAIKAL TEAL": "花脸鸭", "BALD EAGLE": "白头海雕", "BALD IBIS": "隐鹮",
    "BALI STARLING": "巴厘岛长冠八哥", "BALTIMORE ORIOLE": "橙腹拟黄鹂", "BANANAQUIT": "蕉森莺",
    "BAND TAILED GUAN": "斑尾冠雉", "BAND TAILED PUAN": "斑尾鹃鸠",
    "BANDED BROADBILL": "斑阔嘴鸟", "BANDED PITA": "斑背八色鸫", "BANDED STILT": "斑长脚鹬",
    "BAR-TAILED GODWIT": "斑尾塍鹬", "BARN OWL": "仓鸮", "BARN SWALLOW": "家燕",
    "BARRED PUFFBIRD": "横斑喷鴷", "BARROWS GOLDENEYE": "巴氏鹊鸭", "BAY-BREASTED WARBLER": "栗胸林莺",
    "BEARDED BARBET": "须拟啄木鸟", "BEARDED BELLBIRD": "须钟雀", "BEARDED REEDLING": "文须雀",
    "BELTED KINGFISHER": "白腹鱼狗", "BIRD OF PARADISE": "极乐鸟", "BLACK AND YELLOW BROADBILL": "黑黄阔嘴鸟",
    "BLACK BAZA": "黑冠鹃隼", "BLACK BREASTED PUFFBIRD": "黑胸喷鴷", "BLACK COCKATO": "黑凤头鹦鹉",
    "BLACK COCKATOO": "黑凤头鹦鹉", "BLACK FACED SPOONBILL": "黑脸琵鹭",
    "BLACK FRANCOLIN": "黑鹧鸪", "BLACK HEADED CAIQUE": "黑头凯克鹦鹉",
    "BLACK NECKED STILT": "黑颈长脚鹬", "BLACK SKIMMER": "黑剪嘴鸥", "BLACK SWAN": "黑天鹅",
    "BLACK TAIL CRAKE": "黑尾田鸡", "BLACK THROATED BUSHTIT": "黑喉长尾山雀", "BLACK THROATED HUET": "黑喉隐雀",
    "BLACK THROATED WARBLER": "黑喉林莺", "BLACK VENTED SHEARWATER": "黑腹剪水鹱",
    "BLACK VULTURE": "黑美洲鹫", "BLACK-CAPPED CHICKADEE": "黑顶奇鹛",
    "BLACK-NECKED GREBE": "黑颈䴙䴘", "BLACK-THROATED SPARROW": "黑喉漠鹀", "BLACKBURNIAM WARBLER": "橙胸林莺",
    "BLONDE CRESTED WOODPECKER": "黄冠拟啄木鸟", "BLOOD PHEASANT": "血雉", "BLUE COAU": "蓝马岛鹃",
    "BLUE DACNIS": "蓝锥嘴雀", "BLUE GRAY GNATCATCHER": "蓝灰蚋蚊捕手",
    "BLUE GROSBEAK": "蓝蜡嘴雀", "BLUE GROUSE": "蓝松鸡",
    "BLUE HERON": "大蓝鹭", "BLUE JAY": "冠蓝鸦", "BLUE MALKOHA": "蓝地鹃",
    "BLUE THROATED TOUCANET": "蓝喉小巨嘴鸟",
    "BOBOLINK": "刺歌雀", "BORNEAN BRISTLEHEAD": "婆罗洲刷鸟", "BORNEAN LEAFBIRD": "婆罗洲叶鹎",
    "BORNEAN PHEASANT": "婆罗洲雉鸡",
    "BRANDT CORMARANT": "勃兰特鸬鹚", "BREWERS BLACKBIRD": "布鲁尔黑鸟",
    "BROWN CREPPER": "棕色旋木雀", "BROWN HEADED COWBIRD": "褐头牛鹂",
    "BROWN NOODY": "白顶玄鸥", "BROWN THRASHER": "褐弯嘴嘲鸫", "BUFFLEHEAD": "鹊鸭",
    "BULWERS PHEASANT": "白尾鹇", "BURCHELLS COURSER": "走鸻",
    "BUSH TURKEY": "丛冢雉",
    # C
    "CAATINGA CACHOLOTE": "卡廷加穴鸟",
    "CACTUS WREN": "仙人掌鹪鹩", "CALIFORNIA CONDOR": "加州神鹫", "CALIFORNIA GULL": "加州鸥",
    "CALIFORNIA QUAIL": "加州鹌鹑", "CAMPO FLICKER": "坎波扑翅鴷",
    "CANARY": "金丝雀", "CANVASBACK": "帆背潜鸭",
    "CAPE GLOSSY STARLING": "南非辉椋鸟", "CAPE LONGCLAW": "橙喉长爪鹡鸰", "CAPE MAY WARBLER": "栗颊林莺",
    "CAPE ROCK THRUSH": "南非岩鸫","CINNAMON ATTILA": "桂红阿蒂拉霸鹟","CINNAMON FLYCATCHER": "桂红霸鹟", 
    "CAPPED HERON": "黑冠白鹭", "CAPUCHINBIRD": "秃伞鸟", "CARMINE BEE-EATER": "红蜂虎",
    "CASPIAN TERN": "红嘴巨鸥", "CASSOWARY": "鹤鸵", "CEDAR WAXWING": "雪松太平鸟",
    "CERULEAN WARBLER": "天蓝林莺", "CHARA DE COLLAR": "领鸻", "CHATTERING LORY": "喋喋吸蜜鹦鹉",
    "CHESTNET BELLIED EUPHONIA": "栗腹歌雀", "CHESTNUT WEAVER": "栗织雀",
    "CHINESE BAMBOO PARTRIDGE": "中国竹鸡", "CHINESE POND HERON": "中国池鹭",
    "CHIPPING SPARROW": "chipping 麻雀", "CHUCAO TAPACULO": "chucao 塔帕库洛",
    "CHUKAR PARTRIDGE": "石鸡", "CLARKS GREBE": "克氏䴙䴘","CINNAMON TEAL": "桂红鸭",
    "CLARKS NUTCRACKER": "北美星鸦", "COLLARED ARACARI": "领簇舌巨嘴鸟",
    "COLLARED CRESCENTCHEST": "领新月胸雀","COCK OF THE ROCK": "动冠伞鸟",
    "COMMON FIRECREST": "火冠戴菊", "COMMON GRACKLE": "紫翅椋鸟", "COMMON HOUSE MARTIN": "白腹毛脚燕",
    "COMMON IORA": "黑翅雀鹎", "COMMON LOON": "普通潜鸟", "COMMON POORWILL": "北美小夜鹰",
    "COMMON STARLING": "紫翅椋鸟", "COPPERY TAILED COUCAL": "铜尾鸦鹃",
    "COPPERSMITH BARBET": "赤胸拟啄木鸟", "CORMORANT": "鸬鹚",
    "CORONED KINGLET": "戴菊", "COUCHS KINGBIRD": "库氏王霸鹟", "CRAB PLOVER": "蟹鸻",
    "CRANE HAWK": "鹤鹰","COCK OF THE  ROCK": "动冠伞鸟",
    "CREAM COLORED WOODPECKER": "乳白色啄木鸟","COCKATOO": "凤头鹦鹉",
    "CRESTED AUKLET": "冠小海雀", "CRESTED CARACARA": "凤头卡拉鹰", "CRESTED COUA": "冠马岛鹃",
    "CRESTED FIREBACK": "凤头火背鹇", "CRESTED KINGFISHER": "冠鱼狗", "CRESTED NUTHATCH": "冠鳾",
    "CRESTED OROPENDOLA": "冠拟黄鹂", "CRESTED SERPENT EAGLE": "冠蛇雕",
    "CRESTED SHRIKETIT": "冠鵙雀", "CRESTED WOOD PARTRIDGE": "冠林鹑",
    "CROW": "乌鸦", "CRIMSON CHAT": "深红鸲", "CRIMSON SUNBIRD": "深红太阳鸟",
    "CROWNED PIGEON": "维多利亚冠鸠",
    "CUBAN TODY": "古巴短尾鴗", "CUBAN TROGON": "古巴咬鹃", "CURL CRESTED ARACARI": "卷冠簇舌巨嘴鸟",
    "CURL CRESTED ARACURI": "卷冠阿拉库里",
    # D
    "D-ARNAUDS BARBET": "达氏拟啄木鸟", "DALMATIAN PELICAN": "卷羽鹈鹕", "DARJEELING WOODPECKER": "大吉岭啄木鸟",
    "DARWINS FLYCATCHER": "达尔文霸鹟",
    "DAURIAN REDSTART": "北红尾鸲",
    "DARK EYED JUNCO": "暗眼灯草鹀", "DEMOISELLE CRANE": "蓑羽鹤", "DOUBLE BARRED FINCH": "双斑草雀",
    "DOUBLE BRESTED CORMARANT": "双冠鸬鹚", "DOUBLE BREASTED CORMARANT": "双冠鸬鹚",
    "DOUBLE EYED FIG PARROT": "双眼无花果鹦鹉",
    "DOWNY WOODPECKER": "绒啄木鸟", "DUSKY LORY": "暗色吸蜜鹦鹉", "DUSKY ROBIN": "暗色鸲",
    # E
    "EARED GREBE": "角䴙䴘", "EARED PITA": "耳状八色鸫",
    "EASTERN BLUEBIRD": "东蓝鸲", "EASTERN BLUEBONNET": "东蓝帽雀",
    "EASTERN GOLDEN WEAVER": "东非金织雀", "EASTERN MEADOWLARK": "东草地鹨",
    "EASTERN ROSELLA": "东玫瑰鹦鹉", "EASTERN TOWEE": "棕胁唧鹀", "EASTERN WIP POOR WILL": "北美夜鹰",
    "EASTERN YELLOW ROBIN": "东黄鸲", "ECUADORIAN HILLSTAR": "厄瓜多尔闪羽蜂鸟", "EGYPTIAN GOOSE": "埃及雁",
    "ELEGANT TROGON": "丽咬鹃", "ELLIOTS  PHEASANT": "白颈长尾雉", "EMERALD TANAGER": "绿唐纳雀",
    "EMPEROR PENGUIN": "帝企鹅", "EMU": "鸸鹋", "ENGGANO MYNA": "恩加诺八哥",
    "EURASIAN BULLFINCH": "红腹灰雀", "EURASIAN COLLARED DOVE": "灰斑鸠", "EURASIAN GOLDEN ORIOLE": "金黄鹂",
    "EURASIAN MAGPIE": "喜鹊", "EUROPEAN GOLDFINCH": "红额金翅雀", "EUROPEAN SHAG": "欧洲鸬鹚",
    "EUROPEAN TURTLE DOVE": "欧斑鸠", "EVENING GROSBEAK": "黄昏蜡嘴雀",
    # F
    "FAIRY BLUEBIRD": "和平鸟",
    "FAIRY PENGUIN": "小蓝企鹅", "FAIRY TERN": "仙燕鸥", "FAN TAILED WIDOW": "扇尾寡妇鸟",
    "FASCIATED WREN": "横斑鹪鹩", "FIERY MINIVET": "赤红山椒鸟", "FIORDLAND PENGUIN": "峡湾企鹅",
    "FIRE TAILLED MYZORNIS": "火尾绿鹛", "FLAME BOWERBIRD": "焰色园丁鸟", "FLAME TANAGER": "焰色唐纳雀",
    "FLAMINGO": "火烈鸟", "FRIGATE": "军舰鸟", "FRILL BACK PIGEON": "褶背鸽",
    # G
    "GAMBELS QUAIL": "甘氏鹌鹑",
    "GANG GANG COCKATOO": "红冠灰凤头鹦鹉", "GILA WOODPECKER": "吉拉啄木鸟", "GILDED FLICKER": "鎏金扑翅鴷",
    "GLOSSY IBIS": "彩鹮", "GO AWAY BIRD": "灰蕉鹃", "GOLD WING WARBLER": "金翅森莺",
    "GOLDEN BOWER BIRD": "金园丁鸟", "GOLDEN CHEEKED WARBLER": "金颊森莺", "GOLDEN CHLOROPHONIA": "金绿宽嘴雀",
    "GOLDEN EAGLE": "金雕", "GOLDEN PARAKEET": "金黄长尾鹦鹉",
    "GOLDEN PHEASANT": "红腹锦鸡", "GOLDEN PIPIT": "金鹨",
    "GOULDIAN FINCH": "胡锦鸟", "GRANDALA": "蓝大翅鸲", "GRAY CATBIRD": "灰猫鸟",
    "GRAY KINGBIRD": "灰王霸鹟", "GRAY PARTRIDGE": "灰山鹑", "GREAT ARGUS": "大眼斑雉",
    "GREAT BLUE HERON": "大蓝鹭", "GREAT GRAY OWL": "大灰鸮",
    "GREAT HORNED OWL": "大角鸮", "GREAT JACAMAR": "大鹟鴷",
    "GREAT KISKADEE": "大食蝇霸鹟", "GREAT POTOO": "大林鸱", "GREAT TINAMOU": "大䳍",
    "GREAT XENOPS": "大异嘴雀",
    "GREATER PEWEE": "大绿霸鹟", "GREATER PRAIRIE CHICKEN": "大草原榛鸡", "GREATOR SAGE GROUSE": "大艾草松鸡",
    "GREBE": "䴙䴘",
    "GREEN BROADBILL": "绿阔嘴鸟", "GREEN JAY": "绿鸦", "GREEN MAGPIE": "蓝绿鹊",
    "GREEN WINGED DOVE": "绿翅鸠",
    "GREY CUCKOOSHRIKE": "灰鹃鵙", "GREY HEADED FISH EAGLE": "灰头渔雕",
    "GREY PLOVER": "灰斑鸻", "GROVED BILLED ANI": "沟嘴犀鹃",
    "GUINEA TURACO": "几内亚蕉鹃", "GUINEAFOWL": "珠鸡", "GURNEYS PITTA": "黑冠八色鸫",
    "GYRFALCON": "矛隼",
    # H
    "HAMERKOP": "锤头鹳", "HARLEQUIN DUCK": "丑鸭",
    "HARLEQUIN QUAIL": "丑鹑", "HARPY EAGLE": "角雕", "HAWAIIAN GOOSE": "夏威夷雁",
    "HAWFINCH": "锡嘴雀", "HELMET VANGA": "盔鵙", "HEPATIC TANAGER": "肝色唐纳雀",
    "HIMALAYAN BLUETAIL": "红胁蓝尾鸲", "HIMALAYAN MONAL": "棕尾虹雉", "HOATZIN": "麝雉",
    "HOODED MERGANSER": "棕胁秋沙鸭", "HOOPOES": "戴胜", "HORNBILL": "犀鸟",
    "HORNED GUAN": "角冠雉", "HORNED LARK": "角百灵", "HORNED SUNGEM": "角蜂鸟",
    "HOUSE FINCH": "家朱雀", "HOUSE SPARROW": "家麻雀", "HYACINTH MACAW": "紫蓝金刚鹦鹉",
    # I
    "IBERIAN MAGPIE": "伊比利亚灰喜鹊", "IBIS": "鹮", "IBISBILL": "鹮嘴鹬",
    "IMPERIAL SHAQ": "imperial 鸬鹚",
    "INCA TERN": "印加燕鸥", "INDIAN BUSTARD": "大印度鸨", "INDIAN PITTA": "印度八色鸫",
    "INDIAN ROLLER": "印度佛法僧", "INDIAN VULTURE": "印度白背兀鹫",
    "INDIGO BUNTING": "靛蓝彩鹀", "INDIGO FLYCATCHER": "靛蓝霸鹟",
    "INLAND DOTTEREL": "内陆鸻", "IVORY BILLED ARACARI": "象牙嘴簇舌巨嘴鸟", "IVORY GULL": "象牙鸥",
    "IWI": "镰嘴管舌雀",
    # J
    "JABIRU": "南美鹳", "JACK SNIPE": "姬鹬", "JACOBIN PIGEON": "雅各宾鸽",
    "JANDAYA PARAKEET": "金头锥尾鹦鹉", "JAPANESE ROBIN": "日本歌鸲", "JAVA SPARROW": "禾雀",
    "JOCOTOCO ANTPITTA": "娇小蚁鸫",
    # K
    "KAGU": "鹭鹤", "KAKAPO": "鸮鹦鹉",
    "KILLDEAR": "双领鸻", "KING EIDER": "王绒鸭",
    "KING VULTURE": "王鹫", "KIWI": "几维鸟",
    "KOOKABURRA": "笑翠鸟",
    # L
    "LALAGE": "鸣鹃鵙", "LAUGHING GULL": "笑鸥",
    "LAZULI BUNTING": "琉璃彩鹀", "LARK BUNTING": "lark 彩鹀",
    "LESSER ADJUTANT": "秃鹳", "LILAC ROLLER": "紫胸佛法僧",
    "LIMPKIN": "limpkin",
    "LITTLE AUK": "小海雀", "LOGGERHEAD SHRIKE": "呆头伯劳", "LONG-EARED OWL": "长耳鸮",
    "LOONEY BIRDS": "滑稽鸟",
    "LUCIFER HUMMINGBIRD": "lucifer 蜂鸟",
    # M
    "MAGPIE GOOSE": "鹊雁", "MALABAR HORNBILL": "斑犀鸟", "MALACHITE KINGFISHER": "冠鱼狗",
    "MALAGASY WHITE EYE": "马岛绣眼鸟", "MALEO": "苏拉冢雉", "MALLARD": "绿头鸭",
    "MALLARD DUCK": "绿头鸭", "MANDARIN DUCK": "鸳鸯", "MANDRIN DUCK": "鸳鸯",
    "MANGROVE CUCKOO": "红树美洲鹃", "MARABOU STORK": "秃鹳",
    "MASKED BOBWHITE": "蒙面 bobwhite", "MASKED BOOBY": "蓝脸鲣鸟", "MASKED LAPWING": "白颈麦鸡",
    "MCKAYS BUNTING": "mckay 鹀",
    "MERLIN": "灰背隼",
    "MIKADO  PHEASANT": "黑长尾雉", "MILITARY MACAW": "军金刚鹦鹉",
    "MOURNING DOVE": "哀鸠", "MYNA": "八哥", "NICOBAR PIGEON": "尼科巴鸠",
    # N
    "NOISY FRIARBIRD": "喧噪吸蜜鸟", "NORTHERN BALD IBIS": "隐鹮", "NORTHERN BEARDLESS TYRANNULET": "北无须小霸鹟",
    "NORTHERN CARDINAL": "主红雀", "NORTHERN FLICKER": "北扑翅鴷", "NORTHERN FULMAR": "暴风鹱",
    "NORTHERN GANNET": "北方鲣鸟", "NORTHERN GOSHAWK": "苍鹰", "NORTHERN JACANA": "北美水雉",
    "NORTHERN MOCKINGBIRD": "小嘲鸫", "NORTHERN PARULA": "北森莺", "NORTHERN RED BISHOP": "红寡妇鸟",
    "NORTHERN SHOVELER": "琵嘴鸭",
    # O
    "OCELLATED TURKEY": "眼斑火鸡", "OKINAWA RAIL": "冲绳秧鸡", "ORANGE BRESTED BUNTING": "橙胸鹀",
    "ORCHARD ORIOLE": "圃拟黄鹂", "ORIENTAL BAY OWL": "东方湾鸮",
    "ORNATE HAWK EAGLE": "饰纹鹰雕",
    "OSPREY": "鱼鹰", "OSTRICH": "鸵鸟",
    "OVENBIRD": "橙顶灶莺", "OYSTER CATCHER": "蛎鹬",
    # P
    "PAINTED BUNTING": "丽彩鹀",
    "PALILA": "黄胸拟管舌雀", "PALM NUT VULTURE": "棕榈鹫", "PARADISE TANAGER": "七彩唐纳雀",
    "PARAKETT  AKULET": "鹦鹉海雀", "PARAKETT  AUKLET": "鹦鹉海雀",
    "PARUS MAJOR": "大山雀", "PATAGONIAN SIERRA FINCH": "巴塔哥尼亚岭雀",
    "PEACOCK": "孔雀", "PELICAN": "鹈鹕", "PEREGRINE FALCON": "游隼",
    "PHAINOPEPLA": "silky flycatcher",
    "PHILIPPINE EAGLE": "食猿雕", "PINK BANDED FRUIT DOVE": "粉斑果鸠", "PINK ROBIN": "粉红鸲",
    "PLUSH CRESTED JAY": "绒冠松鸦",
    "POMARINE JAEGER": "中贼鸥", "PUFFIN": "海鹦", "PURPLE FINCH": "紫朱雀",
    "PURPLE GALLINULE": "紫水鸡", "PURPLE MARTIN": "紫崖燕", "PURPLE SWAMPHEN": "紫水鸡",
    "PUNA TEAL": "普纳绿翅鸭",
    "PYGMY KINGFISHER": "非洲小鱼狗", "PYRRHULOXIA": "pyrrhuloxia",
    # Q
    "QUETZAL": "凤尾绿咬鹃",
    # R
    "RAINBOW LORIKEET": "虹彩吸蜜鹦鹉",
    "RAZORBILL": "刀嘴海雀", "RED BELLIED PITTA": "红腹八色鸫", "RED BLANDED BROADBILL": "红宽嘴鸟",
    "RED BREASTED MERGANSER": "红胸秋沙鸭", "RED FACED CORMORANT": "红脸鸬鹚", "RED FACED WARBLER": "红脸森莺",
    "RED FODY": "红福迪雀", "RED HEADED DUCK": "红头潜鸭", "RED HEADED WOODPECKER": "红头啄木鸟",
    "RED HONEY CREEPER": "红旋蜜雀", "RED KNOT": "red knot",
    "RED LEGGED HONEYCREEPER": "红腿旋蜜雀",
    "RED NAPED TROGON": "红枕咬鹃", "RED SHOULDERED HAWK": "红肩鹰",
    "RED TAILED HAWK": "红尾𫛭", "RED TAILED THRUSH": "红尾鸫", "RED WINGED BLACKBIRD": "红翅黑鹂",
    "RED WISKERED BULBUL": "红耳鹎","RED BEARDED BEE EATER": "赤须夜蜂虎",
    "REGENT BOWERBIRD": "黄头园丁鸟", "RING-NECKED PHEASANT": "环颈雉", "ROADRUNNER": "走鹃",
    "ROBIN": "知更鸟", "ROCK DOVE": "原鸽", "ROSE BREASTED COCKATOO": "玫瑰胸凤头鹦鹉",
    "ROSE BREASTED GROSBEAK": "玫瑰胸蜡嘴雀",
    "ROSEATE SPOONBILL": "玫瑰琵鹭","RED BILLED TROPICBIRD": "红嘴鹲",
    "ROSY FACED LOVEBIRD": "桃脸情侣鹦鹉","RED BROWED FINCH": "红眉火尾雀",
    "ROUGH LEG BUZZARD": "毛脚𫛭", "ROYAL FLYCATCHER": "皇霸鹟", "RUBY CROWNED KINGLET": "红冠戴菊",
    "RUBY THROATED HUMMINGBIRD": "红喉北蜂鸟", "RUDY KINGFISHER": "鲁迪翡翠",
    "RUFOUS KINGFISHER": "棕背翡翠", "RUFOUS TAILED JACAMAR": "棕尾鹟鴷",
    "RUFOUS TREPE": "棕树鹊", "RUFUOS MOTMOT": "棕翠鴗",
    # S
    "SADDLE BILLED STORK": "鞍嘴鹳", "SAFFRON FINCH": "藏红花雀", "SAMATRAN THRUSH": "苏门答腊鸫",
    "SAND MARTIN": "沙燕", "SANDHILL CRANE": "沙丘鹤", "SATYR TRAGOPAN": "角雉",
    "SAYS PHOEBE": "say 菲比霸鹟",
    "SCARLET CROWNED FRUIT DOVE": "红冠果鸠", "SCARLET FACED LIOCICHLA": "scarlet 薮鹛",
    "SCARLET IBIS": "美洲红鹮", "SCARLET MACAW": "绯红金刚鹦鹉", "SCARLET TANAGER": "猩红丽唐纳雀",
    "SHOEBILL": "鲸头鹳", "SHORT BILLED DOWITCHER": "短嘴半蹼鹬", "SMITHS LONGSPUR": "史氏铁爪鹀",
    "SNOW GOOSE": "雪雁", "SNOWY EGRET": "雪鹭", "SNOWY OWL": "雪鸮",
    "SNOWY PLOVER": "雪鸻","STRIATED CARACARA": "纹卡拉鹰",
    "SORA": "北美田鸡", "SPANGLED COTINGA": "辉伞鸟", "SPLENDID FAIRYWREN": "壮丽细尾鹩莺",
    "SPLENDID WREN": "壮丽鹪鹩",
    "SPOON BILED SANDPIPER": "勺嘴鹬", "SPOTTED CATBIRD": "斑猫鸟", "SPOTTED WHISTLING DUCK": "斑啸鸭",
    "SQUIACCO HERON": "池鹭",
    "SRI LANKA BLUE MAGPIE": "斯里兰卡蓝鹊", "STEAMER DUCK": "船鸭", "STORK BILLED KINGFISHER": "鹳嘴翡翠",
    "STRAWBERRY FINCH": "红梅花雀", "STRIPED OWL": "条纹鸮",
    "STRIPPED MANAKIN": "纹头侏儒鸟", "STRIPPED SWALLOW": "斑腰燕",
    "SUNBITTERN": "日鳽",
    "SUPERB STARLING": "栗头丽椋鸟", "SURF SCOTER": "surf scoter",
    "SWINHOES PHEASANT": "蓝鹇",
    # T
    "TAILORBIRD": "缝叶莺",
    "TAIWAN MAGPIE": "台湾蓝鹊", "TAKAHE": "南岛秧鸡", "TASMANIAN HEN": "塔斯马尼亚水鸡",
    "TAWNY FROGMOUTH": "茶色蟆口鸱",
    "TEAL DUCK": "绿翅鸭", "TIT MOUSE": "山雀", "TOUCHAN": "巨嘴鸟",
    "TOWNSENDS WARBLER": "汤氏森莺", "TREE SWALLOW": "双色树燕", "TRICOLORED BLACKBIRD": "三色黑鹂",
    "TROPICAL KINGBIRD": "热带王霸鹟", "TRUMPETER SWAN": "吹号天鹅", "TRUMPTER SWAN": "吹号天鹅",
    "TURKEY VULTURE": "红头美洲鹫", "TURQUOISE MOTMOT": "绿眉翠鴗",
    # U
    "UMBRELLA BIRD": "伞鸟",
    # V
    "VARIED THRUSH": "杂色鸫",
    "VEERY": "veery",
    "VENEZUELIAN TROUPIAL": "委内瑞拉拟黄鹂", "VENEZUELAN TROPIAL": "拟黄鹂",
    "VERDIN": "verdin",
    "VERMILION FLYCATCHER": "朱红霸鹟", "VERMILION FLYCATHER": "朱红霸鹟",
    "VICTORIA CROWNED PIGEON": "维多利亚冠鸠",
    "VIOLET BACKED STARLING": "violet 背椋鸟",
    "VIOLET GREEN SWALLOW": "绿紫树燕", "VIOLET TURACO": "紫蕉鹃", "VULTURINE GUINEAFOWL": "鹫珠鸡",
    # W
    "WALL CREAPER": "红翅旋壁雀", "WATTLED CURASSOW": "肉垂凤冠雉", "WATTLED LAPWING": "肉垂麦鸡",
    "WHIMBREL": "中杓鹬", "WHITE BREASTED WATERHEN": "白胸苦恶鸟", "WHITE BROWED CRAKE": "白眉田鸡",
    "WHITE CHEEKED TURACO": "白颊蕉鹃", "WHITE CRESTED HORNBILL": "白冠犀鸟",
    "WHITE EARED HUMMINGBIRD": "白耳蜂鸟",
    "WHITE NECKED RAVEN": "白颈渡鸦", "WHITE TAILED TROPIC": "白尾鹲",
    "WHITE THROATED BEE EATER": "白喉蜂虎",
    "WILD TURKEY": "野生火鸡", "WILLOW PTARMIGAN": "柳雷鸟",
    "WILSONS BIRD OF PARADISE": "威氏极乐鸟", "WOOD DUCK": "林鸳鸯", "WOOD THRUSH": "林鸫",
    "WRENTIT": "wrentit",
    # Y
    "YELLOW BELLIED FLOWERPECKER": "黄腹啄花鸟", "YELLOW CACIQUE": "黄酋长鹂",
    "YELLOW HEADED BLACKBIRD": "黄头黑鹂",
    # Z
    "ZEBRA DOVE": "斑姬地鸠"
}

@lru_cache(maxsize=1000)
def translate_bird_name(name):
    """
    加强版翻译函数：自动处理空格、下划线、大小写和序号前缀
    使用 lru_cache 缓存结果，提升重复查询性能
    """
    # 1. 基础清理：去除首尾空格
    name = name.strip()
    
    # 2. 如果名字里带点（如 001.Black_footed_Albatross），只取后面部分
    if '.' in name:
        name = name.split('.')[-1].strip()

    # 3. 准备几个变体进行匹配
    variants = [
        name,
        name.replace(' ', '_'),
        name.replace('_', ' ')
    ]

    # 4. 尝试在两个字典中查找（支持大小写模糊）
    dicts_to_search = [VISION_BIRD_TRANSLATOR, BIRD_TRANSLATOR]
    
    for bird_dict in dicts_to_search:
        for v in variants:
            # 直接匹配
            if v in bird_dict:
                return bird_dict[v]
            # 忽略大小写匹配
            for k, v_cn in bird_dict.items():
                if k.lower() == v.lower():
                    return v_cn

    # 5. 如果实在找不到，把下划线转成空格，看起来至少像标准的英文名
    return name.replace('_', ' ').title()


# ================= 2. 功能函数 =================

# 相似物种警告字典
SIMILAR_SPECIES = {
    "柳莺": ["黄眉柳莺", "黄腰柳莺", "极北柳莺", "双斑绿柳莺", "灰脚柳莺"],
    "山雀": ["大山雀", "远东山雀", "沼泽山雀", "煤山雀", "褐头山雀"],
    "鸫": ["乌鸫", "白腹鸫", "斑鸫", "红尾斑鸫", "白眉歌鸫"],
    "鹀": ["小鹀", "灰头鹀", "黄喉鹀", "栗耳鹀", "三道眉草鹀"],
}

def get_similarity_warning(pred_class, topk_results=None):
    """
    如果预测结果与 Top-K 中的其他物种相似，给出警告提示
    """
    if not topk_results or len(topk_results) < 2:
        return None
    
    # 检查前 3 个预测
    for group_name, species_list in SIMILAR_SPECIES.items():
        # 统计有多少个预测属于这个相似组
        similar_in_topk = []
        for result in topk_results[:3]:
            cn_name = result['name_cn']
            # 检查中文名是否包含组名或是组内物种
            if group_name in cn_name or cn_name in species_list:
                similar_in_topk.append(cn_name)
        
        # 如果有 2 个或以上相似物种
        if len(similar_in_topk) >= 2:
            return f"⚠️ 注意：检测到多个相似的{group_name}种类（{', '.join(similar_in_topk)}），建议结合其他特征判断"
    
    return None


def generate_spectrogram_base64(audio_path):
    import warnings
    try:
        # 1. 优雅屏蔽底层的读取警告（解决 PySoundFile 报错），固定读取最多6秒
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # 移除 backend 参数，让 librosa 自动处理降级
            y, sr = librosa.load(audio_path, duration=6, sr=22050)
            
        # 2. 核心修复：防止短音频被拉伸成马赛克！
        # 如果音频不足 3 秒，在末尾补充静音，保证时间轴比例正常，声纹不会变形
        min_length = int(3.0 * sr)
        if len(y) < min_length:
            y = librosa.util.fix_length(y, size=min_length)
            
        # 3. 信号预加重：专门增强鸟叫的高频穿透力
        y = librosa.effects.preemphasis(y, coef=0.97)
        
        # 4. 专业算法：使用 STFT（短时傅里叶变换）构建线性频率谱
        # 放弃 melspectrogram，改用线性谱，让人眼能看清鸟类的平行谐波！
        n_fft = 2048
        hop_length = 256
        D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, window='hann')
        
        # 将幅度转换为分贝 (dB)，设置 top_db=80 使画面具备极高对比度
        S_dB = librosa.amplitude_to_db(np.abs(D), ref=np.max, top_db=40)
        
        # 5. 绘图参数设置
        plt.figure(figsize=(10, 8), dpi=150) # 提高分辨率
        librosa.display.specshow(
            S_dB, 
            sr=sr, 
            hop_length=hop_length,
            x_axis='time', 
            y_axis='linear',  # ⚠️ 强制使用线性频率
            cmap='magma'      # ⚠️ 更换专业声学配色（黑底-紫-橘-亮黄）
        )
        
        # 6. 频率裁剪（声纹灵魂所在）：
        plt.ylim(200, 3800)
        
        # 移除坐标轴和多余的边距，让画面完全填满前端的 UI 圆角容器
        plt.axis('off')
        plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0, wspace=0)
        plt.margins(0)
        
        # 导出为高品质透明抗锯齿图片
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', transparent=True, bbox_inches='tight', pad_inches=0, dpi=300)
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return "data:image/png;base64," + img_str
        
    except Exception as e:
        print(f"画图失败：{e}")
        return ""

def ask_deepseek_about_bird(bird_name):
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
            return f"（雀灵暂时无法回答: {response.status_code}）"
            
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"[雀灵] 网络请求异常: {e}")
        return "（雀灵网络连接错误）"


# ================= 3. 加载模型 =================
print("🎵 正在加载声纹模型...")
audio_predictor = None
try:
    pymodel_path = os.path.join(current_dir, 'pymodel')
    sys.path.append(pymodel_path)
    from macls.predict import MAClsPredictor
    audio_configs = os.path.join(pymodel_path, 'configs', 'cam++.yml')
    audio_model_path = os.path.join(pymodel_path, 'models', 'model.pth')
    
    original_cwd = os.getcwd()
    os.chdir(pymodel_path)
    
    # 尝试加载声纹模型
    try:
        audio_predictor = MAClsPredictor(configs=audio_configs, model_path=audio_model_path, use_gpu=False)
        print("✅ 声纹模型就绪！")
    except RuntimeError as e:
        if "size mismatch" in str(e):
            print(f"⚠️  警告：配置文件参数与模型权重不匹配")
            print(f"   错误信息：{e}")
            print(f"💡 建议：保持 num_mel_bins=80 以兼容现有模型，或重新训练模型使用新参数")
            print(f"   已降级到默认配置继续运行...")
            # 尝试使用原始配置加载
            import yaml
            with open(audio_configs, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 临时修改配置为兼容值
            if 'preprocess_conf' in config and 'method_args' in config['preprocess_conf']:
                config['preprocess_conf']['method_args']['num_mel_bins'] = 80
            
            # 保存临时配置
            temp_config = os.path.join(pymodel_path, 'temp_config.yml')
            with open(temp_config, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            
            try:
                audio_predictor = MAClsPredictor(configs=temp_config, model_path=audio_model_path, use_gpu=False)
                print("✅ 已使用兼容配置加载声纹模型 (num_mel_bins=80)")
            finally:
                if os.path.exists(temp_config):
                    os.remove(temp_config)
        else:
            raise
    
    os.chdir(original_cwd)
except Exception as e:
    print(f"❌ 声纹模型加载失败：{e}")
    audio_predictor = None

print("👁️ 正在加载视觉模型...")
vision_model = None
vision_classes = []
vision_transform = None
try:
    class_path = os.path.join(current_dir, 'bird_classes.txt')
    if os.path.exists(class_path):
        with open(class_path, 'r', encoding='utf-8') as f:
            vision_classes = [line.strip() for line in f.readlines()]
            
        # ⚠️ 核心升级：从 resnet18 换成 resnet50！
        vision_model = models.resnet50(weights=None)
        num_ftrs = vision_model.fc.in_features
        vision_model.fc = nn.Linear(num_ftrs, len(vision_classes))
        
        # ⚠️ 核心升级：读取最新的巅峰模型权重
        model_path = os.path.join(current_dir, 'best_bird_model.pth')
        if os.path.exists(model_path):
            vision_model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            vision_model.eval()
            
            # ⚠️ 核心升级：与 4090 训练时完全一致的预处理流程
            vision_transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            print(f"✅ 视觉大模型就绪！V8 引擎已启动，共支持识别 {len(vision_classes)} 种鸟类。")
        else:
            print("❌ 找不到 best_bird_model.pth，视觉功能无法使用")
    else:
        print("❌ 找不到 bird_classes.txt")
except Exception as e:
    print(f"❌ 视觉模型加载失败: {e}")

# ================= 4. 接口定义 =================

# --- 接口 A: 听音识鸟
@app.route('/predict_audio', methods=['POST'])
def predict_audio():
    if 'file' not in request.files: 
        return jsonify({'code': 400, 'msg': '无文件'}), 400
    
    if 'audio_predictor' not in globals() or audio_predictor is None:
        return jsonify({'code': 500, 'msg': '声纹模型未加载'}), 500
    
    file = request.files['file']
    save_path = os.path.join(current_dir, 'temp_audio.wav')
    file.save(save_path)
    
    try:
        label, score = audio_predictor.predict(save_path)
        cn_name = translate_bird_name(label)
        score_float = float(score)
        
        print(f"[声纹识别] 识别结果: {cn_name} (置信度: {score_float:.2%})")
        
        if score_float < 0.4:
            cn_name = "未知"
            ai_desc = "哎呀，雀灵没听出来这是什么鸟呢🤔\n\n建议：\n• 找个安静的环境重新录制\n• 尽量靠近鸟类，录制清晰的叫声\n• 避免风声或其他噪音干扰"
            confidence = 'very_low'
        elif score_float < 0.6:
            ai_desc = ask_deepseek_about_bird(cn_name)
            confidence = 'low'
        else:
            ai_desc = ask_deepseek_about_bird(cn_name)
            confidence = 'high'
        
        spectrogram_base64 = generate_spectrogram_base64(save_path)
        
        return jsonify({
            'code': 200,
            'msg': '识别成功',
            'data': {
                'name': cn_name,
                'score': score_float,
                'type': 'audio',
                'desc': ai_desc,
                'voiceprint': spectrogram_base64,
                'confidence': confidence
            }
        })
    except Exception as e:
        print(f"[声纹识别] 处理异常: {e}")
        return jsonify({'code': 500, 'msg': f'识别失败: {str(e)}'}), 500
    finally:
        if os.path.exists(save_path):
            os.remove(save_path)

# --- 接口 B: 拍照识鸟 ---
@app.route('/predict_image', methods=['POST'])
def predict_image():
    if 'file' not in request.files: 
        return jsonify({'code': 400, 'msg': '无图片'}), 400
    
    if vision_model is None or vision_transform is None:
        return jsonify({'code': 500, 'msg': '视觉模型未加载'}), 500
    
    file = request.files['file']
    print(f"[图像识别] 正在分析图片: {file.filename}")
    
    try:
        image = Image.open(file.stream).convert('RGB')
            
        # 自动对比度、亮度、锐度增强
        from PIL import ImageEnhance
        image = ImageEnhance.Contrast(image).enhance(1.2)
        image = ImageEnhance.Brightness(image).enhance(1.1)
        image = ImageEnhance.Sharpness(image).enhance(1.3)
            
        # ==================== 优化：多尺度 TTA ====================
        # 多尺度测试（256x320）
        scales = [224, 256, 288]
        all_outputs = []
            
        for scale in scales:
            transform_scale = transforms.Compose([
                transforms.Resize(scale),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            img_scaled = transform_scale(image).unsqueeze(0)
                
            with torch.no_grad():
                outputs = vision_model(img_scaled)
                all_outputs.append(outputs)
                    
                # 水平翻转
                img_flipped = torch.flip(img_scaled, dims=[3])
                outputs_flip = vision_model(img_flipped)
                all_outputs.append(outputs_flip)
            
        # 所有尺度和翻转的平均
        outputs = torch.stack(all_outputs).mean(dim=0)
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            
        # 获取最可能的鸟类（Top-1）
        score, index = torch.max(probabilities, 0)
        score_float = score.item()
            
        # 翻译成中文
        raw_name = vision_classes[index.item()]
        clean_name = raw_name.split('.')[-1]
        cn_name = translate_bird_name(clean_name)
            
        print(f"[图像识别] 识别结果：{cn_name} (置信度：{score_float:.2%})")
            
        # 置信度分级
        if score_float < 0.5:
            cn_name = "未知"
            ai_desc = "哎呀，雀灵没认出这是什么鸟呢🤔\n\n建议：\n• 拍摄更清晰的鸟类照片\n• 尽量让鸟占据画面主要位置\n• 避免逆光或光线不足"
            confidence = 'very_low'
        elif score_float < 0.7:
            ai_desc = ask_deepseek_about_bird(cn_name)
            confidence = 'low'
        else:
            ai_desc = ask_deepseek_about_bird(cn_name)
            confidence = 'high'
        
        return jsonify({
            'code': 200, 
            'msg': '识别成功',
            'data': {
                'name': cn_name,
                'score': score_float,
                'type': 'visual',
                'desc': ai_desc,
                'confidence': confidence
            }
        })
    except Exception as e:
        print(f"[图像识别] 处理异常: {e}")
        return jsonify({'code': 500, 'msg': f'识别失败: {str(e)}'}), 500

# --- 接口 C: 聊天 ---
@app.route('/chat_about_bird', methods=['POST'])
def chat_about_bird():
    data = request.json
    bird_name = data.get('bird_name', '这种鸟')
    question = data.get('question')

    if not DEEPSEEK_API_KEY: 
        return jsonify({'data': {'answer': '未配置 Key'}})
    
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是雀灵，鸟类专家助手"}, 
                {"role": "user", "content": f"关于{bird_name}：{question}"}
            ]
        }
        res = requests.post(DEEPSEEK_URL, json=payload, headers=headers).json()
        return jsonify({'code': 200, 'data': {'answer': res['choices'][0]['message']['content']}})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500

@app.route('/')
def hello():
    return "Flask 服务正常运行中！"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)