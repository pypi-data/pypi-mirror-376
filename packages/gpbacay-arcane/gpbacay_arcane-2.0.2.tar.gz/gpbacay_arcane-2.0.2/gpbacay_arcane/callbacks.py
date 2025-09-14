from tensorflow.keras.callbacks import Callback

class DynamicSelfModelingReservoirCallback(Callback):
    def __init__(self, reservoir_layer, performance_metric='accuracy', target_metric=0.98,
                 growth_rate=10, prune_rate=0.05, performance_threshold=0.01, 
                 growth_phase_length=10, pruning_phase_length=5, stagnation_epochs=15, apoptosis_rate=1):
        super().__init__()
        self.reservoir_layer = reservoir_layer
        self.performance_metric = performance_metric
        self.target_metric = target_metric
        self.growth_rate = growth_rate
        self.prune_rate = prune_rate
        self.performance_threshold = performance_threshold
        self.growth_phase_length = growth_phase_length
        self.pruning_phase_length = pruning_phase_length
        self.stagnation_epochs = stagnation_epochs # Number of epochs with no improvement to trigger apoptosis
        self.apoptosis_rate = apoptosis_rate # Number of neurons to prune
        self.performance_history = []
        self.stagnation_counter = 0

    def on_epoch_end(self, epoch, logs=None):
        current_metric = logs.get(self.performance_metric, 0)
        self.performance_history.append(current_metric)

        # Calculate the rate of change in performance over the last epoch
        if len(self.performance_history) > 1:
            improvement_rate = current_metric - self.performance_history[-2]
        else:
            improvement_rate = 0

        # If performance improvement is above the threshold, trigger growth
        if improvement_rate > self.performance_threshold:
            self.reservoir_layer.add_neurons(self.growth_rate)
            print(f" - Growing reservoir by {self.growth_rate} neurons.")
            self.stagnation_counter = 0 # Reset stagnation counter on improvement
        else:
            self.stagnation_counter += 1

        # Trigger pruning if needed based on the prune rate
        if improvement_rate < self.performance_threshold:
            self.reservoir_layer.prune_connections(self.prune_rate)
            print(f" - Pruned connections by {self.prune_rate * 100}%.")
        
        # If performance has stagnated, trigger apoptosis
        if self.stagnation_counter >= self.stagnation_epochs:
            self.reservoir_layer.prune_neurons(self.apoptosis_rate)
            print(f" - Performance stagnated. Pruning {self.apoptosis_rate} neuron(s) via apoptosis.")
            self.stagnation_counter = 0 # Reset after apoptosis

        # If the current metric has reached the target, allow for reservoir growth or pruning
        if current_metric >= self.target_metric:
            print(f" - Performance metric {self.performance_metric} reached target {self.target_metric}.")
            if improvement_rate > self.performance_threshold:
                self.reservoir_layer.add_neurons(self.growth_rate)
            elif improvement_rate < self.performance_threshold:
                self.reservoir_layer.prune_connections(self.prune_rate)

        # Optionally print or log the training progress
        if epoch % 10 == 0:
            print(f"Epoch {epoch+1}: {self.performance_metric} = {current_metric:.4f}")

    def reset(self):
        """Resets the monitoring mechanism for a new training session."""
        self.performance_history = []
        self.stagnation_counter = 0

    def get_config(self):
        """Returns the configuration of the callback."""
        config = {
            'reservoir_layer': self.reservoir_layer,
            'performance_metric': self.performance_metric,
            'target_metric': self.target_metric,
            'growth_rate': self.growth_rate,
            'prune_rate': self.prune_rate,
            'performance_threshold': self.performance_threshold,
            'growth_phase_length': self.growth_phase_length,
            'pruning_phase_length': self.pruning_phase_length,
            'stagnation_epochs': self.stagnation_epochs,
            'apoptosis_rate': self.apoptosis_rate
        }
        return config

    @classmethod
    def from_config(cls, config):
        """Creates the callback from its configuration."""
        return cls(**config)