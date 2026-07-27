#### ABC Tyres – eBilling Pipeline (v1.0)
Automated Invoice Delivery Pipeline Using Azure Synapse, ADLS Gen2, Azure SQL, Python & SFTP

📌 Overview
The ABC Tyres eBilling Pipeline is a cloud‑native, automated document delivery system that ingests invoice PDFs from SFTP, enriches them with metadata from Azure Synapse, applies customer delivery rules stored in Azure SQL Database, classifies and renames the documents, and delivers final ZIP bundles back to SFTP for downstream distribution.

This solution modernizes legacy delivery processes using Azure PaaS services, ensuring scalability, reliability, and operational transparency.

🎯 Objectives
Automate ingestion of invoice PDFs from SFTP

Store raw documents securely in ADLS Gen2

Retrieve invoice metadata from Synapse serverless SQL

Retrieve customer delivery preferences from Azure SQL Database

Apply business rules (Key / Sub / Both / Ignore / None)

Rename PDFs using ABC naming convention

Classify into passed, ignored, and failed buckets

Zip passed PDFs and deliver back to SFTP

Provide clear logging, monitoring, and CI/CD integration

🏗️ Architecture
Core Components
Component	Purpose
Azure Data Lake Storage Gen2	Stores raw, processed, classified, and zipped PDFs
Azure Synapse Serverless SQL	Reads ORDER_HDR & CUSTOMER parquet metadata
Azure SQL Database	Stores DDP (customer control matrix)
Python Pipeline	Ingestion, renaming, classification, zipping, SFTP delivery
SFTP (Inbound/Outbound)	Source of raw PDFs and destination for ZIP bundles
Azure Data Factory (ADF)	Orchestration, scheduling, CI/CD integration
GitHub	Source control for all pipeline code


📁 Project Structure
Code
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
🔄 End‑to‑End Workflow
1️⃣ Ingestion (SFTP → ADLS Gen2 /raw)
Connect to SFTP

Download all .pdf files

Validate file size > 0

Upload to ADLS Gen2:

Code
synapse/ebilling/invoice/raw/
Delete files from SFTP

Log ingestion results

2️⃣ Metadata Load (Synapse + SQL)
ORDER_HDR.parquet → Synapse external table

CUSTOMER.parquet → Synapse external table

DDP table → Azure SQL Database

Metadata determines BillTo/SoldTo accounts and delivery rules.

3️⃣ Processing (Rename + Classify)
Business Rules
Customer Control	Meaning	Output
Key	BillTo receives invoice	ABCINV_invoice_billto.pdf
Sub	SoldTo receives invoice	ABCINV_invoice_soldto.pdf
Both	Both receive invoice	Two PDFs generated
Ignore	Do not deliver	Goes to ignored folder
None	No rule found	Goes to failed folder


Classification Output
Code
passed/YYYY-MM-DD/
ignored/YYYY-MM-DD/
failed/YYYY-MM-DD/
4️⃣ Delivery (ZIP + SFTP)
Zip all passed PDFs

Naming convention:

Code
ABCINV_YYYYMMDD_HHMMSS_count.zip
Upload ZIP to SFTP /incoming/invoices

Log delivery results

5️⃣ Orchestration (ADF)
ADF pipeline triggers:

Ingestion

Processing

Delivery

Includes logging + monitoring.

📊 Data Model
ORDER_HDR
Column	Description
EXTERNAL_REF_ID	Invoice number
CUSTOMER_ID	BillTo customer
ALT2_CUSTOMER_ID	SoldTo customer


CUSTOMER
Column	Description
CUSTOMER_ID	Internal customer ID
ALT2_CUSTOMER_ID	Secondary customer ID
EXTERNAL_CUST_ID	External account number


DDP (Azure SQL)
Column	Description
account_number	External account number
doc_type	invoice / confirmation
customer_control	Key / Sub / Both
delivery_mode	email / print / ignore / NULL


🔐 Security
Secrets stored in Azure Key Vault

ADLS Gen2 secured with RBAC + ACLs

Synapse workspace uses managed identity

SQL Database protected with firewall + AAD authentication

SFTP credentials rotated regularly

📈 Monitoring & Logging
Python logs → logs/pipeline.log

ADF pipeline run history

Synapse SQL query logs

Storage access logs

SFTP transfer logs

🚀 CI/CD (GitHub → ADF)
GitHub Actions used for deployment

ADF pipeline JSON stored in /adf/pipeline.json

Automatic deployment on push to main

Versioning of Python scripts and metadata

🧪 Testing
Unit tests located in:

Code
tests/test_processing.py
Tests cover:

Metadata lookup

DDP rule application

Renaming logic

Classification logic

📬 Contact
Engineer: Taiwo
Project: ABC Tyres – eBilling Automation
Version: 1.0
Environment: DEV / QA / PROD
