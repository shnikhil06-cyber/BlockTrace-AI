"""
Forensic Case Manager and Dossier Builder for BlockTrace-AI.
Enables investigators to tag evidence, bookmark suspect entities,
record investigative hypotheses, and maintain tamper-evident case state.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import datetime
import json


@dataclass
class BookmarkedEvidence:
    entity_id: str
    entity_type: str  # 'transaction', 'address', 'ip'
    risk_score: float
    risk_tier: str
    pattern: str
    notes: str
    added_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ForensicCaseManager:
    """
    Manages active investigation case dossier, notes, and evidence bookmarks.
    """

    def __init__(
        self,
        case_id: str = "BT-CASE-2026-001",
        case_title: str = "Bitcoin & Network Telemetry Forensic Inquiry",
        investigator: str = "Lead Forensic Analyst",
        organization: str = "Tech Titans Cybercrime Lab"
    ):
        self.case_id = case_id
        self.case_title = case_title
        self.investigator = investigator
        self.organization = organization
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.notes: List[str] = [
            f"Case initialized on {self.created_at} by {investigator} ({organization})."
        ]
        self.bookmarks: Dict[str, BookmarkedEvidence] = {}

    def add_note(self, note_text: str):
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.notes.append(f"[{now}] {note_text}")

    def bookmark_entity(
        self,
        entity_id: str,
        entity_type: str,
        risk_score: float,
        risk_tier: str,
        pattern: str,
        notes: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> BookmarkedEvidence:
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        evidence = BookmarkedEvidence(
            entity_id=entity_id,
            entity_type=entity_type,
            risk_score=risk_score,
            risk_tier=risk_tier,
            pattern=pattern,
            notes=notes,
            added_at=now,
            metadata=metadata or {}
        )
        self.bookmarks[entity_id] = evidence
        self.add_note(f"Bookmarked {entity_type} {entity_id} ({risk_tier}, Score: {risk_score:.1f}). Note: {notes}")
        return evidence

    def remove_bookmark(self, entity_id: str) -> bool:
        if entity_id in self.bookmarks:
            del self.bookmarks[entity_id]
            self.add_note(f"Removed bookmark for {entity_id}.")
            return True
        return False

    def is_bookmarked(self, entity_id: str) -> bool:
        return entity_id in self.bookmarks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_title": self.case_title,
            "investigator": self.investigator,
            "organization": self.organization,
            "created_at": self.created_at,
            "notes": self.notes,
            "bookmarks": {
                k: {
                    "entity_id": v.entity_id,
                    "entity_type": v.entity_type,
                    "risk_score": v.risk_score,
                    "risk_tier": v.risk_tier,
                    "pattern": v.pattern,
                    "notes": v.notes,
                    "added_at": v.added_at,
                    "metadata": v.metadata
                }
                for k, v in self.bookmarks.items()
            }
        }

