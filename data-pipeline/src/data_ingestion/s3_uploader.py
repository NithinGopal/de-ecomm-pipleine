import os
import boto3
from pathlib import Path
from dotenv import load_dotenv

def upload_data_to_s3():
    """
    Upload data from data/ raw to S3 bucket
    """
    print("Starting data upload to S3...")
    
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
    
    try:
        # Create s3 client
        s3 = boto3.client('s3', region_name=region)
        
        # Create bucket if it doesnt exist
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' exists")
        except:
            print(f"Creating bucket '{bucket_name}' ...")
            if region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            print(f"Bucket created!")
            
        # Find CSV files in data/raw/
        data_folder = Path("data/raw")
        
        if not data_folder.exists():
            data_folder = Path('../../../data/raw')
            
        if not data_folder.exists():
            print("ERROR: Raw Data Folder Not Found!")
            print("Make sure to have data/raw with CSV files")        
            return False
        
        # Get List of CSV files
        csv_files = list(data_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"ERROR: No CSV files fount in {data_folder}")
            return False
        
        print(f"Found {len(csv_files)} files to upload ...")
            
        # Upload each data file
        uploaded_count = 0
        
        for csv_file in csv_files:
            s3_key = f"raw-data/{csv_file.name}"
            print(f"Uploading {csv_file.name} ...")
            
            try:
                s3.upload_file(str(csv_file), bucket_name, s3_key)
                print(f"SUCCESS: Uploaded to s3://{bucket_name}/{s3_key}")
                uploaded_count += 1
                
            except Exception as upload_error:
                print(f"ERROR: Failed to upload {csv_file.name}: {upload_error}")
                
        if uploaded_count == len(csv_files):
            print(f"\nSUCCESS: All {uploaded_count} files uploaded to S3 Data Lake")
            return True
        else:
            print(f"\nPartial Success: {uploaded_count}/{len(csv_files)} files uploaded")
            return False
        
    except Exception as e:
        print(f"ERROR: Upload Failed: {e}")
        print("Check your AWS Credentials and S3 Bucked permissions")
        return False
    

# Verification
def verify_upload():
    print("\nVerifying Upload ...")
    
    # Load environment variables
    load_dotenv()
    
    # Get AWS credentials from .env file
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    try:
        # Create S3 Client
        s3 = boto3.client('s3', region_name=region)
        
        response = s3.list_objects_v2(Bucket= bucket_name, Prefix = "raw-data/")
        
        if "Contents" not in response:
            print("ERROR: No files found in bucket")
            return False
        
        files = response["Contents"]
        print(f"Found {len(files)} files in S3:")
        
        total_size_mb = 0
        
        for file in files:
            size_mb = file['Size'] / (1024*1024)
            total_size_mb += size_mb
            print(f"{file["Key"]} ({size_mb: .2f} MB)")
            
        print(f"Total Data Size: {total_size_mb: .2f} MB")
        print("Upload verification complete!")
        return True
    
    except Exception as e:
        print(f"ERROR: Upload Verification Failed: {e}")
        return False
        
if __name__ == "__main__":
    # Run upload
    success = upload_data_to_s3()
    
    # Verify if upload was successful
    if success:
        verify_upload()
        
    print("\nNext Step: Data Processing And Transformation!")