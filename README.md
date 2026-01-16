# E-commerce Data Engineering Pipeline

This project implements a robust data engineering pipeline for an e-commerce platform, focusing on efficient data ingestion, processing, and orchestration. It's designed to handle various data formats, transform raw data into a clean, analytical-ready state, and manage complex workflows using modern data tools.

## ✨ Features

*   **Data Ingestion**: Seamlessly ingest raw e-commerce data (customers, orders, products, reviews, order items) from CSV files into an AWS S3 bucket.
*   **Data Processing**: Transform raw data into structured Parquet format, performing necessary cleaning, standardization, and enrichment for downstream analysis.
*   **Workflow Orchestration**: Utilize Prefect for defining, scheduling, and monitoring data pipelines, ensuring reliable and automated execution.
*   **Containerization**: Leverage Docker and Docker Compose to create isolated, reproducible, and scalable environments for the entire data pipeline.
*   **Testing**: Comprehensive unit tests ensure the reliability and correctness of data transformations and cloud interactions.

## 🛠️ Technologies Used

*   **Python**: Core programming language for data processing and orchestration logic.
*   **Pandas**: For efficient data manipulation and analysis.
*   **Prefect**: For building, observing, and reacting to data workflows.
*   **Docker**: For containerizing the application and its services.
*   **Docker Compose**: For defining and running multi-container Docker applications.
*   **AWS S3**: For scalable and secure object storage of raw and processed data.
*   **Pytest**: For writing and running unit tests.

## 🏗️ Architecture Overview

The pipeline follows a layered architecture:

1.  **Raw Data Storage**: Initial raw CSV files are stored locally in the [`data/raw`](data/raw/) directory.
2.  **S3 Ingestion**: The [`s3_uploader.py`](data-pipeline/src/data_ingestion/s3_uploader.py) script ingests these raw CSV files into a designated AWS S3 bucket.
3.  **Data Processing**: The [`data_processing.py`](data-pipeline/src/data_processing/data_processing.py) module reads the raw data (potentially from S3 or local storage for development), performs transformations, and stores the processed data in Parquet format in the [`data/`](data/) directory.
4.  **Orchestration**: Prefect flows defined in [`prefect_flows.py`](data-pipeline/src/orchestration/prefect_flows.py) orchestrate the entire process, including ingestion and processing steps, managing dependencies and retries.
5.  **Containerization**: All components are containerized using Docker, managed by [`docker-compose.yml`](data-pipeline/docker-compose.yml) for easy setup and deployment.

```
data/raw/
└── *.csv (Raw E-commerce Data)
        ↓ S3 Uploader (Python, AWS S3)
AWS S3 Bucket
        ↓ Data Processing (Python, Pandas)
data/
└── *.parquet (Processed Data)
        ↑ Prefect Flows (Python, Prefect)
```

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

*   [**Docker Desktop**](https://www.docker.com/products/docker-desktop) (includes Docker Engine and Docker Compose)
*   [**Python 3.8+**](https://www.python.org/downloads/)
*   [**uv**](https://github.com/astral-sh/uv) (for dependency management, as per custom instructions)

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/de-ecomm-pipleine.git
    cd de-ecomm-pipleine
    ```

2.  **Set up AWS Credentials:**
    Ensure your AWS credentials are configured. You can do this by setting environment variables or using the AWS CLI.
    *   **Environment Variables (Recommended for local development):**
        ```bash
        export AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
        export AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
        # Optional: For a specific region
        export AWS_DEFAULT_REGION="your-aws-region"
        ```
    *   **AWS CLI:**
        Configure your AWS CLI by running `aws configure` and providing your access key ID, secret access key, and default region.

3.  **Build and Run Docker Containers:**
    Navigate to the [`data-pipeline`](data-pipeline/) directory and build the Docker images, then start the services.
    ```bash
    cd data-pipeline
    docker-compose build
    docker-compose up -d
    ```
    This will build the necessary Docker images and start the Prefect server, worker, and any other defined services in the background.

4.  **Activate Python Virtual Environment (for local development/testing):**
    ```bash
    python -m venv .venv
    source .venv/Scripts/activate # On Windows
    # source .venv/bin/activate # On Linux/macOS
    uv pip install -r requirements.txt
    ```

## 🏃 How to Run the Pipeline

Once the Docker services are up and your AWS credentials are set:

1.  **Register Prefect Flows:**
    Ensure your Prefect flows are registered with the Prefect server. From the root of the project, you can run:
    ```bash
    prefect deploy --name ecomm-pipeline-deployment --path data-pipeline/src/orchestration/prefect_flows.py:ecomm_data_pipeline --pool default-agent-pool
    ```
    Replace `default-agent-pool` with your actual Prefect agent pool name if different.

2.  **Start a Prefect Agent:**
    If you haven't started an agent as part of your `docker-compose` setup, you can start one manually:
    ```bash
    prefect agent start --pool default-agent-pool
    ```

3.  **Run a Flow (via Prefect UI or CLI):**
    You can trigger a flow run directly from the Prefect UI (accessible at `http://localhost:4200` by default if running via docker-compose) or via the Prefect CLI.

## 🧪 Testing

Unit tests are implemented using `pytest` to ensure the correctness of individual modules and functions.

1.  **Activate your virtual environment** (if not already active):
    ```bash
    source .venv/Scripts/activate
    ```
2.  **Run tests:**
    ```bash
    cd data-pipeline
    uv pytest
    ```

## 📁 Project Structure

```
.
├── .gitignore
├── prefect.yaml
├── data/
│   ├── customers_sample.json
│   ├── customers.csv
│   ├── customers.parquet
│   ├── ...
│   └── raw/
│       ├── customers.csv
│       ├── order_items.csv
│       ├── orders.csv
│       ├── products.csv
│       └── reviews.csv
├── data-pipeline/
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── infrastructure/
│   │   └── docker/
│   │       └── Dockerfile
│   ├── src/
│   │   ├── data_ingestion/
│   │   │   └── s3_uploader.py
│   │   ├── data_processing/
│   │   │   └── data_processing.py
│   │   └── orchestration/
│   │       └── prefect_flows.py
│   └── tests/
│       └── test_aws_conn.py
└── README.md
```
