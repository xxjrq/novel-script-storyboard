# 分镜 JSON 字段

根对象包含 `title`、`source_type`、`duration_seconds`、`gaps` 和 `scenes`。`scenes` 是场次数组，每场包含 `scene_id`、`location`、`time`、`purpose` 和 `shots`。

每个 `shot` 必须包含：

- `shot_id`：如 `S01-01`，按场次连续编号
- `duration_seconds`：正数
- `framing`：景别，例如远景、中景、近景、特写
- `camera`：视角和运动
- `visual`：观众能看到的主体、动作和构图
- `dialogue_or_voiceover`：对白或旁白，没有则为空字符串
- `sound`：环境声、音效或音乐建议
- `source_anchor`：对应原文的短引用或段落序号
- `creative_note`：新增的制作建议，没有则为空字符串

`gaps` 记录缺失信息。不能用空字符串掩盖无法判断的关键事实。
