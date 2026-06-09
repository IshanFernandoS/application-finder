from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List

import numpy as np
from sqlalchemy.orm import Session

from ..application_space.clustering import cluster_points
from ..application_space.descriptor_schema import descriptor_text
from ..application_space.reducer import reduce_to_2d
from ..database import (
    ApplicationBuildRecord,
    ApplicationClusterRecord,
    ApplicationNodeRecord,
    GapRecord,
)
from ..exceptions import ConfigurationError
from ..schemas import ApplicationCluster, ApplicationNode, ApplicationSpaceBuild, ApplicationSpaceResponse, Gap
from .ids import new_id, stable_id
from .serialization import model_to_dict


class ApplicationSpaceService:
    def build(self, db: Session, scope_id: str, random_seed: int = 42) -> ApplicationSpaceResponse:
        node_records = db.query(ApplicationNodeRecord).filter(ApplicationNodeRecord.scope_id == scope_id).all()
        if not node_records:
            raise ConfigurationError(
                "No ApplicationNode records exist for this scope. Ingest literature and run descriptor extraction first."
            )
        nodes = [ApplicationNode(**record.payload) for record in node_records]
        texts = [descriptor_text(node) for node in nodes]
        from sklearn.feature_extraction.text import TfidfVectorizer

        matrix = TfidfVectorizer(max_features=768, ngram_range=(1, 2), min_df=1).fit_transform(texts)
        coords, reducer_name = reduce_to_2d(matrix, random_seed=random_seed)
        labels, clusterer_name = cluster_points(coords, random_seed=random_seed)

        for node, coord, label in zip(nodes, coords, labels):
            cluster_id = f"cluster_{int(label)}" if int(label) >= 0 else "cluster_noise"
            node.coordinates = [float(coord[0]), float(coord[1])]
            node.cluster_id = cluster_id
            node.evidence_count = len(node.evidence_ids)
            record = db.get(ApplicationNodeRecord, node.node_id)
            record.cluster_id = cluster_id
            record.payload = model_to_dict(node)

        clusters = self._summarize_clusters(nodes, coords, labels, scope_id)
        db.query(ApplicationClusterRecord).filter(ApplicationClusterRecord.scope_id == scope_id).delete()
        for cluster in clusters:
            db.add(
                ApplicationClusterRecord(
                    cluster_id=cluster.cluster_id,
                    scope_id=scope_id,
                    payload=model_to_dict(cluster),
                )
            )
        build = ApplicationSpaceBuild(
            build_id=new_id("build"),
            scope_id=scope_id,
            random_seed=random_seed,
            reducer=reducer_name,
            clusterer=clusterer_name,
            density_method="nearest-neighbour-distance",
            node_count=len(nodes),
            cluster_count=len(clusters),
            created_at=datetime.now(timezone.utc).isoformat(),
            metrics={
                "coordinate_extent": {
                    "x": [float(coords[:, 0].min()), float(coords[:, 0].max())],
                    "y": [float(coords[:, 1].min()), float(coords[:, 1].max())],
                }
            },
        )
        db.add(ApplicationBuildRecord(build_id=build.build_id, scope_id=scope_id, payload=model_to_dict(build)))
        db.commit()
        return ApplicationSpaceResponse(build=build, nodes=nodes, clusters=clusters, gaps=self.list_gaps(db, scope_id))

    def get_space(self, db: Session, scope_id: str) -> ApplicationSpaceResponse:
        build_record = (
            db.query(ApplicationBuildRecord)
            .filter(ApplicationBuildRecord.scope_id == scope_id)
            .order_by(ApplicationBuildRecord.created_at.desc())
            .first()
        )
        if not build_record:
            raise ConfigurationError("Application Space has not been built for this scope.")
        nodes = [
            ApplicationNode(**record.payload)
            for record in db.query(ApplicationNodeRecord).filter(ApplicationNodeRecord.scope_id == scope_id).all()
        ]
        clusters = self.list_clusters(db, scope_id)
        return ApplicationSpaceResponse(
            build=ApplicationSpaceBuild(**build_record.payload),
            nodes=nodes,
            clusters=clusters,
            gaps=self.list_gaps(db, scope_id),
        )

    def list_clusters(self, db: Session, scope_id: str) -> List[ApplicationCluster]:
        return [
            ApplicationCluster(**record.payload)
            for record in db.query(ApplicationClusterRecord).filter(ApplicationClusterRecord.scope_id == scope_id).all()
        ]

    def list_gaps(self, db: Session, scope_id: str) -> List[Gap]:
        return [
            Gap(**record.payload)
            for record in db.query(GapRecord)
            .filter(GapRecord.scope_id == scope_id)
            .order_by(GapRecord.overall_gap_score.desc())
            .all()
        ]

    def get_node(self, db: Session, node_id: str) -> ApplicationNode:
        record = db.get(ApplicationNodeRecord, node_id)
        if not record:
            raise KeyError(node_id)
        return ApplicationNode(**record.payload)

    def _summarize_clusters(
        self, nodes: List[ApplicationNode], coords: np.ndarray, labels: np.ndarray, scope_id: str
    ) -> List[ApplicationCluster]:
        grouped: Dict[str, List[ApplicationNode]] = defaultdict(list)
        coord_grouped: Dict[str, List[List[float]]] = defaultdict(list)
        for node, coord, label in zip(nodes, coords, labels):
            cluster_id = f"cluster_{int(label)}" if int(label) >= 0 else "cluster_noise"
            grouped[cluster_id].append(node)
            coord_grouped[cluster_id].append([float(coord[0]), float(coord[1])])

        clusters: List[ApplicationCluster] = []
        for cluster_id, members in grouped.items():
            domains = [node.domain for node in members if node.domain]
            mechanisms = [node.physical_em_mechanism for node in members if node.physical_em_mechanism]
            materials = [node.material_class for node in members if node.material_class]
            device_types = [node.device_type for node in members if node.device_type]
            center = np.asarray(coord_grouped[cluster_id], dtype=float).mean(axis=0).tolist()
            label = Counter(device_types or domains or [cluster_id]).most_common(1)[0][0]
            summary = (
                f"{label} cluster spanning {', '.join(Counter(domains).keys())[:120]} "
                f"with mechanisms including {', '.join(Counter(mechanisms).keys())[:120]}."
            )
            clusters.append(
                ApplicationCluster(
                    cluster_id=cluster_id,
                    label=label,
                    summary=summary,
                    node_ids=[node.node_id for node in members],
                    centroid=[float(center[0]), float(center[1])],
                    domains=[value for value, _ in Counter(domains).most_common(6)],
                    mechanisms=[value for value, _ in Counter(mechanisms).most_common(6)],
                    material_classes=[value for value, _ in Counter(materials).most_common(6)],
                    evidence_count=sum(len(node.evidence_ids) for node in members),
                )
            )
        return sorted(clusters, key=lambda cluster: cluster.cluster_id)
