# Experiment E5 -- Secure Aggregation Integration (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Starting checkpoint** | checkpoints/e4_best.pth |
| **Rounds** | 1 |
| **Symmetric Encryption** | AES-GCM (256-bit key) |

## Full run output (captured this run)

```
[93mWARNING [0m:   DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
09/16/2026 15:03:58:WARNING:DEPRECATED FEATURE: flwr.simulation.start_simulation() is deprecated.
	Instead, use the `flwr run` CLI command to start a local simulation in your Flower app, as shown for example below:

		$ flwr new  # Create a new Flower app from a template

		$ flwr run  # Run the Flower app in Simulation Mode

	Using `start_simulation()` is deprecated.

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        
[92mINFO [0m:      Starting Flower simulation, config: num_rounds=1, no round_timeout
09/16/2026 15:03:58:INFO:Starting Flower simulation, config: num_rounds=1, no round_timeout
2026-09-16 15:04:01,864	INFO worker.py:1771 -- Started a local Ray instance.
[92mINFO [0m:      Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17747573147.0, 'object_store_memory': 8873786572.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
09/16/2026 15:04:07:INFO:Flower VCE: Ray initialized with resources: {'node:172.19.2.2': 1.0, 'node:__internal_head__': 1.0, 'CPU': 4.0, 'memory': 17747573147.0, 'object_store_memory': 8873786572.0, 'accelerator_type:T4': 1.0, 'GPU': 2.0}
[92mINFO [0m:      Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
09/16/2026 15:04:07:INFO:Optimize your simulation with Flower VCE: https://flower.ai/docs/framework/how-to-run-simulations.html
[92mINFO [0m:      Flower VCE: Resources for each Virtual Client: {'num_cpus': 4, 'num_gpus': 1.0}
09/16/2026 15:04:07:INFO:Flower VCE: Resources for each Virtual Client: {'num_cpus': 4, 'num_gpus': 1.0}
[92mINFO [0m:      Flower VCE: Creating VirtualClientEngineActorPool with 1 actors
09/16/2026 15:04:07:INFO:Flower VCE: Creating VirtualClientEngineActorPool with 1 actors
[92mINFO [0m:      [INIT]
09/16/2026 15:04:07:INFO:[INIT]
[92mINFO [0m:      Using initial global parameters provided by strategy
09/16/2026 15:04:07:INFO:Using initial global parameters provided by strategy
[92mINFO [0m:      Starting evaluation of initial global parameters
09/16/2026 15:04:07:INFO:Starting evaluation of initial global parameters
[92mINFO [0m:      Evaluation returned no results (`None`)
09/16/2026 15:04:07:INFO:Evaluation returned no results (`None`)
[92mINFO [0m:      
09/16/2026 15:04:07:INFO:
[92mINFO [0m:      [ROUND 1]
09/16/2026 15:04:07:INFO:[ROUND 1]
[92mINFO [0m:      configure_fit: strategy sampled 3 clients (out of 3)
09/16/2026 15:04:07:INFO:configure_fit: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=10935)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m 09/16/2026 15:04:15:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m /usr/local/lib/python3.12/dist-packages/opacus/privacy_engine.py:142: UserWarning: Secure RNG turned off. This is perfectly fine for experimentation as it allows for much faster training performance, but remember to turn it on and retrain one last time before production with ``secure_mode`` turned on.
[36m(ClientAppActor pid=10935)[0m   warnings.warn(
[36m(ClientAppActor pid=10935)[0m /usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py:1830: FutureWarning: Using a non-full backward hook when the forward contains multiple autograd Nodes is deprecated and will be removed in future versions. This hook will be missing some grad_input. Please use register_full_backward_hook to get the documented behavior.
[36m(ClientAppActor pid=10935)[0m   self._maybe_warn_non_full_backward_hook(args, result, grad_fn)
[36m(ClientAppActor pid=10935)[0m /usr/local/lib/python3.12/dist-packages/opacus/accountants/analysis/prv/prvs.py:50: RuntimeWarning: invalid value encountered in log
[36m(ClientAppActor pid=10935)[0m   z = np.log((np.exp(t) + q - 1) / q)
[36m(ClientAppActor pid=10935)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m 09/16/2026 15:05:51:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m 09/16/2026 15:07:20:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[92mINFO [0m:      aggregate_fit: received 3 results and 0 failures
09/16/2026 15:08:52:INFO:aggregate_fit: received 3 results and 0 failures
[92mINFO [0m:      configure_evaluate: strategy sampled 3 clients (out of 3)
09/16/2026 15:08:52:INFO:configure_evaluate: strategy sampled 3 clients (out of 3)
[36m(ClientAppActor pid=10935)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m 09/16/2026 15:08:52:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m 09/16/2026 15:08:53:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m [93mWARNING [0m:   DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[36m(ClientAppActor pid=10935)[0m 09/16/2026 15:08:54:WARNING:DEPRECATED FEATURE: `client_fn` now expects a signature `def client_fn(context: Context)`.The provided `client_fn` has signature: {'cid': <Parameter "cid: str">}. You can import the `Context` like this: `from flwr.common import Context`
[36m(ClientAppActor pid=10935)[0m 
[36m(ClientAppActor pid=10935)[0m             This is a deprecated feature. It will be removed
[36m(ClientAppActor pid=10935)[0m             entirely in future versions of Flower.
[36m(ClientAppActor pid=10935)[0m         
[92mINFO [0m:      aggregate_evaluate: received 3 results and 0 failures
09/16/2026 15:08:55:INFO:aggregate_evaluate: received 3 results and 0 failures
[93mWARNING [0m:   No evaluate_metrics_aggregation_fn provided
09/16/2026 15:08:55:WARNING:No evaluate_metrics_aggregation_fn provided
[92mINFO [0m:      
09/16/2026 15:08:55:INFO:
[92mINFO [0m:      [SUMMARY]
09/16/2026 15:08:55:INFO:[SUMMARY]
[92mINFO [0m:      Run finished 1 round(s) in 287.94s
09/16/2026 15:08:55:INFO:Run finished 1 round(s) in 287.94s
[92mINFO [0m:      	History (loss, distributed):
09/16/2026 15:08:55:INFO:	History (loss, distributed):
[92mINFO [0m:      		round 1: 0.5809211158058019
09/16/2026 15:08:55:INFO:		round 1: 0.5809211158058019
[92mINFO [0m:      	History (metrics, distributed, evaluate):
09/16/2026 15:08:55:INFO:	History (metrics, distributed, evaluate):
[92mINFO [0m:      	{'val_dice': [(1, 0.2576443311369535)], 'val_iou': [(1, 0.16557453468586633)]}
09/16/2026 15:08:55:INFO:	{'val_dice': [(1, 0.2576443311369535)], 'val_iou': [(1, 0.16557453468586633)]}
[92mINFO [0m:      
09/16/2026 15:08:55:INFO:
=== Running E5 Secure Aggregation Isolation Tests ===
Test 1: Single encrypt/decrypt passed.
Test 2: Encrypted aggregation correctness passed.
All isolation tests passed successfully!

=== Running E5 Secure Aggregation Simulation ===

Simulation Results:
- val_dice: 0.2576
- val_iou: 0.1656
- epsilon (privacy spending): 0.9793
Saved best E5 model checkpoint to checkpoints/e5_best.pth
```

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`. Checkpoint: checkpoints/e5_best.pth
