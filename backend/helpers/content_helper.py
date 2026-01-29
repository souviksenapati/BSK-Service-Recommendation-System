import os
import argparse
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import openai
from dotenv import load_dotenv

# Load environment variables from the backend .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def load_data(path: str) -> pd.DataFrame:
    """Load the service master CSV into a DataFrame."""
    return pd.read_csv(path)


def enhance_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Enhance each service description using the OpenAI API and add as a new column."""
    enhanced = []
    prompt_template = (
        "You are a helpful assistant for BSK in West Bengal providing government services to common citizens, that enhances service descriptions.\n"
        "Do not use any special characters or formatting.\n"
        "Your task is to enhance the service description by making it more informative, concise, and structured.\n"
        "Do not hallucinate or make up information.\n"
        "Example:\n"
        "Original: It is a conditional cash transfer scheme with the aim of improving the status and well-being of the girl child.\n"
        "Enhanced: A flagship conditional cash transfer scholarship for unmarried girls aged 13–18 in West Bengal offering ₹750 annual and ₹25,000 one-time grant at 18, supporting education and delaying marriage."
        " The online system uses Applicant ID/DOB/Captcha to track application status; funds are transferred via bank. Primary Domain: Education (80%), Cross-Domain: Social Welfare, Legal Services (age/marital proof), Finance, Public Services (wbkanyashree.gov.in, buddy4study.com)\n\n"
        "Example:\n"
        "Original: Income certificate is an essential legal document which serves as a proof of an individual annual income earned from all sources.\n"
        "Enhanced: Digital portal to apply for and receive income certificates via bank statements or affidavits, crucial for subsidies, scholarships, fee waivers, housing and welfare eligibility. Works via upload, verification, and digital issuance."
        " Primary Domain: Certificates (80%), Cross-Domain: Finance, Social Welfare, Legal Services\n\n"
        "Original: {orig}\n"
        "Enhanced:"
    )
    for desc in tqdm(df["service_desc"], desc="Enhancing descriptions"):
        prompt = prompt_template.format(orig=desc)
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You enhance service descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        enhanced.append(resp.choices[0].message.content.strip())

    df["enhanced_desc"] = enhanced
    return df


def generate_embeddings(df: pd.DataFrame) -> np.ndarray:
    """Generate OpenAI embeddings for each enhanced description."""
    embs = []
    for text in tqdm(df["enhanced_desc"], desc="Generating embeddings"):
        result = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=text
        )
        embs.append(result["data"][0]["embedding"])
    return np.array(embs)


def compute_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute the cosine similarity matrix from embeddings."""
    return cosine_similarity(embeddings)


def save_similarity_matrix(sim_mat: np.ndarray, ids: pd.Series, output_path: str) -> None:
    """Save the similarity matrix as a CSV with service_id labels."""
    sim_df = pd.DataFrame(sim_mat, index=ids, columns=ids)
    sim_df["service_id"] = sim_df["service_id"].astype(int)

    sim_df.to_csv(output_path)
    print(f"Saved similarity matrix to {output_path}")


def main():
    # Load environment variables from .env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Please set it in .env or as an environment variable.")
    openai.api_key = api_key

    parser = argparse.ArgumentParser(
        description="Pipeline to enhance descriptions, generate embeddings, and compute similarity matrix for services."
    )
    parser.add_argument(
        "input_csv",
        help="Path to the input CSV file with columns [service_id, service_desc, ...]"
    )
    parser.add_argument(
        "-e", "--enhanced",
        default="service_master_enhanced.csv",
        help="Path to save the CSV with enhanced descriptions"
    )
    parser.add_argument(
        "-s", "--sim_output",
        default="openai_similarity_matrix.csv",
        help="Path to save the similarity matrix CSV"
    )
    args = parser.parse_args()

    # Step 1: Load original data
    df = load_data(args.input_csv)

    # Step 2: Enhance descriptions
    df = enhance_descriptions(df)
    df.to_csv(args.enhanced, index=False)
    print(f"Saved enhanced descriptions to {args.enhanced}")

    # Step 3: Generate embeddings
    embeddings = generate_embeddings(df)

    # Step 4: Compute similarity matrix
    sim_mat = compute_similarity_matrix(embeddings)

    # Step 5: Save similarity matrix
    save_similarity_matrix(sim_mat, df["service_id"], args.sim_output)

if __name__ == "__main__":
    main()
