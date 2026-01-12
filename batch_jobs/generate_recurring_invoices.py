#!/usr/bin/env python
"""
Batch job to generate invoices from recurring invoice templates.

This script should be run daily via cron (e.g., at 2 AM):
    0 2 * * * /path/to/venv/bin/python /path/to/PayPing/batch_jobs/generate_recurring_invoices.py >> /var/log/payping_recurring.log 2>&1
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.services.recurring_invoice_service import generate_invoices_from_templates


def main():
    """Generate invoices from active recurring invoice templates."""
    db = SessionLocal()
    try:
        print(f"[{datetime.utcnow().isoformat()}] Starting recurring invoice generation...")
        generated = generate_invoices_from_templates(db)
        
        if generated:
            print(
                f"[{datetime.utcnow().isoformat()}] "
                f"Successfully generated {len(generated)} recurring invoices."
            )
            for invoice in generated:
                print(f"  - Invoice ID: {invoice.id}, Number: {invoice.invoice_number or 'N/A'}")
        else:
            print(f"[{datetime.utcnow().isoformat()}] No invoices generated (no templates due).")
        
        return 0
    except Exception as exc:
        print(
            f"[{datetime.utcnow().isoformat()}] ERROR: "
            f"Failed to generate recurring invoices: {exc}",
            file=sys.stderr
        )
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

