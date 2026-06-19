# Tetra-cube D&D 工具站 - 中文汉化版

原站：[Tetra-cube/Tetra-cube.github.io](https://github.com/Tetra-cube/Tetra-cube.github.io) — D&D 5e 随机角色/魔法物品/属性块生成器

## 汉化范围

- ✅ 所有 HTML 页面 UI 文本
- ✅ JavaScript 动态生成文本
- ✅ JSON 数据（种族、职业、背景、魔法物品、属性块模板）
- ✅ 角色卡、属性块、物品描述等导出产物
- ✅ 专有名词保护（Numenera, Fire Emblem, Tetracube 等）

## 翻译参考

- **[5etools-cn](https://github.com/pttsw/5etools-cn)** — D&D 术语中文翻译的主要参考
- 技能名、状态名、伤害类型、书名等严格遵循 5etools-cn 约定
- 中文翻译数据遵循 5etools-cn 的 [CC BY-NC-SA 4.0](https://github.com/pttsw/5etools-cn/blob/cn2.0/LICENSE)

## 翻译方案

### 三层架构

**第 1 层：Schema 精确映射** (`schema_map.py`)
```
从 5etools-cn 拉取 JSON → 提取 ENG_name→name 映射 (1,524 对)
→ 对 13 个 JSON 数据文件做精确术语替换
→ JS 查键保留英文（skills, conditions, damage types）
```

**第 2 层：字典匹配** (`translate_v2.py` Phase 1)
```
提取 HTML 文本节点 + 属性值 + JS 字符串字面量
→ 字典匹配（最长优先 + 词边界）
→ 专有名词占位保护
```

**第 3 层：Ollama LLM 翻译** (`translate_v2.py` Phase 2)
```
收集所有剩余英文 → 统一批量翻译
模型：qwen2.5:14b (16G VRAM)
专有名词黑名单保护
```

**修正循环** (`fix_terms.py`)
```
抽样检查 → fix_list.txt → 全局替换修正
→ 重复直到连续 5 轮零新错误
```

### 使用方法

```bash
# 前提：Ollama 运行中，已下载 qwen2.5:14b
ollama pull qwen2.5:14b

# 1. JSON 术语精确映射
python schema_map.py fetch       # 从 5etools-cn 拉取数据（仅首次）
python schema_map.py apply       # 应用到所有 JSON 文件

# 2. HTML/JS 全文翻译
python translate_v2.py           # 字典 + Ollama 全量翻译

# 3. 修正循环（反复执行直到无明显错误）
# 编辑 fix_list.txt 添加修正条目
python fix_terms.py
```

### 文件结构

```
translate_v2.py    # 统一翻译管道（提取→字典→Ollama→校验）
schema_map.py      # 5etools-cn schema 映射（JSON 精确替换）
fix_terms.py       # 修正工具（fix_list.txt → 全局替换）
fix_list.txt       # 修正条目列表
cn_mapping.json    # 缓存的 1,524 对英→中映射（自动生成）
5etools-cn-data/   # 参考用的 5etools-cn 源 JSON
```

## 工具页面

| 页面 | 说明 |
|------|------|
| [首页](https://dajiaohuang.github.io/Tetra-cube.github.io/) | 导航 |
| [内容参考](https://dajiaohuang.github.io/Tetra-cube.github.io/dnd/dnd-reference.html) | 种族/职业/背景/姓名 |
| [角色生成器](https://dajiaohuang.github.io/Tetra-cube.github.io/dnd/dnd-char-gen.html) | 随机角色 |
| [魔法物品生成器](https://dajiaohuang.github.io/Tetra-cube.github.io/dnd/dnd-magic-items.html) | 随机魔法物品 |
| [属性块生成器](https://dajiaohuang.github.io/Tetra-cube.github.io/dnd/dnd-statblock.html) | 怪物属性块 |
| [属性块打印](https://dajiaohuang.github.io/Tetra-cube.github.io/dnd/dnd-statblock-print.html) | 批量打印 |
| [火纹台词生成器](https://dajiaohuang.github.io/Tetra-cube.github.io/fea-quote-gen/fea-quote-gen.html) | FE:A |
| [NFT 生成器](https://dajiaohuang.github.io/Tetra-cube.github.io/nft/generator.html) | 恶搞 |
| [Numenera 生成器](https://dajiaohuang.github.io/Tetra-cube.github.io/numenera/generator.html) | Numenera |

## 许可

- 原站代码：MIT
- 中文翻译数据：CC BY-NC-SA 4.0（遵循 5etools-cn 许可）
