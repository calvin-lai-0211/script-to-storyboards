# 工具脚本

本目录包含项目的辅助工具脚本。

## upload_images_to_r2.py

上传本地图片到 Cloudflare R2 存储的命令行工具。

### 功能特性

- 上传单个图片文件
- 批量上传目录中的所有图片
- 递归上传子目录（保持目录结构）
- 自定义 R2 存储路径
- Dry-run 模式（预览上传计划）
- 自动识别图片格式（jpg、png、gif、webp 等）
- 显示上传进度和 CDN URL

### 使用方法

#### 1. 上传单个图片

```bash
# 最简单的方式 - 使用文件名作为 R2 key
python tools/upload_images_to_r2.py images/character.jpg

# 指定自定义 R2 路径
python tools/upload_images_to_r2.py images/character.jpg --key "天归/1/characters/玛丽亚.jpg"
```

#### 2. 批量上传目录

```bash
# 上传目录中所有图片（不含子目录）
python tools/upload_images_to_r2.py images/episode1/

# 上传目录并添加文件夹前缀
python tools/upload_images_to_r2.py images/episode1/ --folder "天归/1/characters"

# 递归上传所有子目录（保持目录结构）
python tools/upload_images_to_r2.py images/ --recursive --folder "天归/1"
```

#### 3. Dry-run 模式（预览）

```bash
# 查看将要上传什么，但不实际上传
python tools/upload_images_to_r2.py images/ --dry-run --recursive
```

### 参数说明

| 参数 | 缩写 | 说明 |
|------|------|------|
| `path` | - | 图片文件或目录路径（必需） |
| `--key` | `-k` | 自定义 R2 key（仅单文件） |
| `--folder` | `-f` | R2 文件夹前缀 |
| `--recursive` | `-r` | 递归上传子目录 |
| `--dry-run` | `-d` | 预览模式，不实际上传 |
| `--verbose` | `-v` | 详细日志输出 |

### 使用示例

```bash
# 上传单个图片
python tools/upload_images_to_r2.py images/天归/1/玛丽亚.jpg --key "天归/1/characters/玛丽亚.jpg"

# 批量上传整个剧集（保持目录结构）
python tools/upload_images_to_r2.py images/天归/1/ --recursive --folder "天归/1"

# 预览上传计划
python tools/upload_images_to_r2.py images/ --dry-run --recursive
```

### 支持的图片格式

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WebP (`.webp`)
- BMP (`.bmp`)
- SVG (`.svg`)

### 注意事项

1. **R2 配置**: 脚本使用 `utils/config.py` 中的 `R2_CONFIG` 配置
2. **CDN URL**: 上传成功后会显示完整的 CDN URL
3. **覆盖**: 相同 key 的文件会被覆盖，请谨慎使用

### 输出示例

```
2025-10-04 14:30:21 - INFO - Found 15 image(s) to upload
--------------------------------------------------------------------------------
2025-10-04 14:30:21 - INFO - Uploading: images/天归/1/玛丽亚.jpg -> 天归/1/characters/玛丽亚.jpg (245.3 KB)
2025-10-04 14:30:23 - INFO - ✅ Success! CDN URL: https://file.ai.telereels.app/天归/1/characters/玛丽亚.jpg
--------------------------------------------------------------------------------
2025-10-04 14:30:45 - INFO - Upload complete: 15 succeeded, 0 failed
2025-10-04 14:30:45 - INFO - CDN Base URL: https://file.ai.telereels.app
```
