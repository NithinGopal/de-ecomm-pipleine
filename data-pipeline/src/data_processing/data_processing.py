"""
Download data from S3, clean it, transforme it and upload it back to S3
"""

import os
import boto3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import tempfile

def process_ecomm_data():
    """
    Download, process, and upload e-comm data
    """
    # Load environment variables
    load_dotenv()
    
    # Get AWS credentials from .env file
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not bucket_name:
        print(f"ERROR: AWS_S3_BUCKET_NAME not found in .env file!")
        return False
    
    print(f"Bucket: {bucket_name}")
    print(f"Region: {region}")
    
    print(f"Processing data from bucket: {bucket_name}")
    
    try:
        # Create S3 Client
        s3 = boto3.client('s3', region_name = region)
        
        # Step 1: Download data from S3 bucket
        print(f"\nStep 1: Downloading data from S3 bucket - {bucket_name} ...")
        datasets = download_data_from_s3(s3, bucket_name)
        
        # Step 2: Clean and transform data
        print("\nStep 2: Cleaning and transforming data ...")
        processed_datasets = transform_data(datasets)
        
        # Step 3: Create Business Metrics
        print("\nStep 3: Creating Business Metrics ...")
        business_metrics = create_business_metrics(processed_datasets)
        
        # Step 4: Upload processed data back to S3
        print("\nStep 4: Uploading processed data back to S3 ...")        
        upload_success = upload_processed_data(s3, bucket_name, processed_datasets, business_metrics)
        
        if upload_success:
            print("\nSUCCESS: Data Pipeline Processing Completed!")
            return True
        else:
            print("\nERROR:Failed to upload processed data")
            return False
    except Exception as e:
        print(f"ERROR: Data Processing Pipeline Failed: {e}")
        return False

def download_data_from_s3(s3, bucket_name):
    # Save each data file dataframe into the datasets dict
    datasets = {}
    
    data_files = ['customers.csv','products.csv','orders.csv','order_items.csv','reviews.csv']
    
    for file_name in data_files:
        try:
            print(f"Downloading {file_name} ...")
            
            s3_key = f"raw-data/{file_name}"
            
            # Local temp location to save the data to be processed
            local_path = os.path.join(tempfile.gettempdir(), file_name)
            
            s3.download_file(bucket_name, s3_key, local_path)
            
            # Create a Dataframe with Pandas 
            df = pd.read_csv(local_path)
            dataset_name = file_name.replace(".csv", "")
            
            datasets[dataset_name] = df
            
            print(f"Loaded {dataset_name}: {len(df)} records")
            
            # Remove the temporary local files as the dataset is saved in a dataframe to be processed
            os.remove(local_path)
            
        except Exception as e:
            print(f"Failed to download {file_name}: {e}")
            return False
    
    return datasets