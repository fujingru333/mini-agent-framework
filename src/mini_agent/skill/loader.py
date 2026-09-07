"""FileSkillLoader：把磁盘上的 SKILL.md 解析成 Skill 对象。
"""
from pathlib import Path
from .base import Skill


class FileSkillLoader:

    def load(self, path: str | Path) -> Skill:
        """读取一个SKILL.md，解析成Skill对象
        frontmatter里没有name时，回退所在目录名"""
        text = Path(path).read_text(encoding="utf-8")
        metadata, body = _split_frontmatter(text)
        name = metadata.get("name", "").strip() or Path(path).parent.name
        return Skill(
            name=name,
            description=metadata.get("description", "").strip(),
            instructions=body.strip(),
        )

    def discover(self, directory: str | Path) -> list[Skill]:
        """扫描目录下所有SKILL.md(含子目录)，返回Skill列表"""
        base = Path(directory)
        return [self.load(p) for p in sorted(base.rglob("SKILL.md"))]


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """把 '---\nkey: value\n---\n正文' 拆成 (元数据 dict, 正文)。"""
    metadata: dict[str, str] = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
            return metadata, parts[2]
    return metadata, text