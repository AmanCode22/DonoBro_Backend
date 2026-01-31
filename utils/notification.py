import json
import time
import queue
import uuid
from database import get_db

# The RAM Vaults
_active_clients = {}
_pending_tickets = {}

def generate_stream_ticket(user_id):
    """
    Generates a globally unique, one-time-use ticket.
    Stored in RAM. Impossible to guess (UUID4).
    """
    ticket = str(uuid.uuid4())
    _pending_tickets[ticket] = user_id
    return ticket

def send_wake_up_signal(target_id, message_type, extra_data=None):
    if target_id not in _active_clients:
        return {"status": False, "error": "User is not currently connected."}

    data_payload = {
        "type": message_type,
        "action": "SYNC_NOW",
        "timestamp": time.time()
    }
    
    if extra_data:
        data_payload.update(extra_data)

    try:
        user_queue = _active_clients[target_id]
        sse_message = f"data: {json.dumps(data_payload)}\n\n"
        user_queue.put(sse_message)
        return {"status": True, "message_id": f"local-{int(time.time())}"}
    except Exception as e:
        return {"status": False, "error": str(e)}

def stream_for_user(ticket_or_uid):
    """
    Accepts a TICKET. Atomic Pop ensures it can only be used ONCE.
    """
    user_id = None
    
    # 1. ATOMIC VERIFICATION (Prevents Interception)
    # .pop() removes the key and returns the value in one step.
    # If two people try to use the ticket, only the first one gets the ID.
    user_id = _pending_tickets.pop(ticket_or_uid, None)
    
    # Fallback: Allow internal system calls (DONOR-...) if needed, but Tickets are preferred.
    if not user_id and (ticket_or_uid.startswith("DONOR-") or ticket_or_uid.startswith("PATIENT-")):
        user_id = ticket_or_uid
    
    if not user_id:
        return # Reject connection silently (Security Best Practice)

    # 2. START STREAM
    q = queue.Queue()
    _active_clients[user_id] = q
    db = get_db()

    try:
        yield f"data: {json.dumps({'status': 'connected'})}\n\n"
        
        # Sync Inbox (Memory)
        # Using logic for fetching pending messages
        pending_cursor = db.execute("SELECT * FROM Inbox WHERE recipient_id = ? AND status = 'Pending'", (user_id,))
        pending_messages = pending_cursor.fetchall()
        
        for msg in pending_messages:
            payload = {
                "type": "INBOX_MESSAGE",
                "action": "SYNC_NOW",
                "content": msg['encrypted_content'],
                "timestamp": str(msg['created_at'])
            }
            yield f"data: {json.dumps(payload)}\n\n"
            db.execute("UPDATE Inbox SET status = 'Delivered' WHERE message_id = ?", (msg['message_id'],))
        
        db.commit()

        # Heartbeat Loop
        while True:
            try:
                # Wait for 15s to keep connection alive
                message = q.get(timeout=15)
                yield message
            except queue.Empty:
                # Update Last Heartbeat for Dashboard Accuracy
                db.execute("UPDATE Users SET last_heartbeat = CURRENT_TIMESTAMP WHERE anon_id = ?", (user_id,))
                db.commit()
                yield ": keepalive\n\n"
            
    except GeneratorExit:
        pass
    except Exception:
        pass
    finally:
        # Cleanup
        if user_id in _active_clients:
            del _active_clients[user_id]