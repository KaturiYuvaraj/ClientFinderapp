def test_ai_analyze_lead(client, auth_headers):
    payload = {
        "business": {
            "name": "Grand Palace Hotel",
            "category": "Hotels",
            "phone": "+91 866 244 5566",
            "website": "",
            "address": "Beside City Bus Station",
            "city": "Vijayawada",
            "rating": 4.6,
            "review_count": 180
        },
        "service": "Website Development"
    }
    response = client.post("/api/ai/analyze-lead", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_score"] >= 75
    assert len(data["verified_facts"]) > 0
    assert len(data["inferences"]) > 0
    assert "No website URL" in data["verified_facts"][0]

def test_generate_outreach_message(client, auth_headers):
    payload = {
        "business_name": "Grand Palace Hotel",
        "category": "Hotels",
        "location": "Vijayawada",
        "service": "Website Development",
        "opportunity_reason": "Listing has phone number but no website.",
        "sender_name": "Yuvaraj Tech Agency"
    }
    response = client.post("/api/ai/generate-message", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Grand Palace Hotel" in data["message"]
    assert "Vijayawada" in data["message"]
    assert "Yuvaraj Tech Agency" in data["message"]

def test_dashboard_stats(client, auth_headers):
    # Add a couple leads with different statuses
    client.post(
        "/api/leads",
        json={
            "business_name": "Lead A",
            "service": "Web Dev",
            "lead_score": 92,
            "status": "New"
        },
        headers=auth_headers
    )
    client.post(
        "/api/leads",
        json={
            "business_name": "Lead B",
            "service": "Web Dev",
            "lead_score": 85,
            "status": "Converted"
        },
        headers=auth_headers
    )

    stats_resp = client.get("/api/dashboard/stats", headers=auth_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_leads"] >= 2
    assert stats["converted"] >= 1
    assert stats["high_opportunity_leads"] >= 2
    assert stats["conversion_rate"] > 0
