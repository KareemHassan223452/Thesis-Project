import requests
import json

# Test data
test_code = """function selectBillingOptions() {

}"""

# Make the request
response = requests.post(
    "http://localhost:8000/predict",
    json={"code": test_code}
)

# Print the response
print("Status Code:", response.status_code)
print("Response:", response.json()) 