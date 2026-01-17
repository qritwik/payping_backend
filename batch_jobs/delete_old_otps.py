#!/usr/bin/env python
"""
Batch job to delete expired OTPs from the database.

This script deletes all expired OTPs (expires_at < now).

This script should be run daily via cron (e.g., at 3 AM):
    0 3 * * * /path/to/venv/bin/python /path/to/PayPing/batch_jobs/delete_old_otps.py >> /var/log/payping_otp_cleanup.log 2>&1
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.auth import OTP


def delete_expired_otps(db):
    """Delete expired OTPs from the database."""
    now = datetime.utcnow()
    
    # Delete all expired OTPs
    deleted_count = db.query(OTP).filter(
        OTP.expires_at < now
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return deleted_count


def main():
    """Delete expired OTPs from the database."""
    db = SessionLocal()
    try:
        print(f"[{datetime.utcnow().isoformat()}] Starting OTP cleanup...")
        
        deleted_count = delete_expired_otps(db)
        
        if deleted_count > 0:
            print(
                f"[{datetime.utcnow().isoformat()}] "
                f"Successfully deleted {deleted_count} expired OTPs."
            )
        else:
            print(f"[{datetime.utcnow().isoformat()}] No expired OTPs to delete.")
        
        return 0
    except Exception as exc:
        print(
            f"[{datetime.utcnow().isoformat()}] ERROR: "
            f"Failed to delete expired OTPs: {exc}",
            file=sys.stderr
        )
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
