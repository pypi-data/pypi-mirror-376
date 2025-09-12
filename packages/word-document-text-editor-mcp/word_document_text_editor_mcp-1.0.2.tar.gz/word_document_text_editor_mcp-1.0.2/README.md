# Word文档文本编辑 MCP服务

这是一个基于Model Context Protocol (MCP)的Word文档文本编辑服务，提供对Word文档进行文本格式化、查找替换、段落删除和样式创建的功能。

## 功能特性

### 核心功能
- **文本格式化** - 对文档中指定范围的文本进行格式化（粗体、斜体、下划线、颜色、字体大小、字体名称）
- **查找替换** - 在整个文档中查找并替换指定文本
- **删除段落** - 删除文档中的指定段落
- **创建自定义样式** - 创建带有自定义格式的文档样式

### 技术特性
- 基于FastMCP框架构建
- 支持异步操作
- 完整的错误处理和验证
- 文件权限检查
- 智能跳过目录(TOC)段落
- 支持多种颜色格式
- 自动文件扩展名处理

## 安装要求

- Python 3.10+
- python-docx >= 1.1.0
- fastmcp >= 2.8.1

## 安装方法

使用uv安装依赖：

```bash
cd python/Word文档文本编辑
uv sync
```

或使用pip安装：

```bash
pip install python-docx fastmcp
```

## 使用方法

### 启动MCP服务器

```bash
# 使用uv运行
uv run python -m word_document_text_editor.main

# 或直接运行
python -m word_document_text_editor.main
```

### MCP配置

将以下配置添加到您的MCP客户端配置文件中：

```json
{
  "mcpServers": {
    "Word文档文本编辑": {
      "command": "uvx",
      "args": [
        "word-document-text-editor-mcp"
      ],
      "env": {}
    }
  }
}
```

### 在Claude中使用

配置完成后，在Claude中可以使用以下功能：

1. **格式化文本**
   ```
   请将文档 "example.docx" 第1段的前5个字符设为粗体红色
   ```

2. **查找替换**
   ```
   请在文档 "example.docx" 中将所有的 "旧文本" 替换为 "新文本"
   ```

3. **删除段落**
   ```
   请删除文档 "example.docx" 的第3段
   ```

4. **创建自定义样式**
   ```
   请在文档 "example.docx" 中创建名为 "重要提示" 的样式，设为粗体蓝色
   ```

## API参考

### 格式化文本
```python
format_text_tool(filename: str, paragraph_index: int, start_pos: int, end_pos: int,
                bold: str = "", italic: str = "", underline: str = "",
                color: str = "", font_size: int = 0, font_name: str = "")
```
- `filename`: Word文档路径
- `paragraph_index`: 段落索引（从0开始）
- `start_pos`: 文本开始位置
- `end_pos`: 文本结束位置
- `bold`: 粗体设置（"true"=粗体，"false"=非粗体，""=不改变）
- `italic`: 斜体设置（"true"=斜体，"false"=非斜体，""=不改变）
- `underline`: 下划线设置（"true"=下划线，"false"=无下划线，""=不改变）
- `color`: 文本颜色（如"red"、"blue"，""=不改变）
- `font_size`: 字体大小（磅，0=不改变）
- `font_name`: 字体名称（""=不改变）

### 查找替换
```python
search_and_replace_tool(filename: str, find_text: str, replace_text: str)
```
- `filename`: Word文档路径
- `find_text`: 要查找的文本
- `replace_text`: 替换文本

### 删除段落
```python
delete_paragraph_tool(filename: str, paragraph_index: int)
```
- `filename`: Word文档路径
- `paragraph_index`: 要删除的段落索引（从0开始）

### 创建自定义样式
```python
create_custom_style_tool(filename: str, style_name: str, bold: str = "",
                        italic: str = "", font_size: int = 0,
                        font_name: str = "", color: str = "",
                        base_style: str = "")
```
- `filename`: Word文档路径
- `style_name`: 新样式名称
- `bold`: 粗体设置（"true"=粗体，"false"=非粗体，""=不设置）
- `italic`: 斜体设置（"true"=斜体，"false"=非斜体，""=不设置）
- `font_size`: 字体大小（磅，0=不设置）
- `font_name`: 字体名称（""=不设置）
- `color`: 文本颜色（如"red"、"blue"，""=不设置）
- `base_style`: 基础样式名称（""=不设置）

## 使用示例

### 格式化文本
```python
# 将第一个段落的前10个字符设为粗体红色
result = format_text_tool("document.docx", 0, 0, 10, bold="true", color="red")

# 设置字体大小和字体名称
result = format_text_tool("document.docx", 1, 5, 15, font_size=14, font_name="Arial")

# 设置斜体和下划线
result = format_text_tool("document.docx", 2, 0, 5, italic="true", underline="true")

# 取消粗体格式
result = format_text_tool("document.docx", 0, 10, 20, bold="false")
```

### 查找替换
```python
# 替换所有"旧文本"为"新文本"
result = search_and_replace_tool("document.docx", "旧文本", "新文本")
```

### 删除段落
```python
# 删除第三个段落（索引为2）
result = delete_paragraph_tool("document.docx", 2)
```

### 创建自定义样式
```python
# 创建一个名为"重要提示"的样式
result = create_custom_style_tool("document.docx", "重要提示",
                                 bold="true", italic="true",
                                 color="blue", font_size=12)

# 基于现有样式创建新样式
result = create_custom_style_tool("document.docx", "自定义标题",
                                 base_style="Heading 1",
                                 color="green", font_size=16)

# 创建只设置字体的样式
result = create_custom_style_tool("document.docx", "特殊字体",
                                 font_name="Arial", font_size=14)
```

## 支持的颜色

### 预定义颜色名称
- red, blue, green, black, white
- yellow, orange, purple, gray/grey

### 十六进制颜色
- 支持 #RRGGBB 格式，如 "#FF0000" (红色)
- 支持 RRGGBB 格式，如 "00FF00" (绿色)

## 错误处理

服务提供完整的错误处理：

- 文件存在性检查
- 文件权限验证
- 段落索引有效性验证
- 文本位置范围验证
- 参数类型验证
- 详细的错误信息返回

## 特殊功能

### 智能TOC处理
- 自动跳过目录(Table of Contents)段落
- 避免意外修改文档结构

### 灵活的样式创建
- 支持基于现有样式创建新样式
- 自动处理样式冲突
- 支持多种字体属性组合

## 参数说明

### 布尔参数处理
由于MCP框架的类型限制，布尔参数使用字符串表示：
- `"true"` - 启用该格式（如设为粗体）
- `"false"` - 禁用该格式（如取消粗体）
- `""` (空字符串) - 不改变该格式

### 其他可选参数
- 字符串参数：空字符串 `""` 表示不改变
- 数值参数：`0` 表示不改变
- 所有参数都有合理的默认值，可以省略不填

## 注意事项

1. 确保目标Word文档存在且可写
2. 文档不能被其他程序打开
3. 段落索引从0开始计算
4. 文本位置索引基于字符数
5. 删除段落操作不可撤销
6. 样式名称在文档中必须唯一

## 许可证

MIT License

## 作者

Word MCP Services
