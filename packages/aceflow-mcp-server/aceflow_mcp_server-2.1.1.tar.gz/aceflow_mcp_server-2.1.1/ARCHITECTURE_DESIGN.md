# AceFlow MCP工具架构设计文档

**版本**: 2.0  
**创建时间**: 2025-08-25  
**设计原则**: AI-MCP双向协作架构  

## 🎯 设计目标

### 核心目标
- **职责分离**: AI Agent负责智能分析和内容生成，MCP工具负责数据管理和流程控制
- **双向协作**: AI Agent既从MCP获取数据，也向MCP提供分析结果
- **标准化**: 统一的接口规范和数据格式，保证产出一致性
- **智能化**: 充分利用AI Agent的代码理解和分析能力

## 🏗️ 整体架构

### 架构图
```
┌─────────────────┐    双向数据交换    ┌─────────────────┐
│   AI Agent      │ ←──────────────→ │   MCP 工具      │
│ (Claude Code)   │                  │                 │
│                 │                  │                 │
│ • 项目分析      │ ──── 分析结果 ───→ │ • 数据收集      │
│ • 代码理解      │ ←─── 数据包 ────── │ • 模板管理      │
│ • 内容生成      │                  │ • 流程控制      │
│ • 文档输出      │                  │ • 状态管理      │
└─────────────────┘                  └─────────────────┘
         │                                    │
         ├─── 读取项目文件                    ├─── 管理templates/
         ├─── 分析代码结构                    ├─── 维护project state  
         └─── 输出到aceflow_result/           └─── 跟踪阶段依赖
```

### 职责划分

#### AI Agent (Claude Code) 职责
- **项目分析**: 读取和理解项目文件、代码结构、测试结果
- **数据提供**: 向MCP工具提供分析得出的项目数据
- **内容生成**: 基于MCP提供的数据包生成完整的阶段文档
- **质量保证**: 确保生成内容符合模板结构且具有实际意义

#### MCP 工具职责
- **数据管理**: 收集、存储和管理AI提供的项目数据
- **模板管理**: 加载和提供标准化的阶段模板
- **流程控制**: 管理工作流状态、阶段依赖和推进逻辑
- **数据准备**: 为AI Agent准备完整的执行数据包

## 🔌 MCP工具接口设计

### 核心接口规范

#### 1. aceflow_stage 主接口
```python
aceflow_stage(
    action: str,           # 操作类型
    stage: Optional[str],  # 阶段ID
    data: Optional[Dict]   # 数据载荷
) -> Dict[str, Any]
```

#### 2. 支持的操作类型

##### 2.1 数据设置操作
```python
# AI Agent 向MCP提供分析数据
aceflow_stage(action="set_analysis", stage="current", data={
    "project_info": {
        "tech_stack": ["Vue3", "FastAPI", "DuckDB"],
        "file_count": 45,
        "test_files": 12,
        "dependencies": ["vue", "fastapi", "duckdb"]
    },
    "code_metrics": {
        "total_lines": 5420,
        "test_coverage": 85.6,
        "complexity_score": 7.2
    },
    "test_results": {
        "total_tests": 23,
        "passed": 21,
        "failed": 2,
        "coverage_percent": 85.6
    }
})
```

##### 2.2 输出保存操作
```python
# AI Agent 保存阶段输出供后续使用
aceflow_stage(action="save_output", stage="s1_user_story", data={
    "content": "完整的用户故事内容...",
    "metadata": {
        "word_count": 1200,
        "stories_count": 5,
        "completion_time": "2025-08-25 14:30:00"
    }
})
```

##### 2.3 数据准备操作
```python
# AI Agent 请求执行数据包
aceflow_stage(action="prepare_data", stage="s5_test_report")

# 返回格式:
{
    "success": True,
    "stage_id": "s5_test_report",
    "data_package": {
        "template": {
            "content": "# S5 测试报告模板内容...",
            "format": "markdown",
            "placeholders": ["{{test_count}}", "{{coverage}}"]
        },
        "previous_outputs": {
            "s4_implementation": "实现阶段的输出内容..."
        },
        "analysis_data": {
            "test_results": {...},
            "code_metrics": {...}
        },
        "project_context": {
            "name": "MyProject",
            "mode": "standard",
            "current_stage": "s5_test_report"
        }
    },
    "instructions": {
        "task": "基于模板和数据生成测试报告",
        "output_location": "aceflow_result/s5_test_report.md",
        "requirements": [...]
    }
}
```

##### 2.4 流程控制操作
```python
# 状态查询
aceflow_stage(action="status")

# 阶段推进  
aceflow_stage(action="next")

# 阶段跳转
aceflow_stage(action="goto", stage="s3_testcases")
```

## 🔄 协作工作流程

### 典型阶段执行流程

#### Phase 1: AI Agent 项目分析
```
1. AI Agent 读取项目文件
   - 分析代码结构和技术栈
   - 检查测试文件和覆盖率
   - 理解项目规模和复杂度

2. AI Agent 向MCP提供分析结果
   aceflow_stage(action="set_analysis", data={
       "tech_stack": [...],
       "test_metrics": {...},
       "code_quality": {...}
   })
```

#### Phase 2: MCP工具数据准备
```
3. AI Agent 请求执行数据包
   aceflow_stage(action="prepare_data", stage="s5_test_report")

4. MCP工具准备完整数据包
   - 加载s5_test_report.md模板
   - 收集前一阶段输出(s4_implementation)
   - 整合AI提供的分析数据
   - 返回完整执行包
```

#### Phase 3: AI Agent 内容生成
```
5. AI Agent 基于数据包生成内容
   - 理解模板结构
   - 结合分析数据填充具体内容
   - 基于前一阶段输出保持逻辑连贯
   - 生成完整且有意义的文档

6. AI Agent 输出最终文档
   - 写入 aceflow_result/s5_test_report.md
   - 通知MCP保存输出(可选)
```

#### Phase 4: 流程推进
```
7. 更新项目状态
   aceflow_stage(action="complete_stage", stage="s5_test_report")

8. 推进到下一阶段
   aceflow_stage(action="next")
```

## 📊 数据模型设计

### 项目上下文数据结构
```python
ProjectContext = {
    "project": {
        "name": str,
        "mode": str,  # minimal|standard|complete|smart
        "created_at": str,
        "last_updated": str
    },
    "flow": {
        "current_stage": str,
        "completed_stages": List[str],
        "next_stage": Optional[str],
        "progress_percentage": int
    },
    "analysis_data": {
        "project_info": Dict,
        "code_metrics": Dict, 
        "test_results": Dict,
        "dependencies": List[str]
    }
}
```

### 阶段输出数据结构
```python
StageOutput = {
    "stage_id": str,
    "content": str,
    "metadata": {
        "created_at": str,
        "word_count": int,
        "ai_generated": bool,
        "template_used": str
    },
    "dependencies": List[str],  # 依赖的前置阶段
    "artifacts": List[str]      # 生成的文件路径
}
```

## 🛠️ 技术实现要点

### 1. 数据存储策略
- **项目状态**: `.aceflow/current_state.json`
- **分析数据**: `.aceflow/analysis_data.json` 
- **阶段输出**: `.aceflow/stage_outputs/`
- **最终文档**: `aceflow_result/`

### 2. 模板管理
- **位置**: `templates/` 目录
- **格式**: Markdown + 占位符
- **加载**: 动态读取，支持自定义

### 3. 错误处理
- **数据缺失**: 提供默认值或提示AI补充
- **模板缺失**: 使用通用模板回退
- **格式错误**: 验证并给出修复建议

## 📝 示例场景

### 场景: 生成S5测试报告

#### 1. AI Agent 分析项目
```bash
# AI读取测试文件
ls tests/ 
# 发现: test_user.py, test_task.py, test_api.py

# AI分析测试结果 
pytest --coverage
# 得到: 23个测试，21个通过，覆盖率85.6%
```

#### 2. AI向MCP提供数据
```python
aceflow_stage(action="set_analysis", data={
    "test_results": {
        "total_tests": 23,
        "passed": 21, 
        "failed": 2,
        "coverage_percent": 85.6,
        "test_files": ["test_user.py", "test_task.py", "test_api.py"]
    }
})
```

#### 3. AI请求数据包
```python
result = aceflow_stage(action="prepare_data", stage="s5_test_report")
# MCP返回: 模板 + S4输出 + 测试数据 + 指导信息
```

#### 4. AI生成完整报告
基于数据包生成包含真实测试数据的报告：
```markdown
# S5 测试报告 - MyTaskApp

## 测试概览
- 测试用例总数: 23个
- 通过用例: 21个 (91.3%)
- 失败用例: 2个 (8.7%)
- 测试覆盖率: 85.6%

## 测试文件分析
- test_user.py: 用户管理模块测试
- test_task.py: 任务管理核心测试  
- test_api.py: API接口测试

## 失败用例分析
基于S4实现阶段的代码分析，失败的测试用例主要集中在...
```

## 🎯 预期收益

### 1. 智能化程度大幅提升
- AI能够真正理解项目并生成有意义的内容
- 不再是简单的模板填充

### 2. 数据一致性保证
- 统一的数据格式和接口规范
- MCP工具确保模板结构一致性

### 3. 可扩展性强
- 易于添加新的分析维度
- 支持自定义阶段和模板

### 4. 用户体验优秀  
- AI自动分析，用户无需手动输入数据
- 生成的文档直接可用，无需二次编辑

---
*设计文档版本: 2.0*  
*最后更新: 2025-08-25*