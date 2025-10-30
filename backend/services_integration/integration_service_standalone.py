# backend/integration_service_standalone.py

# --- 1. IMPORTS ---
import os
import sys
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dotenv import load_dotenv
import pymongo
from datetime import datetime
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, status

# --- 2. LOAD .ENV & CONNECT TO MONGODB ---
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError(f"MONGODB_URI not found. Looked for .env file at: {dotenv_path}")

client = pymongo.MongoClient(MONGODB_URI)
db = client.get_database("ZypheryDB")
raw_data_jobs_collection = db.raw_data_jobs

# --- 3. LOGGER SETUP (FIXED) ---
def get_logger(name: str):
    """Configures and returns a standard logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

log = get_logger("IntegrationServiceStandalone (Port 8003)")


# --- 4. BASE SERVICE CLASS ---
class BaseIntegrationService(ABC):
    def __init__(self, company_id: str):
        self.company_id = company_id
        self.csv_file_name = ""
    def _read_mock_csv(self) -> List[Dict[str, Any]]:
        log.info(f"[{self.__class__.__name__}] Fetching data...")
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, 'data', self.csv_file_name)
            log.info(f"[{self.__class__.__name__}] Loading mock data from: {csv_path}")
            df = pd.read_csv(csv_path).fillna('')
            records = df.to_dict(orient='records')
            log.info(f"[{self.__class__.__name__}] Successfully fetched {len(records)} records.")
            return records
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Mock data file for '{self.csv_file_name}' is missing.")
        except Exception as e:
            raise
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        pass
        
# --- 5. CONCRETE SERVICE IMPLEMENTATIONS ---
class ZohoBooksService(BaseIntegrationService):
    def __init__(self, company_id: str): super().__init__(company_id); self.csv_file_name = "zoho_invoices.csv"
    def fetch_data(self) -> List[Dict[str, Any]]: return self._read_mock_csv()
class RazorpayService(BaseIntegrationService):
    def __init__(self, company_id: str): super().__init__(company_id); self.csv_file_name = "razorpay_payments.csv"
    def fetch_data(self) -> List[Dict[str, Any]]: return self._read_mock_csv()
class QuickBooksService(BaseIntegrationService):
    def __init__(self, company_id: str): super().__init__(company_id); self.csv_file_name = "qbo_invoices.csv"
    def fetch_data(self) -> List[Dict[str, Any]]: return self._read_mock_csv()
class TallyService(BaseIntegrationService):
    def __init__(self, company_id: str): super().__init__(company_id); self.csv_file_name = "tally_vouchers.csv"
    def fetch_data(self) -> List[Dict[str, Any]]: return self._read_mock_csv()
class BankService(BaseIntegrationService):
    def __init__(self, company_id: str): super().__init__(company_id); self.csv_file_name = "bank_transactions.csv"
    def fetch_data(self) -> List[Dict[str, Any]]: return self._read_mock_csv()
class GoogleSheetsService(BaseIntegrationService):
    def __init__(self, company_id: str): super().__init__(company_id); self.csv_file_name = "google_sheets_export.csv"
    def fetch_data(self) -> List[Dict[str, Any]]: return self._read_mock_csv()
class NotionService(BaseIntegrationService):
    def __init__(self, company_id: str): super().__init__(company_id); self.csv_file_name = "notion_expenses.csv"
    def fetch_data(self) -> List[Dict[str, Any]]: return self._read_mock_csv()
    
# --- 6. SERVICE FACTORY ---
INTEGRATION_SERVICES: Dict[str, type] = {
    "zoho_invoices": ZohoBooksService, "razorpay_payments": RazorpayService,
    "qbo_invoices": QuickBooksService, "tally_vouchers": TallyService,
    "bank_transactions": BankService, "google_sheets_export": GoogleSheetsService,
    "notion_expenses": NotionService
}

# --- 7. FASTAPI APP AND ROUTER SETUP ---
app = FastAPI(
    title="ZYPHERY - Standalone Integration Service (Service 3)",
    description="Fetches raw data and creates ingestion jobs in MongoDB.",
    version="1.1.0"
)
router = APIRouter()

@router.post("/{company_id}/connect", status_code=status.HTTP_201_CREATED)
async def connect_integration(company_id: str, integration_details: Dict):
    return {"message": "Mock connection successful."}

@router.get("/{company_id}", status_code=status.HTTP_200_OK)
async def get_connected_integrations(company_id: str):
    return [{"integration_id": key, "status": "available"} for key in INTEGRATION_SERVICES.keys()]

@router.post("/{company_id}/sync/{integration_id}", status_code=status.HTTP_201_CREATED)
async def sync_integration_data(company_id: str, integration_id: str):
    log.info(f"Sync triggered for '{company_id}', integration '{integration_id}'.")
    service_class = INTEGRATION_SERVICES.get(integration_id)
    if not service_class:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' is not supported.")
    try:
        service_instance = service_class(company_id=company_id)
        raw_data = service_instance.fetch_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    job_payload = {
        "company_id": company_id, "source_system": integration_id,
        "status": "pending", "data": raw_data, "created_at": datetime.now()
    }
    try:
        result = raw_data_jobs_collection.insert_one(job_payload)
        job_id = str(result.inserted_id)
        log.info(f"Successfully created ingestion job {job_id} in MongoDB.")
    except Exception as e:
        log.error(f"Failed to insert job into MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ingestion job in database.")
    return {"message": "Sync successful. Ingestion job created.", "job_id": job_id, "records_fetched": len(raw_data)}

app.include_router(router, prefix="/integrations", tags=["Integrations"])

# --- 8. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    port = 8003
    log.info(f"🚀 Starting Standalone Integration Service (Service 3) on http://127.0.0.1:{port}")
    uvicorn.run(__name__ + ":app", host="0.0.0.0", port=port, reload=True)