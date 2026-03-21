"""
Main orchestrator Celery task — dispatches engine tasks for an execution.
"""
import sys
import os

# Ensure engines/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

from datetime import datetime
from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models.execution import Execution, TestRun
from app.models.finding import Finding
from engines.base import EngineContext, StackInfo

ENGINE_MAP = {
    "sast": ("engines.sast.engine", "SASTEngine"),
    "property_based": ("engines.property_based.engine", "PropertyEngine"),
    "mutation": ("engines.mutation.engine", "MutationEngine"),
    "contract": ("engines.contract.engine", "ContractEngine"),
    "regression": ("engines.regression.engine", "RegressionEngine"),
    "fuzzing": ("engines.fuzzing.engine", "FuzzingEngine"),
    "differential": ("engines.differential.engine", "DifferentialEngine"),
    "integration": ("engines.integration.engine", "IntegrationEngine"),
    "performance": ("engines.performance.engine", "PerformanceEngine"),
    "chaos": ("engines.chaos.engine", "ChaosEngine"),
}


@celery_app.task(bind=True, max_retries=3)
def run_execution(self, execution_id: str):
    db = SessionLocal()
    try:
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            return

        execution.status = "RUNNING"
        execution.started_at = datetime.utcnow()
        db.commit()

        # Build engine context
        from app.models.application import Application
        app = db.query(Application).filter(Application.id == execution.application_id).first()
        stack = StackInfo(
            languages=app.stack_info.get("languages", []) if app.stack_info else [],
            frameworks=app.stack_info.get("frameworks", []) if app.stack_info else [],
            risk_surfaces=app.stack_info.get("risk_surfaces", []) if app.stack_info else [],
            has_contracts=app.stack_info.get("has_contracts", False) if app.stack_info else False,
            has_tests=app.stack_info.get("has_tests", False) if app.stack_info else False,
        )

        engines_to_run = execution.engines_run or ["sast"]
        pyramid_coverage = {}
        completed_engines = []
        failed_engines = []

        for engine_name in engines_to_run:
            if engine_name not in ENGINE_MAP:
                continue
            try:
                module_path, class_name = ENGINE_MAP[engine_name]
                import importlib
                mod = importlib.import_module(module_path)
                engine_cls = getattr(mod, class_name)
                engine = engine_cls()

                context = EngineContext(
                    execution_id=execution_id,
                    application_id=execution.application_id,
                    tenant_id=execution.tenant_id,
                    stack=stack,
                )

                test_run = TestRun(
                    execution_id=execution_id,
                    engine=engine_name,
                    pyramid_level=engine.pyramid_level,
                    status="RUNNING",
                    started_at=datetime.utcnow(),
                )
                db.add(test_run)
                db.commit()

                result = engine.run(context)

                test_run.status = result.status or "COMPLETED"
                test_run.score = result.score
                test_run.neural_insights = result.neural_insights
                test_run.summary = result.summary
                test_run.evidence = result.evidence
                test_run.execution_time_ms = result.execution_time_ms
                test_run.finished_at = datetime.utcnow()
                db.commit()

                # Persist findings
                for fd in result.findings:
                    finding = Finding(
                        execution_id=execution_id,
                        test_run_id=test_run.id,
                        engine=fd.engine,
                        pyramid_level=fd.pyramid_level,
                        severity=fd.severity,
                        category=fd.category,
                        title=fd.title,
                        description=fd.description,
                        evidence=fd.evidence,
                        seed=fd.seed,
                        file_path=fd.file_path,
                        line_number=fd.line_number,
                        cwe_id=fd.cwe_id,
                        neural_score=fd.neural_score,
                    )
                    db.add(finding)
                db.commit()

                completed_engines.append(engine_name)
                pyramid_coverage[engine.pyramid_level] = {
                    "engine": engine_name,
                    "score": result.score,
                    "status": test_run.status,
                }

            except Exception as e:
                failed_engines.append({"engine": engine_name, "error": str(e)})

        # Mark execution complete
        execution.status = "COMPLETED"
        execution.finished_at = datetime.utcnow()
        execution.pyramid_coverage = pyramid_coverage
        execution.summary = {
            "completed": completed_engines,
            "failed": failed_engines,
            "total_findings": db.query(Finding).filter(Finding.execution_id == execution_id).count(),
        }
        db.commit()

        # Auto-generate release decision
        from app.services.release_service import compute_release_decision
        try:
            compute_release_decision(db, execution_id, "system")
        except Exception:
            pass

    except Exception as exc:
        db.query(Execution).filter(Execution.id == execution_id).update(
            {"status": "FAILED", "finished_at": datetime.utcnow()}
        )
        db.commit()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
