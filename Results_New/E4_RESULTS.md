# Experiment E4 -- DP-SGD Integration (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Starting checkpoint** | checkpoints/e3_best.pth |
| **Grid** | C in {0.5, 1.0, 2.0}, sigma in {0.5, 1.0, 1.5} |
| **Selection rule** | max(val_dice / (epsilon + 1e-5)) |

## Full sweep output (captured this run)

```
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:24:00:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:24:00:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
2026-09-16 14:24:04,369	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8869992038.0, 'memory': 17739984078.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
09/16/2026 14:24:09:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8869992038.0, 'memory': 17739984078.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:24:09:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:24:09:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:24:09:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:24:09:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:24:09:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:24:09:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:24:09:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:24:09:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:24:09:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:24:09:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=6776)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6776)[0m 
[36m(ClientAppActor pid=6776)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=6776)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=6776)[0m         
[36m(ClientAppActor pid=6776)[0m 09/16/2026 14:24:17:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6776)[0m 
[36m(ClientAppActor pid=6776)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=6776)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=6776)[0m         
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[36m(ClientAppActor pid=6776)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=6776)[0m   warnings.warn(
[36m(ClientAppActor pid=6779)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=6779)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=6779)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=6779)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=6779)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6779)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster] (Ray deduplicates logs by default. Set RAY_DEDUP_LOGS=0 to disable log deduplication, or see https://docs.ray.io/en/master/ray-observability/user-guides/configure-logging.html#log-deduplication for more options.)[0m
[36m(ClientAppActor pid=6779)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=6779)[0m 09/16/2026 14:24:18:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6779)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=6779)[0m   warnings.warn(
[36m(ClientAppActor pid=6776)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=6776)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=6779)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[36m(ClientAppActor pid=6779)[0m 09/16/2026 14:26:03:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[36m(ClientAppActor pid=6776)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=6776)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=6779)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=6779)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 14:27:46:INFO:aggregate_fit: received 3 results and 0 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:27:46:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:27:46:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=6779)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[36m(ClientAppActor pid=6779)[0m 09/16/2026 14:27:46:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[36m(ClientAppActor pid=6779)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=6779)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=6776)[0m 
[36m(ClientAppActor pid=6776)[0m         
[36m(ClientAppActor pid=6776)[0m 
[36m(ClientAppActor pid=6776)[0m         
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[36m(ClientAppActor pid=6779)[0m 
[36m(ClientAppActor pid=6779)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:27:48:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:27:48:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:27:48:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:27:48:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 219.15s
09/16/2026 14:27:48:INFO:Run finished 1 round(s) in 219.15s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:27:48:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.566422195689192
09/16/2026 14:27:48:INFO:		round 1: 0.566422195689192
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:27:48:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.262815239302163)], 'val_iou': [(1, 0.1701278751046912)]}
09/16/2026 14:27:48:INFO:	{'val_dice': [(1, 0.262815239302163)], 'val_iou': [(1, 0.1701278751046912)]}
[92mINFO [0m:      
09/16/2026 14:27:48:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:27:49:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:27:49:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=6779)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=6779)[0m 09/16/2026 14:27:47:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=6779)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=6779)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
2026-09-16 14:27:54,824	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8800996147.0, 'memory': 17601992295.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
09/16/2026 14:27:59:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8800996147.0, 'memory': 17601992295.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:27:59:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:27:59:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:27:59:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:27:59:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:27:59:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:27:59:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:27:59:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:27:59:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:27:59:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:27:59:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=7156)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7156)[0m 
[36m(ClientAppActor pid=7156)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=7156)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=7156)[0m         
[36m(ClientAppActor pid=7156)[0m 09/16/2026 14:28:08:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7156)[0m 
[36m(ClientAppActor pid=7156)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=7156)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=7156)[0m         
[36m(ClientAppActor pid=7155)[0m 
[36m(ClientAppActor pid=7155)[0m         
[36m(ClientAppActor pid=7155)[0m 
[36m(ClientAppActor pid=7155)[0m         
[36m(ClientAppActor pid=7156)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=7156)[0m   warnings.warn(
[36m(ClientAppActor pid=7155)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=7155)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=7156)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=7156)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=7155)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7155)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7155)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7155)[0m 09/16/2026 14:28:08:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7155)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=7155)[0m   warnings.warn(
[36m(ClientAppActor pid=7156)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=7156)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=7156)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7156)[0m 
[36m(ClientAppActor pid=7156)[0m         
[36m(ClientAppActor pid=7156)[0m 09/16/2026 14:29:51:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7156)[0m 
[36m(ClientAppActor pid=7156)[0m         
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 14:31:35:INFO:aggregate_fit: received 3 results and 0 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:31:35:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:31:35:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=7155)[0m 
[36m(ClientAppActor pid=7155)[0m         
[36m(ClientAppActor pid=7155)[0m 
[36m(ClientAppActor pid=7155)[0m         
[36m(ClientAppActor pid=7155)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=7155)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=7155)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7155)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7155)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7155)[0m 09/16/2026 14:31:35:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7156)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7156)[0m 
[36m(ClientAppActor pid=7156)[0m         
[36m(ClientAppActor pid=7156)[0m 09/16/2026 14:31:35:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7156)[0m 
[36m(ClientAppActor pid=7156)[0m         
[36m(ClientAppActor pid=7155)[0m 
[36m(ClientAppActor pid=7155)[0m         
[36m(ClientAppActor pid=7155)[0m 
[36m(ClientAppActor pid=7155)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:31:37:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:31:37:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:31:37:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:31:37:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 218.09s
09/16/2026 14:31:37:INFO:Run finished 1 round(s) in 218.09s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:31:37:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.6264167073860909
09/16/2026 14:31:37:INFO:		round 1: 0.6264167073860909
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:31:37:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.13831712489278572)], 'val_iou': [(1, 0.08742863689956157)]}
09/16/2026 14:31:37:INFO:	{'val_dice': [(1, 0.13831712489278572)], 'val_iou': [(1, 0.08742863689956157)]}
[92mINFO [0m:      
09/16/2026 14:31:37:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:31:38:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:31:38:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=7155)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7155)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7155)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7155)[0m 09/16/2026 14:31:36:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
2026-09-16 14:31:42,772	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17505558528.0, 'object_store_memory': 8752779264.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
09/16/2026 14:31:48:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17505558528.0, 'object_store_memory': 8752779264.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:31:48:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:31:48:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:31:48:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:31:48:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:31:48:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:31:48:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:31:48:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:31:48:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:31:48:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:31:48:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=7530)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7530)[0m 
[36m(ClientAppActor pid=7530)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=7530)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=7530)[0m         
[36m(ClientAppActor pid=7530)[0m 09/16/2026 14:31:56:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7530)[0m 
[36m(ClientAppActor pid=7530)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=7530)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=7530)[0m         
[36m(ClientAppActor pid=7529)[0m 
[36m(ClientAppActor pid=7529)[0m         
[36m(ClientAppActor pid=7529)[0m 
[36m(ClientAppActor pid=7529)[0m         
[36m(ClientAppActor pid=7530)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=7530)[0m   warnings.warn(
[36m(ClientAppActor pid=7530)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=7530)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=7530)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=7530)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=7529)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7529)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7529)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7529)[0m 09/16/2026 14:31:56:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7529)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=7529)[0m   warnings.warn(
[36m(ClientAppActor pid=7529)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=7529)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=7530)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7530)[0m 
[36m(ClientAppActor pid=7530)[0m         
[36m(ClientAppActor pid=7530)[0m 09/16/2026 14:33:46:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7530)[0m 
[36m(ClientAppActor pid=7530)[0m         
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 14:35:35:INFO:aggregate_fit: received 3 results and 0 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:35:35:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:35:35:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=7530)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7530)[0m 
[36m(ClientAppActor pid=7530)[0m         
[36m(ClientAppActor pid=7530)[0m 09/16/2026 14:35:35:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7530)[0m 
[36m(ClientAppActor pid=7530)[0m         
[36m(ClientAppActor pid=7529)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=7529)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=7530)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7530)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7529)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7529)[0m 
[36m(ClientAppActor pid=7529)[0m         
[36m(ClientAppActor pid=7529)[0m 09/16/2026 14:35:35:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7529)[0m 
[36m(ClientAppActor pid=7529)[0m         
[36m(ClientAppActor pid=7529)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7529)[0m 
[36m(ClientAppActor pid=7529)[0m         
[36m(ClientAppActor pid=7529)[0m 09/16/2026 14:35:37:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7529)[0m 
[36m(ClientAppActor pid=7529)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:35:37:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:35:37:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:35:37:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:35:37:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 229.77s
09/16/2026 14:35:37:INFO:Run finished 1 round(s) in 229.77s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:35:37:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.6578265390349823
09/16/2026 14:35:37:INFO:		round 1: 0.6578265390349823
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:35:37:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.10753596625064761)], 'val_iou': [(1, 0.06678650977759107)]}
09/16/2026 14:35:37:INFO:	{'val_dice': [(1, 0.10753596625064761)], 'val_iou': [(1, 0.06678650977759107)]}
[92mINFO [0m:      
09/16/2026 14:35:37:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:35:38:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:35:38:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=7529)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7529)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
2026-09-16 14:35:43,098	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17442702951.0, 'object_store_memory': 8721351475.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
09/16/2026 14:35:48:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17442702951.0, 'object_store_memory': 8721351475.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:35:48:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:35:48:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:35:48:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:35:48:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:35:48:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:35:48:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:35:48:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:35:48:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:35:48:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:35:48:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=7898)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7898)[0m 
[36m(ClientAppActor pid=7898)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=7898)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=7898)[0m         
[36m(ClientAppActor pid=7898)[0m 09/16/2026 14:35:56:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7898)[0m 
[36m(ClientAppActor pid=7898)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=7898)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=7898)[0m         
[36m(ClientAppActor pid=7898)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=7898)[0m   warnings.warn(
[36m(ClientAppActor pid=7899)[0m 
[36m(ClientAppActor pid=7899)[0m         
[36m(ClientAppActor pid=7899)[0m 
[36m(ClientAppActor pid=7899)[0m         
[36m(ClientAppActor pid=7898)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=7898)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=7899)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=7899)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=7899)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7899)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7899)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7899)[0m 09/16/2026 14:35:57:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7899)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=7899)[0m   warnings.warn(
[36m(ClientAppActor pid=7899)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=7899)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=7899)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7899)[0m 
[36m(ClientAppActor pid=7899)[0m         
[36m(ClientAppActor pid=7899)[0m 09/16/2026 14:37:47:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7899)[0m 
[36m(ClientAppActor pid=7899)[0m         
[36m(ClientAppActor pid=7898)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=7898)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=7899)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7899)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 14:39:35:INFO:aggregate_fit: received 3 results and 0 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:39:35:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:39:35:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=7899)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7899)[0m 
[36m(ClientAppActor pid=7899)[0m         
[36m(ClientAppActor pid=7899)[0m 09/16/2026 14:39:35:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=7899)[0m 
[36m(ClientAppActor pid=7899)[0m         
[36m(ClientAppActor pid=7899)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7899)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7898)[0m 
[36m(ClientAppActor pid=7898)[0m         
[36m(ClientAppActor pid=7898)[0m 
[36m(ClientAppActor pid=7898)[0m         
[36m(ClientAppActor pid=7898)[0m 
[36m(ClientAppActor pid=7898)[0m         
[36m(ClientAppActor pid=7898)[0m 
[36m(ClientAppActor pid=7898)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:39:37:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:39:37:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:39:37:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:39:37:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 229.23s
09/16/2026 14:39:37:INFO:Run finished 1 round(s) in 229.23s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:39:37:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.5662072205427781
09/16/2026 14:39:37:INFO:		round 1: 0.5662072205427781
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:39:37:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.27091134497262903)], 'val_iou': [(1, 0.1767162809383522)]}
09/16/2026 14:39:37:INFO:	{'val_dice': [(1, 0.27091134497262903)], 'val_iou': [(1, 0.1767162809383522)]}
[92mINFO [0m:      
09/16/2026 14:39:37:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:39:38:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:39:38:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=7898)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7898)[0m 09/16/2026 14:39:36:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=7898)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=7898)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
2026-09-16 14:39:42,818	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8705170636.0, 'memory': 17410341275.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
09/16/2026 14:39:48:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8705170636.0, 'memory': 17410341275.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:39:48:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:39:48:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:39:48:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:39:48:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:39:48:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:39:48:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:39:48:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:39:48:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:39:48:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:39:48:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=8285)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8285)[0m 
[36m(ClientAppActor pid=8285)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=8285)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=8285)[0m         
[36m(ClientAppActor pid=8285)[0m 09/16/2026 14:39:56:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8285)[0m 
[36m(ClientAppActor pid=8285)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=8285)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=8285)[0m         
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m         
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m         
[36m(ClientAppActor pid=8285)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=8285)[0m   warnings.warn(
[36m(ClientAppActor pid=8284)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=8284)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[91mERROR [0m:     Traceback (most recent call last):
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_client_proxy.py", line 94, in _submit_job
    out_mssg, updated_context = self.actor_pool.get_client_result(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 398, in get_client_result
    return self._fetch_future_result(cid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 279, in _fetch_future_result
    res_cid, out_mssg, updated_context = ray.get(
                                         ^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/auto_init_hook.py", line 21, in auto_init_wrapper
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/client_mode_hook.py", line 103, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 2639, in get
    values, debugger_breakpoint = worker.get_objects(object_refs, timeout=timeout)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 864, in get_objects
    raise value.as_instanceof_cause()
ray.exceptions.RayTaskError(ClientAppException): [36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 106, in fit
    loss.backward()
  File "/usr/local/lib/python3.12/dist-packages/torch/_tensor.py", line 626, in backward
    torch.autograd.backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/__init__.py", line 347, in backward
    _engine_run_backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/graph.py", line 823, in _engine_run_backward
    return Variable._execution_engine.run_backward(  # Calls into the C++ engine to run the backward pass
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 98, in __call__
    return self.hook(module, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/grad_sample_module.py", line 337, in capture_backprops_hook
    grad_samples = grad_sampler_fn(module, activations, backprops)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/conv.py", line 55, in compute_conv_grad_sample
    activations = unfold2d(
                  ^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/utils/tensor_utils.py", line 172, in unfold2d
    return out.reshape(input.size(0), -1, H_effective * W_effective)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

09/16/2026 14:41:45:ERROR:Traceback (most recent call last):
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_client_proxy.py", line 94, in _submit_job
    out_mssg, updated_context = self.actor_pool.get_client_result(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 398, in get_client_result
    return self._fetch_future_result(cid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 279, in _fetch_future_result
    res_cid, out_mssg, updated_context = ray.get(
                                         ^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/auto_init_hook.py", line 21, in auto_init_wrapper
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/client_mode_hook.py", line 103, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 2639, in get
    values, debugger_breakpoint = worker.get_objects(object_refs, timeout=timeout)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 864, in get_objects
    raise value.as_instanceof_cause()
ray.exceptions.RayTaskError(ClientAppException): [36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 106, in fit
    loss.backward()
  File "/usr/local/lib/python3.12/dist-packages/torch/_tensor.py", line 626, in backward
    torch.autograd.backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/__init__.py", line 347, in backward
    _engine_run_backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/graph.py", line 823, in _engine_run_backward
    return Variable._execution_engine.run_backward(  # Calls into the C++ engine to run the backward pass
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 98, in __call__
    return self.hook(module, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/grad_sample_module.py", line 337, in capture_backprops_hook
    grad_samples = grad_sampler_fn(module, activations, backprops)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/conv.py", line 55, in compute_conv_grad_sample
    activations = unfold2d(
                  ^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/utils/tensor_utils.py", line 172, in unfold2d
    return out.reshape(input.size(0), -1, H_effective * W_effective)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

[91mERROR [0m:     [36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 106, in fit
    loss.backward()
  File "/usr/local/lib/python3.12/dist-packages/torch/_tensor.py", line 626, in backward
    torch.autograd.backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/__init__.py", line 347, in backward
    _engine_run_backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/graph.py", line 823, in _engine_run_backward
    return Variable._execution_engine.run_backward(  # Calls into the C++ engine to run the backward pass
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 98, in __call__
    return self.hook(module, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/grad_sample_module.py", line 337, in capture_backprops_hook
    grad_samples = grad_sampler_fn(module, activations, backprops)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/conv.py", line 55, in compute_conv_grad_sample
    activations = unfold2d(
                  ^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/utils/tensor_utils.py", line 172, in unfold2d
    return out.reshape(input.size(0), -1, H_effective * W_effective)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
09/16/2026 14:41:45:ERROR:[36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 106, in fit
    loss.backward()
  File "/usr/local/lib/python3.12/dist-packages/torch/_tensor.py", line 626, in backward
    torch.autograd.backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/__init__.py", line 347, in backward
    _engine_run_backward(
  File "/usr/local/lib/python3.12/dist-packages/torch/autograd/graph.py", line 823, in _engine_run_backward
    return Variable._execution_engine.run_backward(  # Calls into the C++ engine to run the backward pass
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 98, in __call__
    return self.hook(module, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/grad_sample_module.py", line 337, in capture_backprops_hook
    grad_samples = grad_sampler_fn(module, activations, backprops)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/grad_sample/conv.py", line 55, in compute_conv_grad_sample
    activations = unfold2d(
                  ^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/utils/tensor_utils.py", line 172, in unfold2d
    return out.reshape(input.size(0), -1, H_effective * W_effective)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=8284, ip=172.19.2.2, actor_id=fb999fbb2df1f91d2638f4e101000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7a647609a030>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: CUDA out of memory. Tried to allocate 4.22 GiB. GPU 0 has a total capacity of 14.56 GiB of which 3.51 GiB is free. Process 58 has 2.98 GiB memory in use. Process 6490 has 148.00 MiB memory in use. Including non-PyTorch memory, this process has 7.92 GiB memory in use. Of the allocated memory 4.78 GiB is allocated by PyTorch, and 3.00 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m         
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m         
[36m(ClientAppActor pid=8284)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8284)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=8284)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=8284)[0m 09/16/2026 14:41:45:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8284)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=8284)[0m   warnings.warn(
[36m(ClientAppActor pid=8285)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=8285)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=8285)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=8285)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=8284)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=8284)[0m   z = np.log((np.exp(t) + q - 1) / q)
[92mINFO [0m:      aggregate_fit: received 2 results and 1 failures
09/16/2026 14:43:31:INFO:aggregate_fit: received 2 results and 1 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:43:31:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:43:31:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=8284)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=8284)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=8284)[0m         
[36m(ClientAppActor pid=8284)[0m 09/16/2026 14:43:31:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=8284)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=8284)[0m         
[36m(ClientAppActor pid=8285)[0m 
[36m(ClientAppActor pid=8285)[0m         
[36m(ClientAppActor pid=8285)[0m 
[36m(ClientAppActor pid=8285)[0m         
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m         
[36m(ClientAppActor pid=8284)[0m 
[36m(ClientAppActor pid=8284)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:43:33:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:43:33:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:43:33:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:43:33:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 225.47s
09/16/2026 14:43:33:INFO:Run finished 1 round(s) in 225.47s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:43:33:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.6411339993615752
09/16/2026 14:43:33:INFO:		round 1: 0.6411339993615752
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:43:33:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.06749104071213323)], 'val_iou': [(1, 0.04112862577195426)]}
09/16/2026 14:43:33:INFO:	{'val_dice': [(1, 0.06749104071213323)], 'val_iou': [(1, 0.04112862577195426)]}
[92mINFO [0m:      
09/16/2026 14:43:33:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:43:34:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:43:34:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=8284)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8284)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=8284)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=8284)[0m 09/16/2026 14:43:32:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
2026-09-16 14:43:39,020	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8696446156.0, 'memory': 17392892315.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
09/16/2026 14:43:44:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8696446156.0, 'memory': 17392892315.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:43:44:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:43:44:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:43:44:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:43:44:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:43:44:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:43:44:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:43:44:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:43:44:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:43:44:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:43:44:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=8664)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=8664)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=8664)[0m         
[36m(ClientAppActor pid=8664)[0m 09/16/2026 14:43:52:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=8664)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=8664)[0m         
[36m(ClientAppActor pid=8663)[0m 
[36m(ClientAppActor pid=8663)[0m         
[36m(ClientAppActor pid=8663)[0m 
[36m(ClientAppActor pid=8663)[0m         
[36m(ClientAppActor pid=8664)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=8664)[0m   warnings.warn(
[36m(ClientAppActor pid=8664)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=8664)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=8664)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=8664)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=8663)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8663)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8663)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8663)[0m 09/16/2026 14:43:52:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8663)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=8663)[0m   warnings.warn(
[36m(ClientAppActor pid=8663)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=8663)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=8664)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m         
[36m(ClientAppActor pid=8664)[0m 09/16/2026 14:45:39:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m         
[36m(ClientAppActor pid=8663)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=8663)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=8664)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8664)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 14:47:24:INFO:aggregate_fit: received 3 results and 0 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:47:24:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:47:24:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=8664)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m         
[36m(ClientAppActor pid=8664)[0m 09/16/2026 14:47:25:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m         
[36m(ClientAppActor pid=8664)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8664)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8663)[0m 
[36m(ClientAppActor pid=8663)[0m         
[36m(ClientAppActor pid=8663)[0m 
[36m(ClientAppActor pid=8663)[0m         
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m         
[36m(ClientAppActor pid=8664)[0m 
[36m(ClientAppActor pid=8664)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:47:27:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:47:27:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:47:27:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:47:27:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 222.81s
09/16/2026 14:47:27:INFO:Run finished 1 round(s) in 222.81s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:47:27:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.6579104527686406
09/16/2026 14:47:27:INFO:		round 1: 0.6579104527686406
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:47:27:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.11754566964883251)], 'val_iou': [(1, 0.07318252577148016)]}
09/16/2026 14:47:27:INFO:	{'val_dice': [(1, 0.11754566964883251)], 'val_iou': [(1, 0.07318252577148016)]}
[92mINFO [0m:      
09/16/2026 14:47:27:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:47:27:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:47:27:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=8664)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8664)[0m 09/16/2026 14:47:25:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=8664)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=8664)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
2026-09-16 14:47:32,336	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8687775744.0, 'memory': 17375551488.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
09/16/2026 14:47:37:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8687775744.0, 'memory': 17375551488.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:47:37:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:47:37:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:47:37:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:47:37:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:47:37:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:47:37:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:47:37:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:47:37:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:47:37:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:47:37:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=9030)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9030)[0m 
[36m(ClientAppActor pid=9030)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=9030)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=9030)[0m         
[36m(ClientAppActor pid=9030)[0m 09/16/2026 14:47:45:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9030)[0m 
[36m(ClientAppActor pid=9030)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=9030)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=9030)[0m         
[36m(ClientAppActor pid=9031)[0m 
[36m(ClientAppActor pid=9031)[0m         
[36m(ClientAppActor pid=9031)[0m 
[36m(ClientAppActor pid=9031)[0m         
[36m(ClientAppActor pid=9030)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=9030)[0m   warnings.warn(
[36m(ClientAppActor pid=9031)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=9031)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=9031)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=9031)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=9031)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9031)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9031)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9031)[0m 09/16/2026 14:47:45:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9031)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=9031)[0m   warnings.warn(
[36m(ClientAppActor pid=9030)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=9030)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=9031)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9031)[0m 
[36m(ClientAppActor pid=9031)[0m         
[36m(ClientAppActor pid=9031)[0m 09/16/2026 14:49:32:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9031)[0m 
[36m(ClientAppActor pid=9031)[0m         
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 14:51:22:INFO:aggregate_fit: received 3 results and 0 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:51:22:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:51:22:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=9031)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9031)[0m 
[36m(ClientAppActor pid=9031)[0m         
[36m(ClientAppActor pid=9031)[0m 09/16/2026 14:51:22:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9031)[0m 
[36m(ClientAppActor pid=9031)[0m         
[36m(ClientAppActor pid=9030)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=9030)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=9031)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9031)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9030)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9030)[0m 
[36m(ClientAppActor pid=9030)[0m         
[36m(ClientAppActor pid=9030)[0m 09/16/2026 14:51:22:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9030)[0m 
[36m(ClientAppActor pid=9030)[0m         
[36m(ClientAppActor pid=9030)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9030)[0m 
[36m(ClientAppActor pid=9030)[0m         
[36m(ClientAppActor pid=9030)[0m 09/16/2026 14:51:23:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9030)[0m 
[36m(ClientAppActor pid=9030)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:51:24:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:51:24:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:51:24:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:51:24:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 227.07s
09/16/2026 14:51:24:INFO:Run finished 1 round(s) in 227.07s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:51:24:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.5702865362167359
09/16/2026 14:51:24:INFO:		round 1: 0.5702865362167359
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:51:24:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.22212262061035748)], 'val_iou': [(1, 0.14175709131562594)]}
09/16/2026 14:51:24:INFO:	{'val_dice': [(1, 0.22212262061035748)], 'val_iou': [(1, 0.14175709131562594)]}
[92mINFO [0m:      
09/16/2026 14:51:24:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:51:24:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:51:24:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=9030)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9030)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
2026-09-16 14:51:29,762	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17374897767.0, 'object_store_memory': 8687448883.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
09/16/2026 14:51:35:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17374897767.0, 'object_store_memory': 8687448883.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:51:35:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:51:35:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:51:35:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:51:35:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:51:35:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:51:35:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:51:35:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:51:35:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:51:35:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:51:35:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=9424)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9424)[0m 
[36m(ClientAppActor pid=9424)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=9424)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=9424)[0m         
[36m(ClientAppActor pid=9424)[0m 09/16/2026 14:51:44:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9424)[0m 
[36m(ClientAppActor pid=9424)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=9424)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=9424)[0m         
[36m(ClientAppActor pid=9423)[0m 
[36m(ClientAppActor pid=9423)[0m         
[36m(ClientAppActor pid=9423)[0m 
[36m(ClientAppActor pid=9423)[0m         
[36m(ClientAppActor pid=9424)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=9424)[0m   warnings.warn(
[36m(ClientAppActor pid=9423)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=9423)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=9423)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=9423)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=9423)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9423)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9423)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9423)[0m 09/16/2026 14:51:44:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9423)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=9423)[0m   warnings.warn(
[36m(ClientAppActor pid=9424)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=9424)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=9423)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9423)[0m 
[36m(ClientAppActor pid=9423)[0m         
[36m(ClientAppActor pid=9423)[0m 09/16/2026 14:53:29:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9423)[0m 
[36m(ClientAppActor pid=9423)[0m         
[91mERROR [0m:     Traceback (most recent call last):
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_client_proxy.py", line 94, in _submit_job
    out_mssg, updated_context = self.actor_pool.get_client_result(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 398, in get_client_result
    return self._fetch_future_result(cid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 279, in _fetch_future_result
    res_cid, out_mssg, updated_context = ray.get(
                                         ^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/auto_init_hook.py", line 21, in auto_init_wrapper
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/client_mode_hook.py", line 103, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 2639, in get
    values, debugger_breakpoint = worker.get_objects(object_refs, timeout=timeout)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 864, in get_objects
    raise value.as_instanceof_cause()
ray.exceptions.RayTaskError(ClientAppException): [36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 96, in fit
    for images, masks, _ in self.trainloader:
                            ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 708, in __next__
    data = self._next_data()
           ^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 764, in _next_data
    data = self._dataset_fetcher.fetch(index)  # may raise StopIteration
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/_utils/fetch.py", line 55, in fetch
    return self.collate_fn(data)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/data_loader.py", line 56, in collate
    torch.zeros(shape, dtype=dtype)
TypeError: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)


The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)

09/16/2026 14:55:00:ERROR:Traceback (most recent call last):
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_client_proxy.py", line 94, in _submit_job
    out_mssg, updated_context = self.actor_pool.get_client_result(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 398, in get_client_result
    return self._fetch_future_result(cid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 279, in _fetch_future_result
    res_cid, out_mssg, updated_context = ray.get(
                                         ^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/auto_init_hook.py", line 21, in auto_init_wrapper
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/client_mode_hook.py", line 103, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 2639, in get
    values, debugger_breakpoint = worker.get_objects(object_refs, timeout=timeout)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/ray/_private/worker.py", line 864, in get_objects
    raise value.as_instanceof_cause()
ray.exceptions.RayTaskError(ClientAppException): [36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 96, in fit
    for images, masks, _ in self.trainloader:
                            ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 708, in __next__
    data = self._next_data()
           ^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 764, in _next_data
    data = self._dataset_fetcher.fetch(index)  # may raise StopIteration
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/_utils/fetch.py", line 55, in fetch
    return self.collate_fn(data)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/data_loader.py", line 56, in collate
    torch.zeros(shape, dtype=dtype)
TypeError: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)


The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)

[91mERROR [0m:     [36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 96, in fit
    for images, masks, _ in self.trainloader:
                            ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 708, in __next__
    data = self._next_data()
           ^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 764, in _next_data
    data = self._dataset_fetcher.fetch(index)  # may raise StopIteration
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/_utils/fetch.py", line 55, in fetch
    return self.collate_fn(data)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/data_loader.py", line 56, in collate
    torch.zeros(shape, dtype=dtype)
TypeError: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)


The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
09/16/2026 14:55:00:ERROR:[36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 143, in __call__
    return self._call(message, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client_app.py", line 126, in ffn
    out_message = handle_legacy_message_from_msgtype(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/message_handler/message_handler.py", line 129, in handle_legacy_message_from_msgtype
    fit_res = maybe_call_fit(
              ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/client.py", line 255, in maybe_call_fit
    return client.fit(fit_ins)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/client/numpy_client.py", line 259, in _fit
    results = self.numpy_client.fit(parameters, ins.config)  # type: ignore
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/kaggle/working/SDFL/e4_dpsgd.py", line 96, in fit
    for images, masks, _ in self.trainloader:
                            ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 708, in __next__
    data = self._next_data()
           ^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/dataloader.py", line 764, in _next_data
    data = self._dataset_fetcher.fetch(index)  # may raise StopIteration
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/utils/data/_utils/fetch.py", line 55, in fetch
    return self.collate_fn(data)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/opacus/data_loader.py", line 56, in collate
    torch.zeros(shape, dtype=dtype)
TypeError: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)


The above exception was the direct cause of the following exception:

[36mray::ClientAppActor.run()[39m (pid=9423, ip=172.19.2.2, actor_id=87cdfef35043ba8849be843d01000000, repr=<flwr.simulation.ray_transport.ray_actor.ClientAppActor object at 0x7f443b1527e0>)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/flwr/simulation/ray_transport/ray_actor.py", line 63, in run
    raise ClientAppException(str(ex)) from ex
flwr.client.client_app.ClientAppException: 
Exception ClientAppException occurred. Message: zeros() received an invalid combination of arguments - got (tuple, dtype=type), but expected one of:
 * (tuple of ints size, *, tuple of names names, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
 * (tuple of ints size, *, Tensor out = None, torch.dtype dtype = None, torch.layout layout = None, torch.device device = None, bool pin_memory = False, bool requires_grad = False)
[92mINFO [0m:      aggregate_fit: received 2 results and 1 failures
09/16/2026 14:55:00:INFO:aggregate_fit: received 2 results and 1 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:55:00:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:55:00:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=9424)[0m 
[36m(ClientAppActor pid=9424)[0m         
[36m(ClientAppActor pid=9424)[0m 
[36m(ClientAppActor pid=9424)[0m         
[36m(ClientAppActor pid=9424)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=9424)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=9424)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9424)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9424)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9424)[0m 09/16/2026 14:55:00:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9423)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9423)[0m 
[36m(ClientAppActor pid=9423)[0m         
[36m(ClientAppActor pid=9423)[0m 09/16/2026 14:55:00:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9423)[0m 
[36m(ClientAppActor pid=9423)[0m         
[36m(ClientAppActor pid=9424)[0m 
[36m(ClientAppActor pid=9424)[0m         
[36m(ClientAppActor pid=9424)[0m 
[36m(ClientAppActor pid=9424)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:55:02:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:55:02:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:55:02:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:55:02:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 207.26s
09/16/2026 14:55:02:INFO:Run finished 1 round(s) in 207.26s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:55:02:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.6303167723914952
09/16/2026 14:55:02:INFO:		round 1: 0.6303167723914952
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:55:02:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.2946967094268613)], 'val_iou': [(1, 0.19161534870712502)]}
09/16/2026 14:55:02:INFO:	{'val_dice': [(1, 0.2946967094268613)], 'val_iou': [(1, 0.19161534870712502)]}
[92mINFO [0m:      
09/16/2026 14:55:02:INFO:
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 14:55:02:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 14:55:02:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
[36m(ClientAppActor pid=9424)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9424)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9424)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9424)[0m 09/16/2026 14:55:01:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
2026-09-16 14:55:08,619	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8687404646.0, 'memory': 17374809294.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
09/16/2026 14:55:13:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'object_store_memory': 8687404646.0, 'memory': 17374809294.0, 'GPU': 2.0, 'accelerator_type:T4': 1.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 14:55:13:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
09/16/2026 14:55:13:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 1, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
09/16/2026 14:55:13:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 2 actors
[92mINFO [0m:      [INIT]
09/16/2026 14:55:13:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 14:55:13:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 14:55:13:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 14:55:13:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 14:55:13:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 14:55:13:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 14:55:13:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=9796)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9796)[0m 
[36m(ClientAppActor pid=9796)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=9796)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=9796)[0m         
[36m(ClientAppActor pid=9796)[0m 09/16/2026 14:55:21:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9796)[0m 
[36m(ClientAppActor pid=9796)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=9796)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=9796)[0m         
[36m(ClientAppActor pid=9794)[0m 
[36m(ClientAppActor pid=9794)[0m         
[36m(ClientAppActor pid=9794)[0m 
[36m(ClientAppActor pid=9794)[0m         
[36m(ClientAppActor pid=9796)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=9796)[0m   warnings.warn(
[36m(ClientAppActor pid=9794)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=9794)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=9796)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=9796)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=9794)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9794)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9794)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9794)[0m 09/16/2026 14:55:21:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9794)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=9794)[0m   warnings.warn(
[36m(ClientAppActor pid=9796)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=9796)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=9796)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9796)[0m 
[36m(ClientAppActor pid=9796)[0m         
[36m(ClientAppActor pid=9796)[0m 09/16/2026 14:57:09:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9796)[0m 
[36m(ClientAppActor pid=9796)[0m         
[36m(ClientAppActor pid=9794)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=9794)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=9796)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9796)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 14:58:50:INFO:aggregate_fit: received 3 results and 0 failures
[93mWARNING [0m:   No fit_metrics_aggregation_fn provided
09/16/2026 14:58:50:WARNING:No fit_metrics_aggregation_fn provided
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 14:58:50:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=9796)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9796)[0m 
[36m(ClientAppActor pid=9796)[0m         
[36m(ClientAppActor pid=9796)[0m 09/16/2026 14:58:50:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=9796)[0m 
[36m(ClientAppActor pid=9796)[0m         
[36m(ClientAppActor pid=9796)[0m             This is a deprecated feature. It will be removed[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9796)[0m             entirely in future versions of Flower.[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9794)[0m 
[36m(ClientAppActor pid=9794)[0m         
[36m(ClientAppActor pid=9794)[0m 
[36m(ClientAppActor pid=9794)[0m         
[36m(ClientAppActor pid=9794)[0m 
[36m(ClientAppActor pid=9794)[0m         
[36m(ClientAppActor pid=9794)[0m 
[36m(ClientAppActor pid=9794)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 14:58:52:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 14:58:52:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 14:58:52:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 14:58:52:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 219.32s
09/16/2026 14:58:52:INFO:Run finished 1 round(s) in 219.32s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 14:58:52:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.6579915964487687
09/16/2026 14:58:52:INFO:		round 1: 0.6579915964487687
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 14:58:52:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.10482819908416098)], 'val_iou': [(1, 0.0650485293853811)]}
09/16/2026 14:58:52:INFO:	{'val_dice': [(1, 0.10482819908416098)], 'val_iou': [(1, 0.0650485293853811)]}
[92mINFO [0m:      
09/16/2026 14:58:52:INFO:
Sweep Results:
| C   | σ   | val_dice | val_iou | epsilon |
|-----|-----|----------|---------|---------|
| 0.5 | 0.5 | 0.2628 | 0.1701 | 12.6931 |
| 0.5 | 1.0 | 0.1383 | 0.0874 | 2.1410 |
| 0.5 | 1.5 | 0.1075 | 0.0668 | 0.9793 |
| 1.0 | 0.5 | 0.2709 | 0.1767 | 12.6931 |
| 1.0 | 1.0 | 0.0675 | 0.0411 | 2.1410 |
| 1.0 | 1.5 | 0.1175 | 0.0732 | 0.9793 |
| 2.0 | 0.5 | 0.2221 | 0.1418 | 12.6931 |
| 2.0 | 1.0 | 0.2947 | 0.1916 | 2.1410 |
| 2.0 | 1.5 | 0.1048 | 0.0650 | 0.9793 |
Best Configuration:
- C: 2.0
- σ: 1.0
- val_dice: 0.2947
- val_iou: 0.1916
- epsilon: 2.1410
- delta: 1e-5
[36m(ClientAppActor pid=9794)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9794)[0m 09/16/2026 14:58:51:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`[32m [repeated 2x across cluster][0m
[36m(ClientAppActor pid=9794)[0m             This is a deprecated feature. It will be removed[32m [repeated 4x across cluster][0m
[36m(ClientAppActor pid=9794)[0m             entirely in future versions of Flower.[32m [repeated 4x across cluster][0m
```

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`. Checkpoint: checkpoints/e4_best.pth
