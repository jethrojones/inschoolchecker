from datetime import date


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_get_cached_result_for_existing_district(client, seeded_district):
    response = client.post(
        "/api/check",
        json={"district_url": seeded_district.homepage_url, "target_date": "2026-03-27"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["district"]["canonical_domain"] == "examplek12.org"
    assert body["status"] == "out_of_school"
    assert body["target_date"] == "2026-03-27"


def test_manual_override_supersedes_inference(client, seeded_district):
    response = client.post(
        "/api/admin/overrides",
        json={
            "district_id": seeded_district.id,
            "target_date": "2026-03-27",
            "status": "delayed_or_modified",
            "explanation": "Manual review found a district-wide two-hour delay.",
            "created_by": "operator@example.com",
            "reason": "Same-day announcement confirmed after cached result was generated."
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result_type"] == "manual_override"
    assert body["status"] == "delayed_or_modified"


def test_admin_results_lists_cached_inference(client, seeded_district):
    response = client.get("/api/admin/results")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["district_name"] == "Example Public Schools"


def test_invalid_url_returns_400(client):
    response = client.post("/api/check", json={"district_url": "ftp://bad.example", "target_date": "2026-03-27"})
    assert response.status_code == 400


def test_cors_preflight_allows_frontend_origin(client):
    response = client.options(
        "/api/check",
        headers={
            "Origin": "https://jethrojones.github.io",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://jethrojones.github.io"
