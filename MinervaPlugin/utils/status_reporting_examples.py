#!/usr/bin/env python3
"""
Status Reporting System - PCC Use Cases and Examples

This file demonstrates practical use cases for the status reporting system
in the PCC (Plugin Control Center) environment.
"""

from ..core.status_reporting import StatusSeverity, StatusCategory

# Example: How to use status reporting in your PCC components

class PCCExamples:
    """Examples of status reporting usage in PCC components"""
    
    def __init__(self, plugin):
        self.plugin = plugin
    
    # ========================================
    # CONNECTIVITY STATUS EXAMPLES
    # ========================================
    
    def report_rabbitmq_connection_issue(self):
        """Report RabbitMQ connectivity problems"""
        self.plugin.report_status(
            severity=StatusSeverity.CRITICAL,
            category=StatusCategory.CONNECTIVITY,
            code="RABBITMQ_CONNECTION_LOST",
            message="Lost connection to RabbitMQ server",
            details={
                'server': 'localhost:5672',
                'queue': 'command_queue',
                'retry_count': 3
            },
            component="rabbitmq_client"
        )
    
    def report_network_timeout(self):
        """Report network timeout issues"""
        self.plugin.report_status(
            severity=StatusSeverity.HIGH,
            category=StatusCategory.CONNECTIVITY,
            code="NETWORK_TIMEOUT",
            message="Network timeout while communicating with server",
            details={
                'timeout_seconds': 30,
                'endpoint': '/api/commands'
            },
            component="network_client"
        )
    
    # ========================================
    # COMMAND PROCESSING STATUS EXAMPLES
    # ========================================
    
    def report_command_validation_failure(self, command):
        """Report command validation issues"""
        self.plugin.report_status(
            severity=StatusSeverity.MEDIUM,
            category=StatusCategory.VALIDATION,
            code="COMMAND_VALIDATION_FAILED",
            message="Command failed validation checks",
            details={
                'command_type': command.get('type'),
                'missing_fields': ['userId', 'timestamp'],
                'command_id': command.get('id')
            },
            component="command_validator"
        )
    
    def report_successful_command_processing(self, command):
        """Report successful command processing"""
        self.plugin.report_status(
            severity=StatusSeverity.INFO,
            category=StatusCategory.COMMAND_PROCESSING,
            code="COMMAND_PROCESSED_SUCCESS",
            message="Command processed successfully",
            details={
                'command_type': command.get('type'),
                'processing_time_ms': 150,
                'command_id': command.get('id')
            },
            component="command_processor"
        )
    
    def report_command_queue_full(self):
        """Report when command queue is full"""
        self.plugin.report_status(
            severity=StatusSeverity.HIGH,
            category=StatusCategory.PERFORMANCE,
            code="COMMAND_QUEUE_FULL",
            message="Command queue has reached maximum capacity",
            details={
                'queue_size': 1000,
                'max_capacity': 1000,
                'dropped_commands': 5
            },
            component="command_queue"
        )
    
    # ========================================
    # DATA PROCESSING STATUS EXAMPLES
    # ========================================
    
    def report_signal_generation_success(self, signal_type):
        """Report successful signal generation"""
        self.plugin.report_status(
            severity=StatusSeverity.INFO,
            category=StatusCategory.DATA_PROCESSING,
            code="SIGNAL_GENERATION_SUCCESS",
            message=f"Successfully generated {signal_type} signal data",
            details={
                'signal_type': signal_type,
                'data_points': 1000,
                'frequency_hz': 5
            },
            component="signal_generator"
        )
    
    def report_data_corruption(self, data_source):
        """Report data corruption issues"""
        self.plugin.report_status(
            severity=StatusSeverity.HIGH,
            category=StatusCategory.DATA_PROCESSING,
            code="DATA_CORRUPTION_DETECTED",
            message="Data corruption detected in stream",
            details={
                'data_source': data_source,
                'corrupted_packets': 15,
                'total_packets': 1000
            },
            component="data_validator"
        )
    
    def report_stream_data_update(self, user_count):
        """Report stream data updates"""
        self.plugin.report_status(
            severity=StatusSeverity.INFO,
            category=StatusCategory.DATA_PROCESSING,
            code="STREAM_DATA_UPDATED",
            message="Stream data updated for active users",
            details={
                'active_users': user_count,
                'signals_updated': ['ECG', 'BPM', 'Airflow'],
                'update_time_ms': 25
            },
            component="stream_updater"
        )
    
    # ========================================
    # HARDWARE STATUS EXAMPLES
    # ========================================
    
    def report_sensor_malfunction(self, sensor_id):
        """Report hardware sensor issues"""
        self.plugin.report_status(
            severity=StatusSeverity.CRITICAL,
            category=StatusCategory.HARDWARE,
            code="SENSOR_MALFUNCTION",
            message="Hardware sensor not responding",
            details={
                'sensor_id': sensor_id,
                'sensor_type': 'ECG',
                'last_reading': '2025-08-15T12:30:00Z'
            },
            component="hardware_monitor"
        )
    
    def report_device_calibration_needed(self, device_id):
        """Report when device needs calibration"""
        self.plugin.report_status(
            severity=StatusSeverity.MEDIUM,
            category=StatusCategory.HARDWARE,
            code="DEVICE_CALIBRATION_NEEDED",
            message="Device requires calibration",
            details={
                'device_id': device_id,
                'last_calibration': '2025-08-01T09:00:00Z',
                'drift_percentage': 2.5
            },
            component="calibration_monitor"
        )
    
    # ========================================
    # SYSTEM STATUS EXAMPLES
    # ========================================
    
    def report_plugin_startup(self, mac_address):
        """Report successful plugin startup"""
        self.plugin.report_status(
            severity=StatusSeverity.INFO,
            category=StatusCategory.SYSTEM,
            code="PLUGIN_STARTUP_SUCCESS",
            message="Plugin started successfully",
            details={
                'mac_address': mac_address,
                'startup_time_ms': 2500,
                'version': '1.0.0'
            },
            component="plugin_manager"
        )
    
    def report_memory_usage_high(self, usage_percent):
        """Report high memory usage"""
        self.plugin.report_status(
            severity=StatusSeverity.MEDIUM,
            category=StatusCategory.PERFORMANCE,
            code="HIGH_MEMORY_USAGE",
            message="Memory usage is above recommended threshold",
            details={
                'memory_usage_percent': usage_percent,
                'threshold_percent': 80,
                'available_mb': 512
            },
            component="resource_monitor"
        )
    
    def report_system_shutdown(self):
        """Report system shutdown"""
        self.plugin.report_status(
            severity=StatusSeverity.INFO,
            category=StatusCategory.SYSTEM,
            code="SYSTEM_SHUTDOWN_INITIATED",
            message="System shutdown initiated",
            details={
                'shutdown_reason': 'user_request',
                'active_connections': 0
            },
            component="system_manager"
        )
    
    # ========================================
    # CONFIGURATION STATUS EXAMPLES
    # ========================================
    
    def report_config_validation_warning(self, config_key, value):
        """Report configuration validation warnings"""
        self.plugin.report_status(
            severity=StatusSeverity.LOW,
            category=StatusCategory.CONFIGURATION,
            code="CONFIG_VALUE_OUT_OF_RANGE",
            message="Configuration value is outside recommended range",
            details={
                'config_key': config_key,
                'current_value': value,
                'recommended_range': '1-100'
            },
            component="config_validator"
        )
    
    def report_config_loaded_successfully(self, config_file):
        """Report successful configuration loading"""
        self.plugin.report_status(
            severity=StatusSeverity.INFO,
            category=StatusCategory.CONFIGURATION,
            code="CONFIG_LOADED_SUCCESS",
            message="Configuration loaded successfully",
            details={
                'config_file': config_file,
                'settings_count': 25
            },
            component="config_loader"
        )

# ========================================
# USAGE PATTERNS AND BEST PRACTICES
# ========================================

def usage_examples():
    """
    Best practices for using the status reporting system:
    
    1. SEVERITY LEVELS:
       - CRITICAL: System-breaking issues that require immediate attention
       - HIGH: Major functionality problems that impact operations
       - MEDIUM: Minor issues that don't break core functionality
       - LOW: Warnings and non-critical issues
       - INFO: Informational messages and successful operations
    
    2. CATEGORIES:
       - CONNECTIVITY: Network, RabbitMQ, communication issues
       - COMMAND_PROCESSING: Command handling and processing
       - DATA_PROCESSING: Stream data, signal processing
       - HARDWARE: Sensor, device-related issues
       - CONFIGURATION: Setup, initialization, config issues
       - PERFORMANCE: Timing, resource usage issues
       - VALIDATION: Data validation problems
       - SYSTEM: General system operations
    
    3. STATUS CODES:
       - Use descriptive, consistent naming (e.g., "RABBITMQ_CONNECTION_FAILED")
       - Include the component and action (e.g., "SIGNAL_GENERATION_SUCCESS")
       - Use UPPER_CASE with underscores
    
    4. DETAILS:
       - Include relevant context for debugging
       - Add timing information when relevant
       - Include IDs, counts, and other metrics
       - Keep sensitive information out of details
    
    5. COMPONENTS:
       - Use consistent component names
       - Match the actual code component generating the status
       - Use lowercase with underscores (e.g., "command_processor")
    """
    pass

if __name__ == "__main__":
    print("Status Reporting Examples for PCC")
    print("See the PCCExamples class for practical use cases")
    print("Run usage_examples() for best practices")
