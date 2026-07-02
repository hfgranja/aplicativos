from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services import execution

router = APIRouter(prefix="/receivables/webhooks", tags=["webhooks"])


@router.post("/{method}", response_model=schemas.AttemptOut)
def receive_webhook(method: str, payload: schemas.WebhookIn, db: Session = Depends(get_db)):
    """Endpoint de entrada de webhooks de provedor (secao 6/7/18).

    Em producao a assinatura HMAC do provedor seria validada aqui antes de
    qualquer processamento (secao 18). Nesta demo, a resolucao normal das
    tentativas ja ocorre de forma assincrona simulada (services/execution.py
    -> schedule_resolution); este endpoint existe para permitir que um
    integrador force um resultado explicito, replicando a superficie de API
    descrita no design doc.
    """
    attempt = execution.apply_webhook_result(db, payload.route_id, payload.status, payload.failure_reason)
    if not attempt:
        raise HTTPException(status_code=404, detail="Rota ou tentativa pendente não encontrada")
    return attempt
