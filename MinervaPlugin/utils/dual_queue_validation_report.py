#!/usr/bin/env python3

"""
Dual Queue Architecture Validation Report Generator

This script generates a comprehensive validation report for the dual queue architecture,
including system health, performance metrics, and architecture compliance.

Usage:
    python3 dual_queue_validation_report.py
"""

import json
import time
from datetime import datetime
from ..core.plugin import PCC_Plugin
from ..core.config import *

class DualQueueValidator:
    """Comprehensive validation and reporting for dual queue architecture"""
    
    def __init__(self):
        self.validation_results = {}
        self.test_mac_address = "validation:test:mac"
        
    def validate_architecture_compliance(self):
        """Validate that the system meets dual queue architecture requirements"""
        print("🔍 VALIDATING ARCHITECTURE COMPLIANCE")
        print("=" * 60)
        
        # Mock registration parameters
        class MockRegistrationParams:
            def __init__(self):
                self.mac_address = self.test_mac_address
                self.rig_id = "validation_rig"
        
        plugin = PCC_Plugin(MockRegistrationParams())
        
        compliance_checks = []
        
        # Check 1: Dual queue mode detection
        dual_queue_active = plugin.is_dual_queue_mode()
        compliance_checks.append(("Dual Queue Mode", dual_queue_active))
        
        # Check 2: Required components present
        required_components = [
            ("Stream Control Consumer", hasattr(plugin, '_stream_control_consumer')),
            ("Rig Stream Producer", hasattr(plugin, '_rig_stream_producer')),
            ("Active Users Tracking", hasattr(plugin, '_active_users')),
            ("Heartbeat Management", hasattr(plugin, '_last_heartbeat')),
            ("Command Queue", hasattr(plugin, '_commands')),
        ]
        
        for component_name, present in required_components:
            compliance_checks.append((component_name, present))
        
        # Check 3: Architecture mode reporting
        stats = plugin.get_command_processing_stats()
        correct_mode = stats.get('architecture_mode') == 'dual_queue_pure'
        compliance_checks.append(("Architecture Mode", correct_mode))
        
        # Check 4: Streaming metrics availability
        metrics = plugin.get_streaming_metrics()
        metrics_complete = all(key in metrics for key in [
            'timestamp', 'mac_address', 'active_users', 'commands', 
            'streaming', 'system', 'queues'
        ])
        compliance_checks.append(("Streaming Metrics", metrics_complete))
        
        plugin.stop()
        
        # Report compliance
        passed_checks = sum(1 for _, passed in compliance_checks if passed)
        total_checks = len(compliance_checks)
        compliance_rate = passed_checks / total_checks
        
        print(f"Architecture Compliance: {compliance_rate:.1%} ({passed_checks}/{total_checks})")
        
        for check_name, passed in compliance_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
        
        self.validation_results['architecture_compliance'] = {
            'rate': compliance_rate,
            'passed': passed_checks,
            'total': total_checks,
            'checks': compliance_checks
        }
        
        return compliance_rate >= 1.0  # 100% compliance required
    
    def validate_performance_characteristics(self):
        """Validate system performance meets requirements"""
        print("\n⚡ VALIDATING PERFORMANCE CHARACTERISTICS")
        print("=" * 60)
        
        class MockRegistrationParams:
            def __init__(self):
                self.mac_address = self.test_mac_address
                self.rig_id = "perf_test_rig"
        
        plugin = PCC_Plugin(MockRegistrationParams())
        
        performance_metrics = {}
        
        # Test 1: Stream data generation performance
        start_time = time.time()
        for _ in range(100):
            stream_data = plugin._generate_stream_data()
        generation_time = (time.time() - start_time) / 100
        
        performance_metrics['stream_generation_ms'] = generation_time * 1000
        print(f"  Stream Data Generation: {generation_time*1000:.2f}ms per call")
        
        # Test 2: User management performance
        start_time = time.time()
        for i in range(1000):
            mock_heartbeat = {
                'body': json.dumps({
                    'type': 'stream',
                    'macAddress': self.test_mac_address,
                    'userId': f'user_{i}',
                    'payload': {}
                }).encode()
            }
            plugin._handle_stream_control(mock_heartbeat)
        
        user_mgmt_time = (time.time() - start_time) / 1000
        performance_metrics['user_management_ms'] = user_mgmt_time * 1000
        print(f"  User Management: {user_mgmt_time*1000:.2f}ms per heartbeat")
        
        # Test 3: Command processing performance
        start_time = time.time()
        for i in range(100):
            mock_command = {
                'body': json.dumps({
                    'type': 'go_to_next',
                    'macAddress': self.test_mac_address,
                    'payload': {},
                    'userId': f'cmd_user_{i}'
                }).encode()
            }
            plugin._handle_command(mock_command)
        
        command_time = (time.time() - start_time) / 100
        performance_metrics['command_processing_ms'] = command_time * 1000
        print(f"  Command Processing: {command_time*1000:.2f}ms per command")
        
        # Test 4: Metrics collection performance
        start_time = time.time()
        for _ in range(100):
            metrics = plugin.get_streaming_metrics()
        metrics_time = (time.time() - start_time) / 100
        
        performance_metrics['metrics_collection_ms'] = metrics_time * 1000
        print(f"  Metrics Collection: {metrics_time*1000:.2f}ms per call")
        
        plugin.stop()
        
        # Evaluate performance
        performance_thresholds = {
            'stream_generation_ms': 10.0,      # < 10ms
            'user_management_ms': 1.0,         # < 1ms
            'command_processing_ms': 5.0,      # < 5ms
            'metrics_collection_ms': 2.0       # < 2ms
        }
        
        performance_passed = all(
            performance_metrics[metric] <= threshold
            for metric, threshold in performance_thresholds.items()
        )
        
        print(f"\nPerformance Validation: {'✅ PASS' if performance_passed else '❌ FAIL'}")
        
        self.validation_results['performance'] = {
            'passed': performance_passed,
            'metrics': performance_metrics,
            'thresholds': performance_thresholds
        }
        
        return performance_passed
    
    def validate_scalability_limits(self):
        """Test system behavior under load"""
        print("\n📈 VALIDATING SCALABILITY LIMITS")
        print("=" * 60)
        
        class MockRegistrationParams:
            def __init__(self):
                self.mac_address = self.test_mac_address
                self.rig_id = "scale_test_rig"
        
        plugin = PCC_Plugin(MockRegistrationParams())
        
        scalability_results = {}
        
        # Test 1: Maximum concurrent users
        print("  Testing concurrent user capacity...")
        max_users = 0
        
        for user_count in [10, 50, 100, 500, 1000]:
            try:
                start_time = time.time()
                
                # Add users
                for i in range(user_count):
                    mock_heartbeat = {
                        'body': json.dumps({
                            'type': 'stream',
                            'macAddress': self.test_mac_address,
                            'userId': f'scale_user_{i}',
                            'payload': {}
                        }).encode()
                    }
                    plugin._handle_stream_control(mock_heartbeat)
                
                # Check if system is still responsive
                metrics = plugin.get_streaming_metrics()
                response_time = time.time() - start_time
                
                if response_time < 1.0 and metrics['active_users']['count'] == user_count:
                    max_users = user_count
                    print(f"    ✅ {user_count} users: {response_time:.3f}s")
                else:
                    print(f"    ❌ {user_count} users: Failed ({response_time:.3f}s)")
                    break
                    
            except Exception as e:
                print(f"    ❌ {user_count} users: Exception ({e})")
                break
        
        scalability_results['max_concurrent_users'] = max_users
        
        # Test 2: Command throughput
        print("  Testing command throughput...")
        
        start_time = time.time()
        commands_processed = 0
        
        for i in range(1000):
            try:
                mock_command = {
                    'body': json.dumps({
                        'type': 'go_to_next',
                        'macAddress': self.test_mac_address,
                        'payload': {},
                        'userId': f'throughput_user_{i}'
                    }).encode()
                }
                plugin._handle_command(mock_command)
                commands_processed += 1
            except Exception:
                break
        
        throughput_time = time.time() - start_time
        commands_per_second = commands_processed / throughput_time
        
        scalability_results['commands_per_second'] = commands_per_second
        print(f"    Command Throughput: {commands_per_second:.1f} commands/second")
        
        plugin.stop()
        
        # Evaluate scalability
        scalability_passed = (
            max_users >= 100 and  # Support at least 100 concurrent users
            commands_per_second >= 500  # Process at least 500 commands/second
        )
        
        print(f"\nScalability Validation: {'✅ PASS' if scalability_passed else '❌ FAIL'}")
        
        self.validation_results['scalability'] = {
            'passed': scalability_passed,
            'max_users': max_users,
            'commands_per_second': commands_per_second
        }
        
        return scalability_passed
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 80)
        print("🎯 DUAL QUEUE ARCHITECTURE VALIDATION REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().isoformat()}")
        print(f"Test MAC Address: {self.test_mac_address}")
        
        # Run all validations
        validations = [
            ("Architecture Compliance", self.validate_architecture_compliance),
            ("Performance Characteristics", self.validate_performance_characteristics),
            ("Scalability Limits", self.validate_scalability_limits),
        ]
        
        validation_results = []
        for validation_name, validation_func in validations:
            try:
                result = validation_func()
                validation_results.append(result)
            except Exception as e:
                print(f"\n❌ {validation_name} failed: {e}")
                validation_results.append(False)
        
        # Overall assessment
        passed_validations = sum(validation_results)
        total_validations = len(validation_results)
        overall_success = passed_validations == total_validations
        
        print(f"\n" + "=" * 80)
        print("📋 VALIDATION SUMMARY")
        print("=" * 80)
        
        validation_names = [name for name, _ in validations]
        for i, (name, result) in enumerate(zip(validation_names, validation_results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {name}")
        
        print(f"\n🏆 Overall Result: {passed_validations}/{total_validations} validations passed")
        
        if overall_success:
            print("\n🎉 DUAL QUEUE ARCHITECTURE VALIDATION: SUCCESSFUL!")
            print("   ✅ Architecture is compliant with requirements")
            print("   ✅ Performance meets or exceeds targets")
            print("   ✅ Scalability limits are acceptable")
            print("   ✅ System is ready for production deployment")
        else:
            print("\n⚠️  DUAL QUEUE ARCHITECTURE VALIDATION: INCOMPLETE")
            print("   Some validation criteria were not met.")
            print("   Review the detailed results above.")
        
        # Detailed metrics
        if 'performance' in self.validation_results:
            print(f"\n📊 Performance Metrics:")
            for metric, value in self.validation_results['performance']['metrics'].items():
                threshold = self.validation_results['performance']['thresholds'][metric]
                status = "✅" if value <= threshold else "❌"
                print(f"   {status} {metric.replace('_', ' ').title()}: {value:.2f}ms (threshold: {threshold}ms)")
        
        if 'scalability' in self.validation_results:
            print(f"\n📈 Scalability Results:")
            print(f"   Max Concurrent Users: {self.validation_results['scalability']['max_users']}")
            print(f"   Command Throughput: {self.validation_results['scalability']['commands_per_second']:.1f} cmd/s")
        
        return {
            'overall_success': overall_success,
            'passed_validations': passed_validations,
            'total_validations': total_validations,
            'detailed_results': self.validation_results,
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    validator = DualQueueValidator()
    report = validator.generate_validation_report()
    
    # Save report to file
    with open('dual_queue_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: dual_queue_validation_report.json")
    
    # Exit with appropriate code
    exit_code = 0 if report['overall_success'] else 1
    exit(exit_code)
