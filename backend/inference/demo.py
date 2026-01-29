import pandas as pd
import os

def recommend_services_2(citizen_id, df, grouped_df, cluster_service_map, service_id_to_name, service_df, top_n=5, citizen_master=None, searched_service_name=None):
    """
    Robust demographic recommendations that handle numpy/pandas import issues
    """
    # Step 1: Fetch the citizen's record
    citizen_row = df[df['citizen_id'] == citizen_id]
    if citizen_row.empty:
        # For manual entries, create a virtual citizen row from citizen_master
        if citizen_master is not None and not citizen_master.empty:
            # Create a virtual row with the manual entry data
            manual_data = citizen_master.iloc[0].to_dict()
            
            # Process demographic data if missing
            age = manual_data.get('age')
            religion = manual_data.get('religion')
            
            # Calculate age_group if not present (without numpy dependency)
            if 'age_group' not in manual_data or pd.isna(manual_data.get('age_group')):
                if pd.isna(age) or age is None or age <= 0:
                    age_group = 'adult'  # Default
                else:
                    # Simple age grouping without numpy
                    if age < 18:
                        age_group = 'child'
                    elif age < 35:
                        age_group = 'youth'
                    elif age < 60:
                        age_group = 'adult'
                    else:
                        age_group = 'senior'
            else:
                age_group = manual_data.get('age_group')
            
            # Calculate religion_group if not present
            if 'religion_group' not in manual_data or pd.isna(manual_data.get('religion_group')):
                if pd.isna(religion) or religion is None or religion == '':
                    religion_group = 'Minority'  # Default
                else:
                    religion_group = 'Hindu' if religion == 'Hindu' else 'Minority'
            else:
                religion_group = manual_data.get('religion_group')
            
            # Create a citizen row with necessary demographic columns
            citizen_row = pd.DataFrame([{
                'citizen_id': citizen_id,
                'district_id': manual_data.get('district_id', 2),  # Default to district 2 if not provided
                'gender': manual_data.get('gender'),
                'caste': manual_data.get('caste'),
                'age_group': age_group,
                'religion_group': religion_group,
                'age': age
            }])
        else:
            print(f"No data found for citizen_id: {citizen_id}")
            return []

    # Print citizen's age, gender, caste, religion from citizen_master (robust to missing 'religion')
    if citizen_master is not None:
        citizen_info_row = citizen_master[citizen_master['citizen_id'] == citizen_id]
        if not citizen_info_row.empty:
            age = citizen_info_row['age'].iloc[0] if 'age' in citizen_info_row.columns else None
            gender = citizen_info_row['gender'].iloc[0] if 'gender' in citizen_info_row.columns else None
            caste = citizen_info_row['caste'].iloc[0] if 'caste' in citizen_info_row.columns else None
            religion = citizen_info_row['religion'].iloc[0] if 'religion' in citizen_info_row.columns else None
        else:
            pass
    else:
        pass

    # Get citizen's age and caste EARLY for age-based rules
    if citizen_master is not None and 'age' in citizen_master.columns:
        if citizen_id == 'manual_entry':
            citizen_age = int(citizen_master['age'].iloc[0])
        else:
            citizen_master_row = citizen_master[citizen_master['citizen_id'] == citizen_id]
            if not citizen_master_row.empty:
                citizen_age = int(citizen_master_row['age'].iloc[0])
            else:
                citizen_age = None
    else:
        citizen_age = None

    # Get citizen's caste
    citizen_caste = None
    if citizen_master is not None:
        if citizen_id == 'manual_entry':
            citizen_caste = citizen_master['caste'].iloc[0] if 'caste' in citizen_master.columns else None
        else:
            citizen_master_row = citizen_master[citizen_master['citizen_id'] == citizen_id]
            if not citizen_master_row.empty and 'caste' in citizen_master_row.columns:
                citizen_caste = citizen_master_row['caste'].iloc[0]

    # HARD RULE: If user age <= 18, use under18_top_services.csv
    if citizen_age is not None and citizen_age <= 18:
        try:
            # Load the under-18 top services CSV
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
            under18_csv_path = os.path.join(data_dir, "under18_top_services.csv")
            
            if os.path.exists(under18_csv_path):
                under18_df = pd.read_csv(under18_csv_path)
                
                # Get the service names from the CSV
                available_services = under18_df['service_name'].tolist()
                
                # Apply filters
                filtered_services = []
                for service_name in available_services:
                    # Rule 1: Skip if this is the searched service
                    if searched_service_name and service_name == searched_service_name:
                        continue
                    
                    # Rule 2: Skip Aikyasree Scholarship if caste is General
                    if citizen_caste and citizen_caste.upper() == 'GENERAL' and 'Aikyasree Scholarship' in service_name:
                        continue
                    
                    filtered_services.append(service_name)
                    
                    # Get top 5 services
                    if len(filtered_services) >= top_n:
                        break
                
                print(f"\n🟦 Under-18 Rule Applied for Citizen {citizen_id} (Age: {citizen_age})")
                print(f"Returning top {len(filtered_services)} services from under18_top_services.csv")
                return filtered_services
            else:
                print(f"Warning: under18_top_services.csv not found at {under18_csv_path}, falling back to regular recommendations")
        except Exception as e:
            print(f"Error loading under-18 services: {e}, falling back to regular recommendations")
    
    # HARD RULE: If user age >= 60, use above60_top_services.csv
    if citizen_age is not None and citizen_age >= 60:
        try:
            # Load the above-60 top services CSV
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
            above60_csv_path = os.path.join(data_dir, "above60_top_services.csv")
            
            if os.path.exists(above60_csv_path):
                above60_df = pd.read_csv(above60_csv_path)
                
                # Get the service names from the CSV
                available_services = above60_df['service_name'].tolist()
                
                # Apply filters
                filtered_services = []
                for service_name in available_services:
                    # Rule 1: Skip if this is the searched service
                    if searched_service_name and service_name == searched_service_name:
                        continue
                    
                    # Rule 2: Skip Taposili Bandhu Scheme if caste is General
                    if citizen_caste and citizen_caste.upper() == 'GENERAL' and 'Taposili Bandhu' in service_name:
                        continue
                    
                    filtered_services.append(service_name)
                    
                    # Get top 5 services
                    if len(filtered_services) >= top_n:
                        break
                
                print(f"\n🟧 Above-60 Rule Applied for Citizen {citizen_id} (Age: {citizen_age})")
                print(f"Returning top {len(filtered_services)} services from above60_top_services.csv")
                return filtered_services
            else:
                print(f"Warning: above60_top_services.csv not found at {above60_csv_path}, falling back to regular recommendations")
        except Exception as e:
            print(f"Error loading above-60 services: {e}, falling back to regular recommendations")

    # Step 2: Identify group attributes for cluster matching - include district_id
    group_cols = ['district_id', 'gender', 'caste', 'age_group', 'religion_group']
    citizen_group_values = citizen_row[group_cols].iloc[0].to_dict()

    # Step 3: Match the citizen's group to get the cluster_id
    cluster_match = grouped_df
    for col in group_cols:
        cluster_match = cluster_match[cluster_match[col] == citizen_group_values[col]]

    if cluster_match.empty:
        print(f"No cluster match found for citizen_id: {citizen_id}")
        return []

    cluster_id = cluster_match['cluster_id'].iloc[0]
    recommendations = cluster_service_map.get(cluster_id)
    if not recommendations:
        print(f"No recommendations found for cluster_id: {cluster_id}")
        return []

    # Step 4: Get all service columns
    service_columns = [col for col in df.columns if col.startswith('service_')]

    # Step 5: Extract services already used by the citizen
    used_service_ids = []
    # For manual entries, assume no previous services used
    if citizen_id == 'manual_entry':
        used_service_ids = []
    else:
        for col in service_columns:
            if col in citizen_row.columns and citizen_row[col].iloc[0] > 0:
                try:
                    service_id = int(float(col.replace('service_', '')))
                    used_service_ids.append(service_id)
                except Exception:
                    continue
    used_service_names = [service_id_to_name.get(sid, f"Unknown Service {sid}") for sid in used_service_ids]

    print(f"\n🟩 Services already used by Citizen {citizen_id}:")
    for name in used_service_names:
        print(f"  - {name}")

    # Step 6: Prepare recurrence info and age range from service_df
    recurrence_map = dict(zip(service_df['service_id'], service_df['is_recurrent'])) if 'is_recurrent' in service_df.columns else {}
    min_age_map = dict(zip(service_df['service_id'], service_df['min_age'])) if 'min_age' in service_df.columns else {}
    max_age_map = dict(zip(service_df['service_id'], service_df['max_age'])) if 'max_age' in service_df.columns else {}

    # Step 7: Get top services for the cluster, applying all filters
    recommended_service_ids = []
    for sid in recommendations:
        # Age filter
        min_age = min_age_map.get(sid, None)
        max_age = max_age_map.get(sid, None)
        if citizen_age is not None:
            if (min_age is not None and citizen_age < min_age) or (max_age is not None and citizen_age > max_age):
                continue
        # If already used and not recurrent, skip
        if sid in used_service_ids and not recurrence_map.get(sid, False):
            continue
        # If already recommended, skip
        if sid in recommended_service_ids:
            continue
        recommended_service_ids.append(sid)
        if len(recommended_service_ids) >= top_n:
            break

    recommended_service_names = [service_id_to_name.get(sid, f"Unknown Service {sid}") for sid in recommended_service_ids]

    # Return the recommended services as a list
    return recommended_service_names
