from ...measurement.hooks.base_hooks import BasePostExecutionHook

class AutoClose(BasePostExecutionHook):
    def run(self, workbench, engine):
        print('  Closing Exopy...')
        ui = workbench.get_plugin(u'enaml.workbench.ui')
        ui.stop_application()