import os
import shutil
import uuid
import uvicorn
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
import database


# 请求体模型
class RecordCreate(BaseModel):
    username: str
    title: str
    content: str = ""


# 用户相关请求体模型
class UserRegister(BaseModel):
    username: str
    password: str
    nickname: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    nickname: str = None
    avatar: str = None


# 1. 初始化数据库表结构
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Bird Watcher Backend")

# 2. 配置静态资源
os.makedirs("uploads/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# 3. 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================
# 4. 上传接口 (图片/声纹)
# ==========================================
@app.post("/upload")
async def upload_file(
        request: Request,
        username: str = Form(...),
        title: str = Form("AI识别记录"),
        content: str = Form(""),
        record_id: int = Form(None),
        file: UploadFile = File(...),
        db: Session = Depends(database.get_db)
):
    # 保存文件
    file_ext = file.filename.split(".")[-1].lower() or "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"uploads/images/{file_name}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 动态生成 URL（从前端请求中获取服务器地址）
    # 支持 localhost、服务器IP、ngrok 等各种环境
    server_host = request.headers.get('host', 'localhost:8000')
    
    # 判断协议：有 ngrok 域名用 https，否则用 http
    scheme = 'https' if 'ngrok' in server_host else 'http'
    
    # ngrok 域名不需要端口，其他情况需要加端口（如果不是标准端口）
    if ':' not in server_host and not server_host.endswith('.ngrok.app'):
        server_host = f"{server_host}:8000"
    
    url = f"{scheme}://{server_host}/static/images/{file_name}"

    # 如果提供了 record_id，则更新现有记录
    if record_id:
        db_record = db.query(models.Record).filter(models.Record.id == record_id).first()
        if db_record:
            # 验证记录所有者
            if db_record.owner_username != username:
                return {"code": 403, "msg": "无权修改此记录"}
            db_record.title = title
            db_record.content = content
            db_record.file_url = url
            db.commit()
            db.refresh(db_record)
            return {"code": 200, "msg": "更新成功", "url": url, "id": record_id}
    
    # 否则创建新记录
    new_record = models.Record(
        title=title,
        content=content,
        file_url=url,
        owner_username=username
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return {"code": 200, "msg": "上传成功", "url": url}


# ==========================================
# 5. 创建记录接口（纯文本，无文件）
# ==========================================
@app.post("/records")
def create_record(
    record: RecordCreate,
    db: Session = Depends(database.get_db)
):
    new_record = models.Record(
        title=record.title,
        content=record.content,
        file_url="",  # 无图片
        owner_username=record.username
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return {"code": 200, "msg": "创建成功", "data": new_record}


# ==========================================
# 6. 获取列表接口
# ==========================================
@app.get("/records")
def get_records(username: str = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Record)

    # 过滤当前用户
    if username:
        query = query.filter(models.Record.owner_username == username)

    records = query.order_by(models.Record.id.desc()).all()

    # 统一返回格式，前端更容易解析
    return {"code": 200, "data": records}


# ==========================================
# 7. 更新记录接口
# ==========================================
@app.put("/records/{record_id}")
def update_record(
    record_id: int,
    record: RecordCreate,
    db: Session = Depends(database.get_db)
):
    db_record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="记录不存在")

    db_record.title = record.title
    db_record.content = record.content
    db.commit()
    db.refresh(db_record)

    return {"code": 200, "msg": "更新成功", "data": db_record}


# ==========================================
# 8. 删除记录接口
# ==========================================
@app.delete("/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(database.get_db)):
    record = db.query(models.Record).filter(models.Record.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 可选：如果需要删除物理文件，可以在这里添加 os.remove(file_path)

    db.delete(record)
    db.commit()

    return {"code": 200, "msg": "删除成功"}


# ==========================================
# 8. 用户注册接口
# ==========================================
@app.post("/auth/register")
def register(user: UserRegister, db: Session = Depends(database.get_db)):
    # 检查用户名是否已存在
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建新用户
    new_user = models.User(
        username=user.username,
        password=user.password,
        nickname=user.nickname or user.username
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "code": 200,
        "msg": "注册成功",
        "data": {
            "id": new_user.id,
            "username": new_user.username,
            "nickname": new_user.nickname,
            "avatar": new_user.avatar,
            "created_at": new_user.created_at
        }
    }


# ==========================================
# 9. 用户登录接口
# ==========================================
@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(database.get_db)):
    # 查找用户
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码（明文比对）
    if user.password != db_user.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return {
        "code": 200,
        "msg": "登录成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "nickname": db_user.nickname,
            "avatar": db_user.avatar,
            "created_at": db_user.created_at
        }
    }


# ==========================================
# 10. 获取用户信息接口
# ==========================================
@app.get("/auth/user/{username}")
def get_user_info(username: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "created_at": user.created_at
        }
    }


# ==========================================
# 11. 更新用户信息接口
# ==========================================
@app.put("/auth/user/{username}")
def update_user_info(
    username: str,
    user_update: UserUpdate,
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    if user_update.nickname is not None:
        user.nickname = user_update.nickname
    if user_update.avatar is not None:
        user.avatar = user_update.avatar

    db.commit()
    db.refresh(user)

    return {
        "code": 200,
        "msg": "更新成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "created_at": user.created_at
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)