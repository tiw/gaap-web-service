# US GAAP 2025 Web Service

这是一个基于Python FastAPI的Web服务，用于查询US GAAP 2025标准中的财务指标标签定义和参考标准。

## 功能特点

- 根据指标名称查询英文标签定义
- 获取指标对应的参考标准和FASB链接
- 提供RESTful API接口
- 提供简单的Web界面查询

## 安装和运行

### 1. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行服务
```bash
./start.sh
```

或者直接运行：
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

## API接口

### 1. 根路径
- **URL**: `/`
- **方法**: GET
- **描述**: 获取API基本信息

### 2. 获取元素完整信息
- **URL**: `/element/{element_name}`
- **方法**: GET
- **描述**: 获取指定元素的标签定义和参考标准
- **示例**: `GET /element/AccumulatedOtherComprehensiveIncomeLossNetOfTax`

### 3. 获取元素标签定义
- **URL**: `/element/{element_name}/label`
- **方法**: GET
- **描述**: 仅获取指定元素的英文标签定义
- **示例**: `GET /element/AccumulatedOtherComprehensiveIncomeLossNetOfTax/label`

### 4. 获取元素参考标准
- **URL**: `/element/{element_name}/references`
- **方法**: GET
- **描述**: 仅获取指定元素的参考标准列表
- **示例**: `GET /element/AccumulatedOtherComprehensiveIncomeLossNetOfTax/references`

## Web界面

访问 `http://localhost:8000/index.html` 可以使用简单的Web界面查询指标信息。

## 示例

### 查询完整信息
```bash
curl http://localhost:8000/element/AccumulatedOtherComprehensiveIncomeLossNetOfTax
```

响应:
```json
{
  "element_name": "AccumulatedOtherComprehensiveIncomeLossNetOfTax",
  "label": "Accumulated Other Comprehensive Income (Loss), Net of Tax",
  "references": [
    {
      "uri": "https://asc.fasb.org/1943274/2147482790/220-10-45-14A",
      "topic": "220",
      "subtopic": "10",
      "section": "45",
      "paragraph": "14A"
    },
    ...
  ]
}
```

## 项目结构

```
gaap-web-service/
├── main.py              # 主应用文件
├── gaap_parser.py       # GAAP文件解析器
├── requirements.txt     # 依赖包列表
├── index.html           # Web查询界面
├── start.sh             # 启动脚本
└── README.md           # 本说明文件
```

## 依赖

- FastAPI: Web框架
- Uvicorn: ASGI服务器
- lxml: XML解析库

## 注意事项

1. 需要US GAAP 2025文件目录，路径在 `main.py` 中配置
2. 确保文件目录具有读取权限
3. 服务默认运行在8000端口

## 许可证

本项目仅供学习和研究使用。