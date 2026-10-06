"""
routers/sla.py — Эндпоинты для расчёта SLA-метрик.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth import get_current_user, CurrentUser
from zabbix_client import zabbix_client
from models import Service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sla"])


class SLAMetrics(BaseModel):
    """Метрики SLA для сервиса."""
    service_id: str
    service_name: str
    sla_percentage: float
    total_time_seconds: float
    downtime_seconds: float
    excluded_downtime_seconds: float
    effective_downtime_seconds: float
    availability_seconds: float


class SLAReportRequest(BaseModel):
    """Запрос на расчёт SLA-отчёта."""
    period_from: datetime
    period_to: datetime
    service_ids: Optional[List[str]] = None


class SLAReportResponse(BaseModel):
    """Ответ с SLA-отчётом."""
    period_from: str
    period_to: str
    services: List[SLAMetrics]
    summary: dict


@router.post("/sla/calculate", response_model=SLAReportResponse)
def calculate_sla_report(
    request: SLAReportRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Расчёт SLA-отчёта за период.
    
    Учитывает:
    - Время простоя сервисов
    - Исключённое время (плановые работы)
    - Формулу SLA %
    """
    # Валидация периода
    if request.period_to <= request.period_from:
        raise HTTPException(
            status_code=400,
            detail="period_to must be after period_from"
        )
    
    # Ограничение периода (не более 1 года)
    max_period = timedelta(days=365)
    if request.period_to - request.period_from > max_period:
        raise HTTPException(
            status_code=400,
            detail="Period cannot exceed 1 year"
        )
    
    # Получаем список сервисов
    if request.service_ids:
        services = db.query(Service).filter(Service.id.in_(request.service_ids)).all()
    else:
        # Все сервисы доступные пользователю
        from auth import get_accessible_services
        accessible_ids = get_accessible_services(current_user, db)
        services = db.query(Service).filter(Service.id.in_(accessible_ids)).all()
    
    if not services:
        raise HTTPException(
            status_code=404,
            detail="No services found"
        )
    
    # Рассчитываем SLA для каждого сервиса
    sla_metrics = []
    for service in services:
        try:
            result = zabbix_client.calculate_sla_availability(
                service_id=service.id,
                period_from=request.period_from,
                period_to=request.period_to,
            )
            
            if "error" in result:
                logger.warning(f"Failed to calculate SLA for service {service.id}: {result['error']}")
                continue
            
            sla_metrics.append(SLAMetrics(
                service_id=service.id,
                service_name=service.name,
                sla_percentage=result["sla_percentage"],
                total_time_seconds=result["total_time_seconds"],
                downtime_seconds=result["downtime_seconds"],
                excluded_downtime_seconds=result["excluded_downtime_seconds"],
                effective_downtime_seconds=result["effective_downtime_seconds"],
                availability_seconds=result["availability_seconds"],
            ))
        except Exception as e:
            logger.error(f"Error calculating SLA for service {service.id}: {e}")
            continue
    
    # Сводная статистика
    if sla_metrics:
        avg_sla = sum(m.sla_percentage for m in sla_metrics) / len(sla_metrics)
        min_sla = min(m.sla_percentage for m in sla_metrics)
        max_sla = max(m.sla_percentage for m in sla_metrics)
        
        summary = {
            "total_services": len(sla_metrics),
            "average_sla": round(avg_sla, 4),
            "min_sla": round(min_sla, 4),
            "max_sla": round(max_sla, 4),
            "services_below_target": len([m for m in sla_metrics if m.sla_percentage < 99.9]),
        }
    else:
        summary = {
            "total_services": 0,
            "average_sla": 0,
            "min_sla": 0,
            "max_sla": 0,
            "services_below_target": 0,
        }
    
    return SLAReportResponse(
        period_from=request.period_from.isoformat(),
        period_to=request.period_to.isoformat(),
        services=sla_metrics,
        summary=summary,
    )


@router.get("/sla/service/{service_id}")
def get_service_sla(
    service_id: str,
    period: str = Query("month", description="Period: day, week, month, quarter, year"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Получение SLA-метрик для конкретного сервиса за период.
    """
    # Проверяем доступ
    from auth import check_service_access
    if not check_service_access(current_user, service_id, db):
        raise HTTPException(
            status_code=403,
            detail="No access to this service"
        )
    
    # Определяем период
    now = datetime.utcnow()
    period_map = {
        "day": (now - timedelta(days=1), now),
        "week": (now - timedelta(weeks=1), now),
        "month": (now - timedelta(days=30), now),
        "quarter": (now - timedelta(days=90), now),
        "year": (now - timedelta(days=365), now),
    }
    
    if period not in period_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Must be one of: {list(period_map.keys())}"
        )
    
    period_from, period_to = period_map[period]
    
    # Рассчитываем SLA
    result = zabbix_client.calculate_sla_availability(
        service_id=service_id,
        period_from=period_from,
        period_to=period_to,
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate SLA: {result['error']}"
        )
    
    # Получаем имя сервиса
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )
    
    result["service_name"] = service.name
    result["period"] = period
    
    return result


@router.get("/sla/summary")
def get_sla_summary(
    period: str = Query("month", description="Period: day, week, month, quarter, year"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Сводка по SLA за период.
    """
    # Определяем период
    now = datetime.utcnow()
    period_map = {
        "day": (now - timedelta(days=1), now),
        "week": (now - timedelta(weeks=1), now),
        "month": (now - timedelta(days=30), now),
        "quarter": (now - timedelta(days=90), now),
        "year": (now - timedelta(days=365), now),
    }
    
    if period not in period_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Must be one of: {list(period_map.keys())}"
        )
    
    period_from, period_to = period_map[period]
    
    # Получаем доступные сервисы
    from auth import get_accessible_services
    accessible_ids = get_accessible_services(current_user, db)
    services = db.query(Service).filter(Service.id.in_(accessible_ids)).all()
    
    if not services:
        return {
            "period": period,
            "total_services": 0,
            "services": [],
        }
    
    # Рассчитываем SLA для всех сервисов
    sla_data = []
    for service in services:
        try:
            result = zabbix_client.calculate_sla_availability(
                service_id=service.id,
                period_from=period_from,
                period_to=period_to,
            )
            
            if "error" not in result:
                sla_data.append({
                    "service_id": service.id,
                    "service_name": service.name,
                    "sla_percentage": result["sla_percentage"],
                    "downtime_hours": result["effective_downtime_seconds"] / 3600,
                })
        except Exception as e:
            logger.error(f"Error calculating SLA for service {service.id}: {e}")
            continue
    
    # Сортируем по SLA %
    sla_data.sort(key=lambda x: x["sla_percentage"], reverse=True)
    
    return {
        "period": period,
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
        "total_services": len(sla_data),
        "services": sla_data,
    }
