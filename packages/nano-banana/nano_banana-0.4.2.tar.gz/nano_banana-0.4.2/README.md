# nano-banana 🍌

基于 Google Gemini 2.5 Flash Image 的 Python 包装器，简单易用的图像生成和分析工具。

## 功能和应用场景

- 🎨 **AI绘画创作**: 从文字描述生成艺术作品、插画、概念图
- 🔄 **图片风格转换**: 将照片转换为卡通、油画、素描等不同风格
- 📸 **产品图片优化**: 为电商、营销生成产品展示图
- 🔍 **智能图片分析**: 识别物体、场景、文字，提供详细描述
- 📚 **教育内容制作**: 生成教学插图、图表、示意图
- 🎮 **游戏素材创作**: 角色设计、场景概念图、UI元素

## 安装

```bash
uv add nano-banana
# 或
pip install nano-banana
```

## 快速开始

### 设置 API 密钥

```bash
export SIMEN_AI_API_KEY="your-api-key"
export SIMEN_BASEURL="https://api.simen.ai/v1"
```

### 典型使用场景

#### 场景1：电商产品图生成
```python
import nano_banana as nb

# 为咖啡店生成产品展示图
result = nb.text_to_image("一杯精美的拿铁咖啡，白色陶瓷杯，木质桌面，温暖灯光，专业产品摄影风格")
if result['success']:
    print(f"产品图URL: {result['urls'][0]}")
```

#### 场景2：头像风格转换
```python
# 将自拍照转换为动漫风格
result = nb.image_to_image("转换成日系动漫风格，保持人物特征", "selfie.jpg")
if result['success']:
    print(f"动漫头像: {result['urls'][0]}")
```

#### 场景3：图片内容分析
```python
# 分析商品图片用于自动标签生成
analysis = nb.analyze("product.jpg", "这个商品的类别、颜色、材质和主要特征是什么？")
print(f"商品信息: {analysis}")
```

## API 接口说明

### 函数接口

#### `text_to_image(prompt: str) -> Dict[str, Any]`
**参数:**
- `prompt` (str): 图片生成描述，支持中英文

**返回值:**
```python
{
    "success": bool,           # 是否成功提取到图片URL
    "urls": List[str],         # 图片URL列表
    "raw_response": str,       # AI原始响应文本
    "message": str            # 状态信息
}
```

#### `image_to_image(prompt: str, reference_images: Union[str, Path, List]) -> Dict[str, Any]`
**参数:**
- `prompt` (str): 图片编辑/转换指令
- `reference_images`: 参考图片，支持本地文件路径、URL或列表

**返回值:** 同 `text_to_image()`

#### `analyze(image: Union[str, Path, List], question: str = "描述图片") -> str`
**参数:**
- `image`: 待分析图片，支持本地文件、URL或多图列表
- `question` (str): 分析问题，默认为"描述图片"

**返回值:** 分析结果文本字符串

### 类接口

```python
from nano_banana import NanoBanana

# 初始化（可选参数，优先使用环境变量）
client = NanoBanana(api_key="your-key", base_url="your-url")

# 调用方法
result = client.text_to_image("prompt")
result = client.image_to_image("prompt", "image.jpg")
analysis = client.analyze("image.jpg", "question")
```

## 真实返回值示例

### 成功生成图片
```python
{
    "success": True,
    "urls": ["https://storage.googleapis.com/generated-image-abc123.png"],
    "raw_response": "我为您生成了一张图片：\n![生成的图片](https://storage.googleapis.com/generated-image-abc123.png)",
    "message": "成功生成图片"
}
```

### 未找到图片URL（但API调用成功）
```python
{
    "success": False,
    "urls": [],
    "raw_response": "抱歉，我无法生成包含版权内容的图片，建议修改描述后重试。",
    "message": "未找到图片URL，请检查响应内容"
}
```

### 图片分析结果
```python
"这张图片显示了一只橙色的短毛猫坐在木质地板上，猫咪有着绿色的眼睛，正专注地看向镜头。背景是温暖的室内环境，光线柔和自然。"
```

## 完整使用示例

### 批量处理图片
```python
import nano_banana as nb

# 批量生成产品图
products = ["红色连衣裙", "蓝色牛仔裤", "白色运动鞋"]
for product in products:
    result = nb.text_to_image(f"{product}，白色背景，专业产品摄影")
    if result['success']:
        print(f"{product}图片: {result['urls'][0]}")
```

### 错误处理
```python
try:
    result = nb.text_to_image("生成图片")
    if not result['success']:
        print(f"生成失败: {result['message']}")
        print(f"AI回复: {result['raw_response']}")
except Exception as e:
    print(f"API调用错误: {e}")
```

