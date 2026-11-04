"""
Tests for JARVIS Google Maps Harvester & 20-Email Outreach Dispatch Engine
Architect: Ansh Tiwari
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
from core.google_maps_harvester import US_METROS, METRO_AREA_CODES, METRO_VALID_AREA_CODES, google_maps_harvester


def test_500_businesses_generation_and_valid_maps_urls():
    leads = google_maps_harvester.generate_500_businesses()
    assert len(leads) == 500, f"Expected 500 leads, got {len(leads)}"

    for lead in leads:
        # 1. No website presence
        assert lead["has_website"] is False
        assert lead["website"] == ""

        # 2. Good Google reviews (>= 4.0 stars)
        assert lead["rating"] >= 4.0
        assert lead["review_count"] >= 10

        # 3. 100% Working Canonical Google Maps Place URL (Direct Place Card Profile, Zero Competitor List Ambiguity)
        url = lead["google_maps_url"]
        assert "google.com/maps/place" in url
        assert "place_id" in url or "data=" in url
        assert "?cid=" not in url

        # 4. Zero whitespace in contact emails
        assert " " not in lead["contact_email"], f"Email '{lead['contact_email']}' contains invalid whitespace"

        # 5. Verified area code matches the city's valid telecommunication overlay
        city = lead["city"]
        valid_areas = METRO_VALID_AREA_CODES.get(city, {METRO_AREA_CODES.get(city)})
        assert any(f"({ac})" in lead["phone"] for ac in valid_areas), (
            f"Phone {lead['phone']} does not match valid area codes {valid_areas} for {city}"
        )


def test_20_grounded_emails_brevity_and_anti_spam():
    leads = google_maps_harvester.generate_500_businesses()
    emails = google_maps_harvester.draft_20_grounded_emails(leads, sender_name="Ansh")
    assert len(emails) == 20

    for i, em in enumerate(emails, start=1):
        assert em["index"] == i
        assert em["word_count"] < 100, f"Email {i} exceeds 100 words: {em['word_count']} words"
        assert em["business_name"] in em["body"]
        assert str(em["verified_facts"]["rating"]) in em["body"]
        assert str(em["verified_facts"]["review_count"]) in em["body"]
        assert em["to"]
        assert " " not in em["to"]
        assert "google_maps_url" in em
        assert "google.com/maps/place/" in em["google_maps_url"]


def test_export_and_dispatcher_script(tmp_path):
    leads = google_maps_harvester.generate_500_businesses()
    exp_files = google_maps_harvester.export_csv_and_json(leads, tmp_path)

    csv_p = Path(exp_files["csv_path"])
    json_p = Path(exp_files["json_path"])
    assert csv_p.exists()
    assert json_p.exists()

    with open(csv_p, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 500
        # Check first lead
        first = reader[0]
        assert "google.com/maps/place" in first["google_maps_url"]
        assert "?cid=" not in first["google_maps_url"]

    emails = google_maps_harvester.draft_20_grounded_emails(leads, sender_name="Ansh")
    out_files = google_maps_harvester.write_outreach_files(emails, tmp_path)
    disp_p = Path(out_files["dispatcher_file"])
    assert disp_p.exists()

    # Verify python syntax and preview execution
    res = subprocess.run(
        [sys.executable, str(disp_p), "--dry-run"],
        cwd=str(tmp_path),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    assert res.returncode == 0, f"Dispatcher failed: {res.stderr}"
    assert "Generated 20 dispatch logs" in res.stdout
    assert (tmp_path / "email_dispatch_log.json").exists()
    assert (tmp_path / "outreach_status.csv").exists()
