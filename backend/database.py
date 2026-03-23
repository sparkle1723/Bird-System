from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库文件将生成在当前目录下，名为 birdwatcher.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./birdwatcher.db"

# 创建数据库引擎
# check_same_thread=False 是 SQLite 必须的配置，允许在不同线程中使用连接
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建所有模型的基类
Base = declarative_base()


# 依赖项：获取数据库会话
# 这种写法可以确保每次请求结束后数据库连接都会被正确关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()