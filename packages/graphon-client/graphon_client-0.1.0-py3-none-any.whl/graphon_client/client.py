# graphon_client.py
import os
import time
import requests

API_BASE_URL = "https://indexer-api-485250924682.us-central1.run.app"

class GraphonClient:
    """A client library for interacting with the Graphon API."""

    def __init__(self, token: str):
        """
        Initializes the client with an API token and the base URL of the service.
        """
        #if not token or not api_base_url:
        #    raise ValueError("API token and base URL are required.")
        
        api_base_url = API_BASE_URL
        self.api_base_url = api_base_url.rstrip('/')
        self._headers = {"Authorization": f"Bearer {token}"}

    def index(self, video_file_path: str, show_progress: bool = True, detailed: bool = False) -> str:
        """
        Gets a signed URL, uploads a video directly to GCS, and starts the indexing job.
        """
        if not os.path.exists(video_file_path):
            raise FileNotFoundError(f"Video file not found at: {video_file_path}")

        file_name = os.path.basename(video_file_path)

        # --- Step 1: Get the Signed URL from our API ---
        if show_progress:
            print("Requesting secure upload URL...")
        
        url_payload = {"filename": file_name}
        get_url_endpoint = f"{self.api_base_url}/generate-upload-url"
        response = requests.post(get_url_endpoint, headers=self._headers, json=url_payload)
        response.raise_for_status()
        
        upload_info = response.json()
        signed_url = upload_info['signed_url']
        gcs_path = upload_info['gcs_path']

        # --- Step 2: Upload the file DIRECTLY to Google Cloud Storage ---
        if show_progress:
            print(f"Uploading {file_name} directly to GCS...")
        
        with open(video_file_path, 'rb') as f:
            # Note: No 'Authorization' header is needed here. The URL is the token.
            upload_headers = {'Content-Type': 'application/octet-stream'}
            upload_response = requests.put(signed_url, headers=upload_headers, data=f)
            upload_response.raise_for_status()

        if show_progress:
            print(f"✅ Video uploaded successfully. GCS path: {gcs_path}")

        # --- Step 3: Start the Indexing Job (as before) ---
        if show_progress:
            print("Starting indexing job...")
            
        start_url = f"{self.api_base_url}/start-indexing"
        start_payload = {"gcs_path": gcs_path, "detailed": detailed}
        response = requests.post(start_url, headers=self._headers, json=start_payload)
        response.raise_for_status()

        job_id = response.json()['job_id']
        if show_progress:
            print(f"✅ Job '{job_id}' started.")
            
        return job_id


    def get_status(self, job_id: str) -> dict:
        """
        Fetches the raw status of a job.

        Args:
            job_id: The ID of the job to check.

        Returns:
            A dictionary containing the job status details.
        """
        status_url = f"{self.api_base_url}/job-status/{job_id}"
        response = requests.get(status_url, headers=self._headers)

        if response.status_code == 404:
            return {"status": "NOT_FOUND"}
            
        response.raise_for_status() # Raise an exception for other bad statuses (500, etc.)
        return response.json()

    def query(self, job_id: str, query_text: str) -> dict:
        """
        Sends a query to a completed index.

        Args:
            job_id: The ID of the completed job.
            query_text: The question to ask the index.

        Returns:
            A dictionary containing the query result.
        """
        print(f"\nQuerying job '{job_id}' with: '{query_text}'")
        query_url = f"{self.api_base_url}/query"
        payload = {"job_id": job_id, "query": query_text}
        response = requests.post(query_url, headers=self._headers, json=payload)
        
        response.raise_for_status()
        return response.json()
        
    def wait_for_completion(self, job_id: str, poll_interval: int = 10):
        """
        Polls the job status until it is COMPLETED or FAILED.

        Args:
            job_id: The ID of the job to wait for.
            poll_interval: Seconds to wait between status checks.
        """
        print(f"\nWaiting for job '{job_id}' to complete (checking every {poll_interval}s)...")
        while True:
            status_data = self.get_status(job_id)
            current_status = status_data.get("status", "UNKNOWN")
            print(f"  -> Current status: {current_status}")

            if current_status == "COMPLETED":
                print("✅ Job completed!")
                return
            elif current_status == "FAILED":
                error_message = status_data.get('error', 'Unknown error')
                raise Exception(f"Job failed: {error_message}")
            
            time.sleep(poll_interval)