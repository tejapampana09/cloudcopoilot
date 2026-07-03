import os
import urllib.request
import zipfile
import shutil

def download_and_setup_terraform():
    url = "https://releases.hashicorp.com/terraform/1.9.2/terraform_1.9.2_windows_amd64.zip"
    zip_path = "terraform.zip"
    dest_dir = "venv/Scripts"
    
    print(f"Downloading Terraform from {url}...")
    try:
        # Download the zip file
        urllib.request.urlretrieve(url, zip_path)
        print("Download completed successfully.")
        
        # Extract the binary
        print(f"Extracting terraform.exe to {dest_dir}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extract("terraform.exe", dest_dir)
            
        print("Extraction completed successfully.")
        
        # Verify the installation
        binary_path = os.path.join(dest_dir, "terraform.exe")
        if os.path.exists(binary_path):
            print(f"Terraform successfully installed at: {binary_path}")
            
            # Remove the temporary zip file
            os.remove(zip_path)
            print("Cleaned up temporary zip file.")
        else:
            print("Error: terraform.exe not found in destination directory after extraction.")
            
    except Exception as e:
        print(f"An error occurred during setup: {e}")

if __name__ == "__main__":
    download_and_setup_terraform()
