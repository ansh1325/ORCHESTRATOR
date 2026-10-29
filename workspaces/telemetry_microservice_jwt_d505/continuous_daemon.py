"""24/7 Continuous Background PC Daemon."""
import time
from data_connector import DataConnector
from core_engine import CoreAutomationEngine
from storage_manager import StorageManager

def run_continuous_cycle():
    """Executes one continuous autonomous cycle."""
    connector = DataConnector()
    engine = CoreAutomationEngine(connector)
    storage = StorageManager("autonomous_system.db")
    
    result = engine.execute_pipeline()
    for act in result["actions"]:
        storage.insert_record(act["target_id"], act["target_name"], "ContinuousDaemon", act["status"])
    print(f"[Continuous Daemon] Processed {result['total_processed']} actions successfully.")
    return result

if __name__ == "__main__":
    run_continuous_cycle()
