# ABC Tyres – eBilling Pipeline (v1.0)
Automated Invoice Delivery Pipeline Using Azure Synapse, ADLS Gen2, Azure SQL, Python & SFTP

---

## 📌 Overview
The ABC Tyres eBilling Pipeline is a cloud‑native, automated document delivery system that ingests invoice PDFs from SFTP, enriches them with metadata from Azure Synapse, applies customer delivery rules stored in Azure SQL Database, classifies and renames the documents, and delivers final ZIP bundles back to SFTP for downstream distribution.

This solution modernizes legacy delivery processes using Azure PaaS services, ensuring scalability, reliability, and operational transparency.

---

## 🎯 Objectives
- Automate ingestion of invoice PDFs from SFTP  
- Store raw documents securely in ADLS Gen2  
- Retrieve invoice metadata from Synapse serverless SQL  
- Retrieve customer delivery preferences from Azure SQL Database  
- Apply business rules (Key / Sub / Both / Ignore / None)  
- Rename PDFs using ABC naming convention  
- Classify into passed, ignored, and failed buckets  
- Zip passed PDFs and deliver back to SFTP  
- Provide clear logging, monitoring, and CI/CD integration  

---

## 🏗️ Architecture

### Core Components
| Component | Purpose |
|----------|---------|
| Azure Data Lake Storage Gen2 | Stores raw, processed, classified, and zipped PDFs |
| Azure Synapse Serverless SQL | Reads ORDER_HDR & CUSTOMER parquet metadata |
| Azure SQL Database | Stores DDP (customer control matrix) |
| Python Pipeline | Ingestion, renaming, classification, zipping, SFTP delivery |
| SFTP (Inbound/Outbound) | Source of raw PDFs and destination for ZIP bundles |
| Azure Data Factory (ADF) | Orchestration, scheduling, CI/CD integration |
| GitHub | Source control for all pipeline code |

---

## 📁 Project Structure

```text
ebilling_project/
│
├── ingestion/
│   └── sftp_ingest.py
│
├── processing/
│   └── rename_and_classify.py
│
├── delivery/
│   └── zip_and_send.py
│
├── metadata/
│   ├── ORDER_HDR.parquet
│   ├── CUSTOMER.parquet
│   └── ddp_schema.sql
│
├── config/
│   └── settings.json
│
├── logs/
│   └── pipeline.log
│
├── tests/
│   └── test_processing.py
│
├── adf/
│   └── pipeline.json
│
└── README.md
