import os
import random
import requests
import json
import base64
import io
import urllib.parse
import xml.etree.ElementTree as ET
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def verify_api_keys():
    """Verify that the required API keys are available."""
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set")

    return True


def get_random_coordinates():
    """
    Get random coordinates from the 3geonames API.

    Returns:
        dict: Dictionary containing latitude and longitude
    """
    try:
        # Make request to 3geonames API for random land coordinates
        response = requests.get("https://api.3geonames.org/?randomland=yes&json=1")
        response.raise_for_status()

        try:
            # Parse JSON response
            data = response.json()
            return {
                "latitude": data["major"]["latt"],
                "longitude": data["major"]["longt"],
                "name": data["major"]["name"],
            }
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            return None

        # return None
    except Exception as e:
        # Log the error but don't display it to the user
        print(f"Error getting random coordinates (this won't be shown to users): {e}")
        return None


def get_street_view_image(place=None, coordinates=None):
    """
    Get a Street View image for the given place or coordinates using Google Street View Static API.

    Args:
        place: String value of a place's name (optional if coordinates provided)
        coordinates: Dictionary containing latitude and longitude (optional if place provided)

    Returns:
        dict: Response containing image data or error
    """
    verify_api_keys()

    # Street View Static API URL
    url = "https://maps.googleapis.com/maps/api/streetview"

    # Generate random heading for variety
    heading = random.randint(0, 359)

    # Determine the location parameter
    if coordinates and "latitude" in coordinates and "longitude" in coordinates:
        # Use coordinates
        location = f"{coordinates['latitude']},{coordinates['longitude']}"
        loc_name = coordinates.get("name", f"Coordinates: {location}")
        latitude = coordinates["latitude"]
        longitude = coordinates["longitude"]
    elif place:
        # Use place string
        location = urllib.parse.quote(place)
        loc_name = place
        latitude = 0
        longitude = 0
    else:
        return {
            "success": False,
            "error": "Either place or coordinates must be provided",
        }

    # Parameters for the Street View request
    params = {
        "size": "600x400",  # Image size
        "location": location,  # Using either place string or coordinates
        "heading": heading,  # Random direction
        "key": GOOGLE_MAPS_API_KEY,  # API key
        "return_error_code": "true",  # Return error code instead of generic image
    }

    try:
        # Make the request
        print(url)
        print(params)

        # Build and print the full URL for debugging purposes
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_string}"
        print(f"Full request URL: {full_url}")

        response = requests.get(url, params=params)

        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response content length: {len(response.content)} bytes")

        # If we get an error response, try to extract more details
        if response.status_code != 200:
            print(
                f"Error response content: {response.content[:200]}"
            )  # Print first 200 chars of error response

        # Handle 404 errors (no imagery available)
        if response.status_code == 404:
            return {
                "success": False,
                "error": "No Street View imagery found at this location",
            }

        response.raise_for_status()  # Raise exception for other HTTP errors

        # Check if we got an actual image (not too small)
        if len(response.content) < 5000:  # Arbitrary size threshold
            return {
                "success": False,
                "error": "Image too small or placeholder received",
            }

        # Convert image to base64 for easier handling
        image_base64 = base64.b64encode(response.content).decode("utf-8")

        # Create a PIL Image object from the response
        image = Image.open(io.BytesIO(response.content))

        return {
            "success": True,
            "image_base64": image_base64,
            "image_pil": image,
            "latitude": latitude,
            "longitude": longitude,
            "heading": heading,
            "pitch": 0,
            "address": location,  # Use location string as address
            "name": loc_name,  # Use place or location name
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def save_street_view_image(image_data, output_dir, base_filename="street_view"):
    """
    Save Street View image to disk.

    Args:
        image_data: Dict containing image data from get_street_view_image
        output_dir: Directory to save image
        base_filename: Base name for the output file

    Returns:
        str: Path to the saved image
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with location info
    filename = f"{base_filename}_{image_data['latitude']}_{image_data['longitude']}_{image_data['heading']}.jpg"
    image_path = os.path.join(output_dir, filename)

    # Save the image
    image_data["image_pil"].save(image_path)

    return image_path


def find_random_urban_street_view(output_dir="streetview_images", attempts=5):
    """
    Find a random urban street view, save it, and return the image path.

    This function tries to find a valid street view by:
    1. Selecting a random urban location
    2. Getting a street view image at that location
    3. Retrying if any step fails (up to the specified number of attempts)
    4. Falling back to major city coordinates if random ones fail

    Args:
        output_dir: Directory to save the image
        attempts: Number of attempts to find a valid street view

    Returns:
        dict: Information about the street view, including image path if successful
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print(f"Attempting to find a random urban street view (max attempts: {attempts})")

    # First try with random coordinates
    for i in range(min(3, attempts)):
        print(f"\nAttempt {i+1}/{attempts} with random coordinates")
        coords = get_random_coordinates()
        if not coords:
            print("Failed to get random coordinates, trying next attempt")
            continue

        print(
            f"Got coordinates: {coords['latitude']}, {coords['longitude']} ({coords['name']})"
        )
        street_view = get_street_view_image(coordinates=coords)

        if street_view["success"]:
            print(f"Successfully found street view at {coords['name']}")
            # Save the image
            image_path = save_street_view_image(
                street_view,
                output_dir,
                f"street_view_{street_view['latitude']}_{street_view['longitude']}",
            )

            return {
                "success": True,
                "image_path": image_path,
                "location": street_view["name"],
                "latitude": street_view["latitude"],
                "longitude": street_view["longitude"],
                "heading": street_view["heading"],
                "pitch": street_view["pitch"],
            }
        else:
            print(
                f"Failed to get street view: {street_view.get('error', 'Unknown error')}"
            )

    # Fallback to known good locations
    print("\nRandom coordinates failed, trying fallback city coordinates")
    fallback_locations = [
        {"latitude": 40.714728, "longitude": -73.998672, "name": "Manhattan, NY"},
        {"latitude": 48.858370, "longitude": 2.294481, "name": "Paris, France"},
        {"latitude": 35.689487, "longitude": 139.691711, "name": "Tokyo, Japan"},
        {"latitude": 51.507351, "longitude": -0.127758, "name": "London, UK"},
        {"latitude": -33.868820, "longitude": 151.209296, "name": "Sydney, Australia"},
    ]

    for location in fallback_locations:
        print(f"\nTrying fallback location: {location['name']}")
        street_view = get_street_view_image(coordinates=location)

        if street_view["success"]:
            print(f"Successfully found street view at {location['name']}")
            # Save the image
            image_path = save_street_view_image(
                street_view,
                output_dir,
                f"street_view_{street_view['latitude']}_{street_view['longitude']}",
            )

            return {
                "success": True,
                "image_path": image_path,
                "location": street_view["name"],
                "latitude": street_view["latitude"],
                "longitude": street_view["longitude"],
                "heading": street_view["heading"],
                "pitch": street_view["pitch"],
            }
        else:
            print(
                f"Failed to get street view at {location['name']}: {street_view.get('error', 'Unknown error')}"
            )

    # If we've exhausted all attempts
    return {
        "success": False,
        "error": f"Failed to find a valid street view after {attempts} attempts",
    }


def test_api_key():
    """
    Test if the Google Maps API key is valid for Street View API by making a simple request.

    Returns:
        dict: Response indicating if the API key is valid for Street View
    """
    verify_api_keys()

    print(
        f"Using API key: {GOOGLE_MAPS_API_KEY[:5]}...{GOOGLE_MAPS_API_KEY[-5:] if GOOGLE_MAPS_API_KEY else 'None'}"
    )

    # Test with Street View API directly
    url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    params = {
        "location": "40.714728,-73.998672",  # Manhattan coordinates
        "key": GOOGLE_MAPS_API_KEY,
    }

    try:
        print(f"Sending request to: {url}")
        response = requests.get(url, params=params)
        print(f"Response status code: {response.status_code}")

        try:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
        except ValueError:
            print(f"Response content is not JSON. Content: {response.content[:200]}")
            data = {"status": "UNKNOWN"}

        if response.status_code == 200 and data.get("status") == "OK":
            return {
                "success": True,
                "message": "API key is valid for Street View",
                "data": data,
            }
        else:
            error_message = data.get(
                "error_message", f"Status: {data.get('status', 'Unknown')}"
            )
            return {
                "success": False,
                "error": f"API key validation failed for Street View: {error_message}",
            }
    except Exception as e:
        print(f"Exception details: {e}")
        return {"success": False, "error": f"Exception testing API key: {str(e)}"}


def test_street_view(latitude=40.714728, longitude=-73.998672):
    """
    Test the Street View API with known coordinates (default is Manhattan, NY).

    Args:
        latitude: Latitude for the test
        longitude: Longitude for the test

    Returns:
        dict: Response from the Street View API
    """
    print(f"Testing Street View API with coordinates: {latitude}, {longitude}")
    coordinates = {
        "latitude": latitude,
        "longitude": longitude,
        "name": "Test Location",
    }

    result = get_street_view_image(coordinates=coordinates)

    if result["success"]:
        print("Test successful! Street View image retrieved.")
    else:
        print(f"Test failed: {result.get('error', 'Unknown error')}")

    return result


if __name__ == "__main__":
    # If running this file directly, run the test functions
    print("Testing API key...")
    key_test = test_api_key()
    print(f"API key test result: {key_test['success']}")

    if key_test["success"]:
        print("\nTesting Street View API...")
        sv_test = test_street_view()
        print(f"Street View test result: {sv_test['success']}")

        if sv_test["success"]:
            print("\nTesting random urban street view finder...")
            # Create a test output directory
            test_dir = "test_images"
            random_view = find_random_urban_street_view(output_dir=test_dir, attempts=3)

            if random_view["success"]:
                print(
                    f"\nSuccess! Found and saved street view image at {random_view['location']}"
                )
                print(f"Image saved to: {random_view['image_path']}")
            else:
                print(
                    f"\nFailed to find random street view: {random_view.get('error', 'Unknown error')}"
                )
