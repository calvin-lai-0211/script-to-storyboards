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
