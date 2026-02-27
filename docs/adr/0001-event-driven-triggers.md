# ADR 0001: Event-Driven Triggers vs Scheduled Pipelines

## Status
Accepted

## Context
The continuous training pipeline requires a mechanism to initiate retraining. Traditional MLOps architectures frequently rely on scheduled batch jobs (e.g., triggering a pipeline every night at midnight via Cloud Scheduler) to continuously train models on accumulated data. However, this approach can introduce latency if fresh data is highly volatile, or waste compute resources if no new data has arrived by the scheduled runtime.

## Decision
We decided to implement an **Event-Driven trigger mechanism** using Cloud Storage, Cloud Functions, and Pub/Sub.

1. **Storage Trigger:** New training data uploaded to a dedicated Cloud Storage bucket triggers a Cloud Function.
2. **Data Processing:** The function validates the payload (CSV data) and ingests it into BigQuery.
3. **Decoupled Job Submission:** Rather than triggering Vertex AI directly, the first Cloud Function publishes a message payload to a Pub/Sub topic containing the BigQuery URI and pipeline parameters.
4. **Pipeline Execution:** A secondary Cloud Function subscribed to the Pub/Sub topic consumes the payload and submits the precompiled `TabularDatasetCreateOp` and Custom Training Job onto Vertex AI.

## Consequences

**Positive:**
- **Zero-Waste Compute:** The pipeline only executes when fresh data is demonstrably available, optimizing Vertex AI resource utilization.
- **Real-Time Data Relevance:** Models can be retrained and pushed to testing/production immediately upon the availability of novel data points, eliminating the scheduler lag.
- **Extensibility:** The Pub/Sub layer decouples the ingestion event from the training trigger. Future consumers (e.g., a Slack notification bot or an auditing ledger) can subscribe to the same topic without modifying the trigger logic.

**Negative/Trade-offs:**
- **Increased Complexity:** Introduces multiple moving parts (two Cloud Functions, a Pub/Sub Topic, and GCS event triggers) compared to a singular Cloud Scheduler cron job.
- **Permissions Surface Area:** Requires managing granular IAM bindings for Eventarc, Storage, and Pub/Sub publishers.

## Compliance & Security Impact
This pattern requires careful scoped IAM management to ensure Cloud Storage events can securely traverse the Eventarc/PubSub boundary without elevating the runner's privileges beyond specific pipeline execution roles.
