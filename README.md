# 小说剧本转分镜

把小说或剧本片段拆成可执行的中文分镜，交付 `storyboard.md` 和 `storyboard.json`。适合短视频、漫剧、动画和影视前期，不需要 API Key。

## 能解决什么

- 自动整理人物、地点、时间和冲突
- 按场次拆镜头，补齐景别、动作、对白、音效和时长
- Markdown 方便人工改，JSON 方便剪辑或其他 Agent 继续处理

## 使用

```bash
python3 scripts/self_test.py convert --input examples/success-input.md --output ./out
```

真实任务请提供完整片段、目标时长和画幅。文本不完整时会明确列缺口，不替你编造原作事实。

## 许可

本 Skill 代码与说明采用 MIT License。它不包含第三方 Skill 的代码或文案。
