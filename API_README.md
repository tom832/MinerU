# MinerU API 服务 v2.0

简化版 MinerU 文档处理 API 服务，专注于核心功能：PDF 和图片处理。

## 功能特性

- **PDF 处理**: 支持 PDF 文档的 OCR 和文本提取，输出 Markdown 格式
- **图片处理**: 支持各种图片格式的 OCR 文本提取
- **同步处理**: 直接返回处理结果，无需轮询任务状态
- **图片返回**: 可选择返回处理过程中提取的图片（base64 编码）
- **Bearer Token 认证**: 安全的 API 访问控制
- **CORS 支持**: 支持跨域请求

## 安装依赖

```bash
# 安装 MinerU 基础依赖
pip install -r requirements.txt

# 安装 API 服务额外依赖
pip install -r api_requirements.txt
```

## 配置与启动

### 1. 设置 Bearer Token（推荐）

创建 `.env` 文件并设置 API Token：

```bash
# 复制示例文件
cp env_example .env

# 编辑 .env 文件，设置你的 API Token
# API_TOKEN=your-custom-secret-token
```

### 2. 启动服务

```bash
./start_api.sh
# 或者直接运行
python api_server.py
```

服务将在 `http://localhost:8766` 启动。

## API 端点

### 1. 根路径
```
GET /
```
返回 API 服务信息和可用端点列表。

### 2. 健康检查
```
GET /health
```
返回服务健康状态。

### 3. 处理 PDF 文件
```
POST /process/pdf
```
**认证**: Bearer Token

**参数:**
- `file`: PDF 文件 (multipart/form-data)
- `return_images`: 是否返回提取的图片文件 (boolean, 可选, 默认 false)

**返回:**
```json
{
  "success": true,
  "markdown_content": "转换后的 Markdown 内容",
  "images": [
    {
      "filename": "image_1.png",
      "content": "base64编码的图片内容",
      "format": "png"
    }
  ],
  "message": "PDF 处理完成"
}
```

### 4. 处理图片文件
```
POST /process/image
```
**认证**: Bearer Token

**参数:**
- `file`: 图片文件 (支持 .jpg, .jpeg, .png, .bmp, .tiff, .webp)
- `return_images`: 是否返回处理后的图片文件 (boolean, 可选, 默认 false)

**返回:**
```json
{
  "success": true,
  "markdown_content": "OCR 识别的文本内容",
  "images": [
    {
      "filename": "processed_image.png",
      "content": "base64编码的处理后图片",
      "format": "png"
    }
  ],
  "message": "图片处理完成"
}
```

## 认证方式

所有 API 端点都需要 Bearer Token 认证：

```bash
Authorization: Bearer your-secret-token-here
```

## 使用示例

### 使用 curl

```bash
# 1. 处理 PDF 文件（不返回图片）
curl -X POST "http://localhost:8766/process/pdf" \
     -H "Authorization: Bearer your-secret-token-here" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@example.pdf" \
     -F "return_images=false"

# 2. 处理 PDF 文件（返回图片）
curl -X POST "http://localhost:8766/process/pdf" \
     -H "Authorization: Bearer your-secret-token-here" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@example.pdf" \
     -F "return_images=true"

# 3. 处理图片文件
curl -X POST "http://localhost:8766/process/image" \
     -H "Authorization: Bearer your-secret-token-here" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@example.jpg" \
     -F "return_images=true"

# 4. 健康检查
curl -X GET "http://localhost:8766/health"
```

### 使用 Python 客户端

```python
from api_client_example import MinerUClient

# 初始化客户端
client = MinerUClient(
    base_url="http://localhost:8766",
    token="your-secret-token-here"
)

# 处理 PDF 文件
result = client.process_pdf("example.pdf", return_images=True)

if result['success']:
    print("✅ 处理成功")
    print(f"📄 Markdown 内容: {result['markdown_content']}")
    
    # 保存图片到本地
    if result.get('images'):
        client.save_images_from_result(result, "./output_images")
else:
    print(f"❌ 处理失败: {result['message']}")

# 处理图片文件
image_result = client.process_image("example.jpg", return_images=False)
print(f"OCR 结果: {image_result['markdown_content']}")
```

## 响应格式

### 成功响应
```json
{
  "success": true,
  "markdown_content": "处理后的文本内容",
  "images": [
    {
      "filename": "image_name.png",
      "content": "base64_encoded_image_data",
      "format": "png"
    }
  ],
  "message": "处理完成"
}
```

### 失败响应
```json
{
  "success": false,
  "markdown_content": "",
  "images": null,
  "message": "错误描述"
}
```

## 图片处理

### 图片返回功能
- 当 `return_images=true` 时，API 会返回处理过程中提取或生成的图片
- 图片以 base64 编码格式返回，包含文件名和格式信息
- 支持的图片格式：PNG, JPG, JPEG, BMP, TIFF, WEBP

### 保存图片到本地
```python
import base64
from pathlib import Path

def save_image_from_base64(image_data, output_path):
    """从 base64 数据保存图片"""
    image_bytes = base64.b64decode(image_data['content'])
    with open(output_path, 'wb') as f:
        f.write(image_bytes)
```

## 环境变量配置

在项目根目录创建 `.env` 文件：

```bash
# .env 文件内容
API_TOKEN=my-custom-secure-token
```

- `API_TOKEN`: Bearer Token，从 .env 文件读取，默认为 "your-secret-token-here"

## 错误处理

### HTTP 状态码
- `200`: 成功
- `400`: 请求参数错误
- `401`: 认证失败
- `500`: 服务器内部错误

### 错误响应格式
```json
{
  "detail": "错误详细信息"
}
```

## API 文档

启动服务后，访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: `http://localhost:8766/docs`
- **ReDoc**: `http://localhost:8766/redoc`

## 性能说明

1. **处理时间**: 根据文件大小和复杂度，处理时间从几秒到几分钟不等
2. **文件大小限制**: 建议单个文件不超过 100MB
3. **并发处理**: 服务支持多个请求并发处理
4. **内存使用**: 处理大文件时会占用较多内存，处理完成后自动释放

## 安全建议

1. **生产环境**: 请务必更改默认的 Bearer Token
2. **HTTPS**: 生产环境建议使用 HTTPS
3. **防火墙**: 适当配置防火墙规则限制访问
4. **令牌管理**: 定期更换 API 令牌

## 故障排除

### 常见问题

1. **连接被拒绝**
   - 检查服务是否正在运行
   - 确认端口 8766 未被其他程序占用

2. **认证失败**
   - 检查 Bearer Token 是否正确
   - 确认请求头格式：`Authorization: Bearer your-token`

3. **文件处理失败**
   - 检查文件格式是否支持
   - 确认文件未损坏
   - 查看服务日志获取详细错误信息

4. **内存不足**
   - 处理大文件时可能需要更多内存
   - 考虑分批处理或使用更强大的服务器

## 更新日志

### v2.0.0
- 简化 API 功能，专注于核心处理能力
- 添加 Bearer Token 认证
- 支持图片文件返回功能
- 改为同步处理模式
- 端口更改为 8766
- 移除任务管理和下载功能 