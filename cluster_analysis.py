#!/usr/bin/env python3
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import argparse
import os


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cluster analysis of image analysis results"
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="results/analysis_results/analysis_results.json",
        help="Path to the analysis results JSON file",
    )
    parser.add_argument(
        "--n_clusters",
        type=int,
        default=5,
        help="Number of clusters for k-means",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="results/cluster_results",
        help="Directory to save clustering results",
    )
    return parser.parse_args()


def load_analysis_results(file_path):
    """Load and parse the analysis results JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def clean_text(text):
    """Clean text by replacing 'and' with commas and standardizing separators."""
    # Replace 'and' with commas
    text = text.replace(" and ", ", ")
    # Standardize multiple spaces and commas
    text = " ".join(text.split())
    text = ", ".join(filter(None, (x.strip() for x in text.split(","))))
    return text.lower()


def extract_features(analysis_results):
    """Extract features from analysis results for clustering."""
    # Initialize feature extractors for each characteristic with different max_features
    vectorizers = {
        # Primary features (higher weight)
        "architectural_style": TfidfVectorizer(max_features=25),
        "futuristic_elements": TfidfVectorizer(max_features=25),
        "mood": TfidfVectorizer(max_features=15),
        # Secondary features (lower weight)
        "color_palette": TfidfVectorizer(max_features=10),
        "dominant_materials": TfidfVectorizer(max_features=10),
    }

    # Feature weights
    feature_weights = {
        "architectural_style": 1.5,
        "futuristic_elements": 1.5,
        "mood": 1.2,
        "color_palette": 0.7,
        "dominant_materials": 0.7,
    }

    # Prepare separate text lists for each characteristic
    feature_texts = {feature: [] for feature in vectorizers.keys()}

    # Extract and clean texts for each feature
    for result in analysis_results:
        analysis = json.loads(result["analysis"])
        for feature in vectorizers.keys():
            cleaned_text = clean_text(analysis[feature])
            feature_texts[feature].append(cleaned_text)

    # Transform each feature separately and apply weights
    feature_matrices = {}
    feature_names = {}
    for feature, vectorizer in vectorizers.items():
        # Transform text to TF-IDF matrix
        feature_matrix = vectorizer.fit_transform(feature_texts[feature]).toarray()
        # Apply feature weight
        feature_matrix *= feature_weights[feature]
        feature_matrices[feature] = feature_matrix
        feature_names[feature] = vectorizer.get_feature_names_out()

    # Combine all feature matrices horizontally
    combined_matrix = np.hstack(
        [feature_matrices[feature] for feature in vectorizers.keys()]
    )

    # Create combined feature names with prefixes
    all_feature_names = []
    for feature, names in feature_names.items():
        all_feature_names.extend([f"{feature}_{name}" for name in names])

    return combined_matrix, all_feature_names


def perform_clustering(features, n_clusters):
    """Perform k-means clustering on the features."""
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # Perform k-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(scaled_features)

    return cluster_labels, kmeans.cluster_centers_


def analyze_clusters(analysis_results, cluster_labels, feature_names, n_clusters):
    """Analyze the characteristics of each cluster."""
    cluster_info = defaultdict(list)

    # Group images by cluster
    for i, (result, label) in enumerate(zip(analysis_results, cluster_labels)):
        analysis = json.loads(result["analysis"])
        cluster_info[label].append(
            {
                "path": result["original_path"],
                "label": analysis["short_descriptive_label"],
                "style": analysis["architectural_style"],
                "elements": analysis["futuristic_elements"],
                "materials": analysis["dominant_materials"],
                "mood": analysis["mood"],
                "color": analysis["color_palette"],
            }
        )

    # Generate cluster summaries
    cluster_summaries = {}
    for cluster in range(n_clusters):
        images = cluster_info[cluster]
        cluster_summaries[cluster] = {
            "size": len(images),
            "common_labels": list(set(img["label"] for img in images)),
            "common_styles": list(set(img["style"] for img in images)),
            "common_elements": list(set(img["elements"] for img in images)),
            "common_materials": list(set(img["materials"] for img in images)),
            "common_moods": list(set(img["mood"] for img in images)),
            "common_colors": list(set(img["color"] for img in images)),
            "sample_paths": [img["path"] for img in images[:3]],
        }

    return cluster_summaries


def visualize_clusters(features, cluster_labels, output_dir, feature_names):
    """Create visualizations of the clustering results."""
    os.makedirs(output_dir, exist_ok=True)

    # Reduce dimensionality for visualization using PCA
    from sklearn.decomposition import PCA

    pca = PCA(n_components=2)
    features_2d = pca.fit_transform(features)

    # Create scatter plot
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(
        features_2d[:, 0],
        features_2d[:, 1],
        c=cluster_labels,
        cmap="viridis",
        alpha=0.6,
    )
    plt.title("Cluster Visualization (PCA)")
    plt.xlabel("First Principal Component")
    plt.ylabel("Second Principal Component")
    plt.colorbar(scatter, label="Cluster")

    # Add cluster centers
    centers_2d = PCA(n_components=2).fit_transform(
        KMeans(n_clusters=len(set(cluster_labels))).fit(features).cluster_centers_
    )
    plt.scatter(
        centers_2d[:, 0],
        centers_2d[:, 1],
        c="red",
        marker="x",
        s=200,
        linewidths=3,
        label="Cluster Centers",
    )
    plt.legend()

    plt.savefig(
        os.path.join(output_dir, "cluster_visualization.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    # Create feature importance visualization
    plt.figure(figsize=(15, 8))
    pca_components = abs(pca.components_)
    feature_importance = np.sum(pca_components, axis=0)
    sorted_idx = np.argsort(feature_importance)
    pos = np.arange(sorted_idx.shape[0]) + 0.5

    # Plot top 30 most important features
    top_n = min(30, len(feature_names))  # Ensure we don't exceed the number of features
    plt.barh(pos[-top_n:], feature_importance[sorted_idx][-top_n:])
    plt.yticks(pos[-top_n:], np.array(feature_names)[sorted_idx][-top_n:], fontsize=8)
    plt.xlabel("Feature Importance Score")
    plt.title("Top Features Contributing to Clustering")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "feature_importance.png"), dpi=300, bbox_inches="tight"
    )
    plt.close()


def save_results(cluster_summaries, output_dir):
    """Save clustering results to a file."""
    output_file = os.path.join(output_dir, "cluster_analysis_results.json")
    with open(output_file, "w") as f:
        json.dump(cluster_summaries, f, indent=2)


def main():
    args = parse_arguments()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load analysis results
    print("Loading analysis results...")
    analysis_results = load_analysis_results(args.input_file)

    # Extract features
    print("Extracting features...")
    features, feature_names = extract_features(analysis_results)

    # Perform clustering
    print(f"Performing k-means clustering with {args.n_clusters} clusters...")
    cluster_labels, cluster_centers = perform_clustering(features, args.n_clusters)

    # Analyze clusters
    print("Analyzing clusters...")
    cluster_summaries = analyze_clusters(
        analysis_results, cluster_labels, feature_names, args.n_clusters
    )

    # Visualize results
    print("Creating visualizations...")
    visualize_clusters(features, cluster_labels, args.output_dir, feature_names)

    # Save results
    print("Saving results...")
    save_results(cluster_summaries, args.output_dir)

    print(f"\nClustering analysis complete! Results saved in {args.output_dir}")
    print(f"Found {len(cluster_summaries)} clusters with the following distribution:")
    for cluster, info in cluster_summaries.items():
        print(f"Cluster {cluster}: {info['size']} images")


if __name__ == "__main__":
    main()
