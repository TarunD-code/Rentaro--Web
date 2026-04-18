from fastapi import FastAPI, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import jwt
import datetime
import httpx
from typing import List, Optional
from collections import deque

from . import models, schemas, database

# ── Config ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("support_service")

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"
SUBSCRIPTION_SERVICE_URL = "http://127.0.0.1:8000/subscriptions" # Via Gateway

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Support Service", version="1.0.0")

# In-memory Priority Queues
priority_queue = deque() # For premium tenants
normal_queue = deque()   # For standard tenants

# ── Auth ─────────────────────────────────────────────────────────────────────
def get_current_user_info(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"sub": payload.get("sub"), "role": payload.get("role")}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def check_premium_status(tenant_id: str, token: str) -> bool:
    """Check if tenant has an active premium subscription via Gateway."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
               f"http://127.0.0.1:8000/subscriptions/status",
               headers={"Authorization": f"Bearer {token}"}
            )
            data = resp.json()
            return data.get("status") == "active" if data else False
    except Exception as e:
        logger.error(f"Failed to check premium status: {e}")
        return False

# ── Support API ──────────────────────────────────────────────────────────────
@app.post("/tickets", response_model=schemas.TicketOut)
async def create_support_ticket(
    data: schemas.TicketCreate,
    user_info: dict = Depends(get_current_user_info),
    request: Request = None,
    db: Session = Depends(database.get_db)
):
    """Create a support ticket. Premium tenants get priority status."""
    token = request.headers.get("Authorization").split(" ")[1]
    is_premium = await check_premium_status(user_info["sub"], token)
    
    ticket = models.SupportTicket(
        tenant_id=user_info["sub"],
        subject=data.subject,
        description=data.description,
        is_premium=is_premium,
        priority="high" if is_premium else "normal",
        sla_hours=4 if is_premium else 24
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # Enqueue for agent processing
    if is_premium:
        priority_queue.append(ticket.id)
        logger.info(f"Ticket #{ticket.id} added to PRIORITY queue.")
    else:
        normal_queue.append(ticket.id)
        logger.info(f"Ticket #{ticket.id} added to normal queue.")
        
    return ticket

@app.get("/tickets", response_model=List[schemas.TicketOut])
def list_tickets(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    if user_info["role"] == "admin":
        return db.query(models.SupportTicket).all()
    return db.query(models.SupportTicket).filter(models.SupportTicket.tenant_id == user_info["sub"]).all()

@app.get("/tickets/queue/next", response_model=Optional[schemas.TicketOut])
def get_next_queued_ticket(user_info: dict = Depends(get_current_user_info), db: Session = Depends(database.get_db)):
    """Agent endpoint to pull the next ticket from queues (Priority first)."""
    if user_info["role"] not in ["admin", "support_agent"]:
         raise HTTPException(status_code=403, detail="Only agents can pull from queue")
         
    ticket_id = None
    if priority_queue:
        ticket_id = priority_queue.popleft()
    elif normal_queue:
        ticket_id = normal_queue.popleft()
        
    if not ticket_id:
        return None
        
    return db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
