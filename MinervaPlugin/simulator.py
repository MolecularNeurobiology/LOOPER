from datetime import datetime, timedelta
import logging
import os
import sys
from time import sleep
from typing import List

# Legacy typed commands imported for backward compatibility
try:
    from command import GoToNextStep, StartCommand
except Exception:
    GoToNextStep = None
    StartCommand = None
from faker import Faker
from simulation import Simulation

def setup_logger(start_time):
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)

    # Generate a unique filename with the current date and time
    log_filename = start_time.strftime("simulation_%Y-%m-%d_%H-%M-%S.log")
    log_filepath = os.path.join(log_directory, log_filename)

    # Configure logging
    logging.basicConfig(
        filename=log_filepath,          # Log to this file
        level=logging.INFO,             # Set logging level (INFO, DEBUG, etc.)
        format="%(asctime)s - %(levelname)s - %(message)s"  # Log format
    )

    logging.info("Simulation Starting")
    return log_filepath

def load_mac_addresses() -> List[str]:
    """Load MAC addresses from a file, or generate defaults if file not found"""
    try:
        with open('fake_mac_addresses.txt', 'r') as f:
            mac_addresses = [line.strip() for line in f if line.strip()]
            if mac_addresses:
                return mac_addresses
    except FileNotFoundError:
        logging.warning("MAC addresses file not found, using default addresses")
    except Exception as e:
        logging.error(f"Error loading MAC addresses: {e}")

    # Generate default MAC addresses if file not found or empty
    return [f"00:00:00:00:00:{i:02d}" for i in range(1, 11)]

def run_simulation_loop(simulations: List[Simulation], start_time: datetime):
    """Run the simulation loop"""
    running = True
    print("Simulation running. Press Ctrl+C to stop.")

    while running:
        try:
            sleep(0.1)  # 0.1 second delay between updates (10 times per second)

            # Calculate elapsed time
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            formatted_elapsed_time = str(timedelta(seconds=int(elapsed_time.total_seconds())))

            # Print elapsed time on the same line
            sys.stdout.write(f"\rElapsed time: {formatted_elapsed_time}")
            sys.stdout.flush()

            for sim in simulations:
                try:
                    sim.report()

                    commands_to_process = sim.plugin.pop_commands()
                    for command in commands_to_process:
                        # Support both legacy typed commands and new dynamic dict commands
                        try:
                            # Legacy typed command handling (if classes are available)
                            if StartCommand is not None and isinstance(command, StartCommand):
                                if hasattr(command, 'payload') and hasattr(command.payload, 'steps') and command.payload.steps:
                                    logging.info(f"Configuring run with {len(command.payload.steps)} steps from payload (legacy)")
                                    sim.configure_run(command.payload.steps)
                                else:
                                    logging.info("Start received (legacy), using PCC default steps")
                                sim.start()
                                continue
                            if GoToNextStep is not None and isinstance(command, GoToNextStep):
                                sim.go_to_next_step()
                                continue
                        except Exception as e:
                            logging.error(f"Error handling legacy command type: {e}")

                        # New dynamic command handling expects a dict with 'type'
                        if isinstance(command, dict):
                            cmd_type = str(command.get('type', '')).lower()
                            payload = command.get('payload')

                            if cmd_type == 'start':
                                # Ignore steps in payload; PCC owns step resolution now
                                if payload and isinstance(payload, dict) and 'steps' in payload:
                                    logging.info("Start payload contained 'steps' - ignoring per new architecture")
                                sim.start()
                            elif cmd_type in ('go_to_next', 'go_to_next_step'):
                                sim.go_to_next_step()
                            elif cmd_type == 'go_to_step':
                                # Optional: jump to specific step if PCC exposes such API
                                step_id = None
                                if isinstance(payload, dict):
                                    step_id = payload.get('step') or payload.get('index') or payload.get('name')
                                logging.info(f"go_to_step received (step={step_id}) - implement in PCC as needed")
                            else:
                                logging.debug(f"Unknown or unsupported command type: {cmd_type}")
                        else:
                            logging.debug(f"Unknown command format: {type(command)}")

                    # Update metrics
                    metrics = sim.plugin.get_metrics()
                    metrics.avg_bpm = Faker.generate_fake_bpm()
                    metrics.avg_hr = Faker.generate_fake_hr()
                    sim.update_metrics(metrics)
                except Exception as e:
                    logging.error(f"Error processing simulation {sim.rig.mac_address}: {e}")

        except KeyboardInterrupt:
            print("\nReceived shutdown signal. Cleaning up...")
            running = False
        except Exception as e:
            logging.error(f"Error in simulation loop: {e}")
            running = False

def cleanup_simulations(simulations):
    """Cleanup all simulation resources"""
    for sim in simulations:
        try:
            sim.cleanup()
        except Exception as e:
            logging.error(f"Error cleaning up simulation: {e}")

def main():
    start_time = datetime.now()
    log_file = setup_logger(start_time)
    simulations: List[Simulation] = []

    try:
        number_of_rigs = 3
        mac_addresses = load_mac_addresses()

        if len(mac_addresses) < number_of_rigs:
            raise ValueError(f"Not enough MAC addresses. Need {number_of_rigs}, but only found {len(mac_addresses)}")

        print(f"Starting simulation with {number_of_rigs} rigs...")
        print(f"Log file: {log_file}")

        for i in range(number_of_rigs):
            sim = Simulation(mac_addresses[i], logging)
            simulations.append(sim)
            print(f"Initialized rig {i+1} with MAC: {mac_addresses[i]}")

        run_simulation_loop(simulations, start_time)
    except Exception as e:
        logging.error(f"Simulation failed: {e}")
        print(f"Simulation failed: {e}")
    finally:
        print("\nCleaning up simulations...")
        cleanup_simulations(simulations)
        print("Cleanup complete. Exiting.")

if __name__ == "__main__":
    main()
