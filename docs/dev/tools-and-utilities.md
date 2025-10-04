# 开发工具和实用脚本

本文档介绍项目中可用的开发工具和实用脚本，帮助提高开发效率。

## 📁 工具目录

所有工具脚本位于 `tools/` 目录下。

```
tools/
├── upload_images_to_r2.py    # R2 图片上传工具
└── README.md                 # 工具使用文档
```

---

## 🖼️ R2 图片上传工具

### 概述

`upload_images_to_r2.py` 是一个命令行工具，用于将本地图片上传到 Cloudflare R2 存储，并获取 CDN URL。

**主要功能**:

- ✅ 上传单个或批量图片
- ✅ 支持递归上传目录（保持目录结构）
- ✅ 自定义 R2 存储路径
- ✅ Dry-run 预览模式
- ✅ 自动生成 CDN URL

### 快速开始

```bash
# 查看帮助
python tools/upload_images_to_r2.py --help

# 上传单个图片
python tools/upload_images_to_r2.py images/character.jpg --key "tiangui/1/characters/玛丽亚.jpg"

# 批量上传目录
python tools/upload_images_to_r2.py images/tiangui/1/ --recursive --folder "tiangui/1"

# 预览上传计划（推荐先使用）
python tools/upload_images_to_r2.py images/ --dry-run --recursive
```

### R2 Key 生成规则

工具会根据不同参数自动生成 R2 key（存储路径）：

| 场景             | 命令示例                          | 本地路径           | R2 Key           |
| ---------------- | --------------------------------- | ------------------ | ---------------- |
| 单文件，无 key   | `upload file.jpg`                 | `images/file.jpg`  | `file.jpg`       |
| 单文件，指定 key | `upload file.jpg --key "a/b.jpg"` | `images/file.jpg`  | `a/b.jpg`        |
| 目录，无 folder  | `upload dir/`                     | `dir/file.jpg`     | `file.jpg`       |
| 目录，有 folder  | `upload dir/ --folder "a"`        | `dir/file.jpg`     | `a/file.jpg`     |
| 递归，无 folder  | `upload dir/ -r`                  | `dir/sub/file.jpg` | `sub/file.jpg`   |
| 递归，有 folder  | `upload dir/ -r -f "a"`           | `dir/sub/file.jpg` | `a/sub/file.jpg` |

### 参数说明

| 参数          | 缩写 | 说明                      | 示例                                      |
| ------------- | ---- | ------------------------- | ----------------------------------------- |
| `path`        | -    | 文件或目录路径（必需）    | `images/char.jpg`                         |
| `--key`       | `-k` | 自定义 R2 key（单文件）   | `--key "tiangui/1/characters/玛丽亚.jpg"` |
| `--folder`    | `-f` | R2 文件夹前缀（目录上传） | `--folder "tiangui/1"`                    |
| `--recursive` | `-r` | 递归上传子目录            | `--recursive`                             |
| `--dry-run`   | `-d` | 预览模式，不实际上传      | `--dry-run`                               |
| `--verbose`   | `-v` | 详细日志输出              | `--verbose`                               |

### 支持的图片格式

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WebP (`.webp`)
- BMP (`.bmp`)
- SVG (`.svg`)

---

## 🎯 使用场景

### 场景 1: 手动上传角色肖像并写入数据库

**背景**: 你有一些外部设计好的角色图片，需要上传到 R2 并写入数据库。

**步骤**:

1. **准备图片文件**

   ```bash
   # 假设图片在本地目录
   images/
   └── tiangui/
       └── 1/
           ├── 玛丽亚.jpg
           └── 胡安.jpg
   ```

2. **上传到 R2（先预览）**

   ```bash
   # 预览上传计划
   python tools/upload_images_to_r2.py \
     images/tiangui/1/ \
     --folder "tiangui/1/characters" \
     --dry-run

   # 输出:
   # [DRY RUN] Would upload: images/tiangui/1/玛丽亚.jpg -> tiangui/1/characters/玛丽亚.jpg (245.3 KB)
   # [DRY RUN] Would upload: images/tiangui/1/胡安.jpg -> tiangui/1/characters/胡安.jpg (198.7 KB)
   ```

3. **确认无误后正式上传**

   ```bash
   python tools/upload_images_to_r2.py \
     images/tiangui/1/ \
     --folder "tiangui/1/characters"

   # 输出:
   # ✅ Success! CDN URL: https://file.ai.telereels.app/tiangui/1/characters/玛丽亚.jpg
   # ✅ Success! CDN URL: https://file.ai.telereels.app/tiangui/1/characters/胡安.jpg
   ```

4. **记录 R2 Key 并写入数据库**

   ```sql
   -- 使用上传时的 R2 key（不含域名）
   UPDATE character_portraits
   SET image_url = 'tiangui/1/characters/玛丽亚.jpg'
   WHERE character_name = '玛丽亚'
     AND drama_name = 'tiangui'
     AND episode_number = 1;

   UPDATE character_portraits
   SET image_url = 'tiangui/1/characters/胡安.jpg'
   WHERE character_name = '胡安'
     AND drama_name = 'tiangui'
     AND episode_number = 1;
   ```

5. **验证**

   访问前端角色列表，API 会自动将 R2 key 转换为完整 CDN URL：

   - 数据库存储: `tiangui/1/characters/玛丽亚.jpg`
   - API 返回: `https://file.ai.telereels.app/tiangui/1/characters/玛丽亚.jpg`

### 场景 2: 批量上传剧集所有素材

**背景**: 新剧集制作完成，需要上传所有角色、道具、场景图片。

**步骤**:

1. **组织本地文件结构**

   ```bash
   images/
   └── tiangui/
       └── 2/
           ├── characters/
           │   ├── 玛丽亚.jpg
           │   └── 胡安.jpg
           ├── props/
           │   ├── 十字架.jpg
           │   └── 圣经.jpg
           └── scenes/
               ├── scene_教堂.jpg
               └── scene_广场.jpg
   ```

2. **递归上传整个剧集目录**

   ```bash
   # 保持目录结构上传
   python tools/upload_images_to_r2.py \
     images/tiangui/2/ \
     --recursive \
     --folder "tiangui/2"

   # 上传结果:
   # tiangui/2/characters/玛丽亚.jpg
   # tiangui/2/characters/胡安.jpg
   # tiangui/2/props/十字架.jpg
   # tiangui/2/props/圣经.jpg
   # tiangui/2/scenes/scene_教堂.jpg
   # tiangui/2/scenes/scene_广场.jpg
   ```

3. **批量写入数据库**

   使用 Python 脚本批量处理：

   ```python
   from utils.database import Database
   from utils.config import DB_CONFIG

   db = Database(DB_CONFIG)

   # 角色图片
   characters = [
       ("玛丽亚", "tiangui/2/characters/玛丽亚.jpg"),
       ("胡安", "tiangui/2/characters/胡安.jpg"),
   ]

   for name, key in characters:
       db.execute(
           "UPDATE character_portraits SET image_url = %s "
           "WHERE character_name = %s AND drama_name = 'tiangui' AND episode_number = 2",
           (key, name)
       )

   # 道具图片
   props = [
       ("十字架", "tiangui/2/props/十字架.jpg"),
       ("圣经", "tiangui/2/props/圣经.jpg"),
   ]

   for name, key in props:
       db.execute(
           "UPDATE key_prop_definitions SET image_url = %s "
           "WHERE prop_name = %s AND drama_name = 'tiangui' AND episode_number = 2",
           (key, name)
       )
   ```

### 场景 3: 替换已有图片

**背景**: 某个角色的肖像需要重新生成，要用新图片替换旧图片。

**步骤**:

1. **准备新图片**

   ```bash
   images/new/玛丽亚_v2.jpg
   ```

2. **上传到相同的 R2 key（会覆盖旧图片）**

   ```bash
   python tools/upload_images_to_r2.py \
     images/new/玛丽亚_v2.jpg \
     --key "tiangui/1/characters/玛丽亚.jpg"

   # 输出:
   # ✅ Success! CDN URL: https://file.ai.telereels.app/tiangui/1/characters/玛丽亚.jpg
   ```

3. **无需更新数据库**

   因为 R2 key 相同，数据库中的记录无需修改，前端会自动显示新图片。

**注意**: R2 有 CDN 缓存，可能需要等待几分钟或清除缓存才能看到新图片。

### 场景 4: 迁移旧数据到 R2

**背景**: 项目早期使用临时 URL 存储图片，现在需要迁移到 R2。

**步骤**:

1. **查询数据库中的旧 URL**

   ```sql
   SELECT id, character_name, image_url
   FROM character_portraits
   WHERE image_url LIKE 'http%'
     AND drama_name = 'tiangui'
     AND episode_number = 1;
   ```

2. **下载旧图片到本地**

   ```python
   import requests
   from pathlib import Path

   # 下载图片
   for row in results:
       char_id = row['id']
       char_name = row['character_name']
       old_url = row['image_url']

       # 下载
       response = requests.get(old_url)
       output_path = f"images/tiangui/1/{char_name}.jpg"
       Path(output_path).parent.mkdir(parents=True, exist_ok=True)

       with open(output_path, 'wb') as f:
           f.write(response.content)
   ```

3. **上传到 R2**

   ```bash
   python tools/upload_images_to_r2.py \
     images/tiangui/1/ \
     --folder "tiangui/1/characters"
   ```

4. **更新数据库为 R2 key**
   ```sql
   UPDATE character_portraits
   SET image_url = 'tiangui/1/characters/' || character_name || '.jpg'
   WHERE drama_name = 'tiangui'
     AND episode_number = 1
     AND image_url LIKE 'http%';
   ```

---

## 💡 最佳实践

### 1. 使用 Dry-run 预览

上传前始终先用 `--dry-run` 预览：

```bash
# 先预览
python tools/upload_images_to_r2.py images/ --dry-run --recursive

# 确认无误后正式上传
python tools/upload_images_to_r2.py images/ --recursive
```

### 2. 规范化文件命名

建议使用统一的文件命名规范：

```
✅ 推荐:
- 玛丽亚.jpg
- 十字架.jpg
- scene_教堂.jpg

❌ 不推荐:
- 玛丽亚 (1).jpg    # 包含空格和括号
- image_001.jpg     # 不具描述性
- IMG_20250104.jpg  # 无意义的命名
```

### 3. 保持目录结构清晰

按类型和剧集组织文件：

```
images/
└── {剧本名}/
    └── {集数}/
        ├── characters/    # 角色肖像
        ├── props/         # 道具图片
        └── scenes/        # 场景关键帧
```

### 4. 数据库只存储 R2 Key

**正确做法** ✅:

```sql
-- 数据库存储 R2 key（不含域名）
image_url = 'tiangui/1/characters/玛丽亚.jpg'
```

**错误做法** ❌:

```sql
-- 不要存储完整 URL
image_url = 'https://file.ai.telereels.app/tiangui/1/characters/玛丽亚.jpg'
```

**原因**:

- 便于迁移 CDN（只需修改配置文件）
- 节省数据库空间
- API 会自动拼接完整 URL

### 5. 批量操作使用脚本

对于大量文件，编写 Python 脚本自动化处理：

```python
#!/usr/bin/env python3
"""批量上传并更新数据库"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.upload import R2Uploader
from utils.database import Database
from utils.config import DB_CONFIG

def batch_upload_and_update(drama_name: str, episode: int, local_dir: str):
    """批量上传图片并更新数据库"""

    uploader = R2Uploader()
    db = Database(DB_CONFIG)

    # 上传所有图片
    for img_file in Path(local_dir).glob("*.jpg"):
        r2_key = f"{drama_name}/{episode}/characters/{img_file.name}"
        cdn_url = uploader.upload_file(str(img_file), r2_key)

        char_name = img_file.stem  # 文件名去掉扩展名

        # 更新数据库
        db.execute(
            "UPDATE character_portraits SET image_url = %s "
            "WHERE character_name = %s AND drama_name = %s AND episode_number = %s",
            (r2_key, char_name, drama_name, episode)
        )

        print(f"✅ {char_name}: {cdn_url}")

if __name__ == "__main__":
    batch_upload_and_update("tiangui", 1, "images/tiangui/1/characters/")
```

---

## 🔧 故障排查

### 问题 1: 上传失败 "Failed to upload to R2"

**可能原因**:

- R2 配置错误
- 网络连接问题
- 文件权限问题

**解决方法**:

1. 检查 `utils/config.py` 中的 R2 配置
2. 使用 `--verbose` 查看详细错误
3. 确认文件可读取

### 问题 2: 中文文件名乱码

**可能原因**:

- 终端编码问题
- 文件系统编码问题

**解决方法**:

```bash
# 设置环境变量
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 然后运行脚本
python tools/upload_images_to_r2.py ...
```

### 问题 3: CDN 显示旧图片

**原因**: CDN 缓存未更新

**解决方法**:

1. 等待 CDN 缓存过期（通常 5-15 分钟）
2. 或使用不同的 R2 key 上传新图片
3. 或联系 CDN 提供商清除缓存

---

## 📚 相关文档

- **工具脚本源码**: `tools/upload_images_to_r2.py`
- **R2 上传工具类**: `utils/upload.py`
- **R2 配置**: `utils/config.py` 中的 `R2_CONFIG`
- [前端 API 集成](../frontend/api-integration.md)
- [API 文档概览](../api/README.md)
