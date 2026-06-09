from __future__ import annotations

from collections import Counter
from typing import Dict, List

from ..schemas import ApplicationCluster, ApplicationNode


def application_space_metrics(nodes: List[ApplicationNode], clusters: List[ApplicationCluster]) -> Dict[str, float]:
    if not nodes:
        return {"descriptor_coherence_score": 0.0, "nearest_neighbour_relevance": 0.0, "cluster_summary_quality": 0.0}
    cluster_lookup = {cluster.cluster_id: cluster for cluster in clusters}
    coherent = 0
    for node in nodes:
        cluster = cluster_lookup.get(node.cluster_id or "")
        if cluster and (node.domain in cluster.domains or node.physical_em_mechanism in cluster.mechanisms):
            coherent += 1
    nonempty_summaries = sum(1 for cluster in clusters if len(cluster.summary) > 20)
    cluster_sizes = Counter(node.cluster_id for node in nodes)
    balanced = sum(1 for _, count in cluster_sizes.items() if count > 1) / max(len(cluster_sizes), 1)
    return {
        "descriptor_coherence_score": round(coherent / len(nodes), 4),
        "nearest_neighbour_relevance": round(balanced, 4),
        "cluster_summary_quality": round(nonempty_summaries / max(len(clusters), 1), 4),
    }
