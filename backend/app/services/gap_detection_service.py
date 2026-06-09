from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.neighbors import NearestNeighbors
from sqlalchemy.orm import Session

from ..application_space.gap_characterization import pseudo_application_from_boundary, summarize_boundary
from ..application_space.gap_detection import candidate_gap_points
from ..database import ApplicationClusterRecord, ApplicationNodeRecord, GapRecord
from ..exceptions import ConfigurationError
from ..schemas import ApplicationCluster, ApplicationNode, Gap, Scope
from .ids import stable_id
from .serialization import model_to_dict


class GapDetectionService:
    def detect(self, db: Session, scope: Scope) -> List[Gap]:
        node_records = db.query(ApplicationNodeRecord).filter(ApplicationNodeRecord.scope_id == scope.scope_id).all()
        if len(node_records) < 3:
            raise ConfigurationError("At least three scoped application nodes with coordinates are required to detect gaps.")
        nodes = [ApplicationNode(**record.payload) for record in node_records]
        if any(node.coordinates is None for node in nodes):
            raise ConfigurationError("Build the Application Space before gap detection.")
        coords = np.asarray([node.coordinates for node in nodes], dtype=float)
        labels = np.asarray([int((node.cluster_id or "cluster_0").replace("cluster_", "").replace("noise", "-1")) for node in nodes])
        candidates = candidate_gap_points(coords, labels)
        nbrs = NearestNeighbors(n_neighbors=min(6, len(nodes))).fit(coords)
        cluster_records = db.query(ApplicationClusterRecord).filter(ApplicationClusterRecord.scope_id == scope.scope_id).all()
        clusters = {record.cluster_id: ApplicationCluster(**record.payload) for record in cluster_records}

        gaps: List[Gap] = []
        for point, cluster_labels in candidates:
            distances, indices = nbrs.kneighbors([point])
            nearby_nodes = [nodes[index] for index in indices[0]]
            boundary = summarize_boundary(nearby_nodes)
            diversity = len(set(node.cluster_id for node in nearby_nodes if node.cluster_id)) / max(len(nearby_nodes), 1)
            avg_distance = float(np.mean(distances[0]))
            max_distance = float(np.max(np.linalg.norm(coords - coords.mean(axis=0), axis=1))) or 1.0
            novelty = min(1.0, avg_distance / max_distance)
            evidence_score = min(1.0, sum(len(node.evidence_ids) for node in nearby_nodes) / 12.0)
            mechanism_present = bool(boundary.get("mechanisms"))
            material_present = bool(boundary.get("material_classes"))
            feasibility = 0.35 + 0.25 * diversity + 0.2 * float(mechanism_present) + 0.2 * float(material_present)
            property_terms = list(boundary.get("property_requirements") or [])
            mattergen_score = self._mattergen_compatibility(property_terms, boundary)
            uncertainty = max(0.05, 1.0 - (0.35 * evidence_score + 0.35 * feasibility + 0.3 * diversity))
            overall = 0.28 * novelty + 0.24 * feasibility + 0.22 * evidence_score + 0.16 * diversity + 0.10 * mattergen_score
            gap_id = stable_id("gap", scope.scope_id, point, [node.node_id for node in nearby_nodes])
            nearby_cluster_ids = sorted(set(node.cluster_id for node in nearby_nodes if node.cluster_id))
            top_clusters = [clusters[cid].label for cid in nearby_cluster_ids if cid in clusters]
            missing = {
                "descriptor_blend": boundary,
                "hypothesized_missing_pairing": {
                    "domain": (boundary.get("domains") or [None])[0],
                    "mechanism": (boundary.get("mechanisms") or [None])[0],
                    "device_type": (boundary.get("device_types") or [None])[0],
                    "material_class": (boundary.get("material_classes") or [None])[0],
                },
            }
            gap = Gap(
                gap_id=gap_id,
                scope_id=scope.scope_id,
                title=f"Boundary gap near {', '.join(top_clusters[:2]) or 'EM application clusters'}",
                coordinates=[float(point[0]), float(point[1])],
                nearby_cluster_ids=nearby_cluster_ids,
                nearby_application_ids=[node.node_id for node in nearby_nodes],
                missing_descriptor_combination=missing,
                boundary_descriptors=boundary,
                pseudo_application_hypotheses=pseudo_application_from_boundary(boundary),
                novelty_score=float(round(novelty, 4)),
                feasibility_score=float(round(min(feasibility, 1.0), 4)),
                boundary_evidence_score=float(round(evidence_score, 4)),
                neighbour_diversity_score=float(round(diversity, 4)),
                mattergen_compatibility_score=float(round(mattergen_score, 4)),
                uncertainty_score=float(round(uncertainty, 4)),
                overall_gap_score=float(round(min(overall, 1.0), 4)),
                explanation=(
                    "This candidate lies between scoped EM application clusters and is scored from local density, "
                    "neighbour diversity, boundary evidence, mechanism/material feasibility, and MatterGen proxy compatibility."
                ),
            )
            gaps.append(gap)

        db.query(GapRecord).filter(GapRecord.scope_id == scope.scope_id).delete()
        for gap in gaps:
            db.add(
                GapRecord(
                    gap_id=gap.gap_id,
                    scope_id=scope.scope_id,
                    overall_gap_score=gap.overall_gap_score,
                    payload=model_to_dict(gap),
                )
            )
        db.commit()
        return sorted(gaps, key=lambda item: item.overall_gap_score, reverse=True)

    def list(self, db: Session, scope_id: str) -> List[Gap]:
        return [
            Gap(**record.payload)
            for record in db.query(GapRecord).filter(GapRecord.scope_id == scope_id).order_by(GapRecord.overall_gap_score.desc())
        ]

    def get(self, db: Session, gap_id: str) -> Gap:
        record = db.get(GapRecord, gap_id)
        if not record:
            raise KeyError(gap_id)
        return Gap(**record.payload)

    def characterize(self, db: Session, gap_id: str) -> Gap:
        gap = self.get(db, gap_id)
        if "characterized" not in gap.explanation:
            gap.explanation += " Boundary descriptors have been characterized into pseudo-application hypotheses."
        record = db.get(GapRecord, gap_id)
        record.payload = model_to_dict(gap)
        db.commit()
        return gap

    def _mattergen_compatibility(self, property_terms: List[str], boundary: Dict[str, object]) -> float:
        proxy_terms = {"band gap", "stability", "formation", "magnetic", "bulk modulus", "oxide", "nitride", "carbide"}
        joined = " ".join(property_terms + list(boundary.get("material_classes") or [])).lower()
        hits = sum(1 for term in proxy_terms if term in joined)
        return min(1.0, hits / 4.0)
