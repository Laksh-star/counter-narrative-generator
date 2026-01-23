#!/usr/bin/env python3
"""
ingest_lenny_transcripts.py

Parse a folder of Lenny's Podcast transcript .txt files into:
- per-episode structured JSON (with turns + section labels)
- a flat chunks.jsonl file (best for embeddings / RAG ingestion)
- a manifest.csv (episode-level metadata + counts)

Designed to handle common formats:
- "Speaker (HH:MM:SS):" followed by text on next line(s)
- "Speaker (HH:MM:SS): text" on same line
- "(HH:MM:SS):" speakerless/narration
- multi-line continuations until the next timestamped line

No external dependencies (standard library only).

Usage:
  python ingest_lenny_transcripts.py --input_dir /path/to/txts --output_dir out

Optional:
  --include_intro          include intro turns in chunks
  --redact_pii             replace emails/phones with redaction tokens
  --target_words 280       approximate chunk size (words)
  --overlap_turns 1        overlap between consecutive chunks (turns)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------- Regex patterns ----------
# Speaker (HH:MM:SS): ...
RE_SPEAKER_TS = re.compile(
    r'^\s*(?P<speaker>.+?)\s*\((?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})\)\s*:\s*(?P<rest>.*)\s*$'
)
# (HH:MM:SS): ...
RE_TS_ONLY = re.compile(r'^\s*\((?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})\)\s*:\s*(?P<rest>.*)\s*$')

EMAIL_RE = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.IGNORECASE)
# Very loose phone pattern (tune as needed)
PHONE_RE = re.compile(r'(\+?\d[\d\s().-]{7,}\d)')

SPONSOR_START = [
    "this episode is brought to you by",
    "sponsored by",
    "our sponsor",
    "support this podcast",
    "thanks to our sponsor",
]
SPONSOR_TRANSITION = [
    "and so with that",
    "with that",
    "let's get into",
    "now, my guest",
    "here's my conversation",
    "okay, let's start",
    "let's start",
    "today's guest",
    "i bring you",
]
OUTRO_MARKERS = [
    "thank you so much for listening",
    "thanks so much for listening",
    "if you enjoyed this episode",
    "please subscribe",
    "see you next time",
    "leave a review",
]

ELLIPSIS_LINE = re.compile(r'^\s*\.\.\.\s*$')


# ---------- Data models ----------
@dataclass
class Turn:
    speaker: Optional[str]      # None when speakerless
    t: int                     # start time in seconds
    text: str
    section_type: str = "unknown"  # intro/sponsor/conversation/outro/unknown
    is_elided: bool = False
    pii_flags: Optional[List[Dict[str, Any]]] = None


def ts_to_seconds(h: str, m: str, s: str) -> int:
    return int(h) * 3600 + int(m) * 60 + int(s)


def slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]+', '-', name)
    return name.strip('-')[:120]


def detect_pii(text: str) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    for m in EMAIL_RE.finditer(text):
        flags.append({"type": "email", "value": m.group(0)})
    for m in PHONE_RE.finditer(text):
        val = m.group(0)
        if sum(c.isdigit() for c in val) >= 10:
            flags.append({"type": "phone", "value": val})
    return flags


def redact_pii(text: str) -> str:
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)

    def _phone_sub(m: re.Match) -> str:
        val = m.group(0)
        return "[REDACTED_PHONE]" if sum(c.isdigit() for c in val) >= 10 else val

    return PHONE_RE.sub(_phone_sub, text)


def parse_transcript(text: str, redact: bool = False) -> List[Turn]:
    """
    Parse transcript into turns.
    Continuation lines (not matching timestamp patterns) are appended to current turn text.
    Handles cases where timestamp lines have no text after ":" and the actual text follows on next line(s).
    """
    turns: List[Turn] = []
    cur: Optional[Turn] = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        if not line.strip():
            # keep paragraph breaks inside a turn
            if cur is not None and cur.text and not cur.text.endswith("\n"):
                cur.text += "\n"
            continue

        m1 = RE_SPEAKER_TS.match(line)
        m2 = RE_TS_ONLY.match(line)

        if m1 or m2:
            # flush previous
            if cur is not None:
                cur.text = cur.text.strip()
                turns.append(cur)

            if m1:
                speaker = m1.group("speaker").strip()
                t = ts_to_seconds(m1.group("h"), m1.group("m"), m1.group("s"))
                rest = m1.group("rest").strip()
            else:
                speaker = None
                t = ts_to_seconds(m2.group("h"), m2.group("m"), m2.group("s"))
                rest = m2.group("rest").strip()

            # treat a bare timestamp line (no text) as "pending" not true elision
            is_elided = bool(ELLIPSIS_LINE.match(rest)) or rest == ""

            if redact and rest:
                rest = redact_pii(rest)

            cur = Turn(speaker=speaker, t=t, text=rest, is_elided=is_elided, pii_flags=None)
            if rest:
                flags = detect_pii(rest)
                cur.pii_flags = flags if flags else None
        else:
            # continuation line
            if cur is None:
                # If file starts with non-timestamp text, treat as narration at t=0
                cur = Turn(speaker=None, t=0, text="", is_elided=False, pii_flags=None)

            cont = line.strip()
            if redact and cont:
                cont = redact_pii(cont)

            # Append with a space unless we are already at a paragraph break
            if cur.text and not cur.text.endswith("\n"):
                cur.text += " "
            cur.text += cont

            # If the timestamp line had no text after ":", it was marked elided.
            # As soon as we see real content, unmark elision.
            if cont and not ELLIPSIS_LINE.match(cont):
                cur.is_elided = False

            if cont:
                flags = detect_pii(cont)
                if flags:
                    cur.pii_flags = (cur.pii_flags or []) + flags

    if cur is not None:
        cur.text = cur.text.strip()
        turns.append(cur)

    return turns


def label_sections(turns: List[Turn]) -> None:
    """
    In-place section labeling: intro, sponsor, conversation, outro.
    Heuristic-based (works well for typical podcast transcript structure).
    """
    if not turns:
        return

    sponsor_mode = False
    sponsor_start_t = None
    outro_mode = False

    for i, tr in enumerate(turns):
        text_l = (tr.text or "").lower()

        if outro_mode:
            tr.section_type = "outro"
            continue

        if any(k in text_l for k in OUTRO_MARKERS):
            outro_mode = True
            tr.section_type = "outro"
            continue

        if not sponsor_mode and any(k in text_l for k in SPONSOR_START):
            sponsor_mode = True
            sponsor_start_t = tr.t
            tr.section_type = "sponsor"
            continue

        if sponsor_mode:
            tr.section_type = "sponsor"

            if any(k in text_l for k in SPONSOR_TRANSITION):
                sponsor_mode = False
                sponsor_start_t = None
                tr.section_type = "conversation"
                continue

            if sponsor_start_t is not None and (tr.t - sponsor_start_t) > 8 * 60:
                sponsor_mode = False
                sponsor_start_t = None
                tr.section_type = "conversation"
                continue

            continue

        # not sponsor/outro
        if i == 0:
            tr.section_type = "intro"
        else:
            saw_sponsor_before = any(t.section_type == "sponsor" for t in turns[:i])
            tr.section_type = "conversation" if saw_sponsor_before else "intro"


def make_chunks(
    turns: List[Turn],
    include_intro: bool,
    target_words: int,
    overlap_turns: int,
) -> List[Dict[str, Any]]:
    """
    Create retrieval chunks from labeled turns.
    By default, only uses conversation turns. Optionally include intro turns.
    Excludes sponsor/outro, and excludes turns that are elided ("...") or empty.
    """
    allowed = {"conversation"} | ({"intro"} if include_intro else set())

    usable: List[Turn] = [
        t for t in turns
        if t.section_type in allowed
        and (t.text or "").strip()
        and not t.is_elided
        and not ELLIPSIS_LINE.match((t.text or "").strip())
    ]

    chunks: List[Dict[str, Any]] = []
    if not usable:
        return chunks

    def word_count(s: str) -> int:
        return len(re.findall(r"\w+", s))

    i = 0
    chunk_id = 0
    while i < len(usable):
        start_i = i
        words = 0
        buf_parts: List[str] = []
        speakers = set()

        while i < len(usable) and words < target_words:
            t = usable[i]
            spk = (t.speaker or "Narration").strip()
            speakers.add(spk)
            buf_parts.append(f"{spk} ({t.t:06d}s): {t.text}")
            words += word_count(t.text)
            i += 1

        end_i = i - 1
        t_start = usable[start_i].t
        t_end = usable[end_i].t
        chunk_text = "\n".join(buf_parts).strip()

        chunks.append({
            "chunk_id": chunk_id,
            "t_start": t_start,
            "t_end": t_end,
            "speakers": sorted(speakers),
            "text": chunk_text,
        })
        chunk_id += 1

        if overlap_turns > 0:
            i = max(i - overlap_turns, start_i + 1)

    return chunks


def infer_episode_title(file_path: Path) -> str:
    return file_path.stem.replace("_", " ").strip()


def ingest_folder(input_dir: Path, output_dir: Path, include_intro: bool, redact: bool, target_words: int, overlap_turns: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    episodes_dir = output_dir / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = output_dir / "chunks.jsonl"
    episodes_index_path = output_dir / "episodes_index.jsonl"
    manifest_path = output_dir / "manifest.csv"
    stats_path = output_dir / "stats.json"

    txt_files = sorted([p for p in input_dir.glob("*.txt") if p.is_file()])
    all_chunks_count = 0
    all_turns_count = 0
    episodes_written = 0

    with chunks_path.open("w", encoding="utf-8") as f_chunks, \
         episodes_index_path.open("w", encoding="utf-8") as f_index, \
         manifest_path.open("w", newline="", encoding="utf-8") as f_csv:

        writer = csv.DictWriter(f_csv, fieldnames=[
            "episode_id", "title", "source_file", "turns", "chunks", "has_pii", "notes"
        ])
        writer.writeheader()

        for fp in txt_files:
            raw = fp.read_text(encoding="utf-8", errors="ignore")
            turns = parse_transcript(raw, redact=redact)
            label_sections(turns)
            chunks = make_chunks(turns, include_intro=include_intro, target_words=target_words, overlap_turns=overlap_turns)

            title = infer_episode_title(fp)
            episode_id = slugify(title)

            episode_obj = {
                "episode_id": episode_id,
                "title": title,
                "source_file": fp.name,
                "turns": [t.__dict__ for t in turns],
            }
            (episodes_dir / f"{episode_id}.json").write_text(
                json.dumps(episode_obj, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            has_pii = any(t.pii_flags for t in turns if t.pii_flags)
            index_obj = {
                "episode_id": episode_id,
                "title": title,
                "source_file": fp.name,
                "turn_count": len(turns),
                "chunk_count": len(chunks),
                "has_pii": bool(has_pii),
            }
            f_index.write(json.dumps(index_obj, ensure_ascii=False) + "\n")

            for ch in chunks:
                ch_obj = {
                    "episode_id": episode_id,
                    "title": title,
                    "source_file": fp.name,
                    **ch,
                }
                f_chunks.write(json.dumps(ch_obj, ensure_ascii=False) + "\n")

            notes = []
            if has_pii:
                notes.append("PII detected (consider --redact_pii)")
            writer.writerow({
                "episode_id": episode_id,
                "title": title,
                "source_file": fp.name,
                "turns": len(turns),
                "chunks": len(chunks),
                "has_pii": bool(has_pii),
                "notes": "; ".join(notes),
            })

            episodes_written += 1
            all_chunks_count += len(chunks)
            all_turns_count += len(turns)

    stats = {
        "episodes": episodes_written,
        "total_turns": all_turns_count,
        "total_chunks": all_chunks_count,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "include_intro": include_intro,
        "redact_pii": redact,
        "target_words": target_words,
        "overlap_turns": overlap_turns,
    }
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_dir", required=True, help="Folder containing .txt transcripts")
    ap.add_argument("--output_dir", required=True, help="Where to write parsed outputs")
    ap.add_argument("--include_intro", action="store_true", help="Include intro turns in chunks")
    ap.add_argument("--redact_pii", action="store_true", help="Redact emails/phones in outputs")
    ap.add_argument("--target_words", type=int, default=280, help="Approx words per chunk")
    ap.add_argument("--overlap_turns", type=int, default=1, help="Turn overlap between chunks")
    args = ap.parse_args()

    ingest_folder(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        include_intro=args.include_intro,
        redact=args.redact_pii,
        target_words=args.target_words,
        overlap_turns=args.overlap_turns,
    )

    print("Done.")
    print(f"Wrote outputs to: {args.output_dir}")


if __name__ == "__main__":
    main()
