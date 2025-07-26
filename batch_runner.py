#!/usr/bin/env python3
"""
Batch Runner for TRINETRA Darknet Crawler
Handles batch processing of URLs with proper crawler integration
"""

import os
import sys
import subprocess
import threading
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from database.models import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchRunner:
    """Manages batch execution of darknet crawler scans"""
    
    def __init__(self):
        self.running_processes = {}
        self.venv_python = "/home/vector/darknet_crawler/tor-env/bin/python"
        self.scrapy_cmd = "/home/vector/darknet_crawler/tor-env/bin/scrapy"
        self.crawler_dir = "/home/vector/darknet_crawler"
        
    def run_batch(self, batch_id: str) -> bool:
        """Run all URLs in a batch"""
        try:
            # Get batch details
            batch = db_manager.get_batch_details(batch_id)
            if not batch:
                logger.error(f"Batch {batch_id} not found")
                return False
            
            # Get pending URLs for this batch
            pending_urls = db_manager.get_pending_batch_urls(batch_id)
            if not pending_urls:
                logger.info(f"No pending URLs found for batch {batch_id}")
                return True
            
            # Update batch status to RUNNING
            db_manager.update_batch_status(batch_id, "RUNNING")
            
            logger.info(f"🚀 Starting batch {batch_id} with {len(pending_urls)} URLs")
            
            # Process URLs sequentially (can be modified for parallel processing)
            for url_info in pending_urls:
                url = url_info['url']
                
                try:
                    # Start scan for this URL
                    scan_id = db_manager.start_scan(batch_id, url, "web_crawl")
                    logger.info(f"🔍 Starting scan {scan_id} for {url}")
                    
                    # Run crawler for this URL
                    success = self._run_single_url(url, scan_id, batch_id, batch.get('batch_config', {}))
                    
                    if success:
                        logger.info(f"✅ Successfully completed scan {scan_id} for {url}")
                    else:
                        logger.error(f"❌ Failed scan {scan_id} for {url}")
                        
                except Exception as e:
                    logger.error(f"Error processing URL {url}: {e}")
                    # Mark scan as failed
                    db_manager.complete_scan(
                        scan_id,
                        status="FAILED",
                        error_message=str(e)
                    )
            
            # Update batch status to COMPLETED
            db_manager.update_batch_status(batch_id, "COMPLETED")
            logger.info(f"🎉 Batch {batch_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running batch {batch_id}: {e}")
            db_manager.update_batch_status(batch_id, "FAILED")
            return False
    
    def _run_single_url(self, url: str, scan_id: str, batch_id: str, config: Dict) -> bool:
        """Run crawler for a single URL"""
        try:
            start_time = time.time()
            
            # Prepare crawler command
            cmd = [
                self.scrapy_cmd, "crawl", "onion",
                "-a", f"start_url={url}",
                "-s", "LOG_LEVEL=INFO",
                "-s", f"LOG_FILE=crawler_{scan_id}.log"
            ]
            
            # Add configuration parameters
            if config:
                if config.get('max_depth'):
                    cmd.extend(["-s", f"DEPTH_LIMIT={config['max_depth']}"])
                if config.get('delay_between_requests'):
                    cmd.extend(["-s", f"DOWNLOAD_DELAY={config['delay_between_requests']}"])
                if config.get('timeout'):
                    cmd.extend(["-s", f"DOWNLOAD_TIMEOUT={config['timeout']}"])
            
            # Set up environment
            env = {**os.environ, 'PATH': '/home/vector/darknet_crawler/tor-env/bin:' + os.environ.get('PATH', '')}
            
            # Run the crawler
            process = subprocess.Popen(
                cmd,
                cwd=self.crawler_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True
            )
            
            # Store process for monitoring
            self.running_processes[scan_id] = process
            
            # Wait for completion (with timeout)
            timeout = config.get('timeout', 600)  # Default 10 minutes for onion sites
            try:
                stdout, _ = process.communicate(timeout=timeout)
                return_code = process.returncode
                
                processing_time = time.time() - start_time
                
                # Parse output for statistics
                pages_crawled = self._parse_pages_crawled(stdout)
                alerts_found = self._parse_alerts_found(stdout)
                
                # Complete the scan
                if return_code == 0:
                    db_manager.complete_scan(
                        scan_id,
                        status="COMPLETED",
                        pages_crawled=pages_crawled,
                        alerts_found=alerts_found,
                        processing_time=processing_time
                    )
                    return True
                else:
                    db_manager.complete_scan(
                        scan_id,
                        status="FAILED",
                        error_message=f"Crawler exited with code {return_code}",
                        processing_time=processing_time
                    )
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Scan {scan_id} timed out after {timeout} seconds")
                process.kill()
                db_manager.complete_scan(
                    scan_id,
                    status="FAILED",
                    error_message="Scan timeout",
                    processing_time=time.time() - start_time
                )
                return False
                
        except Exception as e:
            logger.error(f"Error running crawler for {url}: {e}")
            db_manager.complete_scan(
                scan_id,
                status="FAILED",
                error_message=str(e)
            )
            return False
        finally:
            # Clean up process tracking
            if scan_id in self.running_processes:
                del self.running_processes[scan_id]
    
    def _parse_pages_crawled(self, output: str) -> int:
        """Parse pages crawled from crawler output"""
        try:
            # Look for patterns in the output
            import re
            patterns = [
                r'Crawled (\d+) pages',
                r'(\d+) pages crawled',
                r'item_scraped_count\': (\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, output)
                if match:
                    return int(match.group(1))
            
            return 0
        except:
            return 0
    
    def _parse_alerts_found(self, output: str) -> int:
        """Parse alerts found from crawler output"""
        try:
            # Look for alert patterns in the output
            import re
            patterns = [
                r'Generated (\d+) alerts',
                r'(\d+) alerts found',
                r'ALERT.*?(\d+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    return sum(int(match) for match in matches if match.isdigit())
            
            return 0
        except:
            return 0
    
    def run_batch_async(self, batch_id: str):
        """Run batch asynchronously in a separate thread"""
        def run_in_thread():
            self.run_batch(batch_id)
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        return thread
    
    def get_running_batches(self) -> List[str]:
        """Get list of currently running batch IDs"""
        return list(self.running_processes.keys())
    
    def stop_batch(self, batch_id: str) -> bool:
        """Stop a running batch"""
        try:
            # Find all processes for this batch
            processes_to_stop = []
            for scan_id, process in self.running_processes.items():
                # You might need to track batch_id -> scan_id mapping
                processes_to_stop.append((scan_id, process))
            
            for scan_id, process in processes_to_stop:
                try:
                    process.terminate()
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                # Update scan status
                db_manager.complete_scan(
                    scan_id,
                    status="STOPPED",
                    error_message="Manually stopped"
                )
                
                if scan_id in self.running_processes:
                    del self.running_processes[scan_id]
            
            # Update batch status
            db_manager.update_batch_status(batch_id, "STOPPED")
            logger.info(f"🛑 Stopped batch {batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping batch {batch_id}: {e}")
            return False

# Global batch runner instance
batch_runner = BatchRunner()

def main():
    """CLI interface for batch runner"""
    if len(sys.argv) < 3:
        print("Usage: python batch_runner.py <command> <batch_id>")
        print("Commands: run, stop, status")
        sys.exit(1)
    
    command = sys.argv[1]
    batch_id = sys.argv[2]
    
    if command == "run":
        print(f"🚀 Starting batch {batch_id}...")
        success = batch_runner.run_batch(batch_id)
        if success:
            print(f"✅ Batch {batch_id} completed successfully")
        else:
            print(f"❌ Batch {batch_id} failed")
    
    elif command == "stop":
        print(f"🛑 Stopping batch {batch_id}...")
        success = batch_runner.stop_batch(batch_id)
        if success:
            print(f"✅ Batch {batch_id} stopped")
        else:
            print(f"❌ Failed to stop batch {batch_id}")
    
    elif command == "status":
        batch = db_manager.get_batch_details(batch_id)
        if batch:
            print(f"📊 Batch {batch_id} Status:")
            print(f"  Name: {batch['batch_name']}")
            print(f"  Status: {batch['status']}")
            print(f"  URLs: {batch['completed_urls']}/{batch['total_urls']}")
            print(f"  Alerts: {batch['alerts_generated']}")
        else:
            print(f"❌ Batch {batch_id} not found")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
