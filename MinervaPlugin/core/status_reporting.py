"""
Comprehensive Status Reporting System for Minerva Plugin

This module provides structured status reporting with severity levels, categorization,
deduplication, and automatic retention management.
"""

import uuid
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class StatusSeverity(Enum):
    """Status severity levels for categorizing issues"""
    CRITICAL = "critical"    # System-breaking issues (connection failures, plugin crashes)
    HIGH = "high"           # Major functionality issues (command processing failures)
    MEDIUM = "medium"       # Minor issues that don't break core functionality
    LOW = "low"            # Warnings and informational issues
    INFO = "info"          # Non-issue informational messages


class StatusCategory(Enum):
    """Categories for different types of status reports"""
    CONNECTIVITY = "connectivity"      # RabbitMQ, network issues
    COMMAND_PROCESSING = "command"     # Command handling issues
    DATA_PROCESSING = "data"          # Stream data, metrics processing
    HARDWARE = "hardware"             # Sensor, device issues
    CONFIGURATION = "config"          # Setup, initialization issues
    PERFORMANCE = "performance"       # Timing, resource issues
    VALIDATION = "validation"         # Data validation issues
    SYSTEM = "system"                 # General system issues


@dataclass
class StatusReport:
    """Individual status report with comprehensive details"""
    id: str                           # Unique status ID
    timestamp: datetime
    severity: StatusSeverity
    category: StatusCategory
    code: str                        # Status code for programmatic handling
    message: str                     # Human-readable status message
    details: Optional[Dict[str, Any]] = None  # Additional context
    component: Optional[str] = None   # Component that generated the status
    stack_trace: Optional[str] = None # Stack trace for debugging
    count: int = 1                   # Number of occurrences
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Initialize first_seen and last_seen if not provided"""
        if self.first_seen is None:
            self.first_seen = self.timestamp
        if self.last_seen is None:
            self.last_seen = self.timestamp


class StatusManager:
    """Centralized status management for the plugin system"""
    
    def __init__(self, max_statuses_per_category=50, status_retention_hours=24):
        """
        Initialize the StatusManager
        
        Args:
            max_statuses_per_category (int): Maximum statuses to retain per category
            status_retention_hours (int): How long to keep resolved statuses (hours)
        """
        self._statuses = []
        self._status_counts = defaultdict(int)
        self._lock = threading.Lock()
        self.max_statuses_per_category = max_statuses_per_category
        self.status_retention_hours = status_retention_hours
        
    def report_status(self, 
                    severity: StatusSeverity,
                    category: StatusCategory,
                    code: str,
                    message: str,
                    details: Dict[str, Any] = None,
                    component: str = None,
                    exception: Exception = None) -> str:
        """
        Report a new status and return its ID
        
        Args:
            severity: Status severity level
            category: Status category
            code: Unique status code for programmatic handling
            message: Human-readable status message
            details: Additional context information
            component: Component that generated the status
            exception: Exception object if available
            
        Returns:
            str: Unique status ID
        """
        
        with self._lock:
            status_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Check for duplicate statuses (same code within last 5 minutes)
            existing_status = self._find_recent_duplicate(code, timestamp)
            if existing_status:
                existing_status.count += 1
                existing_status.last_seen = timestamp
                return existing_status.id
            
            # Create new status report
            status_report = StatusReport(
                id=status_id,
                timestamp=timestamp,
                severity=severity,
                category=category,
                code=code,
                message=message,
                details=details or {},
                component=component,
                stack_trace=str(exception) if exception else None,
                first_seen=timestamp,
                last_seen=timestamp
            )
            
            self._statuses.append(status_report)
            self._status_counts[category] += 1
            
            # Cleanup old statuses
            self._cleanup_old_statuses()
            
            return status_id
    
    def _find_recent_duplicate(self, code: str, timestamp: datetime) -> Optional[StatusReport]:
        """Find duplicate status within the last 5 minutes"""
        cutoff = timestamp - timedelta(minutes=5)
        for status in reversed(self._statuses):
            if (status.code == code and 
                status.timestamp >= cutoff and 
                not status.resolved):
                return status
        return None
    
    def _cleanup_old_statuses(self):
        """Remove statuses older than retention period"""
        cutoff = datetime.now() - timedelta(hours=self.status_retention_hours)
        self._statuses = [s for s in self._statuses if s.timestamp >= cutoff]
    
    def get_active_statuses(self) -> List[StatusReport]:
        """Get all unresolved statuses"""
        with self._lock:
            return [s for s in self._statuses if not s.resolved]
    
    def get_statuses_for_ping(self, max_statuses: int = 10) -> List[StatusReport]:
        """Get the most recent/critical statuses for ping payload"""
        with self._lock:
            # Get active statuses directly without calling get_active_statuses to avoid deadlock
            active_statuses = [s for s in self._statuses if not s.resolved]
            
            # Sort by severity (critical first) then by timestamp (newest first)
            severity_order = {
                StatusSeverity.CRITICAL: 0,
                StatusSeverity.HIGH: 1,
                StatusSeverity.MEDIUM: 2,
                StatusSeverity.LOW: 3,
                StatusSeverity.INFO: 4
            }
            
            sorted_statuses = sorted(
                active_statuses,
                key=lambda s: (severity_order[s.severity], -s.timestamp.timestamp())
            )
            
            return sorted_statuses[:max_statuses]
    
    def resolve_status(self, status_id: str) -> bool:
        """Mark a status as resolved"""
        with self._lock:
            for status in self._statuses:
                if status.id == status_id and not status.resolved:
                    status.resolved = True
                    status.resolution_timestamp = datetime.now()
                    return True
            return False
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary statistics for statuses"""
        with self._lock:
            # Get active statuses directly without calling get_active_statuses to avoid deadlock
            active_statuses = [s for s in self._statuses if not s.resolved]
            
            summary = {
                'total_active': len(active_statuses),
                'by_severity': defaultdict(int),
                'by_category': defaultdict(int),
                'oldest_status': None,
                'newest_status': None
            }
            
            if active_statuses:
                for status in active_statuses:
                    summary['by_severity'][status.severity.value] += 1
                    summary['by_category'][status.category.value] += 1
                
                sorted_by_time = sorted(active_statuses, key=lambda s: s.timestamp)
                summary['oldest_status'] = sorted_by_time[0].timestamp.isoformat()
                summary['newest_status'] = sorted_by_time[-1].timestamp.isoformat()
            
            return dict(summary)
    
    def get_status_by_id(self, status_id: str) -> Optional[StatusReport]:
        """Get a specific status by its ID"""
        with self._lock:
            for status in self._statuses:
                if status.id == status_id:
                    return status
            return None
    
    def clear_resolved_statuses(self):
        """Remove all resolved statuses"""
        with self._lock:
            self._statuses = [s for s in self._statuses if not s.resolved]
    
    def get_status_count_by_category(self, category: StatusCategory) -> int:
        """Get count of active statuses for a specific category"""
        with self._lock:
            return len([s for s in self._statuses 
                       if s.category == category and not s.resolved])
    
    def get_status_count_by_severity(self, severity: StatusSeverity) -> int:
        """Get count of active statuses for a specific severity"""
        with self._lock:
            return len([s for s in self._statuses 
                       if s.severity == severity and not s.resolved])
