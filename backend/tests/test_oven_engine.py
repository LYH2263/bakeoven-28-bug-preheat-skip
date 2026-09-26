from app.services.oven_engine import (
    Interval,
    Occupancy,
    RecipeDurations,
    build_occupancies,
    find_conflicts,
    next_free_window,
    required_preheat_min,
)


def test_half_open_no_touch_conflict():
    a = Occupancy(1, Interval(0, 30), "bake", 1)
    b = Occupancy(1, Interval(30, 60), "bake", 2)
    assert find_conflicts([a], [b]) == []


def test_overlap_detected():
    recipe = RecipeDurations(20, 30)
    cand = build_occupancies(1, 9, 10, recipe)
    existing = [Occupancy(1, Interval(25, 40), "bake", 1)]
    assert find_conflicts(existing, cand)


def test_next_free_window_after_busy():
    existing = [
        Occupancy(1, Interval(0, 40), "ferment", 1),
        Occupancy(1, Interval(40, 70), "bake", 1),
    ]
    w = next_free_window(existing, 1, duration=30, search_from=0)
    assert w == Interval(70, 100)


def test_next_free_in_gap():
    existing = [
        Occupancy(1, Interval(0, 20), "bake", 1),
        Occupancy(1, Interval(80, 100), "bake", 2),
    ]
    w = next_free_window(existing, 1, duration=30, search_from=0)
    assert w == Interval(20, 50)


def test_required_preheat_only_on_profile_change():
    assert required_preheat_min("高温", "中温", 15) == 15
    assert required_preheat_min("高温", "高温", 15) == 0
    assert required_preheat_min(None, "高温", 15) == 0
    assert required_preheat_min("", "高温", 15) == 0
    assert required_preheat_min("高温", "中温", 0) == 0


def test_preheat_occupancy_inserted_before_start():
    occs = build_occupancies(1, 9, 630, RecipeDurations(25, 20), preheat_min=15)
    assert [o.phase for o in occs] == ["preheat", "ferment", "bake"]
    assert occs[0].interval == Interval(615, 630)
    assert occs[1].interval == Interval(630, 655)
    assert occs[2].interval == Interval(655, 675)


def test_no_preheat_occupancy_when_zero():
    occs = build_occupancies(1, 9, 630, RecipeDurations(25, 20), preheat_min=0)
    assert [o.phase for o in occs] == ["ferment", "bake"]


def test_preheat_overlap_detected():
    # 已有批次烘烤到 10:20，新批次 10:30 开工需 15 分钟预热（10:15 起）→ 重叠
    existing = [Occupancy(1, Interval(610, 620), "bake", 1)]
    cand = build_occupancies(1, 9, 630, RecipeDurations(25, 20), preheat_min=15)
    hits = find_conflicts(existing, cand)
    assert hits and hits[0][1].phase == "preheat"


def test_preheat_touching_is_half_open_no_conflict():
    # 已有批次 10:15 结束，预热段 [10:15,10:30) 半开相接 → 不冲突
    existing = [Occupancy(1, Interval(580, 615), "bake", 1)]
    cand = build_occupancies(1, 9, 630, RecipeDurations(25, 20), preheat_min=15)
    assert find_conflicts(existing, cand) == []


def test_preheat_occupancy_blocks_later_windows():
    # 预热段同样占炉：其后的窗口搜索要避开预热段
    existing = [Occupancy(1, Interval(615, 630), "preheat", 1)]
    w = next_free_window(existing, 1, duration=30, search_from=600)
    assert w == Interval(630, 660)
