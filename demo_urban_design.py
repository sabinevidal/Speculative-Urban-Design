#!/usr/bin/env python
# Demo script to test the urban design generator functionality

import os
from dotenv import load_dotenv
from urban_design_generator import (
    generate_urban_design_from_random_location,
    generate_designs_for_specific_location,
)

# Load environment variables
load_dotenv()

# Check if required API keys are present
required_keys = ["RAPIDAPI_KEY", "GOOGLE_MAPS_API_KEY", "STABILITY_API_KEY"]
missing_keys = [key for key in required_keys if not os.getenv(key)]

if missing_keys:
    print("ERROR: The following API keys are missing from your .env file:")
    for key in missing_keys:
        print(f"  - {key}")
    print("\nPlease add them to your .env file and try again.")
    exit(1)


def test_random_location():
    """Test generating an urban design from a random location."""
    print("\n=== Testing Urban Design Generation from Random Location ===\n")

    result = generate_urban_design_from_random_location(strength=0.75, attempts=3)

    if result["success"]:
        print(f"SUCCESS: Generated urban design for {result['location']}")
        print(f"Latitude: {result['latitude']}, Longitude: {result['longitude']}")
        print(f"Original image: {result['original_image']}")
        print(f"Transformed images:")
        for img in result["transformed_images"]:
            print(f"  - {img}")
        print(f"Prompt used: {result['prompt']}")
    else:
        print(f"ERROR: {result['error']}")


def test_specific_location(
    query="Times Square, New York", multiple_views=True, num_views=2
):
    """Test generating urban designs for a specific location."""
    print(f"\n=== Testing Urban Design Generation for '{query}' ===\n")

    result = generate_designs_for_specific_location(
        search_query=query,
        strength=0.75,
        multiple_views=multiple_views,
        num_views=num_views,
    )

    if result["success"]:
        print(
            f"SUCCESS: Generated {len(result['results'])} urban designs for {result['location']}"
        )

        for i, view in enumerate(result["results"]):
            print(f"\nView {i+1} - Heading: {view['heading']}°")
            print(f"Original image: {view['original_image']}")
            print(f"Transformed images:")
            for img in view["transformed_images"]:
                print(f"  - {img}")
            print(f"Prompt used: {view['prompt']}")
    else:
        print(f"ERROR: {result['error']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test urban design generation functionality"
    )
    parser.add_argument(
        "--random", action="store_true", help="Test random location generation"
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Specific location to test (e.g., 'Times Square, New York')",
    )
    parser.add_argument(
        "--views",
        type=int,
        default=2,
        help="Number of views to generate for specific location",
    )

    args = parser.parse_args()

    if args.random:
        test_random_location()
    elif args.location:
        test_specific_location(query=args.location, num_views=args.views)
    else:
        # If no arguments provided, run both tests
        test_random_location()
        test_specific_location()
