# coursework

Module 2 coursework. Most of this module is following along with the material in `02-workflow-orchestration/`.
The flows in this directory (`flows/`) are modifications of the example flows provided by the Module or made to answer homework questions.

- [06_gcp_kv.yml](flows/06_gcp_kv.yml) - A modification of the existing `06_gcp_kv.yml` which allows string inputs to the flow instead of using hardcoded string inputs to set GCP credentials into the Kestra Key-Value store
- [hw_q1.yml](flows/hw_q1.yml) - A flow which provides the answer to question 1 of the [homework](homework.md).
- [hw_subflow_taxi.yml](flows/hw_subflow_taxi.yml) - A flow made to ingest taxi data necessary for the [homework](homework.md) by running the `08_gcp_taxi.md` flow iteratively over a set of inputs determining which data to download and ingest into the database.