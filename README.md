# Tetra-cube D&D 工具站 — 中文汉化版

原站：[Tetra-cube/Tetra-cube.github.io](https://github.com/Tetra-cube/Tetra-cube.github.io)

## 汉化范围

- ✅ 所有 HTML 页面 UI 文本
- ✅ JavaScript 动态生成文本及字符串常量（武器名、护甲名等）
- ✅ JSON 数据（种族、职业、背景、魔法物品、属性块模板）
- ✅ 角色卡、属性块、物品描述等导出产物
- ✅ 属性块预览 / Markdown 导出 / 打印模板
- ✅ 专有名词保留（Numenera、Fire Emblem、Tetracube 等）

## 翻译参考

- **[5etools-cn](https://github.com/pttsw/5etools-cn)** — 技能名、状态名、伤害类型、书名等术语严格遵循 5etools-cn 约定
- 中文翻译数据遵循 5etools-cn 的 [CC BY-NC-SA 4.0](https://github.com/pttsw/5etools-cn/blob/cn2.0/LICENSE)

## 翻译方式

**手动翻译**，辅助以 `schema_map.py` 从 5etools-cn 提取的英文→中文术语映射。

```
schema_map.py → 从 5etools-cn 提取 1,524 对术语映射
               → 对 13 个 JSON 数据文件精确替换
               → JS 查键保留英文原值

HTML / JS 显示文本 → 逐页人工翻译校对
```

## 本地启动

```bash
python -m http.server 8080
# 或双击 start.bat
```

然后访问 `http://localhost:8080`

## 工具页面

| 页面 | 说明 |
|------|------|
| [首页](https://dajiaohuang.github.io/tetra-cube-zh/) | 导航 |
| [内容参考](https://dajiaohuang.github.io/tetra-cube-zh/dnd/dnd-reference.html) | 种族/职业/背景/姓名 |
| [角色生成器](https://dajiaohuang.github.io/tetra-cube-zh/dnd/dnd-char-gen.html) | 随机角色 |
| [魔法物品生成器](https://dajiaohuang.github.io/tetra-cube-zh/dnd/dnd-magic-items.html) | 随机魔法物品 |
| [属性块生成器](https://dajiaohuang.github.io/tetra-cube-zh/dnd/dnd-statblock.html) | 怪物属性块 |
| [属性块打印](https://dajiaohuang.github.io/tetra-cube-zh/dnd/dnd-statblock-print.html) | 批量打印 |
| [火纹台词生成器](https://dajiaohuang.github.io/tetra-cube-zh/fea-quote-gen/fea-quote-gen.html) | FE:A |
| [NFT 生成器](https://dajiaohuang.github.io/tetra-cube-zh/nft/generator.html) | 恶搞 |
| [Numenera 生成器](https://dajiaohuang.github.io/tetra-cube-zh/numenera/generator.html) | Numenera |

## 许可

- 原站代码：MIT
- 中文翻译数据：CC BY-NC-SA 4.0（遵循 5etools-cn 许可）
