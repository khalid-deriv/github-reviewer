import requests
import time
from logger import setup_logger

# Initialize logger
logger = setup_logger()

class LLMWrapper:
    def __init__(self, backends, retry_attempts=3, retry_delay=2):
        """
        Initialize the LLM wrapper.

        Args:
            backends (list): A list of backend configurations. Each backend is a dictionary with keys:
                - `backend_name`: Name of the backend (e.g., "OpenAI", "Azure").
                - `token`: API token for the backend.
                - `model_name`: Model name to use.
                - `url`: API endpoint URL (optional, default depends on backend).
            retry_attempts (int): Number of retry attempts for failed requests.
            retry_delay (int): Delay (in seconds) between retries.
        """
        self.backends = backends
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

    def _make_request(self, backend, payload):
        """
        Make a request to the LLM backend.

        Args:
            backend (dict): Backend configuration.
            payload (dict): Request payload.

        Returns:
            dict: Response from the backend.

        Raises:
            Exception: If the request fails.
        """
        headers = {
            "Authorization": f"Bearer {backend['token']}",
            "Content-Type": "application/json"
        }
        url = backend.get("url", f"https://api.{backend['backend_name'].lower()}.com/v1/completions")
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.info(f"Attempting request to {backend['backend_name']} (Attempt {attempt})")
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Request to {backend['backend_name']} succeeded.")
                    return response.json()
                else:
                    logger.warning(f"Request to {backend['backend_name']} failed with status {response.status_code}: {response.text}")
            except requests.RequestException as e:
                logger.error(f"Request to {backend['backend_name']} failed: {e}")
            
            if attempt < self.retry_attempts:
                time.sleep(self.retry_delay)
        
        raise Exception(f"All attempts to {backend['backend_name']} failed.")

    def query(self, prompt, max_tokens=100, temperature=0.7, top_p=1.0):
        """
        Query the LLM backends.

        Args:
            prompt (str): The input prompt for the LLM.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature.
            top_p (float): Nucleus sampling parameter.

        Returns:
            dict: Response from the first successful backend.

        Raises:
            Exception: If all backends fail.
        """
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        for backend in self.backends:
            try:
                logger.info(f"Querying backend: {backend['backend_name']}")
                return self._make_request(backend, payload)
            except Exception as e:
                logger.error(f"Backend {backend['backend_name']} failed: {e}")
                logger.info("Switching to the next backend.")

        raise Exception("All backends failed to process the request.")
