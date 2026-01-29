import pandas as pd
import pickle
import os
import numpy as np

def generate_demo_csv_files():
    """
    Generate all CSV files required by demo.py from the 4 main CSV files:
    - service_master.csv
    - ml_district.csv  
    - ml_provision.csv
    - ml_citizen_master.csv
    - services.csv (must already exist, used for eligibility, is_recurrent, min_age, max_age)
    This function creates:
    - grouped_df.csv
    - cluster_service_map.pkl
    - service_id_with_name.csv
    - final_df.csv
    """
    print("Loading data files...")
    # Load the 4 main CSV files
    service_master = pd.read_csv("data/service_master.csv", encoding='latin-1')
    district = pd.read_csv("data/ml_district.csv", encoding='latin-1')
    provision = pd.read_csv("data/ml_provision.csv", encoding='latin-1')
    citizen_master = pd.read_csv("data/ml_citizen_master.csv", encoding='latin-1')
    services = pd.read_csv("data/services.csv", encoding='latin-1')  # Use existing services.csv
    print(f"Loaded data:")
    print(f"- service_master: {service_master.shape}")
    print(f"- district: {district.shape}")
    print(f"- provision: {provision.shape}")
    print(f"- citizen_master: {citizen_master.shape}")
    print(f"- services: {services.shape}")
    # Step 1: Merge citizen and provision data
    print("\nStep 1: Merging citizen and provision data...")
    merged_df = pd.merge(citizen_master, provision, left_on='citizen_id', right_on='customer_id', how='inner')
    print(f"Merged data shape: {merged_df.shape}")
    # Step 2: Clean the merged data (only drop rows missing required columns)
    required_cols = ['citizen_id', 'district_id', 'sub_div_id', 'gp_id', 'gender', 'dob', 'age', 'caste', 'religion', 'service_id']
    clean_merged_df = merged_df.dropna(subset=required_cols)
    clean_df = clean_merged_df[required_cols].copy()
    # Ensure district_id is always int
    clean_df['district_id'] = clean_df['district_id'].astype(int)
    print(f"After cleaning: {clean_df.shape}")
    # Step 3: Create one-hot encoded service matrix
    print("\nStep 3: Creating one-hot encoded service matrix...")
    service_ohe = pd.get_dummies(clean_df['service_id'], prefix='service')
    # Rename columns to remove .0 from service names
    service_ohe.columns = [col.replace('.0', '') if col.startswith('service_') else col for col in service_ohe.columns]
    clean_ohe = pd.concat([pd.DataFrame(clean_df[["citizen_id"]]), pd.DataFrame(service_ohe)], axis=1)
    service_agg = clean_ohe.groupby('citizen_id').sum().reset_index()
    print(f"After one-hot/groupby: {service_agg.shape}")
    # Step 4: Get unique citizen attributes
    citizen_info = clean_df.drop_duplicates(subset=['citizen_id']).drop(columns=['service_id']).copy()
    citizen_info['district_id'] = citizen_info['district_id'].astype(int)
    print(f"Unique citizen info: {citizen_info.shape}")
    # Step 5: Merge one-hot service matrix with citizen attributes
    final_df = pd.merge(citizen_info, service_agg, on='citizen_id')
    final_df['district_id'] = final_df['district_id'].astype(int)
    print(f"Final DF: {final_df.shape}")
    # Step 6: Create age groups and religion groups
    print("\nStep 6: Creating demographic groups...")
    bins = [0, 18, 35, 60, 200]
    labels = ['child', 'youth', 'adult', 'senior']
    final_df['age_group'] = pd.cut(final_df['age'], bins=bins, labels=labels, right=False)
    final_df['religion_group'] = final_df['religion'].apply(lambda x: 'Hindu' if x == 'Hindu' else 'Minority')
    # Step 7: Create grouped_df for clustering (include district_id)
    print("\nStep 7: Creating grouped_df for clustering...")
    group_columns = ['district_id', 'gender', 'caste', 'age_group', 'religion_group']
    service_columns = [col for col in final_df.columns if col.startswith('service_')]
    grouped_df = final_df.groupby(group_columns)[service_columns].sum().reset_index()
    grouped_df['district_id'] = grouped_df['district_id'].astype(int)
    grouped_df.insert(0, 'cluster_id', np.arange(1, len(grouped_df) + 1))
    print(f"Grouped data shape: {grouped_df.shape}")
    # Step 8: Create cluster_service_map (matches main.ipynb logic)
    # cluster_id (int) -> list of service_id (int), sorted by descending usage
    cluster_service_map = {}
    for _, row in grouped_df.iterrows():
        cluster_id = int(row['cluster_id'])
        sorted_services = sorted(
            [(col, float(row[col])) for col in service_columns],
            key=lambda x: x[1],
            reverse=True
        )
        # Use int(col.replace('service_', '')) for service IDs, no float conversion of col
        top_service_ids = [int(col.replace('service_', '')) for col, val in sorted_services if val > 0]
        cluster_service_map[cluster_id] = top_service_ids[:100]
    # Step 9: Create service_id_to_name mapping
    print("\nStep 9: Creating service mappings...")
    service_id_to_name = dict(zip(services['service_id'], services['service_name']))
    service_id_with_name_df = pd.DataFrame(list(service_id_to_name.items()), columns=pd.Index(['service_id', 'service_name']))
    # Step 10: Save all generated files (do NOT create services.csv)
    print("\nStep 10: Saving generated files...")
    os.makedirs("data", exist_ok=True)
    grouped_df.to_csv("data/grouped_df.csv", index=False)
    print("✓ Saved grouped_df.csv")
    with open("data/cluster_service_map.pkl", "wb") as f:
        pickle.dump(cluster_service_map, f, protocol=4)
    print("✓ Saved cluster_service_map.pkl")
    service_id_with_name_df.to_csv("data/service_id_with_name.csv", index=False)
    print("✓ Saved service_id_with_name.csv")
    final_df.to_csv("data/final_df.csv", index=False)
    print("✓ Saved final_df.csv")
    print(f"\n✅ Successfully generated all CSV files required by demo.py!")
    print(f"Generated files:")
    print(f"- data/grouped_df.csv ({grouped_df.shape})")
    print(f"- data/cluster_service_map.pkl ({len(cluster_service_map)} clusters)")
    print(f"- data/service_id_with_name.csv ({len(service_id_to_name)} services)")
    print(f"- data/final_df.csv ({final_df.shape})")
    return {
        'grouped_df': grouped_df,
        'cluster_service_map': cluster_service_map,
        'service_id_to_name': service_id_to_name,
        'services': services,
        'final_df': final_df
    }

if __name__ == "__main__":
    generate_demo_csv_files() 