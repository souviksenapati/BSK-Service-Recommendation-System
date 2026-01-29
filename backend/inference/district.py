def get_top_services_for_district_from_csv(csv_path, district_id, top_n=5):
    """
    Returns a list of top N service names for a given district_id from the specified CSV file.
    Updated to work with the new file structure.
    """
    import pandas as pd
    import os
    
    # Handle relative path from backend inference folder
    if not os.path.isabs(csv_path):
        if csv_path.startswith("../"):
            # Already relative to project root
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), csv_path[3:])
        else:
            # Assume it's from data folder
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "district_top_services.csv")
    
    df = pd.read_csv(csv_path)
    
    # Convert district_id to float for consistency
    district_id = float(district_id)
    
    # Filter by district and sort by rank
    district_services = df[df['district_id'] == district_id].sort_values('rank_in_district')
    
    if district_services.empty:
        print(f"No data found for district_id: {district_id}")
        return []
    
    # Get top N service names
    top_services = district_services['service_name'].head(top_n).tolist()
    return top_services

# Example usage:
# top_services = get_top_services_for_district_from_csv("../data/district_top_services.csv", 3)
# print(top_services)
