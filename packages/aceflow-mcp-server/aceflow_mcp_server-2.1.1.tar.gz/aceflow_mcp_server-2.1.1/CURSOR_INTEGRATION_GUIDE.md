# Cursor集成AceFlow MCP Server指南

> 🚀 **双向AI协作** - 让Cursor与AceFlow MCP Server无缝协作，实现智能化项目开发工作流

## 🎯 Cursor集成AceFlow MCP Server

### 📋 步骤1：安装AceFlow MCP Server

```bash
# 方法1：使用pip安装（推荐）
pip install aceflow-mcp-server

# 方法2：从源码安装
git clone <repository-url>
cd aceflow-mcp-server
pip install -e .
```

### 🔧 步骤2：配置Cursor的MCP设置

在Cursor中，你需要添加MCP服务器配置：

#### 方法A：通过Cursor设置界面
1. 打开Cursor
2. 进入 `Settings` > `Extensions` > `MCP Servers`
3. 添加新的MCP服务器配置

#### 方法B：直接编辑配置文件
找到Cursor的MCP配置文件（通常在用户配置目录），添加以下配置：

```json
{
  "mcpServers": {
    "aceflow": {
      "command": "python",
      "args": ["-m", "aceflow_mcp_server.mcp_stdio_server"],
      "cwd": "/path/to/your/project",
      "env": {
        "ACEFLOW_LOG_LEVEL": "INFO",
        "MCP_DEBUG": "false"
      }
    }
  }
}
```

### 🚀 步骤3：开始使用

重启Cursor后，你就可以使用AceFlow的4个核心工具了：

#### 1. 初始化项目
```
@aceflow 请使用aceflow_init工具初始化一个标准的web项目
```

Cursor会调用：
```python
aceflow_init(mode="standard", project_name="my-web-project")
```

#### 2. AI协作工作流（v2.0新特性）

**AI提供分析数据给MCP：**
```
@aceflow 我已经分析了这个项目，请保存以下分析数据：
- 项目类型：React + Node.js全栈应用
- 代码复杂度：中等
- 测试覆盖率：85%
```

Cursor会调用：
```python
aceflow_stage(action="set_analysis", stage="analysis", data={
    "project_info": {"type": "fullstack", "frontend": "react", "backend": "nodejs"},
    "code_metrics": {"complexity": "medium", "coverage": 85},
    "test_metrics": {"unit_tests": 120, "pass_rate": 95}
})
```

**MCP为AI准备数据包：**
```
@aceflow 请为实现阶段准备数据包，包含之前所有阶段的输出
```

Cursor会调用：
```python
aceflow_stage(action="prepare_data", stage="implementation")
```

**AI保存设计输出：**
```
@aceflow 请保存我的设计方案：
架构：微服务架构
数据库：MongoDB + Redis缓存
API：RESTful + GraphQL
```

Cursor会调用：
```python
aceflow_stage(action="save_output", stage="design", data={
    "content": {
        "architecture": "microservices",
        "database": ["mongodb", "redis"],
        "api_style": ["rest", "graphql"]
    },
    "metadata": {"author": "Cursor AI", "confidence": "high"}
})
```

#### 3. 查看项目状态
```
@aceflow 查看当前项目进度和状态
```

#### 4. 验证项目质量
```
@aceflow 验证项目配置和代码质量
```

### 💡 实际使用示例

假设你正在开发一个电商网站：

```
用户: @aceflow 帮我初始化一个电商项目，使用标准模式

Cursor调用: aceflow_init(mode="standard", project_name="e-commerce")

用户: @aceflow 我分析了需求，这是一个B2C电商平台，需要用户系统、商品管理、订单处理、支付集成

Cursor调用: aceflow_stage(action="set_analysis", data={
    "project_info": {"type": "e-commerce", "model": "B2C"},
    "features": ["user_system", "product_management", "order_processing", "payment"],
    "complexity": "high"
})

用户: @aceflow 准备设计阶段的数据包

Cursor调用: aceflow_stage(action="prepare_data", stage="design")
```

### 🏗️ 双向协作架构

AceFlow v2.0 支持双向数据交换：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Cursor AI Agent                          │
│  ┌─────────────────┐                    ┌──────────────────────┐ │
│  │   内容生成      │                    │    数据分析         │ │
│  │   代码编写      │                    │    质量评估         │ │
│  │   文档创建      │                    │    决策建议         │ │
│  └─────────────────┘                    └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │ set_analysis               │ prepare_data
           │ save_output               │ validate
           ↓                          ↑
┌─────────────────────────────────────────────────────────────────┐
│                    AceFlow MCP Server                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ SimplifiedUnified│  │   DataManager   │  │  MCPStdioServer │ │
│  │     Tools       │  │   (缓存+持久化)  │  │   (协议适配)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    本地文件系统                                │
│  .aceflow/                                                     │
│  ├── analysis_data.json    (AI分析数据)                       │
│  ├── stage_outputs/        (阶段产出)                         │
│  ├── cache/                (性能缓存)                         │
│  └── current_state.json    (项目状态)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 🔍 调试和故障排除

如果遇到问题，可以启用调试模式：

```json
{
  "mcpServers": {
    "aceflow": {
      "command": "python",
      "args": ["-m", "aceflow_mcp_server.mcp_stdio_server"],
      "env": {
        "MCP_DEBUG": "true",
        "ACEFLOW_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

#### 常见问题解决：

1. **MCP服务器启动失败**
   ```bash
   # 检查Python环境
   python -c "import aceflow_mcp_server; print('✅ 安装成功')"
   
   # 检查工作目录权限
   ls -la /path/to/your/project
   ```

2. **工具调用失败**
   ```bash
   # 手动测试工具
   python -c "from aceflow_mcp_server.unified_tools import SimplifiedUnifiedTools; tools = SimplifiedUnifiedTools(); print(tools.aceflow_stage(action='status'))"
   ```

3. **性能问题**
   ```bash
   # 查看性能指标
   python -c "from aceflow_mcp_server.data_manager import DataManager; dm = DataManager(); print(dm.get_performance_metrics())"
   ```

### 📊 性能优化

AceFlow v2.0的性能特性会自动为Cursor用户提供：
- **内存缓存**：减少重复数据读取（5分钟TTL）
- **并发处理**：支持4个并发AI请求
- **批处理**：优化大量数据操作
- **线程安全**：保证多线程环境下的数据一致性

### 🛠️ 高级配置

#### 自定义工作流模式：
```json
{
  "mcpServers": {
    "aceflow": {
      "command": "python",
      "args": ["-m", "aceflow_mcp_server.mcp_stdio_server"],
      "env": {
        "ACEFLOW_DEFAULT_MODE": "smart",
        "ACEFLOW_CACHE_TTL": "600",
        "ACEFLOW_MAX_CONCURRENT": "8"
      }
    }
  }
}
```

#### 项目特定配置：
在项目根目录创建 `.aceflow/config.json`：
```json
{
  "project_name": "my-awesome-project",
  "default_mode": "standard",
  "auto_advance_stages": false,
  "quality_threshold": 0.8,
  "collaboration_settings": {
    "ai_input_validation": true,
    "auto_save_outputs": true,
    "cache_analysis_data": true
  }
}
```

### 🔄 工作流程示例

#### 完整的项目开发流程：

1. **项目初始化**
   ```
   @aceflow 初始化一个React+Express的全栈项目，使用标准模式
   ```

2. **需求分析阶段**
   ```
   @aceflow 保存需求分析：用户认证系统、产品展示、购物车功能、订单管理
   ```

3. **设计阶段**
   ```
   @aceflow 准备设计阶段数据包，基于之前的需求分析
   ```
   
   然后进行设计工作，完成后：
   ```
   @aceflow 保存设计方案：前端使用React+Redux，后端Express+MongoDB，API使用RESTful风格
   ```

4. **实现阶段**
   ```
   @aceflow 准备实现阶段数据包，包含设计方案和技术规格
   ```

5. **验证和推进**
   ```
   @aceflow 验证当前阶段数据完整性
   @aceflow 推进到下一个阶段
   ```

### 🎉 开始体验双向AI协作！

配置完成后，你就可以享受AceFlow v2.0的双向AI-MCP协作功能：

✅ **Cursor → AceFlow**: AI分析项目并提供数据
✅ **AceFlow → Cursor**: MCP工具准备结构化数据包  
✅ **智能缓存**: 提升响应速度和用户体验
✅ **数据持久化**: 保持项目状态和历史记录
✅ **错误处理**: 优雅处理异常情况

让Cursor不仅能调用MCP工具，还能向MCP工具提供分析数据和保存工作成果，实现真正的智能协作工作流！

---

## 📚 相关资源

- [AceFlow MCP Server GitHub](https://github.com/aceflow/mcp-server)
- [MCP Protocol 文档](https://modelcontextprotocol.io/)
- [Cursor 使用指南](https://docs.cursor.sh/)
- [问题反馈](https://github.com/aceflow/mcp-server/issues)

**🚀 开始使用 AceFlow + Cursor，体验下一代AI协作开发！**