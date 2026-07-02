from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_merchant_from_api_key, require_merchant_match
from app.services import execution, intents as intents_service

router = APIRouter(prefix="/receivables", tags=["intents"])


def _get_intent_or_404(db: Session, intent_id: str, merchant: models.Merchant) -> models.ReceivableIntent:
    intent = db.get(models.ReceivableIntent, intent_id)
    if not intent or intent.merchant_id != merchant.id:
        raise HTTPException(status_code=404, detail="Intenção não encontrada")
    return intent


@router.post("/intents", response_model=schemas.ReceivableIntentOut, status_code=201)
def create_intent(payload: schemas.ReceivableIntentIn, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                   db: Session = Depends(get_db)):
    require_merchant_match(payload.merchant_id, merchant)
    customer = db.get(models.Customer, payload.customer_id)
    if not customer or customer.merchant_id != merchant.id:
        raise HTTPException(status_code=400, detail="customer_id inválido para este merchant")

    intent = intents_service.create_intent(db, payload)

    policy = (
        db.query(models.MerchantPolicy)
        .filter(models.MerchantPolicy.merchant_id == merchant.id, models.MerchantPolicy.is_default.is_(True))
        .first()
    )
    if policy and intent.status == "scored":
        execution.maybe_autopilot(db, intent, policy)

    return intent


@router.get("/intents/{intent_id}/recommendation", response_model=schemas.RecommendationOut)
def get_recommendation(intent_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                        db: Session = Depends(get_db)):
    intent = _get_intent_or_404(db, intent_id, merchant)
    return intents_service.get_recommendation(db, intent)


@router.post("/intents/{intent_id}/execute", response_model=schemas.RouteOut, status_code=201)
def execute_intent(intent_id: str, payload: schemas.ExecuteIn,
                    merchant: models.Merchant = Depends(get_merchant_from_api_key), db: Session = Depends(get_db)):
    intent = _get_intent_or_404(db, intent_id, merchant)
    option = next((o for o in intent.options if o.method == payload.approved_route), None)
    if not option or not option.eligible:
        raise HTTPException(status_code=400, detail="Meio de pagamento não elegível para esta intenção")
    if intent.status not in ("scored", "payment_failed"):
        raise HTTPException(status_code=409, detail=f"Intenção em status '{intent.status}' não pode ser executada")

    route = execution.approve_and_execute(db, intent, payload.approved_route, payload.approved_by)
    return route


@router.get("/intents/{intent_id}/status", response_model=schemas.IntentTimelineOut)
def get_status(intent_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                db: Session = Depends(get_db)):
    intent = _get_intent_or_404(db, intent_id, merchant)
    return schemas.IntentTimelineOut(intent=intent, routes=intent.routes)


@router.post("/intents/{intent_id}/retry", response_model=schemas.AttemptOut)
def retry_intent(intent_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                  db: Session = Depends(get_db)):
    intent = _get_intent_or_404(db, intent_id, merchant)
    attempt = execution.force_retry(db, intent)
    if not attempt:
        raise HTTPException(status_code=409, detail="Nenhuma rota anterior para reprocessar")
    return attempt


@router.post("/intents/{intent_id}/fallback", response_model=schemas.RouteOut)
def apply_fallback(intent_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                    db: Session = Depends(get_db)):
    intent = _get_intent_or_404(db, intent_id, merchant)
    if not intent.routes:
        raise HTTPException(status_code=409, detail="Intenção ainda não possui rota executada")
    last_route = intent.routes[-1]
    new_route = execution.apply_fallback(db, intent, last_route, last_route.chosen_method)
    if not new_route:
        raise HTTPException(status_code=409, detail="Fallback esgotado para esta intenção")
    return new_route


@router.get("/intents/{intent_id}/explanation", response_model=schemas.ExplanationOut)
def get_explanation(intent_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                     db: Session = Depends(get_db)):
    intent = _get_intent_or_404(db, intent_id, merchant)
    return intents_service.build_explanation(db, intent)


@router.get("/intents", response_model=list[schemas.ReceivableIntentOut])
def list_intents(merchant: models.Merchant = Depends(get_merchant_from_api_key), db: Session = Depends(get_db),
                  limit: int = 50):
    return (
        db.query(models.ReceivableIntent)
        .filter(models.ReceivableIntent.merchant_id == merchant.id)
        .order_by(models.ReceivableIntent.created_at.desc())
        .limit(limit)
        .all()
    )
