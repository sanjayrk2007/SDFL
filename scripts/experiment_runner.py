import os
import sys
import time

# Add root to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.experiment_config import ExperimentConfig
from scripts.result_utils import ResultTracker

class ExperimentRunner:
    def __init__(self, config=None):
        if config is None:
            self.config = ExperimentConfig.parse_args()
        else:
            self.config = config
        
        self.tracker = ResultTracker(self.config)
        
    def setup(self):
        """Override to setup the experiment"""
        pass
        
    def run_iteration(self, iteration):
        """Override to run a single iteration/setting"""
        pass
        
    def run(self):
        print(f"Starting experiment: {self.config.exp_name}")
        if self.config.smoke_test:
            print("RUNNING IN SMOKE TEST MODE")
            
        try:
            self.setup()
            
            # Subclasses should implement their own run logic and call self.tracker.add_result()
            self._execute_experiment()
            
        except Exception as e:
            print(f"Experiment failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.tracker.set_error(str(e))
        finally:
            results_path = self.tracker.save()
            print(f"Experiment completed. Results saved to {results_path}")
            
    def _execute_experiment(self):
        """Subclasses should implement this"""
        raise NotImplementedError("Subclasses must implement _execute_experiment")

if __name__ == "__main__":
    runner = ExperimentRunner()
    runner.run()
