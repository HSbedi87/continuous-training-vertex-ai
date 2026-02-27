import sys
import os
import json
import base64
import pytest
from unittest.mock import patch, MagicMock

# Add functions directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../functions")))

# Our target is the submit_pipeline Cloud Function
from submit_pipeline.main import main

def test_submit_pipeline_success():
    """
    Test that the Cloud Function successfully parses a base64 encoded Pub/Sub message
    and extracts the required pipeline parameters.
    """
    # Create the mock payload exactly as pub/sub delivers it
    mock_request_data = {
        "project_id": "test-project",
        "location": "us-central1",
        "pipeline_root": "gs://test-bucket/pipeline_root",
        "pipeline_parameters": {"job_name": "test"},
        "persistent_resource_name": "projects/123/locations/us/persistentResources/test",
        "pipeline_template_path": "us-docker.pkg.dev/project/repo/pipeline",
        "service_account": "test@gserviceaccount.com",
        "enable_caching": False
    }
    
    # Base64 encode the JSON string as expected by Cloud Events from Pub/Sub
    json_str = json.dumps(mock_request_data)
    encoded_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    
    # Mock CloudEvent structure
    class MockCloudEvent:
        def __init__(self, data):
            self.data = data

    mock_event = MockCloudEvent({"message": {"data": encoded_data}})

    # Patch the actual submission function so we don't try to call Vertex AI
    with patch("submit_pipeline.main.submit_pipeline_job.submit_pipeline_job_with_persistent_resource") as mock_submit:
        # Call the cloud function handler
        response, status_code = main(mock_event)
        
        # Verify success
        assert status_code == 200
        assert "Pipeline job submitted successfully" in response
        
        # Verify it successfully decoded and passed the right params
        mock_submit.assert_called_once_with(
            project_id="test-project",
            location="us-central1",
            pipeline_root="gs://test-bucket/pipeline_root",
            pipeline_parameters={"job_name": "test"},
            pipeline_template_path="us-docker.pkg.dev/project/repo/pipeline",
            service_account="test@gserviceaccount.com",
            enable_caching=False,
            persistent_resource_name="projects/123/locations/us/persistentResources/test"
        )

def test_submit_pipeline_missing_params():
    """
    Test that the Cloud Function correctly throws a 500 error if 
    required parameters are missing from the payload.
    """
    # Missing 'project_id'
    mock_request_data = {
        "location": "us-central1",
        "pipeline_root": "gs://test-bucket/pipeline_root"
    }
    
    json_str = json.dumps(mock_request_data)
    encoded_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    mock_event = MagicMock()
    mock_event.data = {"message": {"data": encoded_data}}

    # Call the cloud function handler
    response, status_code = main(mock_event)
    
    # Verify the error is caught
    assert status_code == 500
    assert "Missing required parameters" in response
