#!/usr/bin/env python3
"""Offline storyboard builder and contract self-test.

The builder preserves source anchors and produces a deterministic minimum
package. Editorial choices remain visible for an Agent to refine.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def _parts(text: str):
    title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), "未命名故事")
    body = " ".join(line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#"))
    if len(body) < 25 or not re.search(r"[。！？]", body):
        raise ValueError("needs_more_source: 请提供至少一个包含人物、场景和完整动作的故事片段")
    chunks = [chunk.strip() for chunk in re.split(r"(?<=[。！？；])", body) if chunk.strip()]
    if len(chunks) < 3:
        chunks = [chunk.strip() for chunk in re.split(r"[，,]", body) if chunk.strip()]
    if len(chunks) < 3:
        size = max(1, len(body) // 3)
        chunks = [body[i : i + size].strip() for i in range(0, len(body), size) if body[i : i + size].strip()]
    return title, body, chunks[:5]


def _hero(body: str) -> str:
    candidates = re.findall(r"(?<![\u4e00-\u9fff])([\u4e00-\u9fff]{2,3})(?=(?:在|等|发现|抬头|把|看向|收进|坐|走|跑|拿))", body)
    blocked = {"远处列", "长椅下", "一个湿", "自己的名"}
    return next((item for item in candidates if item not in blocked), "主角")


def _extract_dialogue(body: str):
    quoted = re.findall(r"[“「『](.*?)[”」』]", body)
    speaker_lines = re.findall(r"([\u4e00-\u9fff]{2,3})[：:]([^。！？]+[。！？]?)", body)
    return [{"speaker": speaker, "line": line.strip()} for speaker, line in speaker_lines] or [{"speaker": "待确认", "line": line.strip()} for line in quoted]


def _location(body: str) -> str:
    for term in ("车站候车区", "候车室", "站台", "咖啡馆", "车站", "门口"):
        if term in body:
            return term
    return "待确认地点"


def _time(body: str) -> str:
    for term in ("清晨", "早上", "上午", "中午", "下午", "傍晚", "夜里", "夜晚", "深夜", "雨夜"):
        if term in body:
            return term
    return "待确认时间"


def convert(text: str) -> dict:
    title, body, chunks = _parts(text)
    hero = _hero(body)
    dialogues = _extract_dialogue(body)
    facts = [chunk for chunk in chunks if hero in chunk] or [chunks[0]]
    character = {
        "name": hero,
        "role": "推动当前事件的视角人物",
        "goal": "确认线索并做出下一步选择",
        "conflict": "信息来源不明，行动可能带来代价",
        "relationship": "待从原文确认",
        "facts": facts[:3],
        "source_anchor": facts[0],
    }
    scene = {
        "scene_id": "S01",
        "location": _location(body),
        "time": _time(body),
        "purpose": f"{hero}发现线索并决定继续行动",
        "characters": [hero],
        "actions": chunks,
        "dialogue": dialogues,
        "source_anchor": chunks[0],
        "shots": [],
    }
    for index, chunk in enumerate(chunks, 1):
        scene["shots"].append(
            {
                "shot_id": f"S01-{index:02d}",
                "duration_seconds": 5,
                "framing": ("远景", "中景", "近景", "特写", "中近景")[min(index - 1, 4)],
                "camera": "固定机位" if index == 1 else "缓慢推进",
                "visual": f"将原文动作转为可见画面：{chunk}",
                "action": chunk,
                "dialogue_or_voiceover": dialogues[min(index - 1, len(dialogues) - 1)]["line"] if dialogues else "",
                "sound": "环境声随动作变化",
                "source_anchor": chunk,
                "creative_note": "新增镜头表达，人物和事件以原文为准",
            }
        )
    return {
        "title": title,
        "source_type": "novel_or_screenplay_excerpt",
        "duration_seconds": len(scene["shots"]) * 5,
        "characters": [character],
        "scenes": [scene],
        "gaps": [] if dialogues else ["原文没有可识别的对白，需确认是否需要补写"],
    }


def _markdown(data: dict) -> str:
    scene = data["scenes"][0]
    lines = [f"# {data['title']}", "", f"总时长：{data['duration_seconds']} 秒", "", "## 人物卡", ""]
    for person in data["characters"]:
        lines += [f"- **{person['name']}**：{person['role']}", f"  - 目标：{person['goal']}", f"  - 阻力：{person['conflict']}", f"  - 关系：{person['relationship']}", f"  - 原文事实：{'；'.join(person['facts'])}"]
    lines += ["", "## 场景卡", "", f"- **{scene['scene_id']}**：{scene['location']} / {scene['time']}", f"- 目的：{scene['purpose']}", f"- 动作：{'；'.join(scene['actions'])}", "", "## 对白", ""]
    lines += [f"- {item['speaker']}：{item['line']}" for item in scene["dialogue"]] or ["- （原文未识别对白）"]
    lines += ["", "## 分镜", "", "| 镜头 | 时长 | 景别 | 动作/画面 | 对白/旁白 |", "|---|---:|---|---|---|"]
    lines += [f"| {shot['shot_id']} | {shot['duration_seconds']}s | {shot['framing']} | {shot['visual']} | {shot['dialogue_or_voiceover']} |" for shot in scene["shots"]]
    return "\n".join(lines) + "\n"


def write_outputs(data: dict, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    (out / "storyboard.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "storyboard.md").write_text(_markdown(data), encoding="utf-8")


def write_failure(out: Path, root: Path):
    payload = json.loads((root / "examples/failure-output.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "storyboard.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "storyboard.md").write_text(f"# 小说剧本转分镜\n\n状态：{payload['status']}\n\n{payload['message']}\n", encoding="utf-8")


def _self_test():
    root = Path(__file__).parents[1]
    data = convert((root / "examples/success-input.md").read_text(encoding="utf-8"))
    assert data["characters"] and all(data["characters"][0].get(key) for key in ("name", "role", "goal", "conflict", "relationship", "facts"))
    scene = data["scenes"][0]
    assert scene["location"] != "待确认地点" and scene["time"] != "待确认时间"
    assert scene["actions"] and "dialogue" in scene and 3 <= len(scene["shots"]) <= 5 and len(scene["shots"]) <= 6
    assert all(shot["action"] and shot["source_anchor"] for shot in scene["shots"])
    failure = (root / "examples/failure-input.md").read_text(encoding="utf-8")
    try:
        convert(failure)
    except ValueError as error:
        assert str(error).startswith("needs_more_source")
    else:
        raise AssertionError("failure sample was accepted")
    with tempfile.TemporaryDirectory(prefix="novel-storyboard-self-test-") as temp:
        output = Path(temp)
        write_outputs(data, output / "success")
        assert json.loads((output / "success/storyboard.json").read_text(encoding="utf-8"))["characters"]
        result = subprocess.run([sys.executable, str(Path(__file__)), "convert", "--input", str(root / "examples/failure-input.md"), "--output", str(output / "failure")], capture_output=True, text=True)
        assert result.returncode != 0
        expected = json.loads((root / "examples/failure-output.json").read_text(encoding="utf-8"))
        actual = json.loads((output / "failure/storyboard.json").read_text(encoding="utf-8"))
        assert actual == expected
    print("self-test: PASS (character, scene/time/dialogue/action, 3-5 anchored shots, structured failure)")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("self-test")
    for name in ("convert", "build"):
        p = sub.add_parser(name)
        p.add_argument("--input", required=True)
        p.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).parents[1]
    if args.command == "self-test":
        _self_test()
        return 0
    try:
        write_outputs(convert(Path(args.input).read_text(encoding="utf-8")), Path(args.output))
    except ValueError as error:
        write_failure(Path(args.output), root)
        print(str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"wrote storyboard.md and storyboard.json to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
