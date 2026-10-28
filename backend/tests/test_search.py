def test_search_businesses(client, auth_headers):
    search_payload = {
        "service": "Website Development",
        "category": "Restaurants",
        "location": "Vijayawada",
        "radius": "20 km"
    }
    response = client.post("/api/leads/search", json=search_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    results = data["results"]
    assert len(results) > 0

    first_item = results[0]
    # Verify normalized structure
    assert "name" in first_item
    assert "phone" in first_item
    assert "website" in first_item
    assert "address" in first_item
    assert "city" in first_item
    assert "latitude" in first_item
    assert "longitude" in first_item
    assert "rating" in first_item
    assert "review_count" in first_item
    assert "source" in first_item

    # Verify AI Opportunity fields
    assert "lead_score" in first_item
    assert isinstance(first_item["lead_score"], int)
    assert 0 <= first_item["lead_score"] <= 100
    assert "verified_facts" in first_item
    assert isinstance(first_item["verified_facts"], list)
    assert "inferences" in first_item
    assert isinstance(first_item["inferences"], list)
    assert len(first_item["verified_facts"]) > 0

def test_search_history_recorded(client, auth_headers):
    client.post(
        "/api/leads/search",
        json={
            "service": "Logo Design",
            "category": "Salons",
            "location": "Vijayawada",
            "radius": "15 km"
        },
        headers=auth_headers
    )
    # Check history
    response = client.get("/api/leads/search-history", headers=auth_headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1
    assert history[0]["service"] == "Logo Design"
    assert history[0]["category"] == "Salons"
    assert history[0]["location"] == "Vijayawada"
