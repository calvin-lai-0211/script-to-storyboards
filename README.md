# Script-to-Storyboards: 剧本到分镜自动化流程

本项目是一个自动化的内容创作管线，旨在将文本剧本转换为包含角色肖像、场景关键帧和详细分镜的视觉故事板。通过结合大型语言模型（LLM）和图像生成模型，该项目实现了从剧本分析、资源生成到最终分镜输出的全流程自动化。

## 项目特性

-   **自动化剧本分析**: 自动从剧本中提取剧集、角色、场景等关键信息。
-   **LLM驱动的分镜生成**: 利用大型语言模型（如Gemini 2.5 Pro）将剧本转化为结构化的、符合导演风格（例如：亚利桑德罗·冈萨雷斯·伊纳里图）的JSON格式分镜脚本。
-   **角色肖像自动生成**:
    1.  分析剧本，为每个角色生成高质量的、符合其人设的图像Prompt。
    2.  调用文生图模型（如Qwen Image, Jimeng）生成角色上半身肖像。
-   **场景关键帧自动生成**:
    1.  从分镜脚本中提取所有独特的场景。
    2.  为每个场景生成符合其氛围和设定的高质量图像Prompt。
    3.  调用文生图模型生成每个场景的关键帧图片。
-   **数据库驱动**: 使用PostgreSQL数据库来存储和管理剧本、分镜、角色和场景数据，确保数据的一致性和可追溯性。
-   **模块化设计**: 项目代码结构清晰，分为数据模型（models）、处理流程（procedure）、工具函数（utils）和演示脚本（demo），易于扩展和维护。

## 项目结构

```
.
├── demo_create_character_portraits.py  # 演示：生成角色肖像Prompt并存入数据库
├── demo_create_scene_definitions.py    # 演示：生成场景定义Prompt并存入数据库
├── demo_make_storyboards_from_scripts.py # 演示：从txt剧本文件生成分镜脚本并存入数据库
├── from_script_to_database.py          # 工具：将txt格式的剧本导入数据库
├── images/                               # 存放生成的图片资源
│   └── 天归（「西语版」）/
│       └── 1/
│           ├── Don Delacruz.jpg        # 角色肖像
│           └── scenes/
│               └── scene_药店.jpg    # 场景关键帧
├── models/                               # AI模型封装
│   ├── jimeng_t2i_RH.py                  # Jimeng文生图模型
│   ├── qwen_image_t2i_RH.py              # Qwen文生图模型
│   └── yizhan_llm.py                     # 易知独角兽LLM封装
├── procedure/                            # 核心处理流程脚本
│   ├── generate_character_portraits.py   # 生成角色肖像Prompt
│   ├── generate_scene_definitions.py     # 生成场景定义Prompt
│   ├── generate_scene_images.py          # 使用Prompt生成场景图片
│   ├── make_portraits_from_t2i.py        # 使用Prompt生成角色肖像图片
│   └── make_storyboards.py               # 从剧本生成分镜脚本
├── requirements.txt                      # 项目依赖
├── scripts/                              # 存放原始剧本文件
│   └── 天归（「西语版」）.txt
└── utils/                                # 工具类
    ├── config.py                         # 数据库等配置信息
    └── database.py                       # 数据库操作封装
```

## 安装指南

1.  **克隆项目**
    ```bash
    git clone <your-repo-url>
    cd script-to-storyboards
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置数据库**
    -   确保您有一个正在运行的PostgreSQL实例。
    -   复制`utils/config.py.template`（如果存在）为`utils/config.py`。
    -   在`utils/config.py`中填写您的数据库连接信息（主机、端口、用户名、密码、数据库名）。

4.  **初始化数据库**
    运行`utils/database.py`脚本来自动创建所需的表结构。
    ```bash
    python utils/database.py
    ```
    该脚本会自动创建`scripts`, `flat_storyboards`, `character_portraits`, 和 `scene_definitions`等表。

## 使用流程

整个流程被设计为按顺序执行的多个步骤。

### 步骤 1: 导入剧本

首先，将您的剧本（.txt格式）放入`scripts/`文件夹中。然后运行`from_script_to_database.py`将其导入数据库。

```bash
python from_script_to_database.py
```
*您可能需要根据实际情况修改此脚本中的剧本文件名和剧集信息。*

### 步骤 2: 生成分镜脚本

运行`demo_make_storyboards_from_scripts.py`来调用LLM分析数据库中的剧本，并生成详细的分镜脚本（JSON格式）存入`flat_storyboards`表。

```bash
python demo_make_storyboards_from_scripts.py
```

### 步骤 3: 生成角色肖像的Prompt

分镜生成后，运行`demo_create_character_portraits.py`来提取所有角色，并为他们生成高质量的图像Prompt，存入`character_portraits`表。

```bash
python demo_create_character_portraits.py
```

### 步骤 4: 生成场景定义的Prompt

同样地，运行`demo_create_scene_definitions.py`来提取所有场景，并为它们生成高质量的图像Prompt，存入`scene_definitions`表。

```bash
python demo_create_scene_definitions.py
```

### 步骤 5: 生成视觉素材（图片）

现在，使用上一步生成的Prompts来实际创建图片。

-   **生成角色肖像**:
    ```bash
    python procedure/make_portraits_from_t2i.py "剧本名" 集数 -m [jimeng|qwen]
    ```
    *示例: `python procedure/make_portraits_from_t2i.py "天归（「西语版」）" 1 -m jimeng`*

-   **生成场景关键帧**:
    ```bash
    python procedure/generate_scene_images.py "剧本名" 集数 -m [jimeng|qwen]
    ```
    *示例: `python procedure/generate_scene_images.py "天归（「西语版」）" 1 -m qwen`*

所有生成的图片将保存在`images/剧本名/集数/`目录下。

## 未来展望

-   [ ] **视频生成**: 集成文生视频模型（如`wan_vace_img2video`），利用分镜中的`video_prompt`直接生成动态视频片段。
-   [ ] **音频集成**: 集成文本转语音（TTS）和音效模型，为每个镜头自动生成对白和音效。
-   [ ] **UI界面**: 开发一个简单的Web界面来可视化整个流程，方便非技术人员使用。

---
*该README由AI辅助生成。*
