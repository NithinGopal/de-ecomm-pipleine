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

# Extract Raw Data files from S3 
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

# Transform the data stored in temporary Dataframe datasets stored in 'datasets' dict
def transform_data(datasets):
    # Store the processed dataframes in this dict
    processed = {}
    
    # process customer data
    if 'customers' in datasets:
        customers = datasets['customers'].copy()
        
        # Clean email addresses: all lower case, leading and trailing spaces trimmed
        customers['email'] = customers['email'].str.lower().str.strip()
        
        # Convert dates
        customers['date_of_birth'] = pd.to_datetime(customers['date_of_birth'])
        customers['registration_date'] = pd.to_datetime(customers['registration_date'])
        
        # Calculate age
        customers['age'] = (datetime.now() - customers['date_of_birth']).dt.days // 365
        
        # Create Age Groups
        customers['age_group'] = pd.cut(
                                        customers['age'], 
                                        bins = [0, 25, 35, 50, 65, 100], 
                                        labels = ['18-25', '26-35', '36-50', '51-65', '65+']
                                    )
        
        processed['customers_clean'] = customers
        
        print(f"Processed customers: {len(customers)} records")
        
    if 'products' in datasets:
        products = datasets['products'].copy()
        
        # Clean product name
        products['product_name'] = products['product_name'].str.strip()
        
        #  Convert price to numeric
        products['price'] = pd.to_numeric(products['price'], errors='coerce')

        # Create age groups
        products['price_category'] = pd.cut(products['price'], bins = [0, 50, 150, 500, float('inf')],
                                        labels = ['Budget','Mid-range','Premium','Luxury'])

        processed['products_clean'] = products

        print(f'Processed products: {len(products)} records')
        
    # Process orders data
    if 'orders' in datasets:
        orders = datasets['orders'].copy()
        
        # Convert date
        orders['order_date'] = pd.to_datetime(orders['order_date'])
        
        # Convert total amount to numeric
        orders['total_amount'] = pd.to_numeric(orders['total_amount'], errors = 'coerce')
        
        # Extract month and year for seasonal analysis
        
        orders['order_month'] = orders['order_date'].dt.month
        orders['order_year'] = orders['order_date'].dt.year
        
        processed['orders_clean'] = orders
        
        print(f"Processed orders: {len(orders)} records")
        
    # Process order items data
    if 'order_items' in datasets:
        order_items = datasets['order_items'].copy()
        
        # Convert numeric columns
        orders['quantity'] = pd.to_numeric(orders['quantity'], errors = 'coerce')
        orders['unit_price'] = pd.to_numeric(orders['unit_price'], errors = 'coerce')
        
        # Claculate total price per item
        order_items['total_price'] = order_items['quantity'] * order_items['unit_price']
        
        processed['order_items_clean'] = order_items
        
        print(f"Processed order_items: {len(order_items)} records")
        
    # Process review data
    if 'reviews' in datasets:
        reviews = datasets['reviews'].copy()
        
        # Convert date
        reviews['review_date'] = pd.to_datetime(reviews['review_date'])
        
        # Convert rating to numeric
        reviews['rating'] = pd.to_numeric(reviews['rating'], errors='coerce')
        
        # create rating categories
        reviews['rating_category'] = reviews['rating'].apply(
            lambda x: 'Excellent' if x >= 4.5 else 
                        'Good' if x >= 3.5 else
                        'Average' if x >= 2.5 else 'Poor'
        )
        
        processed['reviews_clean'] = reviews
        
        print(f"Processed reviews: {len(reviews)} records")
        
    return processed

def create_business_metrics(processed_datasets):
    
    metrics = {}
    
    # Customer metric
    
    if 'customers_clean' in processed_datasets and 'orders_clean' in processed_datasets:
        customers = processed_datasets['customers_clean']
        orders = processed_datasets['orders_clean']
        
        # Customers lifetime value
        customer_metrics = orders.groupby('customer_id').agg({
            'total_amount': ['sum', 'count', 'mean'],
            'order_date': ['min', 'max']
        }).round(2)
        
        # Header columns
        customer_metrics.columns =['total_spent','order_count','ave_order_value','first_order','last_order']
        
        customer_metrics = customer_metrics.reset_index()
        
        # Merge with customer data
        
        customer_metrics = customer_metrics.merge(customers[['customer_id', 'age_group']])
        
        metrics['customer_metrics'] = customer_metrics
        
        print(f"Created customer metrics: {len(customer_metrics)} customers")
        
    # Product performance metrics
    
    if 'products_clean' in processed_datasets and 'order_items_clean' in processed_datasets:
        products = processed_datasets['products_clean']
        order_items = processed_datasets['order_items_clean']
        
        # Product sales metrics
        product_metrics = order_items.groupby('product_id').agg({
            'quantity': 'sum',
            'total_price': 'sum',
            'order_id': 'count'
        }).round(2)
        
        product_metrics.columns = ['total_quantity_sold', 'total_revenue', 'number_of_orders'] 
        product_metrics = product_metrics.reset_index()
        
        # Merge with product data
        product_metrics = product_metrics.merge(products[['product_id', 'product_name', 'category', 'price']], on = 'product_id')
        
        metrics['product_metrics'] = product_metrics
        print(f"Created product metrics: {len(product_metrics)} products")
        
    # Monthly Sales Trends
    
    if 'orders_clean' in processed_datasets:
        orders = processed_datasets['orders_clean']
        
        monthly_sales = orders.grouby(['order_year', 'order_count']).agg({
            'total_amount': 'sum',
            'order_id': 'count'
        }).round(2)
        
        monthly_sales.columns = ['total_revenue', 'order_count']
        monthly_sales = monthly_sales.reset_index()
        
        metrics['monthly_sales'] = monthly_sales
        print(f"Created monthly sales trends: {len(monthly_sales)} months")
        
    return metrics

def upload_processed_data(s3, bucket_name, processed, metrics):
    
    upload_count = 0
    total_files = len(processed) + len(metrics)
    
    # Upload processed datasets
    for dataset_name, df in processed.items():
        try:
            # Save a temporary csv file
            local_path = os.path.join(tempfile.gettempdir(), f"{dataset_name}.csv")
            df.to_csv(local_path, index=False)
            
            # Upload to s3
            s3_key = f"processed/{dataset_name}.csv"
            s3.upload_file(local_path, bucket_name, s3_key)
            
            print(f"Uploaded {dataset_name}: {len(df)} records")
            upload_count += 1
            
            # Clean up temp files
            os.remove(local_path)
            
        except Exception as e:
            print(f"Failed to upload {dataset_name}: {e}")
            
    # Upload business metrics
    for metric_name, df in metrics.items():
        try:
            # Save a temporary csv file
            local_path = os.path.join(tempfile.gettempdir(), f"{metric_name}.csv")
            df.to_csv(local_path, index=False)
            
            # Upload to S3
            s3_key = f"processed/metrics/{metric_name}.csv"
            s3.upload_file(local_path, bucket_name, s3_key)
            
            print(f"Uploaded {metric_name}: {len(df)} records")
            upload_count += 1
            
            # Clean up temp files
            os.remove(local_path)
            
        except Exception as e:
            print(f"ERROR: Failed to Upload {metric_name}: {e}")
            
    return upload_count == total_files


if __name__ == "__main__":
    
    success = process_ecomm_data()
    
    if success:
        print("\nNext Step: Orchestration with prefect!")
        
    else:
        print("\nFix the errors and try again")