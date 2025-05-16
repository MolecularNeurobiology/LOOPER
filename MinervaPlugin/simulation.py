from plugin import Plugin, PluginRegistration, MinervaStreamData
from rig import Rig
from run import Run
from faker import Faker
import random
import json
from command import Stage, Signal

class Simulation:
    def __init__(self, mac_address, logger):
        self.logger = logger
        self.rig = Rig(mac_address)
        self._run = Run()
        
        try:
            self._plugin = Plugin(PluginRegistration(mac_address=mac_address), logger)
            self._plugin.set_step(self._run.get_current_step_name())
            
            # Set up initial stream data
            self._setup_stream_data()
            
            logger.info("Attempting to start plugin")
            self._plugin.start()
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {e}")
            raise

    @property
    def plugin(self):
        """Access the plugin instance"""
        return self._plugin

    def cleanup(self):
        """Cleanup simulation resources"""
        try:
            if hasattr(self, '_plugin'):
                self._plugin.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def _setup_stream_data(self):
        """Set up initial stream data structure for this simulation"""
        try:
            # Create stages based on run steps
            stages = self._create_stages()
            
            # Create diverse signals
            signals = self._create_signals()
            
            # Create stream data
            self.stream_data = MinervaStreamData(
                macAddress=self.rig.mac_address,
                stages=stages,
                signals=signals,
                currentStage=self._run.get_current_step_name()
            )
            
            # Update plugin with stream data
            self._plugin.update_stream_data(self.stream_data)
        except Exception as e:
            self.logger.error(f"Failed to setup stream data: {e}")
            raise

    def report(self):
        """Report simulation status and update stream if active"""
        try:
            self.logger.info(f'{self.rig.mac_address} - {self.rig.state} - {self._run.get_current_step_name()}')
            
            # Only update stream data if plugin is actually streaming
            if self._plugin.get_is_streaming():
                self._update_signal_data()
        except Exception as e:
            self.logger.error(f"Error in report: {e}")

    def _update_signal_data(self):
        """Update all signals with new data values"""
        try:
            if not hasattr(self, 'stream_data'):
                return

            for signal in self.stream_data.signals:
                self._update_single_signal(signal)
            
            # Update the plugin's stream data
            self._plugin.update_stream_data(self.stream_data)
        except Exception as e:
            self.logger.error(f"Error updating signal data: {e}")

    def _update_single_signal(self, signal):
        """Update a single signal based on its type"""
        signal_type = signal.get('type')
        if not signal_type:
            return

        update_methods = {
            'time_series': self._update_time_series_signal,
            'timestamp': self._update_timestamp_signal,
            'single_value': self._update_single_value_signal,
            'status': self._update_status_signal,
            'debug': self._update_debug_signal
        }

        if signal_type in update_methods:
            update_methods[signal_type](signal)

    def update_step(self):
        """Update metrics step and stream data current stage"""
        try:
            metrics = self._plugin.get_metrics()
            metrics.step = self._run.get_current_step_name()
            self._plugin.update_metrics(metrics)
            
            if hasattr(self, 'stream_data'):
                self.stream_data.currentStage = self._run.get_current_step_name()
                self._plugin.update_stream_data(self.stream_data)
        except Exception as e:
            self.logger.error(f"Error updating step: {e}")

    def update_metrics(self, payload):
        """Update metrics in the plugin"""
        self._plugin.update_metrics(payload)
    
    def start(self):
        self.run.start()
        self.update_step()
        
        # Update rig state
        self.rig.state = "RUNNING"
    
    def go_to_next_step(self):
        self.run.go_to_next_step()
        self.update_step()
    
    def configure_run(self, steps):
        """Configure the run with the provided steps"""
        self.run.define_steps(steps)
        
        # Update stream data with new stages based on steps
        if hasattr(self, 'stream_data'):
            stages = []
            for i, step in enumerate(steps):
                # Map step to a stage type
                stage_type = 'wait_for_user'  # Default
                if i == 0 or i == len(steps) - 1:
                    stage_type = 'wait_for_user'  # First and last steps are wait_for_user
                elif i % 2 == 0:
                    stage_type = 'timed'  # Even steps are timed
                else:
                    stage_type = 'wait_for_condition'  # Odd steps wait for condition
                    
                stage = {
                    'name': step.name,
                    'type': stage_type
                }
                
                # Add duration for timed stages
                if stage_type == 'timed':
                    stage['durationInSeconds'] = 120
                    
                stages.append(stage)
                
            self.stream_data.stages = stages
            self.plugin.update_stream_data(self.stream_data)
        
        self.update_step()

    def _create_stages(self):
        """Create initial stages based on run steps"""
        stages = []
        for i, step in enumerate(self._run.steps):
            # Map step to a stage type
            stage_type = 'wait_for_user'  # Default
            if i == 0 or i == len(self._run.steps) - 1:
                stage_type = 'wait_for_user'  # First and last steps are wait_for_user
            elif i % 2 == 0:
                stage_type = 'timed'  # Even steps are timed
            else:
                stage_type = 'wait_for_condition'  # Odd steps wait for condition
            
            stage = {
                'name': step.name,
                'type': stage_type
            }
            
            # Add duration for timed stages
            if stage_type == 'timed':
                stage['durationInSeconds'] = 120
            
            stages.append(stage)
        
        return stages

    def _create_signals(self):
        """Create initial signals for this simulation"""
        signals = [
            {
                'name': 'Heart Rate',
                'type': 'time_series',
                'xUnit': 'seconds',
                'yUnit': 'bpm',
                'xWindowMinInSeconds': 0,
                'xWindowMaxInSeconds': 300,
                'yWindowMinInSeconds': 0,
                'yWindowMaxInSeconds': 200,
                'data': []
            },
            {
                'name': 'Status',
                'type': 'status',
                'data': True
            },
            {
                'name': 'Debug Info',
                'type': 'debug',
                'data': 'Simulation running normally'
            }
        ]
        return signals
