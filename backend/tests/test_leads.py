def test_create_and_get_lead(client, auth_headers):
    lead_data = {
        "business_name": "Spice Garden Biryani",
        "category": "Restaurants",
        "phone": "+91 866 244 9988",
        "website": "",
        "address": "MG Road, Benz Circle",
        "city": "Vijayawada",
        "rating": 4.5,
        "review_count": 140,
        "service": "Website Development",
        "lead_score": 91,
        "opportunity_type": "Website Development",
        "opportunity_reason": "Listing contains public phone but no website.",
        "confidence": "High",
        "status": "New",
        "provider_id": "test_prov_001"
    }
    # Create
    create_resp = client.post("/api/leads", json=lead_data, headers=auth_headers)
    assert create_resp.status_code == 201
    lead_id = create_resp.json()["id"]

    # Get by ID
    get_resp = client.get(f"/api/leads/{lead_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["business_name"] == "Spice Garden Biryani"
    assert data["lead_score"] == 91
    assert data["status"] == "New"

def test_duplicate_lead_prevention(client, auth_headers):
    lead_data = {
        "business_name": "Royal Cafe & Bakers",
        "category": "Bakery",
        "phone": "+91 866 255 1122",
        "address": "Labbipet Main Street",
        "city": "Vijayawada",
        "service": "Logo Design",
        "lead_score": 85,
        "provider_id": "prov_unique_101"
    }
    # Save once
    resp1 = client.post("/api/leads", json=lead_data, headers=auth_headers)
    assert resp1.status_code == 201

    # Save same provider ID again
    resp2 = client.post("/api/leads", json=lead_data, headers=auth_headers)
    assert resp2.status_code == 409
    assert "already saved" in resp2.json()["detail"]

    # Save with different provider ID but same normalized name and phone
    dup_data = lead_data.copy()
    dup_data["provider_id"] = "prov_different_id"
    dup_data["business_name"] = "royal cafe & bakers"  # Case variant
    resp3 = client.post("/api/leads", json=dup_data, headers=auth_headers)
    assert resp3.status_code == 409

def test_update_lead_status_and_notes(client, auth_headers):
    # Create lead
    create_resp = client.post(
        "/api/leads",
        json={
            "business_name": "Green Leaf Clinic",
            "category": "Healthcare",
            "phone": "+91 866 248 3344",
            "service": "Website Development",
            "lead_score": 88
        },
        headers=auth_headers
    )
    lead_id = create_resp.json()["id"]

    # Update status to Contacted and add notes
    update_resp = client.put(
        f"/api/leads/{lead_id}",
        json={
            "status": "Contacted",
            "notes": "Called manager on Tuesday. Interested in menu portfolio."
        },
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["status"] == "Contacted"
    assert "Called manager" in updated_data["notes"]

def test_export_leads_csv(client, auth_headers):
    # Ensure at least one lead exists
    client.post(
        "/api/leads",
        json={
            "business_name": "Export Test Business",
            "category": "Retail",
            "phone": "+91 866 299 0000",
            "city": "Vijayawada",
            "service": "Website Development",
            "lead_score": 90,
            "status": "Interested"
        },
        headers=auth_headers
    )

    export_resp = client.get("/api/leads/export", headers=auth_headers)
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]
    csv_text = export_resp.text
    # Verify all expected column headers
    assert "Business Name" in csv_text
    assert "Category" in csv_text
    assert "Phone" in csv_text
    assert "Website" in csv_text
    assert "Address" in csv_text
    assert "City" in csv_text
    assert "Rating" in csv_text
    assert "Review Count" in csv_text
    assert "Service" in csv_text
    assert "Lead Score" in csv_text
    assert "Opportunity" in csv_text
    assert "Status" in csv_text
    assert "Notes" in csv_text
    assert "Created Date" in csv_text
    assert "Source" in csv_text
    assert "Source URL" in csv_text
    assert "Export Test Business" in csv_text
