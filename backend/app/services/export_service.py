import csv
import io
from typing import List
from app.database.models import Lead

class ExportService:
    @staticmethod
    def generate_csv(leads: List[Lead]) -> str:
        """
        Exports leads to CSV format with exact required schema.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header as requested in specifications
        headers = [
            "Business Name",
            "Category",
            "Phone",
            "Website",
            "Address",
            "City",
            "Rating",
            "Review Count",
            "Service",
            "Lead Score",
            "Opportunity",
            "Status",
            "Notes",
            "Created Date",
            "Source",
            "Source URL"
        ]
        writer.writerow(headers)

        for lead in leads:
            created_str = lead.created_at.strftime("%Y-%m-%d %H:%M:%S") if lead.created_at else ""
            writer.writerow([
                lead.business_name or "",
                lead.category or "",
                lead.phone or "",
                lead.website or "",
                lead.address or "",
                lead.city or "",
                lead.rating or 0.0,
                lead.review_count or 0,
                lead.service or "",
                lead.lead_score or 0,
                lead.opportunity_type or lead.opportunity_reason or "",
                lead.status or "New",
                lead.notes or "",
                created_str,
                lead.source or "",
                lead.source_url or ""
            ])

        return output.getvalue()

export_service = ExportService()
