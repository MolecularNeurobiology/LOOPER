from plugin import Plugin, PluginRegistration, MinervaStreamData
from rig import Rig
from run import Run
import random
import time
import math

class Simulation:
    def __init__(self, mac_address, logger):
        self.logger = logger
        self.rig = Rig(mac_address)
        self._run = Run()

        # Initialize time tracking for signals
        self._start_time = time.time()
        self._last_update_time = self._start_time

        # Heart rate simulation parameters
        self._base_heart_rate = 72  # Base heart rate in BPM
        self._heart_rate_noise_amplitude = 8  # Amplitude of noise
        self._heart_rate_trend_frequency = 0.01  # Frequency of slow trend changes
        self._heart_rate_noise_frequency = 0.1  # Frequency of noise variations

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
                mac_address=self.rig.mac_address,
                stages=stages,
                signals=signals,
                current_stage=self._run.get_current_step_name()
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
        """Update all signals with new data values for all active user sessions"""
        try:
            if not hasattr(self, 'stream_data'):
                return

            # Update signals in the template stream data
            for signal in self.stream_data.signals:
                self._update_single_signal(signal)

            # Debug: Log BPM signal info periodically
            bpm_signal = next((s for s in self.stream_data.signals if s['name'] == 'BPM'), None)
            if bpm_signal and bpm_signal.get('data'):
                self.logger.info(f"BPM signal being sent to frontend: name={bpm_signal['name']}, type={bpm_signal['type']}, display_with={bpm_signal.get('display_with')}, data_length={len(bpm_signal.get('data', []))}")

            # Update stream data for all active user sessions
            active_users = self._plugin.get_active_user_sessions()
            for user_id in active_users:
                # Get the user's stream data and update it
                user_stream_data = self._plugin.get_stream_data(user_id)
                if user_stream_data:
                    # Copy updated signals to user's stream data
                    user_stream_data.signals = self.stream_data.signals.copy()
                    self._plugin.update_stream_data(user_stream_data, user_id)

            # Also update the default stream data (for backward compatibility)
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
                self.stream_data.current_stage = self._run.get_current_step_name()
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

                # Add duration for timed stages (use snake_case for backend)
                if stage_type == 'timed':
                    stage['duration_in_seconds'] = 120

                stages.append(stage)

            self.stream_data.stages = stages
            self._plugin.update_stream_data(self.stream_data)

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

            # Add duration for timed stages (use snake_case for backend)
            if stage_type == 'timed':
                stage['duration_in_seconds'] = 120

            stages.append(stage)

        return stages

    def _create_signals(self):
        """Create initial signals for this simulation"""
        signals = [
            {
                'name': 'ECG',
                'type': 'time_series',
                'x_unit': 's',
                'y_unit': 'mV',
                'x_window_min_in_seconds': -10,
                'x_window_max_in_seconds': 0,
                'y_window_min_in_seconds': -1,
                'y_window_max_in_seconds': 1,
                'data': []
            },
            {
                'name': 'BPM',
                'type': 'timestamp',
                'display_with': 'ECG',
                'data': []
            },
            {
                'name': 'Airflow',
                'type': 'time_series',
                'x_unit': 's',
                'y_unit': 'L/min',
                'x_window_min_in_seconds': -60,
                'x_window_max_in_seconds': 0,
                'y_window_min_in_seconds': -20,
                'y_window_max_in_seconds': 20,
                'data': []
            },
            {
                'name': 'avgHR',
                'type': 'single_value',
                'value_unit': 'bpm',
                'data': 72
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

    def _generate_noisy_heart_rate(self, current_time):
        """Generate a noisy heart rate value based on time"""
        # Create a slow trending component
        trend = math.sin(current_time * self._heart_rate_trend_frequency) * 10

        # Create faster noise component
        noise = math.sin(current_time * self._heart_rate_noise_frequency) * self._heart_rate_noise_amplitude

        # Add random noise
        random_noise = random.gauss(0, 3)

        # Combine all components
        heart_rate = self._base_heart_rate + trend + noise + random_noise

        # Ensure heart rate stays within reasonable bounds
        heart_rate = max(50, min(150, heart_rate))

        return round(heart_rate, 1)

    def _generate_noisy_breathing_rate(self, current_time):
        """Generate a noisy breathing rate value based on time"""
        base_breathing_rate = 25  # Base breathing rate in breaths per minute

        # Create a slow trending component
        trend = math.sin(current_time * 0.005) * 5

        # Create faster noise component
        noise = math.sin(current_time * 0.05) * 3

        # Add random noise
        random_noise = random.gauss(0, 1.5)

        # Combine all components
        breathing_rate = base_breathing_rate + trend + noise + random_noise

        # Ensure breathing rate stays within reasonable bounds
        breathing_rate = max(10, min(50, breathing_rate))

        return round(breathing_rate, 1)

    def _generate_ecg_signal(self, current_time):
        """Generate ECG-like signal with periodic spikes"""
        # Base ECG waveform
        base_ecg = math.sin(current_time * 2) * 0.1

        # Add periodic heart beat spikes (roughly every 0.8-1.2 seconds)
        heart_period = 0.8 + 0.4 * math.sin(current_time * 0.1)  # Variable heart rate
        spike_phase = (current_time % heart_period) / heart_period

        # Create QRS complex-like spike
        if spike_phase < 0.1:
            spike = 0.8 * math.sin(spike_phase * 10 * math.pi)
        else:
            spike = 0

        # Add some noise
        noise = random.gauss(0, 0.02)

        return base_ecg + spike + noise

    def _generate_airflow_signal(self, current_time):
        """Generate airflow signal representing breathing as a clean sin wave"""
        # Breathing cycle (roughly 15 breaths per minute)
        breathing_rate = 15  # breaths per minute
        breathing_period = 60 / breathing_rate  # period in seconds

        # Clean sinusoidal breathing pattern
        airflow = 15 * math.sin(2 * math.pi * current_time / breathing_period)

        # Add minimal noise for realism
        noise = random.gauss(0, 0.5)

        return airflow + noise

    def _update_time_series_signal(self, signal):
        """Update a time series signal with new data points"""
        current_time = time.time()
        elapsed_time = current_time - self._start_time

        # Only update if enough time has passed (e.g., every 0.1 seconds for higher resolution)
        if current_time - self._last_update_time < 0.1:
            return

        self._last_update_time = current_time

        # Generate new data point based on signal name
        if signal['name'] == 'ECG':
            y_value = self._generate_ecg_signal(elapsed_time)
        elif signal['name'] == 'Airflow':
            y_value = self._generate_airflow_signal(elapsed_time)
        else:
            # Default to a simple sine wave for other signals
            y_value = 50 + 20 * math.sin(elapsed_time * 0.1)

        # Create new data point with relative time (negative for sliding window)
        window_min = signal.get('x_window_min_in_seconds', -60)

        new_point = {
            'x': 0,  # Current time is always 0 in sliding window
            'y': y_value
        }

        # Add to data array
        if 'data' not in signal:
            signal['data'] = []

        # Shift existing points back in time
        for point in signal['data']:
            point['x'] -= 0.1  # Move back by update interval

        # Add new point at current time (x=0)
        signal['data'].append(new_point)

        # Remove points that are outside the window
        signal['data'] = [point for point in signal['data'] if point['x'] >= window_min]

    def _update_timestamp_signal(self, signal):
        """Update a timestamp signal with new events using sliding window approach"""
        current_time = time.time()
        elapsed_time = current_time - self._start_time

        if 'data' not in signal:
            signal['data'] = []

        # Initialize timestamp-specific last update time if not exists
        if not hasattr(self, '_last_timestamp_update_time'):
            self._last_timestamp_update_time = 0

        # Use the same update interval as time series signals
        if current_time - self._last_timestamp_update_time < 0.1:
            return

        self._last_timestamp_update_time = current_time

        if signal['name'] == 'BPM':
            # Shift existing points back in time (same as time series)
            for point in signal['data']:
                point['x'] -= 0.1  # Move back by update interval

            # Add BPM timestamp events every 0.8-1.2 seconds (realistic heartbeat timing)
            # Use a simple time-based approach for consistent spacing
            if int(elapsed_time * 10) % 8 == 0 and elapsed_time > 1:  # Every 0.8 seconds
                # Check if we should add a new event (avoid duplicates at x=0)
                should_add = True
                if signal['data']:
                    # Check if there's already a recent event near x=0
                    recent_events = [p for p in signal['data'] if p['x'] >= -0.1]
                    if recent_events:
                        should_add = False

                if should_add:
                    current_bpm = self._generate_noisy_heart_rate(elapsed_time)
                    new_event = {
                        'x': 0,  # Current time is always 0 in sliding window
                        'y': 1,  # Fixed y value for timestamp events - always 1
                        'label': f'{int(current_bpm)} BPM'
                    }
                    signal['data'].append(new_event)
                    self.logger.info(f"Added BPM event: {new_event}")

            # Remove points that are outside the window (use ECG window for consistency)
            window_min = -10  # Same as ECG window
            signal['data'] = [point for point in signal['data'] if point['x'] >= window_min]

            # Debug: Log current BPM signal data
            if signal['data']:
                self.logger.info(f"BPM signal has {len(signal['data'])} events. Recent events: {[{'x': p['x'], 'y': p['y'], 'label': p['label']} for p in signal['data'][-3:]]}")
        else:
            # Default timestamp behavior for other signals
            # Shift existing points back in time
            for point in signal['data']:
                point['x'] -= 0.1

            # Add a timestamp event every 30 seconds
            if int(elapsed_time) % 30 == 0 and elapsed_time > 1:
                # Check if we should add a new event
                should_add = True
                if signal['data']:
                    recent_events = [p for p in signal['data'] if p['x'] >= -0.5]
                    if recent_events:
                        should_add = False

                if should_add:
                    signal['data'].append({
                        'x': 0,  # Current time is always 0 in sliding window
                        'y': 1,  # Fixed y value for timestamp events
                        'label': f'Event at {int(elapsed_time)}s'
                    })

            # Remove points outside window
            window_min = -60
            signal['data'] = [point for point in signal['data'] if point['x'] >= window_min]

    def _update_single_value_signal(self, signal):
        """Update a single value signal"""
        current_time = time.time()
        elapsed_time = current_time - self._start_time

        # Update based on signal name
        if signal['name'] == 'avgHR':
            # Generate average heart rate with some variation
            signal['data'] = round(self._generate_noisy_heart_rate(elapsed_time), 1)
        else:
            # Default to a slowly changing value
            signal['data'] = 50 + 10 * math.sin(elapsed_time * 0.02)

    def _update_status_signal(self, signal):
        """Update a status signal"""
        # Toggle status occasionally for demonstration
        current_time = time.time()
        elapsed_time = current_time - self._start_time

        # Toggle every 60 seconds
        signal['data'] = (int(elapsed_time) // 60) % 2 == 0

    def _update_debug_signal(self, signal):
        """Update a debug signal with current information"""
        current_time = time.time()
        elapsed_time = current_time - self._start_time

        signal['data'] = f'Simulation running for {int(elapsed_time)}s - Step: {self._run.get_current_step_name()}'
