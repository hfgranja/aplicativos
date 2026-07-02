"""Autenticacao por API key (secao 18 do design doc).

Nota de escopo: em producao a autenticacao seria OAuth2/mTLS entre servicos
e API key + assinatura por integrador (ver secao 18). Nesta demo,
simplificamos para API key por merchant via header `X-Api-Key`, suficiente
para demonstrar isolamento multi-tenant sem a complexidade de um IdP real.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db


def get_merchant_from_api_key(
    x_api_key: str = Header(..., alias="X-Api-Key"),
    db: Session = Depends(get_db),
) -> models.Merchant:
    merchant = db.query(models.Merchant).filter(models.Merchant.api_key == x_api_key).first()
    if not merchant:
        raise HTTPException(status_code=401, detail="API key inválida")
    return merchant


def require_merchant_match(merchant_id: str, merchant: models.Merchant) -> None:
    if merchant_id != merchant.id:
        raise HTTPException(status_code=403, detail="API key não autorizada para este merchant_id")
