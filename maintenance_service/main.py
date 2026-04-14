"""
Rentora Maintenance Service — FastAPI Application
Port: 8005

Handles service requests, vendor assignments, status tracking,
and maintenance history.
"""

import logging
import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
import jwt

from . import models, schemas, database

# ── Config ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maintenance_service")

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Maintenance Service", version="1.0.0")


# ── Auth ─────────────────────────────────────────────────────────────────────

def get_current_user_info(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        role: str = payload.get("role")
        if user_identifier is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"sub": user_identifier, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# ══════════════════════════════════════════════════════════════════════════════
#  SERVICE REQUEST ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/request", response_model=schemas.MaintenanceRequestOut, status_code=201)
def create_request(
    data: schemas.MaintenanceRequestCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Tenant creates a new maintenance/service request."""
    logger.info(f"New request by {data.tenant_id}: {data.category} - {data.title}")

    req = models.MaintenanceRequest(
        agreement_id=data.agreement_id,
        property_id=data.property_id,
        tenant_id=data.tenant_id,
        owner_id=data.owner_id,
        category=data.category,
        title=data.title,
        description=data.description,
        photo_urls=",".join(data.photo_urls) if data.photo_urls else None,
        priority=data.priority,
        status=models.RequestStatus.open.value,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    logger.info(f"Request #{req.id} created (category={data.category}, priority={data.priority})")
    return req


@app.get("/request/{request_id}", response_model=schemas.MaintenanceRequestOut)
def get_request(
    request_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Get maintenance request details."""
    req = db.query(models.MaintenanceRequest).filter(
        models.MaintenanceRequest.id == request_id,
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@app.get("/requests", response_model=List[schemas.MaintenanceRequestOut])
def list_requests(
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    property_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """List maintenance requests with filters (role-based)."""
    query = db.query(models.MaintenanceRequest)

    # Role-based filtering
    if user_info["role"] == "admin":
        pass  # Admin sees all
    elif user_info["role"] == "owner":
        query = query.filter(models.MaintenanceRequest.owner_id == user_info["sub"])
    else:  # tenant
        query = query.filter(models.MaintenanceRequest.tenant_id == user_info["sub"])

    if category:
        query = query.filter(models.MaintenanceRequest.category == category)
    if status:
        query = query.filter(models.MaintenanceRequest.status == status)
    if priority:
        query = query.filter(models.MaintenanceRequest.priority == priority)
    if property_id:
        query = query.filter(models.MaintenanceRequest.property_id == property_id)

    return query.order_by(
        models.MaintenanceRequest.created_at.desc()
    ).offset(offset).limit(limit).all()


@app.get("/requests/active", response_model=List[schemas.MaintenanceRequestOut])
def get_active_requests(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Get active (non-closed/cancelled) requests for the current user."""
    user_id = user_info["sub"]
    return db.query(models.MaintenanceRequest).filter(
        or_(
            models.MaintenanceRequest.tenant_id == user_id,
            models.MaintenanceRequest.owner_id == user_id,
        ),
        models.MaintenanceRequest.status.notin_(["closed", "cancelled"]),
    ).order_by(models.MaintenanceRequest.created_at.desc()).all()


@app.put("/request/{request_id}/status", response_model=schemas.MaintenanceRequestOut)
def update_request_status(
    request_id: int,
    data: schemas.StatusUpdate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Update maintenance request status."""
    req = db.query(models.MaintenanceRequest).filter(
        models.MaintenanceRequest.id == request_id,
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    valid_statuses = [s.value for s in models.RequestStatus]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be: {valid_statuses}")

    req.status = data.status

    if data.resolution_notes:
        req.resolution_notes = data.resolution_notes

    if data.status == models.RequestStatus.resolved.value:
        req.resolved_at = datetime.datetime.utcnow()
    elif data.status == models.RequestStatus.closed.value:
        req.closed_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(req)

    logger.info(f"Request #{request_id} status → {data.status}")
    return req


# ══════════════════════════════════════════════════════════════════════════════
#  VENDOR ASSIGNMENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/assign", response_model=schemas.VendorAssignmentOut, status_code=201)
def assign_vendor(
    data: schemas.VendorAssignmentCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Owner/admin assigns a vendor to a maintenance request."""
    # Verify request exists
    req = db.query(models.MaintenanceRequest).filter(
        models.MaintenanceRequest.id == data.request_id,
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.owner_id != user_info["sub"] and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only owner/admin can assign vendors")

    assignment = models.VendorAssignment(
        request_id=data.request_id,
        vendor_name=data.vendor_name,
        vendor_phone=data.vendor_phone,
        vendor_email=data.vendor_email,
        vendor_type=data.vendor_type,
        assigned_by=user_info["sub"],
        estimated_date=data.estimated_date,
        cost_estimate=data.cost_estimate,
        notes=data.notes,
        status=models.AssignmentStatus.assigned.value,
    )
    db.add(assignment)

    # Update request status
    if req.status == models.RequestStatus.open.value:
        req.status = models.RequestStatus.assigned.value

    db.commit()
    db.refresh(assignment)

    logger.info(f"Vendor '{data.vendor_name}' assigned to request #{data.request_id}")
    return assignment


@app.get("/assignments/{request_id}", response_model=List[schemas.VendorAssignmentOut])
def get_assignments(
    request_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Get vendor assignments for a request."""
    return db.query(models.VendorAssignment).filter(
        models.VendorAssignment.request_id == request_id,
    ).order_by(models.VendorAssignment.created_at.desc()).all()


@app.put("/assignment/{assignment_id}/status", response_model=schemas.VendorAssignmentOut)
def update_assignment_status(
    assignment_id: int,
    data: schemas.AssignmentStatusUpdate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Vendor updates their assignment status."""
    assignment = db.query(models.VendorAssignment).filter(
        models.VendorAssignment.id == assignment_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    valid_statuses = [s.value for s in models.AssignmentStatus]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be: {valid_statuses}")

    assignment.status = data.status

    if data.actual_cost is not None:
        assignment.actual_cost = data.actual_cost
    if data.notes:
        assignment.notes = data.notes

    if data.status == models.AssignmentStatus.completed.value:
        assignment.actual_date = datetime.datetime.utcnow()

        # Also update the parent request
        req = db.query(models.MaintenanceRequest).filter(
            models.MaintenanceRequest.id == assignment.request_id,
        ).first()
        if req and req.status != models.RequestStatus.resolved.value:
            req.status = models.RequestStatus.resolved.value
            req.resolved_at = datetime.datetime.utcnow()
            if data.notes:
                req.resolution_notes = data.notes

    db.commit()
    db.refresh(assignment)

    logger.info(f"Assignment #{assignment_id} status → {data.status}")
    return assignment


# ══════════════════════════════════════════════════════════════════════════════
#  HISTORY & EXPORT
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/history", response_model=List[schemas.MaintenanceRequestOut])
def get_history(
    agreement_id: Optional[int] = None,
    property_id: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Get maintenance history with filters."""
    query = db.query(models.MaintenanceRequest)

    if user_info["role"] != "admin":
        query = query.filter(
            or_(
                models.MaintenanceRequest.tenant_id == user_info["sub"],
                models.MaintenanceRequest.owner_id == user_info["sub"],
            )
        )

    if agreement_id:
        query = query.filter(models.MaintenanceRequest.agreement_id == agreement_id)
    if property_id:
        query = query.filter(models.MaintenanceRequest.property_id == property_id)
    if category:
        query = query.filter(models.MaintenanceRequest.category == category)

    return query.order_by(
        models.MaintenanceRequest.created_at.desc()
    ).offset(offset).limit(limit).all()


@app.get("/history/export")
def export_history(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Export maintenance history as CSV."""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    query = db.query(models.MaintenanceRequest)
    if user_info["role"] != "admin":
        query = query.filter(
            or_(
                models.MaintenanceRequest.tenant_id == user_info["sub"],
                models.MaintenanceRequest.owner_id == user_info["sub"],
            )
        )

    requests = query.order_by(models.MaintenanceRequest.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Category", "Title", "Priority", "Status", "Tenant", "Created", "Resolved"])

    for r in requests:
        writer.writerow([
            r.id, r.category, r.title, r.priority, r.status,
            r.tenant_id, r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
            r.resolved_at.strftime("%Y-%m-%d") if r.resolved_at else "Pending",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=maintenance_history.csv"},
    )


@app.get("/stats")
def get_stats(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Get maintenance stats for dashboard."""
    from sqlalchemy import func

    user_id = user_info["sub"]
    base = db.query(models.MaintenanceRequest)

    if user_info["role"] != "admin":
        base = base.filter(
            or_(
                models.MaintenanceRequest.tenant_id == user_id,
                models.MaintenanceRequest.owner_id == user_id,
            )
        )

    total = base.count()
    open_count = base.filter(models.MaintenanceRequest.status.in_(["open", "assigned"])).count()
    in_progress = base.filter(models.MaintenanceRequest.status == "in_progress").count()
    resolved = base.filter(models.MaintenanceRequest.status.in_(["resolved", "closed"])).count()

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
    }
