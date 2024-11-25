from plugin import Plugin, PluginRegistration
from rig import Rig
from run import BasicRun


class Simulation:
    def __init__(self, mac_address, logger):
        _run = BasicRun()
        self.run = _run
        self.rig = Rig(mac_address)
        self.logger = logger
        _plugin = Plugin(PluginRegistration(mac_address=mac_address), logger)
        _plugin.set_step(_run.get_current_step_name())
        self.plugin = _plugin
        

        logger.info("Attempting to start plugin")
        self.plugin.start()

    def report(self):
        self.logger.info(f'{self.rig.mac_address} - {self.rig.state} - {self.run.get_current_step_name()}')

    def update_step(self):
        metrics = self.plugin.get_metrics()
        metrics.step = self.run.get_current_step_name()
        self.plugin.update_metrics(metrics)

    def update_metrics(self, payload):
        self.plugin.update_metrics(payload)

    def start(self):
        self.run.start()
        self.update_step()

    def go_to_next_step(self):
        self.run.go_to_next_step()
        self.update_step()