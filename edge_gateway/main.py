import os
import sys
import time
from app.core.logging import logger
from edge_gateway.scanner.file_watcher import EdgeFileWatcher

def start_edge_gateway():
    logger.info("==================================================")
    logger.info("⚡ VERDICT EDGE GATEWAY — Standalone Enterprise Node")
    logger.info("==================================================")
    logger.info("Running in READ-ONLY mode on local organization boundary.")
    logger.info("Authorized Connectors: [PostgreSQL, MySQL, CSV Feed, Excel Watcher]")
    
    watcher = EdgeFileWatcher("./sample_data")
    logger.info("Edge Gateway scanner listening for local files and query requests on port 8001...")
    
    new_items = watcher.scan_directory()
    logger.info(f"Initial scan complete. Discovered {len(new_items)} enterprise evidence files ready for targeted dispatch.")

if __name__ == "__main__":
    start_edge_gateway()
