"""
Simplified Usage Analytics Module (Stub)

This is a minimal implementation to prevent import errors.
The original complex analytics has been removed.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UsageAnalytics:
    """Simplified usage analytics stub"""
    
    def __init__(self, db_manager=None):
        """Initialize analytics (no-op)"""
        self.db_manager = db_manager
        self.enabled = False  # Analytics disabled by default
        
    def log_search(self, query: str, results_count: int, duration_ms: float):
        """Log search event (no-op)"""
        if self.enabled:
            logger.debug(f"Search: {query[:20]}... ({results_count} results, {duration_ms}ms)")
    
    def log_memory_add(self, block_id: int, importance: float):
        """Log memory addition (no-op)"""
        if self.enabled:
            logger.debug(f"Memory added: Block #{block_id}")
    
    def log_operation(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Log generic operation (no-op)"""
        if self.enabled:
            logger.debug(f"Operation: {operation}")
    
    def get_analytics_data(self, days: int = 7, report_type: str = 'usage') -> Dict[str, Any]:
        """Get analytics data (returns empty structure)"""
        return {
            'period_days': days,
            'report_type': report_type,
            'total_operations': 0,
            'total_searches': 0,
            'total_memories': 0,
            'average_search_time': 0.0,
            'memory_growth_rate': 0.0,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics (returns empty structure)"""
        return {
            'duplicate_rate': 0.0,
            'average_quality_score': 1.0,
            'promotion_success_rate': 1.0,
            'error_rate': 0.0
        }
    
    def track_slots_operation(self, operation: str, slot_name: str = None, **kwargs):
        """Track slots operation (no-op stub)"""
        if self.enabled:
            logger.debug(f"Slots operation: {operation} on {slot_name}")
    
    def close(self):
        """Close analytics (no-op)"""
        pass