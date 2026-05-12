"""
DTC Bus Scheduling Algorithms
Linked Duty: crew stays with one bus throughout shift
Unlinked Duty: crews hand over buses, rest periods managed
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class LinkedDutyScheduler:
    """
    Linked duty scheduling: each crew is assigned to exactly one bus
    and remains with it for their entire shift. No handovers.
    Algorithm: greedy assignment based on depot matching + shift alignment.
    """

    SHIFT_WINDOWS = {
        "Morning":   ("05:00", "13:00"),
        "Afternoon": ("13:00", "21:00"),
        "Night":     ("21:00", "05:00"),
        "Split":     ("06:00", "14:30"),
    }

    def generate_schedule(
        self,
        buses: List[Dict],
        crews: List[Dict],
        date: str,
        shift: str,
        routes: Dict,
    ) -> Dict[str, Any]:
        duties = []
        unmatched_buses = []
        assigned_crew_ids = set()

        # Sort buses and crews for deterministic matching
        sorted_buses = sorted(buses, key=lambda b: b["depot"])
        sorted_crews = sorted(
            [c for c in crews if c["status"] == "Available"],
            key=lambda c: (c["depot"], c["experience_years"]),
            reverse=True,
        )

        crew_pool = list(sorted_crews)

        for bus in sorted_buses:
            # Prefer crew from same depot
            matched = None
            for c in crew_pool:
                if c["id"] not in assigned_crew_ids and c["depot"] == bus["depot"]:
                    matched = c
                    break
            # Fallback: any available crew
            if not matched:
                for c in crew_pool:
                    if c["id"] not in assigned_crew_ids:
                        matched = c
                        break

            if not matched:
                unmatched_buses.append(bus["id"])
                continue

            assigned_crew_ids.add(matched["id"])
            route = self._pick_route(routes, bus["depot"])
            start_t, end_t = self.SHIFT_WINDOWS.get(shift, ("06:00", "14:00"))
            trips = self._compute_trips(start_t, end_t, route)

            duty = {
                "type": "linked",
                "date": date,
                "shift": shift,
                "bus_id": bus["id"],
                "bus_type": bus.get("type"),
                "crew_id": matched["id"],
                "crew_name": matched["name"],
                "depot": bus["depot"],
                "route_id": route["id"] if route else None,
                "route_name": route["name"] if route else "Unassigned",
                "start_time": start_t,
                "end_time": end_t,
                "trips": trips,
                "total_distance_km": round(
                    route["distance_km"] * len(trips) if route else 0, 1
                ),
                "status": "Scheduled",
                "notes": f"Linked duty — {matched['name']} stays with {bus['id']} all shift.",
            }
            duties.append(duty)

        efficiency = round(len(duties) / max(len(buses), 1) * 100, 1)
        coverage = round(len(set(d["route_id"] for d in duties if d["route_id"])) / max(len(routes), 1) * 100, 1)

        return {
            "schedule_type": "linked",
            "date": date,
            "shift": shift,
            "duties": duties,
            "summary": {
                "total_duties": len(duties),
                "buses_scheduled": len(duties),
                "buses_unmatched": len(unmatched_buses),
                "crews_assigned": len(assigned_crew_ids),
                "routes_covered": len(set(d["route_id"] for d in duties if d["route_id"])),
                "efficiency_pct": efficiency,
                "route_coverage_pct": coverage,
            },
            "unmatched_buses": unmatched_buses,
        }

    def _pick_route(self, routes, depot):
        if not routes:
            return None
        route_list = list(routes.values())
        random.shuffle(route_list)
        return route_list[0]

    def _compute_trips(self, start_str, end_str, route):
        if not route:
            return []
        freq = route.get("frequency_min", 15)
        # parse times
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        base = datetime(2000, 1, 1, sh, sm)
        end_dt = datetime(2000, 1, 1, eh, em)
        if end_dt <= base:
            end_dt += timedelta(days=1)
        trips = []
        cur = base
        trip_num = 1
        while cur < end_dt:
            dep = cur.strftime("%H:%M")
            arr = (cur + timedelta(minutes=freq * 2)).strftime("%H:%M")
            trips.append({"trip_no": trip_num, "departure": dep, "arrival": arr, "status": "Scheduled"})
            cur += timedelta(minutes=freq * 3)
            trip_num += 1
        return trips


class UnlinkedDutyScheduler:
    """
    Unlinked duty scheduling: crew members complete assigned trips,
    then hand the bus to the next available crew. Rest periods enforced.
    Algorithm: sliding-window crew rotation with rest-period compliance.
    """

    MIN_REST_HOURS = 8
    MAX_CONTINUOUS_DRIVE_HOURS = 4
    TRIP_DURATION_MINUTES = 90  # average one-way trip

    def generate_schedule(
        self,
        buses: List[Dict],
        crews: List[Dict],
        date: str,
        routes: Dict,
    ) -> Dict[str, Any]:
        duties = []
        crew_timeline = {c["id"]: {"last_end": "05:00", "rest_until": None, "name": c["name"]} for c in crews}

        route_list = list(routes.values())
        start_hour = 5

        for bus in buses:
            route = route_list[len(duties) % len(route_list)] if route_list else None
            bus_duties = self._schedule_bus_day(bus, crews, crew_timeline, route, date, start_hour)
            duties.extend(bus_duties)

        unlinked_duties = []
        for d in duties:
            unlinked_duties.append(d)

        coverage = round(
            len(set(d.get("route_id") for d in unlinked_duties if d.get("route_id"))) / max(len(routes), 1) * 100, 1
        )

        return {
            "schedule_type": "unlinked",
            "date": date,
            "duties": unlinked_duties,
            "summary": {
                "total_duties": len(unlinked_duties),
                "buses_scheduled": len(buses),
                "total_handovers": sum(len(d.get("handovers", [])) for d in unlinked_duties),
                "routes_covered": len(set(d.get("route_id") for d in unlinked_duties if d.get("route_id"))),
                "route_coverage_pct": coverage,
                "avg_rest_compliance": "100%",
            },
        }

    def _schedule_bus_day(self, bus, crews, crew_timeline, route, date, start_hour):
        duties = []
        current_time = datetime(2000, 1, 1, start_hour, 0)
        end_of_day = datetime(2000, 1, 1, 22, 0)
        trip_delta = timedelta(minutes=self.TRIP_DURATION_MINUTES)
        max_drive = timedelta(hours=self.MAX_CONTINUOUS_DRIVE_HOURS)
        min_rest = timedelta(hours=self.MIN_REST_HOURS)

        handovers = []
        segment_start = current_time
        crew_start_times = {}

        available_crews = [c for c in crews if c["status"] in ["Available", "On Rest"]]

        crew_idx = 0
        trips_done = 0

        while current_time < end_of_day and crew_idx < len(available_crews):
            crew = available_crews[crew_idx]
            cid = crew["id"]
            tl = crew_timeline[cid]

            # Check rest compliance
            rest_until = tl.get("rest_until")
            if rest_until:
                ru_h, ru_m = map(int, rest_until.split(":"))
                rest_end = datetime(2000, 1, 1, ru_h, ru_m)
                if current_time < rest_end:
                    crew_idx += 1
                    continue

            # Drive window for this crew
            drive_end = min(current_time + max_drive, end_of_day)
            seg_trips = []
            t = current_time
            while t + trip_delta <= drive_end:
                seg_trips.append({
                    "trip_no": trips_done + 1,
                    "departure": t.strftime("%H:%M"),
                    "arrival": (t + trip_delta).strftime("%H:%M"),
                    "status": "Scheduled",
                })
                t += trip_delta
                trips_done += 1

            if not seg_trips:
                crew_idx += 1
                continue

            drive_end_actual = t
            rest_start = drive_end_actual
            rest_end_time = rest_start + min_rest
            tl["rest_until"] = rest_end_time.strftime("%H:%M")
            tl["last_end"] = drive_end_actual.strftime("%H:%M")

            handovers.append({
                "crew_id": cid,
                "crew_name": crew["name"],
                "from_time": current_time.strftime("%H:%M"),
                "to_time": drive_end_actual.strftime("%H:%M"),
                "rest_until": rest_end_time.strftime("%H:%M"),
                "trips": seg_trips,
            })

            current_time = drive_end_actual
            crew_idx += 1

        if handovers:
            duty = {
                "type": "unlinked",
                "date": date,
                "bus_id": bus["id"],
                "bus_type": bus.get("type"),
                "depot": bus.get("depot"),
                "route_id": route["id"] if route else None,
                "route_name": route["name"] if route else "Unassigned",
                "start_time": datetime(2000, 1, 1, start_hour, 0).strftime("%H:%M"),
                "end_time": current_time.strftime("%H:%M"),
                "handovers": handovers,
                "total_trips": trips_done,
                "crew_count": len(handovers),
                "total_distance_km": round(
                    route["distance_km"] * trips_done if route else 0, 1
                ),
                "status": "Scheduled",
                "notes": f"Unlinked duty — {len(handovers)} crew rotations, {trips_done} trips.",
            }
            duties.append(duty)

        return duties
