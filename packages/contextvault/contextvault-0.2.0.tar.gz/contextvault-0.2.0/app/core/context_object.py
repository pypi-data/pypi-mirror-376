# app/core/context_object.py

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import zipfile
import tempfile
import os
from io import BytesIO

from app.core.utils import encode_binary_to_image, decode_image_to_binary, pack_payload, unpack_payload
from app.core.indexer import index_context_object_snapshot


class ContextObject:
    def __init__(self):
        self.data: Dict[str, Any] = {
            "collections": [],
            "created_at": datetime.now().isoformat()
        }

        self.snapshot_dir = Path("data/context_snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        self.snapshot_log_file = self.snapshot_dir / "snapshot_log.json"
        self.snapshot_log: List[Dict[str, Any]] = []
        if self.snapshot_log_file.exists():
            try:
                text = self.snapshot_log_file.read_text(encoding="utf-8").strip()
                if text:
                    self.snapshot_log = json.loads(text)
            except Exception:
                self.snapshot_log = []

    # -------- Collections helpers --------
    def list_collections(self) -> List[str]:
        return [c["name"] for c in self.data.get("collections", [])]

    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        for c in self.data.get("collections", []):
            if c.get("name") == name:
                return c
        return None

    def add_collection(self, name: str) -> None:
        if not self.get_collection(name):
            self.data["collections"].append({"name": name, "entries": {}})
            self.save_snapshot()

    def add_entry_to_collection(self, collection_name: str, category: str, entry_id: str, entry: dict) -> None:
        col = self.get_collection(collection_name)
        if not col:
            self.add_collection(collection_name)
            col = self.get_collection(collection_name)

        if category not in col["entries"]:
            col["entries"][category] = {}
        col["entries"][category][entry_id] = entry
        self.save_snapshot()

    # -------- Back-compat default collection --------
    def add_entry(self, category: str, entry_id: str, entry: dict) -> None:
        if not self.data["collections"]:
            self.data["collections"].append({"name": "default", "entries": {}})

        entries = self.data["collections"][0]["entries"]
        if category not in entries:
            entries[category] = {}
        entries[category][entry_id] = entry
        self.save_snapshot()

    def get_full_state(self) -> Dict[str, Any]:
        return self.data

    # -------- Search inside context object --------
    def search(self, q: str, collection: Optional[str] = None, category: Optional[str] = None, limit: int = 50):
        ql = q.lower().strip()
        out: List[Dict[str, Any]] = []

        def match_entry(cid: str, ent: Dict[str, Any]) -> bool:
            if ql in cid.lower():
                return True
            name = str(ent.get("file_name", ""))
            if ql in name.lower():
                return True
            # search in values
            for v in ent.values():
                if isinstance(v, str) and ql in v.lower():
                    return True
            return False

        for col in self.data.get("collections", []):
            if collection and col.get("name") != collection:
                continue
            entries = col.get("entries", {})
            for cat, cat_entries in entries.items():
                if category and cat != category:
                    continue
                for eid, ent in cat_entries.items():
                    if match_entry(eid, ent):
                        out.append({
                            "collection": col.get("name"),
                            "category": cat,
                            "entry_id": eid,
                            "entry": ent,
                        })
                        if len(out) >= limit:
                            return out
        return out

    # -------- Snapshotting & versions (COMPRESSED with header) --------
    def save_snapshot(self) -> str:
        """
        Serialize current context object to JSON, ZIP it, then zlib-compress the ZIP and
        store in a PNG. We prepend a small header so we can strip padding reliably later.
        """
        context_json = json.dumps(self.data, indent=2).encode("utf-8")
        version_hash = uuid.uuid4().hex[:8]

        # zip the json
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, "w") as zf:
                zf.writestr("context.json", context_json)
            raw_zip = Path(tmp_zip.name).read_bytes()
        try:
            os.remove(tmp_zip.name)
        except Exception:
            pass

        # compress with header (so no external length needed)
        payload = pack_payload(raw_zip, with_header=True)
        img = encode_binary_to_image(payload)
        img_path = self.snapshot_dir / f"ctxobj_{version_hash}.png"
        img.save(img_path)

        # snapshot metadata
        total_entries = 0
        for col in self.data["collections"]:
            for cat_entries in col["entries"].values():
                total_entries += len(cat_entries)

        snapshot_info = {
            "version": version_hash,
            "timestamp": datetime.now().isoformat(),
            "collections": len(self.data["collections"]),
            "total_entries": total_entries,
            "snapshot_image": img_path.name
        }

        self.snapshot_log.append(snapshot_info)
        self.snapshot_log_file.write_text(json.dumps(self.snapshot_log, indent=2), encoding="utf-8")

        # index hook (non-fatal)
        try:
            index_context_object_snapshot(version_hash, snapshot_info, json.loads(context_json))
        except Exception:
            pass

        return version_hash

    def load_version(self, version_hash: str) -> Dict[str, Any]:
        """
        Load a specific version of the context object from its snapshot PNG.
        Works with new (compressed + header) snapshots and remains tolerant if older ones exist.
        """
        img_path = self.snapshot_dir / f"ctxobj_{version_hash}.png"
        if not img_path.exists():
            raise FileNotFoundError(f"Version {version_hash} not found")

        buf = decode_image_to_binary(img_path)
        # unpack with header (new snapshots), fallback to raw/decompress
        zip_bytes = unpack_payload(buf, with_header=True, known_len=None)

        with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zf:
            context_json = zf.read("context.json")
        return json.loads(context_json)

    def list_versions(self) -> List[str]:
        return [entry["version"] for entry in self.snapshot_log]

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self.snapshot_log:
            return None
        return self.snapshot_log[-1]


# Global singleton instance
context_object = ContextObject()
