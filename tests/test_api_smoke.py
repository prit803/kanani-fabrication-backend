import os
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("STT_API_KEY", "test-api-key")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor
from app.routes.bill_item_routes import router as bill_item_router
from app.routes.bill_routes import router as bill_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.engineering_routes import router as engineering_router
from app.routes.gujarati_stt_routes import router as gujarati_stt_router
from app.routes.stt_routes import router as stt_router
from app.routes.vendor_routes import router as vendor_router


def create_test_app():
    app = FastAPI()

    @app.get("/")
    def home():
        return {"message": "Kanani Fabrication Works FastAPI Running"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(vendor_router)
    app.include_router(bill_router)
    app.include_router(bill_item_router)
    app.include_router(engineering_router)
    app.include_router(stt_router)
    app.include_router(gujarati_stt_router)
    app.include_router(dashboard_router)
    return app


class ApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.session_factory = sessionmaker(
            bind=cls.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        cls.app = create_test_app()

        def get_test_db():
            with cls.session_factory() as db:
                yield db

        cls.app.dependency_overrides[get_db] = get_test_db
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        with self.session_factory() as db:
            for model in (BillItem, Bill, Vendor, Engineering):
                db.query(model).delete(synchronize_session=False)
            db.add_all(
                [
                    Engineering(engineer_id=0, name="Engineer Zero", is_deleted=False),
                    Engineering(engineer_id=1, name="Engineer One", is_deleted=False),
                    Vendor(
                        vendor_id=1,
                        vendor_name="Test Vendor",
                        mobile_number="1234567890",
                        status="active",
                        is_deleted=False,
                    ),
                ]
            )
            db.commit()

    def create_bill_item(self):
        response = self.client.post(
            "/bill-items",
            json={
                "vendor_id": 1,
                "engineer_id": 0,
                "bill_date": "2026-08-07",
                "status": "pending",
                "items": [
                    {
                        "item_description": "Test fabrication item",
                        "quantity": 2,
                        "rate": 150,
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]

    def test_health_and_disabled_admin_routes(self):
        self.assertEqual(
            self.client.get("/").json()["message"],
            "Kanani Fabrication Works FastAPI Running",
        )
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/admin/database").status_code, 404)
        self.assertEqual(self.client.post("/admin/database").status_code, 404)

    def test_vendor_and_engineering_endpoints(self):
        self.assertEqual(self.client.get("/vendors").status_code, 200)
        self.assertEqual(self.client.get("/vendors?vendor_id=1").status_code, 200)
        self.assertEqual(self.client.get("/vendors?vendor_id=999").status_code, 404)
        self.assertEqual(
            self.client.post("/vendors", data={"vendor_name": "Missing number"}).status_code,
            422,
        )

        created_vendor = self.client.post(
            "/vendors",
            data={
                "vendor_name": "Created Vendor",
                "mobile_number": "9876543210",
                "shop_name": "Test Shop",
            },
        )
        self.assertEqual(created_vendor.status_code, 200, created_vendor.text)
        vendor_id = created_vendor.json()["data"]["vendor_id"]
        updated_vendor = self.client.post(
            "/vendors",
            data={
                "vendor_id": vendor_id,
                "vendor_name": "Updated Vendor",
                "mobile_number": "9876543210",
            },
        )
        self.assertEqual(updated_vendor.status_code, 200, updated_vendor.text)
        self.assertEqual(
            updated_vendor.json()["data"]["vendor_name"], "Updated Vendor"
        )
        self.assertEqual(self.client.delete(f"/vendors/{vendor_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/vendors?vendor_id={vendor_id}").status_code, 404)
        self.assertEqual(self.client.delete(f"/vendors/{vendor_id}").status_code, 404)

        self.assertEqual(self.client.get("/engineering").status_code, 200)
        self.assertEqual(self.client.get("/engineering?engineer_id=0").status_code, 200)
        self.assertEqual(
            self.client.get("/engineering?engineer_id=999").status_code, 404
        )
        self.assertEqual(
            self.client.post("/engineering", data={"name": "  "}).status_code, 400
        )
        created_engineer = self.client.post(
            "/engineering",
            data={"name": "Created Engineer", "pan_number": "ABCDE1234F"},
        )
        self.assertEqual(created_engineer.status_code, 200, created_engineer.text)
        engineer_id = created_engineer.json()["data"]["engineer_id"]
        updated_engineer = self.client.post(
            "/engineering",
            data={"engineer_id": engineer_id, "name": "Updated Engineer"},
        )
        self.assertEqual(updated_engineer.status_code, 200, updated_engineer.text)
        self.assertEqual(
            updated_engineer.json()["data"]["name"], "Updated Engineer"
        )

    def test_bill_and_bill_item_endpoints(self):
        created = self.create_bill_item()
        bill_id = created["bill_id"]
        item_id = created["items"][0]["bill_item_id"]

        self.assertEqual(self.client.get("/bills").status_code, 200)
        self.assertEqual(self.client.get(f"/bills?bill_id={bill_id}").status_code, 200)
        self.assertEqual(self.client.get("/bills?bill_id=999").status_code, 404)
        self.assertEqual(self.client.get("/bill-items").status_code, 200)
        self.assertEqual(
            self.client.get(f"/bill-items?bill_id={bill_id}").status_code, 200
        )
        self.assertEqual(
            self.client.get(f"/bill-items?bill_item_id={item_id}").status_code, 200
        )
        self.assertEqual(self.client.get("/bill-items?bill_item_id=999").status_code, 404)

        updated_item = self.client.post(
            "/bill-items",
            json={
                "bill_id": bill_id,
                "items": [
                    {
                        "bill_item_id": item_id,
                        "item_description": "Updated item",
                        "quantity": 3,
                        "rate": 200,
                    }
                ],
            },
        )
        self.assertEqual(updated_item.status_code, 200, updated_item.text)
        self.assertEqual(
            updated_item.json()["data"]["items"][0]["amount"], 600
        )
        self.assertEqual(
            self.client.post("/bill-items", json={"items": []}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                "/bill-items",
                json={
                    "bill_id": 999,
                    "items": [{"item_description": "Missing bill"}],
                },
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/bill-items",
                json={
                    "vendor_id": 999,
                    "items": [{"item_description": "Missing vendor"}],
                },
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/bill-items",
                json={"items": [{"item_description": "No vendor"}]},
            ).status_code,
            400,
        )
        self.assertEqual(self.client.post("/bill-items", json={}).status_code, 422)

        date_range = {
            "vendor_id": 1,
            "from_date": "2026-08-01",
            "to_date": "2026-08-31",
        }
        self.assertEqual(
            self.client.get("/bills/vendor-total", params=date_range).status_code, 200
        )
        self.assertEqual(
            self.client.get(
                "/bills/vendor-total",
                params={**date_range, "vendor_id": 999},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                "/bills/vendor-total",
                params={**date_range, "from_date": "not-a-date"},
            ).status_code,
            422,
        )
        class FakeHTML:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.options = kwargs

            def render(self, **kwargs):
                self.render_options = kwargs
                return object()

            def write_pdf(self, **kwargs):
                self.pdf_options = kwargs

        def fake_measure_rows(document, count):
            if document is None:
                raise AssertionError("PDF measurement document was not created")
            return [1.0] * count, 1.0, 1.0

        with (
            patch("app.services.bill_service._delete_expired_bill_pdfs"),
            patch("app.services.bill_service.threading.Timer"),
            patch("app.services.bill_service._configure_weasyprint_dlls"),
            patch(
                "app.services.bill_service._measure_item_table_rows",
                side_effect=fake_measure_rows,
            ),
            patch.dict(sys.modules, {"weasyprint": SimpleNamespace(HTML=FakeHTML)}),
        ):
            pdf_data = self.client.get("/bills/pdf-data", params=date_range)
        self.assertEqual(pdf_data.status_code, 200, pdf_data.text)
        self.assertEqual(
            self.client.get(
                "/bills/pdf-data",
                params={**date_range, "vendor_id": 999},
            ).status_code,
            404,
        )

        self.assertEqual(self.client.delete(f"/bill-items/{item_id}").status_code, 200)
        self.assertEqual(
            self.client.delete(f"/bill-items/{item_id}").status_code, 404
        )
        self.assertEqual(self.client.delete(f"/bills/{bill_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/bills/{bill_id}").status_code, 404)
        self.assertEqual(self.client.post("/bills").status_code, 405)

    def test_dashboard_queries_and_date_validation(self):
        self.create_bill_item()
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        filtered = self.client.get(
            "/dashboard",
            params={"from_date": "2026-08-01", "to_date": "2026-08-31"},
        )
        self.assertEqual(filtered.status_code, 200, filtered.text)
        self.assertEqual(
            filtered.json()["data"]["monthly_summary"][0]["month"], "2026-08"
        )
        self.assertEqual(
            self.client.get("/dashboard?from_date=invalid").status_code, 422
        )

    def test_speech_endpoint_validation_and_mocked_success(self):
        self.assertEqual(self.client.post("/stt/speech-to-text").status_code, 422)
        invalid_stt = self.client.post(
            "/stt/speech-to-text",
            files={"file": ("invalid.txt", b"audio", "text/plain")},
        )
        self.assertEqual(invalid_stt.status_code, 400)
        with patch(
            "app.services.stt_service.STTService.speech_to_text",
            new=AsyncMock(return_value={"success": True}),
        ):
            response = self.client.post(
                "/stt/speech-to-text",
                files={"file": ("audio.wav", b"audio", "audio/wav")},
            )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.client.post("/speech-to-text/upload").status_code, 422
        )
        with patch(
            "app.services.gujarati_stt_service.GujaratiSTTService.speech_to_text_upload",
            new=Mock(return_value={"success": True}),
        ):
            response = self.client.post(
                "/speech-to-text/upload",
                files={"file": ("audio.wav", b"audio", "audio/wav")},
            )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
