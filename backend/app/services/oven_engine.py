"""Oven scheduling with half-open ferment+bake intervals and next free window."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class Interval:
    start: int  # minutes from day origin
    end: int  # exclusive

    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class RecipeDurations:
    ferment_min: int
    bake_min: int

    @property
    def total(self) -> int:
        return self.ferment_min + self.bake_min


@dataclass(frozen=True)
class Occupancy:
    oven_id: int
    interval: Interval
    phase: str  # preheat | ferment | bake
    batch_id: int


def required_preheat_min(prev_profile: str | None, profile: str, oven_preheat_min: int) -> int:
    """Preheat minutes required: only when the oven's previous batch ran a different profile."""
    if not prev_profile or prev_profile == profile:
        return 0
    return oven_preheat_min


def same_profile_may_overlap(prev_profile: str | None, profile: str) -> bool:
    """Whether batches may overlap on the same oven: only while the profile is unchanged."""
    if not prev_profile:
        return True
    return prev_profile == profile


def preheat_conflict_phase_label(phase: str) -> str:
    return {"preheat": "预热", "ferment": "发酵", "bake": "烘烤"}.get(phase, phase)


def build_occupancies(
    oven_id: int,
    batch_id: int,
    start_min: int,
    recipe: RecipeDurations,
    preheat_min: int = 0,
) -> list[Occupancy]:
    out: list[Occupancy] = []
    if preheat_min > 0:
        out.append(Occupancy(oven_id, Interval(start_min - preheat_min, start_min), "preheat", batch_id))
    ferment = Interval(start_min, start_min + recipe.ferment_min)
    bake = Interval(ferment.end, ferment.end + recipe.bake_min)
    out.extend(
        [
            Occupancy(oven_id, ferment, "ferment", batch_id),
            Occupancy(oven_id, bake, "bake", batch_id),
        ]
    )
    return out


def find_conflicts(existing: list[Occupancy], candidates: list[Occupancy]) -> list[tuple[Occupancy, Occupancy]]:
    hits: list[tuple[Occupancy, Occupancy]] = []
    for cand in candidates:
        for ex in existing:
            if ex.oven_id != cand.oven_id:
                continue
            if ex.interval.overlaps(cand.interval):
                hits.append((ex, cand))
    return hits


def next_free_window(
    existing: list[Occupancy],
    oven_id: int,
    duration: int,
    search_from: int = 0,
    search_to: int = 24 * 60,
) -> Interval | None:
    """Find earliest half-open [start, start+duration) free on oven."""
    if duration <= 0:
        return None
    busy = sorted(
        [o.interval for o in existing if o.oven_id == oven_id],
        key=lambda i: i.start,
    )
    cursor = search_from
    for iv in busy:
        if iv.end <= cursor:
            continue
        if iv.start >= cursor + duration:
            end = cursor + duration
            if end <= search_to:
                return Interval(cursor, end)
            return None
        cursor = max(cursor, iv.end)
    if cursor + duration <= search_to:
        return Interval(cursor, cursor + duration)
    return None
