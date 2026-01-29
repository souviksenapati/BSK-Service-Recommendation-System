import pandas as pd
import os
import numpy as np

def generate_district_csv_files():
    """
    Generate CSV files required by district.py from the main CSV files.
    This function creates district_top_services.csv with format:
    district_id, district_name, service_id, service_name, unique_citizen_count, citizen_percentage, rank_in_district
    """
    print("Loading data files...")
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    # Load required files with latin-1 encoding
    service_master = pd.read_csv(os.path.join(data_dir, "service_master.csv"), encoding="latin-1")
    district = pd.read_csv(os.path.join(data_dir, "ml_district.csv"), encoding="latin-1")
    provision = pd.read_csv(os.path.join(data_dir, "ml_provision.csv"), encoding="latin-1")
    citizen_master = pd.read_csv(os.path.join(data_dir, "ml_citizen_master.csv"), encoding="latin-1")
    services = pd.read_csv(os.path.join(data_dir, "services.csv"), encoding="latin-1")
    print(f"Loaded data:")
    print(f"- service_master: {service_master.shape}")
    print(f"- district: {district.shape}")
    print(f"- provision: {provision.shape}")
    print(f"- citizen_master: {citizen_master.shape}")
    print(f"- services: {services.shape}")
    # Step 1: Merge citizen and provision data
    print("\nStep 1: Merging provision with citizen data...")
    provision_citizen = pd.merge(
        provision,
        citizen_master[['citizen_id', 'district_id']],
        left_on='customer_id',
        right_on='citizen_id',
        how='inner'
    )
    
    # Step 2: Count service usage by district
    print("\nStep 2: Calculating service usage by district...")
    district_service_counts = provision_citizen.groupby(['district_id', 'service_id']).size().reset_index(name='usage_count')
    
    # Step 3: Get district names
    district_names = district[['district_id', 'district_name']].drop_duplicates()
    district_service_counts = pd.merge(district_service_counts, district_names, on='district_id')
    
    # Step 4: Get service names
    service_names = services[['service_id', 'service_name']].drop_duplicates()
    district_service_counts = pd.merge(district_service_counts, service_names, on='service_id')
    
    # Step 5: Calculate total citizens per district for percentages
    total_citizens_per_district = provision_citizen.groupby('district_id')['customer_id'].nunique().reset_index(name='total_citizens')
    unique_citizens_per_service = provision_citizen.groupby(['district_id', 'service_id'])['customer_id'].nunique().reset_index(name='unique_citizen_count')
    
    district_service_stats = pd.merge(unique_citizens_per_service, total_citizens_per_district, on='district_id')
    district_service_stats['citizen_percentage'] = (district_service_stats['unique_citizen_count'] / district_service_stats['total_citizens'] * 100).round(1)
    
    # Step 6: Add ranking within each district
    district_service_stats['rank_in_district'] = district_service_stats.groupby('district_id')['unique_citizen_count'].rank(method='dense', ascending=False)
    
    # Step 7: Merge all information
    final_df = pd.merge(
        district_service_stats,
        district_names,
        on='district_id'
    )
    final_df = pd.merge(
        final_df,
        service_names,
        on='service_id'
    )
    
    # Sort by district_id and rank
    final_df = final_df.sort_values(['district_id', 'rank_in_district'])
    
    # Select and order columns
    columns = [
        'district_id', 'district_name', 'service_id', 'service_name',
        'unique_citizen_count', 'citizen_percentage', 'rank_in_district'
    ]
    final_df = final_df[columns]
    
    # Save to CSV
    output_path = os.path.join(data_dir, "district_top_services.csv")
    final_df.to_csv(output_path, index=False)
    print(f"\n✅ Successfully generated district_top_services.csv!")
    print(f"- Saved to: {output_path}")
    print(f"- Shape: {final_df.shape}")
    print("\nFirst few rows of generated file:")
    print(final_df.head().to_string())
    
    return final_df

if __name__ == "__main__":
    generate_district_csv_files() 