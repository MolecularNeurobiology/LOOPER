from datetime import datetime, timedelta
import logging
import os
import sys
from time import sleep
from typing import List

from command import GoToNextStep, StartCommand
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

def main(): 
    start_time = datetime.now()
    setup_logger(start_time)

    number_of_rigs = 3
    simulations: List[Simulation] = []

    mac_addresses = []

    with open('fake_mac_addresses.txt', 'r') as f:
        mac_addresses = [line.strip() for line in f if line.strip()]

    for i in range(number_of_rigs):
        simulations.append(Simulation(mac_addresses[i], logging))

    running = True
    while running:
        try:
            sleep(1)

             # Calculate elapsed time
            current_time = datetime.now()
            elapsed_time = current_time - start_time  # Time difference
            formatted_elapsed_time = str(timedelta(seconds=elapsed_time.total_seconds()))

            # Print elapsed time on the same line
            sys.stdout.write(f"\rElapsed time: {formatted_elapsed_time}")
            sys.stdout.flush()

            logging.info("")
            for sim in simulations:
                sim.report()

                commands_to_process = sim.plugin.pop_commands()
                for command in commands_to_process:
                    match command:
                        case StartCommand():
                            sim.start()
                        case GoToNextStep():
                            sim.go_to_next_step()
                        case _:
                            pass
                # for demo purposes, simulate updating the metrics
                metrics = sim.plugin.get_metrics()
                metrics.avg_bpm = Faker.generate_fake_bpm()
                metrics.avg_hr = Faker.generate_fake_hr()
                sim.update_metrics(metrics)


        except (EOFError, KeyboardInterrupt):
            logging.info('')
            logging.info("Simulation Ending")
            running = False
        

if __name__ == "__main__":
    main()