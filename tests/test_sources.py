def test_create_and_list_sources(client):
    source_payload = {
        "name": "MIT News",
        "url": "https://news.mit.edu",
        "feed_url": "https://news.mit.edu/rss/feed",
        "source_type": "rss",
        "domain": "Science",
        "reliability_score": 0.98,
        "enabled": True
    }
    create_resp = client.post("/api/v1/sources", json=source_payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["name"] == "MIT News"
    assert created_data["id"] is not None

    # List sources
    list_resp = client.get("/api/v1/sources")
    assert list_resp.status_code == 200
    sources = list_resp.json()
    assert len(sources) >= 1
    assert any(s["name"] == "MIT News" for s in sources)


def test_duplicate_source_rejection(client):
    source_payload = {
        "name": "Duplicate Test Feed",
        "url": "https://example.com",
        "feed_url": "https://example.com/rss",
        "source_type": "rss",
        "domain": "Technology",
        "reliability_score": 1.0,
        "enabled": True
    }
    client.post("/api/v1/sources", json=source_payload)
    dup_resp = client.post("/api/v1/sources", json=source_payload)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]
