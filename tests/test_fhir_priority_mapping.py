from app.fhir import triage_task, TRIAGE_TO_PRIORITY


class TestTriageToPriorityMapping:
    """Ensure agent triage labels map to correct FHIR Task priorities."""

    def test_urgent_review_maps_to_asap(self):
        task = triage_task("urgent review", ["spo2=88 < 92"], "2025-01-01T00:00:00Z", "p1")
        assert task["priority"] == "asap"

    def test_watch_maps_to_urgent(self):
        task = triage_task("watch", ["hr=120 > 110"], "2025-01-01T00:00:00Z", "p1")
        assert task["priority"] == "urgent"

    def test_ok_maps_to_routine(self):
        task = triage_task("ok", ["all vitals within range"], "2025-01-01T00:00:00Z", "p1")
        assert task["priority"] == "routine"

    def test_legacy_critical_maps_to_asap(self):
        task = triage_task("critical", ["spo2=80"], "2025-01-01T00:00:00Z", "p1")
        assert task["priority"] == "asap"

    def test_unknown_triage_defaults_to_urgent(self):
        task = triage_task("unknown_label", [], "2025-01-01T00:00:00Z", "p1")
        assert task["priority"] == "urgent"

    def test_mapping_keys_include_agent_labels(self):
        for label in ("urgent review", "watch", "ok"):
            assert label in TRIAGE_TO_PRIORITY
