"""Bilgi tabaninin yerel yapisal kontrolleri; ag ve yazma islemi yapmaz."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


HEADER_EXCEPTIONS = {"AGENTS.md", "CLAUDE.md", "CHANGELOG.md"}
STATES = {"dogrulandi", "taslak", "eski", "bos"}


def frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = re.search(r"^---\s*$", text[4:], re.MULTILINE)
        if end:
            stop = 4 + end.start()
            return text[4:stop], text[4 + end.end():]
    return "", text


def prose(text: str) -> str:
    """Fenced code icindeki lambda/array ifadelerini link sayma."""
    result = []
    fence = None
    for line in frontmatter(text)[1].splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            if re.match(r"^\s{0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$", line):
                fence = None
            result.append("")
        elif marker:
            fence = marker[1]
            result.append("")
        else:
            result.append(line)
    return "\n".join(result)


def heading_ids(text: str) -> set[str]:
    ids = set()
    counts: dict[str, int] = defaultdict(int)
    for line in prose(text).splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"<[^>]+>", "", match[1])
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        number = counts[slug]
        ids.add(slug + (f"-{number}" if number else ""))
        counts[slug] += 1
    return ids


def scalar(block: str, key: str) -> str:
    match = re.search(r"^" + re.escape(key) + r":[ \t]*([^\n]*)", block, re.MULTILINE)
    return match[1].split(" #", 1)[0].strip().strip("\"'") if match else ""


def source_records(block: str) -> list[dict[str, str]]:
    records = []
    for line in block.splitlines():
        match = re.match(r"\s*- repo:\s*([^\s#]+)", line)
        if match:
            records.append({"repo": match[1]})
        else:
            match = re.match(r"\s+(branch|commit|dogrulanan_commit|dokuman):\s*([^\s#]+)", line)
            if match and records:
                records[-1][match[1]] = match[2].strip("\"'")
    return records


def audit(root: Path, sources: Path | None = None) -> tuple[list[str], dict]:
    errors = []
    files = sorted(p for p in root.rglob("*.md") if not any(part.startswith(".") for part in p.relative_to(root).parts))
    texts = {p.resolve(): p.read_text(encoding="utf-8-sig") for p in files}
    ids = {p: heading_ids(s) for p, s in texts.items()}
    states: dict[str, int] = defaultdict(int)
    refs: dict[str, set[str]] = defaultdict(set)
    branches: dict[str, set[str]] = defaultdict(set)
    links = 0

    def fail(path: Path, message: str) -> None:
        errors.append(f"{path.relative_to(root).as_posix()}: {message}")

    for path, text in texts.items():
        relative = path.relative_to(root)
        header, _ = frontmatter(text)
        if not header and relative.as_posix() not in HEADER_EXCEPTIONS:
            fail(path, "frontmatter eksik veya kapanmamis")
        if header:
            for key in ("kapsam", "dogrulama", "durum"):
                if not scalar(header, key):
                    fail(path, f"frontmatter {key} eksik")
            try:
                date.fromisoformat(scalar(header, "dogrulama"))
            except ValueError:
                fail(path, "dogrulama YYYY-MM-DD olmali")
            state = scalar(header, "durum")
            states[state] += 1
            if state not in STATES:
                fail(path, f"gecersiz durum: {state}")
            records = source_records(header)
            if relative.parts[0] in {"10-servisler", "20-stratejiler", "30-akislar", "40-operasyon"} and not records and not scalar(header, "dis_kaynak"):
                fail(path, "kaynak/dis_kaynak eksik")
            for record in records:
                if not {"repo", "branch", "commit"} <= record.keys():
                    fail(path, f"eksik kaynak kaydi: {record}")
                    continue
                if not re.fullmatch(r"[0-9a-f]{7,40}", record["commit"]):
                    fail(path, f"gecersiz commit: {record['commit']}")
                refs[record["repo"]].add(record["commit"])
                branches[record["repo"]].add(record["branch"])
        if len(text.splitlines()) > 400:
            fail(path, "400 satir siniri asildi")

        visible = re.sub(r"(`+).*?\1", " ", prose(text))
        for match in re.finditer(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", visible):
            target = match[1].strip("<>")
            url = urlsplit(target)
            if url.scheme or url.netloc:
                continue
            links += 1
            name, _, anchor = target.partition("#")
            destination = ((root / unquote(name).lstrip("/")) if name.startswith("/") else (path.parent / unquote(name))).resolve() if name else path
            if not destination.is_relative_to(root):
                fail(path, f"repo disina link: {target}")
            elif not destination.exists():
                fail(path, f"dosya yok: {target}")
            elif anchor and destination.suffix == ".md" and unquote(anchor) not in ids.get(destination, heading_ids(destination.read_text(encoding="utf-8-sig"))):
                fail(path, f"baslik yok: {target}")

    issue_file = root / "ACIK-KONULAR.md"
    if issue_file.exists():
        issue_ids = re.findall(r"^\| (K-\d+) \|", issue_file.read_text(encoding="utf-8-sig"), re.MULTILINE)
        if len(issue_ids) != len(set(issue_ids)):
            fail(issue_file, "tekrarlanan K numarasi")

    manifest_file = root / "manifest.yaml"
    if manifest_file.exists():
        manifest = source_records(manifest_file.read_text(encoding="utf-8-sig"))
        for record in manifest:
            if not {"repo", "branch", "dogrulanan_commit", "dokuman"} <= record.keys():
                fail(manifest_file, f"eksik repo kaydi: {record}")
                continue
            if not (root / record["dokuman"] / "README.md").is_file():
                fail(manifest_file, f"README yok: {record['dokuman']}")
            refs[record["repo"]].add(record["dogrulanan_commit"])
            branches[record["repo"]].add(record["branch"])

    resolved_commits = set()
    if sources:
        for repo, commits in sorted(refs.items()):
            folder = (sources / repo).resolve()
            expressions = sorted(commits) + [f"origin/{branch}^{{commit}}" for branch in sorted(branches[repo])]
            result = subprocess.run(
                ["git", "-c", f"safe.directory={folder.as_posix()}", "-C", str(folder), "cat-file", "--batch-check=%(objectname) %(objecttype)"],
                input="\n".join(expressions) + "\n", capture_output=True, text=True, encoding="utf-8",
            )
            if result.returncode:
                errors.append(f"kaynak {repo}: git okuma basarisiz ({result.stderr.strip()})")
                continue
            for expression, answer in zip(expressions, result.stdout.splitlines()):
                if not answer.endswith(" commit"):
                    errors.append(f"kaynak {repo}: commit/branch bulunamadi: {expression}")
                elif expression in commits:
                    resolved_commits.add((repo, answer.split()[0]))

    return errors, {"markdown": len(files), "links": links, "states": dict(sorted(states.items())), "source_repos": len(refs), "commit_refs": sum(len(v) for v in refs.values()), "resolved_commits": len(resolved_commits) if sources else None, "sources_checked": sources is not None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--sources", type=Path, help="Salt okunur yerel kaynak klonlarinin kok dizini")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    errors, summary = audit(args.root.resolve(), args.sources)
    for error in errors:
        print("HATA", error)
    print("SONUC", summary, "hata:", len(errors))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
