"""
PyArrow-free demographic recommendations helper
This module provides demographic recommendations without any pandas/pyarrow dependencies
Updated for the new backend structure
"""

import csv
import pickle
import os
from typing import List, Dict, Any, Optional

def load_csv_without_pandas(filepath: str) -> List[Dict[str, Any]]:
    """Load CSV file without pandas, returning list of dictionaries."""
    
    # Handle relative paths from backend helpers folder
    if not os.path.isabs(filepath):
        if filepath.startswith("data/"):
            # Convert to absolute path from project root
            filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), filepath)
        else:
            # Assume it's already relative to project root
            filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), filepath)
    
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Convert numeric strings to appropriate types
                converted_row = {}
                for key, value in row.items():
                    if value == '' or value is None:
                        converted_row[key] = None
                    elif value.isdigit():
                        converted_row[key] = int(value)
                    else:
                        try:
                            converted_row[key] = float(value)
                        except ValueError:
                            converted_row[key] = value
                data.append(converted_row)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []
    return data

def find_citizen_by_id(citizen_id: str) -> Optional[Dict[str, Any]]:
    """Find citizen by ID in the ml_citizen_master.csv file."""
    citizens_data = load_csv_without_pandas("data/ml_citizen_master.csv")
    
    for citizen in citizens_data:
        if str(citizen.get('citizen_id')) == str(citizen_id):
            return citizen
    return None

def calculate_age_group(age: int) -> str:
    """Calculate age group without numpy dependency."""
    if age < 18:
        return 'child'
    elif age < 60:
        return 'youth'
    else:
        return 'elderly'

def calculate_religion_group(religion: str) -> str:
    """Calculate religion group."""
    if not religion or religion == '' or religion is None:
        return 'Minority'
    return 'Hindu' if religion == 'Hindu' else 'Minority'

def pyarrow_free_demographic_recommendations(citizen_id: str) -> List[str]:
    """
    Generate demographic recommendations without pandas/pyarrow dependencies.
    Returns list of service names.
    """
    # Find citizen in ml_citizen_master.csv
    citizen = find_citizen_by_id(citizen_id)
    if not citizen:
        print(f"❌ Citizen {citizen_id} not found in ml_citizen_master.csv")
        return []
    
    print(f"✅ Found citizen: {citizen.get('citizen_name', 'Unknown')}")
    
    # Extract demographics
    age = citizen.get('age', 0)
    gender = citizen.get('gender', '')
    caste = citizen.get('caste', '')
    religion = citizen.get('religion', '')
    district_id = citizen.get('district_id', 0)
    
    # Calculate derived fields
    age_group = calculate_age_group(age)
    religion_group = calculate_religion_group(religion)
    
    print(f"📊 Demographics: {gender}, {caste}, {age_group}, {religion_group}, district {district_id}")
    
    # Load grouped_df.csv to find matching clusters
    grouped_data = load_csv_without_pandas("data/grouped_df.csv")
    
    # Find matching demographic clusters
    matching_clusters = []
    for row in grouped_data:
        if (row.get('gender') == gender and 
            row.get('caste') == caste and 
            row.get('age_group') == age_group and 
            row.get('religion_group') == religion_group and
            row.get('district_id') == district_id):
            matching_clusters.append(row.get('cluster_id'))
    
    # If no exact match, try without district
    if not matching_clusters:
        for row in grouped_data:
            if (row.get('gender') == gender and 
                row.get('caste') == caste and 
                row.get('age_group') == age_group and 
                row.get('religion_group') == religion_group):
                matching_clusters.append(row.get('cluster_id'))
    
    if not matching_clusters:
        print("❌ No matching demographic clusters found")
        return []
    
    print(f"✅ Found {len(matching_clusters)} matching clusters")
    
    # Load cluster service mapping
    try:
        cluster_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cluster_service_map.pkl")
        with open(cluster_map_path, "rb") as f:
            cluster_service_map = pickle.load(f)
    except Exception as e:
        print(f"❌ Failed to load cluster service map: {e}")
        return []
    
    # Get services from matching clusters
    all_services = []
    for cluster_id in matching_clusters:
        # Try both integer and string cluster IDs
        cluster_id_int = int(cluster_id) if isinstance(cluster_id, str) else cluster_id
        cluster_id_str = str(cluster_id)
        
        if cluster_id_int in cluster_service_map:
            services = cluster_service_map[cluster_id_int]
            all_services.extend(services)
        elif cluster_id_str in cluster_service_map:
            services = cluster_service_map[cluster_id_str]
            all_services.extend(services)
    
    if not all_services:
        print("❌ No services found for matching clusters")
        return []
    
    # Load service names
    service_names_data = load_csv_without_pandas("data/service_id_with_name.csv")
    service_id_to_name = {}
    for row in service_names_data:
        service_id_to_name[row.get('service_id')] = row.get('service_name')
    
    # Convert service IDs to names
    service_names = []
    seen_services = set()
    
    for service_id in all_services:
        if service_id not in seen_services:
            service_name = service_id_to_name.get(service_id)
            if service_name:
                service_names.append(service_name)
                seen_services.add(service_id)
    
    # Return top 10 recommendations
    return service_names[:10]

def pyarrow_free_manual_demographic_recommendations(age: int, gender: str, caste: str, religion: str, district_id: int) -> List[str]:
    """
    Generate demographic recommendations for manually entered demographics.
    Returns list of service names.
    """
    print(f"📊 Manual Demographics: {gender}, {caste}, age {age}, {religion}, district {district_id}")
    
    # Calculate derived fields
    age_group = calculate_age_group(age)
    religion_group = calculate_religion_group(religion)
    
    print(f"📊 Processed Demographics: {gender}, {caste}, {age_group}, {religion_group}, district {district_id}")
    
    # Load grouped_df.csv to find matching clusters
    grouped_data = load_csv_without_pandas("data/grouped_df.csv")
    
    # Find matching demographic clusters
    matching_clusters = []
    for row in grouped_data:
        if (row.get('gender') == gender and 
            row.get('caste') == caste and 
            row.get('age_group') == age_group and 
            row.get('religion_group') == religion_group and
            row.get('district_id') == district_id):
            matching_clusters.append(row.get('cluster_id'))
    
    # If no exact match, try without district
    if not matching_clusters:
        for row in grouped_data:
            if (row.get('gender') == gender and 
                row.get('caste') == caste and 
                row.get('age_group') == age_group and 
                row.get('religion_group') == religion_group):
                matching_clusters.append(row.get('cluster_id'))
    
    if not matching_clusters:
        print("❌ No matching demographic clusters found")
        return []
    
    print(f"✅ Found {len(matching_clusters)} matching clusters")
    
    # Load cluster service mapping
    try:
        cluster_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cluster_service_map.pkl")
        with open(cluster_map_path, "rb") as f:
            cluster_service_map = pickle.load(f)
    except Exception as e:
        print(f"❌ Failed to load cluster service map: {e}")
        return []
    
    # Get services from matching clusters
    all_services = []
    for cluster_id in matching_clusters:
        # Try both integer and string cluster IDs
        cluster_id_int = int(cluster_id) if isinstance(cluster_id, str) else cluster_id
        cluster_id_str = str(cluster_id)
        
        if cluster_id_int in cluster_service_map:
            services = cluster_service_map[cluster_id_int]
            all_services.extend(services)
        elif cluster_id_str in cluster_service_map:
            services = cluster_service_map[cluster_id_str]
            all_services.extend(services)
    
    if not all_services:
        print("❌ No services found for matching clusters")
        return []
    
    # Load service names
    service_names_data = load_csv_without_pandas("data/service_id_with_name.csv")
    service_id_to_name = {}
    for row in service_names_data:
        service_id_to_name[row.get('service_id')] = row.get('service_name')
    
    # Convert service IDs to names
    service_names = []
    seen_services = set()
    
    for service_id in all_services:
        if service_id not in seen_services:
            service_name = service_id_to_name.get(service_id)
            if service_name:
                service_names.append(service_name)
                seen_services.add(service_id)
    
    # Return top 10 recommendations
    return service_names[:10]
