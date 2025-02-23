import requests
import json
import time

# Base URL - replace with your actual server URL
BASE_URL = "http://localhost:5000"  # Change this to match your server

def test_query_outline():
    """Test the query outline endpoint"""
    print("\n=== Testing Query Outline API ===")
    task_id = "test_task_123"  # Replace with an actual task ID
    response = requests.get(f"{BASE_URL}/query_outline", params={"task_id": task_id})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_query_document():
    """Test the query document endpoint"""
    print("\n=== Testing Query Document API ===")
    task_id = "test_task_123"  # Replace with an actual task ID
    # Test with different formats
    formats = ["text", "html", "markdown"]
    for format_type in formats:
        print(f"\nTesting format: {format_type}")
        response = requests.get(
            f"{BASE_URL}/query_document",
            params={"task_id": task_id, "format": format_type}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_generate_outline():
    """Test the generate outline endpoint"""
    print("\n=== Testing Generate Outline API ===")
    # You can customize the request data based on your needs
    data = {
        "project_name": "测试项目",
        "project_type": "软件开发"
    }
    response = requests.post(f"{BASE_URL}/generate_outline", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_create_outline_v1():
    """Test the create outline v1 endpoint"""
    print("\n=== Testing Create Outline V1 API ===")
    # You can customize the request data based on your needs
    data = {
        "project_name": "测试项目",
        "project_type": "软件开发"
    }
    response = requests.post(f"{BASE_URL}/api/v1/outline", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def main():
    """Run all API tests"""
    try:
        # Test all endpoints
        test_query_outline()
        test_query_document()
        test_generate_outline()
        test_create_outline_v1()
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Please make sure the server is running.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
