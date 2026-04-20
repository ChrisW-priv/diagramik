---
title: Use GCP as Cloud Provider
date: 2026-04-20
status: accepted
---

## Decision

Google Cloud Platform is the deployment target for all runtime infrastructure: Cloud Run (containerized API services), GCS (static frontend assets and diagram storage), Cloud SQL (PostgreSQL database), Secret Manager (runtime credentials), and a Global HTTPS Load Balancer with CDN.

## Rationale

Best performance profile for the expected workload. GCP's managed container platform (Cloud Run) handles autoscaling and cold starts well for API services with variable traffic. Strong tooling for ML-adjacent workloads aligns with the AI-driven diagram generation use case. Developer familiarity with GCP console and tooling reduces operational overhead and accelerates incident response.
