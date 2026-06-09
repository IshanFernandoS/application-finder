from __future__ import annotations

from typing import List

from ..schemas import Gap


class QueryPlannerService:
    def boundary_queries(self, gap: Gap) -> List[str]:
        descriptors = gap.boundary_descriptors
        terms: List[str] = []
        for key in ["domains", "device_types", "mechanisms", "material_classes", "property_requirements"]:
            terms.extend(list(descriptors.get(key) or [])[:3])
        base = " ".join(term for term in terms if term)
        queries = [
            base,
            f"{base} electromagnetic material property limitation",
            f"{base} device architecture mechanism evidence",
            f"{base} failure limitation validation",
        ]
        return [query.strip() for query in queries if query.strip()]
