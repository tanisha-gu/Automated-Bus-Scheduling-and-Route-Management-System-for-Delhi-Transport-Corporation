"""
Route Manager — overlap detection and route optimization for DTC
Uses stop-name intersection to find shared segments between routes.
"""

from typing import List, Dict, Any


class RouteManager:

    def find_overlaps(self, candidate: Dict, existing_routes: List[Dict]) -> List[Dict]:
        """
        Find overlapping stops between a candidate route and all existing routes.
        Returns list of overlap descriptors with severity assessment.
        """
        overlaps = []
        cand_stops = set(s.strip().lower() for s in candidate.get("stops", []))

        if not cand_stops:
            return overlaps

        for route in existing_routes:
            if route["id"] == candidate.get("id"):
                continue
            route_stops = set(s.strip().lower() for s in route.get("stops", []))
            common = cand_stops & route_stops

            if not common:
                continue

            overlap_pct = round(len(common) / max(len(cand_stops), 1) * 100, 1)
            severity = self._severity(overlap_pct)

            # Find contiguous overlap segments
            cand_list = [s.strip().lower() for s in candidate.get("stops", [])]
            route_list = [s.strip().lower() for s in route.get("stops", [])]
            segments = self._find_contiguous_segments(cand_list, route_list, common)

            overlaps.append({
                "route_id": route["id"],
                "route_name": route["name"],
                "route_color": route.get("color", "#999"),
                "common_stops": sorted(list(common)),
                "common_stop_count": len(common),
                "overlap_pct": overlap_pct,
                "severity": severity,
                "segments": segments,
                "recommendation": self._recommend(severity, overlap_pct, route),
            })

        overlaps.sort(key=lambda x: x["overlap_pct"], reverse=True)
        return overlaps

    def _severity(self, pct: float) -> str:
        if pct >= 60:
            return "High"
        elif pct >= 30:
            return "Medium"
        return "Low"

    def _find_contiguous_segments(self, cand_list, route_list, common):
        """Find runs of consecutive shared stops in candidate order."""
        segments = []
        current_seg = []
        for stop in cand_list:
            if stop in common:
                current_seg.append(stop)
            else:
                if len(current_seg) >= 2:
                    segments.append(current_seg)
                current_seg = []
        if len(current_seg) >= 2:
            segments.append(current_seg)
        return segments

    def _recommend(self, severity: str, pct: float, route: Dict) -> str:
        if severity == "High":
            return (
                f"High overlap ({pct}%) with {route['name']}. "
                "Consider merging routes or adjusting frequency to avoid duplication."
            )
        elif severity == "Medium":
            return (
                f"Moderate overlap ({pct}%) with {route['name']}. "
                "Stagger departure times to distribute passenger load."
            )
        return (
            f"Minor overlap ({pct}%) with {route['name']}. "
            "Acceptable — ensures passenger connectivity at shared stops."
        )

    def optimize_coverage(self, routes: List[Dict]) -> Dict:
        """Basic coverage analysis — identify under-served areas."""
        all_stops = {}
        for r in routes:
            for stop in r.get("stops", []):
                s = stop.strip().lower()
                all_stops[s] = all_stops.get(s, 0) + 1

        over_served = [s for s, c in all_stops.items() if c >= 3]
        adequately_served = [s for s, c in all_stops.items() if c == 2]
        under_served = [s for s, c in all_stops.items() if c == 1]

        return {
            "total_unique_stops": len(all_stops),
            "over_served_stops": over_served,
            "adequately_served_stops": adequately_served,
            "under_served_stops": under_served,
            "coverage_score": round(
                (len(adequately_served) + len(over_served)) / max(len(all_stops), 1) * 100, 1
            ),
        }
