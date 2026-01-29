import pandas as pd
import numpy as np
import os

def find_similar_services_from_csv(data_csv_path, similarity_matrix_csv_path, service_id, n=5):
    """
    Finds the top N most similar unique services for a given service ID by loading
    data and similarity matrix from CSV files, by initially retrieving 2*N.
    Updated to work with the new file structure.

    Args:
      data_csv_path: The path to the original data CSV file (e.g., servie_with_domains.csv).
      similarity_matrix_csv_path: The path to the similarity matrix CSV file which now
                                  includes a 'service_id' column as the first column.
      service_id: The ID of the service (1-based) from the original data.
      n: The number of unique similar services to return (excluding the service itself).

    Returns:
      A list of unique service names of the top N similar services.
    """
    try:
        # Handle relative paths from backend inference folder
        if not os.path.isabs(data_csv_path):
            if data_csv_path.startswith("../"):
                # Already relative to project root
                data_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), data_csv_path[3:])
            else:
                # Assume it's from data folder
                data_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", os.path.basename(data_csv_path))
        
        if not os.path.isabs(similarity_matrix_csv_path):
            if similarity_matrix_csv_path.startswith("../"):
                # Already relative to project root
                similarity_matrix_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), similarity_matrix_csv_path[3:])
            else:
                # Assume it's from data folder
                similarity_matrix_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", os.path.basename(similarity_matrix_csv_path))
        
        # Load the original data DataFrame
        df = pd.read_csv(data_csv_path, encoding='latin1')

        # Load the similarity matrix from the CSV file
        similarity_matrix_df = pd.read_csv(similarity_matrix_csv_path)

        # Extract the service_ids from the similarity matrix DataFrame
        matrix_service_ids = similarity_matrix_df['service_id'].values

        # Drop the service_id column to get the pure similarity matrix
        similarity_matrix = similarity_matrix_df.drop(columns=['service_id']).values

    except FileNotFoundError:
        print("Error: One or both of the CSV files not found.")
        return []
    except KeyError:
         print("Error: 'service_id' column not found in the similarity matrix CSV.")
         return []
    except Exception as e:
        print(f"An error occurred while loading data or similarity matrix: {e}")
        return []

    # Find the 0-based index corresponding to the input service_id in the matrix_service_ids
    try:
        service_index = np.where(matrix_service_ids == service_id)[0][0]
    except IndexError:
        print(f"Service ID {service_id} not found in the similarity matrix CSV.")
        return []

    # Check if the similarity matrix dimensions match the number of services in the matrix_service_ids
    if similarity_matrix.shape[0] != len(matrix_service_ids):
        print("Error: Similarity matrix dimensions do not match the number of services in the matrix file.")
        return []

    # Get the similarity scores for the given service from the similarity matrix
    service_similarities = similarity_matrix[service_index]

    # Get the indices of the top 2*N most similar services (excluding the service itself)
    n_retrieve = 2 * n
    similar_service_indices_in_matrix = np.argsort(service_similarities)[::-1][1:n_retrieve+1]

    # Get the corresponding service_ids from the matrix_service_ids using these indices
    similar_service_ids = matrix_service_ids[similar_service_indices_in_matrix]

    # Get the 'service_name' from the original df using these service_ids
    # Need to handle cases where a service_id from the similarity matrix might not be in the original df (though unlikely)
    similar_service_names = df[df['service_id'].isin(similar_service_ids)]['service_name'].tolist()


    # Get unique service names while maintaining order and take the top N
    unique_similar_service_names = []
    seen_names = set()
    for name in similar_service_names:
        if name not in seen_names:
            unique_similar_service_names.append(name)
            seen_names.add(name)
        if len(unique_similar_service_names) == n:
            break

    # Get the name of the input service from the original df
    try:
        input_service_name = df[df['service_id'] == service_id]['service_name'].iloc[0]
        print(f"Input Service (ID: {service_id}): {input_service_name}\n")
    except IndexError:
        print(f"Input Service ID {service_id} not found in the original data CSV.")


    return unique_similar_service_names

# Example usage (optional, for testing the function)
# data_file = "../data/service_with_domains.csv"
# similarity_file = "../data/openai_similarity_matrix.csv"
# test_service_id_csv = 1
# num_similar_services = 5
# similar_services_from_csv = find_similar_services_from_csv(data_file, similarity_file, test_service_id_csv, num_similar_services)
# print(f"Top {num_similar_services} unique similar services for ID {test_service_id_csv} loaded from CSV:")
# for service_name in similar_services_from_csv:
#     print(service_name)
