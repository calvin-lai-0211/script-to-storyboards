DB_CONFIG = {
    'host': 'ai-database.cluster-cbkc4usgshmy.us-east-1.rds.amazonaws.com',
    'database': 'script_to_storyboards',
    'user': 'postgres',
    'password': '2VscIi3KhVx2J5uNWECr47SLQDR9fl3EH4JYk8LS5y2WucjYeN',
    'connect_timeout': 10,  # Connection timeout in seconds
    'options': '-c statement_timeout=30000'  # Query timeout: 30 seconds
}

YIZHAN_API_CONFIG = {
    "deepseek_api_key": "sk-MKLACC640iS1xVNwBb77Ae4251114d4f9aBd31Da26B4298e",
    "gemini_api_key": "sk-8kiZAPVRybw7DHsmA757A8A2B5C84fC68f8dD80dF84b28F6",
    "default_api_key": "sk-xFi3kt8xeS5BiE2hC0169f1aD9E04eB195D958599840825a",
    "base_url": "https://hk.yi-zhan.top/v1",
    "image_model": "gpt-4o-image",
    "default_model": "deepseek-reasoner"
}

RUNNINGHUB_API_CONFIG = {
    "api_key": "4724f31ca1194012a3cf814bb77b2c4f",
    "host": "www.runninghub.cn",
    "base_url": "https://www.runninghub.cn",
    "upload_url": "https://www.runninghub.cn/task/openapi/upload",
    "run_url": "https://www.runninghub.cn/task/openapi/ai-app/run",
    "status_url": "https://www.runninghub.cn/task/openapi/ai-app/task-status",
    "outputs_url": "https://www.runninghub.cn/task/openapi/ai-app/task-outputs",
    "webapp_id": 1935285737619116034,  # 新的webapp_id
    "image_node_id": "2",             # 图片节点ID
    "model_node_id": "6",             # 模型节点ID（统一使用节点6）
    "output_node_id": "9",            # 输出节点ID
    "scale_node_id": "145",           # 缩放节点ID
    "default_scale_to_length": 512,   # 默认缩放边长度
    "default_model": "flux-kontext-pro",
    "default_aspect_ratio": "match_input_image",
    "default_seed": "1234",           # 随机种子
    "default_guidance_scale": "3.5",  # 引导强度
    "control_after_generate": "fixed", # 生成后控制
    "safety_tolerance": "6",          # 安全容忍度
    "makoto_shinkai_prompt": "Maintain the facial similarity of the characters,the color and structure of the photo and keep the same age,turn this image into a Makoto Shinkai style,a Japanese anime aesthetics,remove text at the bottom and the logo on the right top; all races must be East Asians with Light skin tone",
    "evil_mother_in_law_prompt": "turn this woman in to 55 year old,(add wrinkles and nasolabial folds to her face:1.4), (maintain this woman's hair color unchanged:2.0), (with evil and fierce expression:1.2)",
    "upload_timeout": 60,            # 上传超时时间（秒）
    "generate_timeout": 300,         # 生成超时时间（秒）
    "poll_interval": 5,              # 轮询间隔（秒）
}

# Image generation model configuration
T2I_MODEL_CONFIG = {
    "jimeng_t2i_rh": {
        "api_key": "your_jimeng_api_key_here",
        "base_url": "https://jimeng.dev.metastead.com"
    },
     "qwen_image_t2i_rh": {
        "api_key": "your_qwen_api_key_here",
        "base_url": "https://qwen-image.dev.metastead.com"
    }
}

# Concurrency settings
MAX_CONCURRENT_THREADS = 5

# Cloudflare R2 Storage Configuration
R2_CONFIG = {
    "region_name": "auto",
    "endpoint_url": "https://17505f788c7c54ec3ab4ddc52da5c140.r2.cloudflarestorage.com",
    "access_key_id": "398a4f0dd4a4b760eef50ce18ae69d93",
    "secret_access_key": "dc322d84ca5781b9f19768d7c42b062739057980c934fc7a60df6cff55127d80",
    "bucket_name": "ai-file",
    "cdn_base_url": "https://file.ai.telereels.app",
    "default_folder": "drama/upload"  # Default upload folder
}

# Google OAuth Configuration
import os
GOOGLE_OAUTH_CONFIG = {
    "client_id": os.getenv("GOOGLE_CLIENT_ID", "853108816347-dloqr123n98ranv7k3jn76puirchqdvk.apps.googleusercontent.com"),
    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "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"),
    "redirect_path": "/api/user/google/callback",  # 相对路径，域名在代码中拼接
    "auth_url": "https://accounts.google.com/o/oauth2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "user_info_url": "https://www.googleapis.com/oauth2/v3/userinfo"
}

# API Base URL Configuration
# 优先级: 环境变量 > config 配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# Redis Configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": 0,
    "decode_responses": True,
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "retry_on_timeout": True,
    "max_connections": 50
}

# Session Configuration
SESSION_CONFIG = {
    "timeout": 2592000,  # 30 days in seconds
    "key_prefix": "st_session:"
}

# Background Task Processor Configuration
TASK_PROCESSOR_CONFIG = {
    "poll_interval": 20,        # 轮询间隔（秒）
    "task_timeout": 30,        # 任务超时时间（分钟）
    "max_pending_batch": 5,    # 每次最多处理的 PENDING 任务数
    "max_active_batch": 50,    # 每次最多查询的 ACTIVE 任务数
    "max_consecutive_errors": 10  # 连续错误阈值
}
