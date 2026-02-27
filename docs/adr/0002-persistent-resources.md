# ADR 0002: Vertex AI Persistent Resources for Training 

## Status
Accepted

## Context
In continuous training architectures, models are frequently retrained upon the arrival of new data. Using standard, ephemeral Vertex AI Custom Training Jobs requires provisioning new compute clusters (VMs, network interfaces, container pulls) for *every* execution. For smaller, fast-iterating models or high-frequency triggers, the cluster initialization time can constitute a significant portion of the total pipeline duration, leading to delayed deployments and inefficient scaling.

## Decision
We decided to provision and leverage **Vertex AI Persistent Resources** to host the Custom Training Job executions.

Rather than defining ephemeral `worker_pool_specs` that spin up and teardown nodes on demand, the project utilizes an overarching Terraform module (`terraform-modules/persistent_resource`) to maintain an active, dedicated worker pool of compute nodes (defaulting to `n1-standard-4`). The `CustomTrainingJobOp` in the pipeline is then configured with a generic `persistent_resource_id` parameter to route the training workload directly onto this pre-warmed cluster.

## Consequences

**Positive:**
- **Decreased Latency:** Pipeline start-up time is drastically reduced as the training containers can immediately schedule onto the active, running VM nodes without waiting for Google Cloud to provision underlying infrastructure.
- **Resource Predictability:** Provides a guaranteed allocation of compute capacity for mission-critical training tasks, immune to temporary zone-level capacity constraints for specific machine types.

**Negative/Trade-offs:**
- **Cost Accumulation:** Persistent resources bill continuously for the entire duration the cluster is active, regardless of whether a training job is actively utilizing it. This creates a baseline operational cost even during periods of zero data ingestion.
- **Lifecycle Management:** The resource lifecycle is decoupled from the pipeline execution. If the Terraform state is lost or the resource is manually deleted, pipeline triggers will fail until the resource is explicitly recreated via the `create_persistent_resource.sh` utility or Terraform.

## Performance Impact
This is a critical performance optimization intended for high-frequency continuous training loops, explicitly trading increased idle costs for minimized training latency.
