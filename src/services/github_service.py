"""GitHub API Service"""

import base64
from typing import Optional, Dict, Any
import requests

from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()


class GitHubService:
    """Manages GitHub API interactions"""
    
    def __init__(self):
        self.token = config.GITHUB_TOKEN
        self.owner = config.GITHUB_OWNER
        self.repo = config.GITHUB_REPO
        self.api_url = config.GITHUB_API_URL
        self.timeout = config.GITHUB_TIMEOUT
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
    
    def get_file(self, path: str) -> Optional[Dict[str, Any]]:
        """Get file content and SHA from GitHub"""
        url = f"{self.api_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                logger.debug(f"Successfully fetched file: {path}")
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"GitHub error {response.status_code}: {response.text}")
                return None
                
        except requests.Timeout:
            logger.error(f"Timeout fetching file: {path}")
            return None
        except Exception as e:
            logger.error(f"Error getting file {path}: {e}")
            return None
    
    def read_file_content(self, path: str) -> Optional[str]:
        """Read file content from GitHub"""
        file_data = self.get_file(path)
        
        if not file_data:
            return None
        
        try:
            content = base64.b64decode(file_data["content"]).decode()
            logger.debug(f"Successfully decoded file: {path}")
            return content
        except Exception as e:
            logger.error(f"Error decoding file {path}: {e}")
            return None
    
    def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        sha: Optional[str] = None
    ) -> bool:
        """Create or update file on GitHub"""
        url = f"{self.api_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        
        # Encode content to base64
        encoded_content = base64.b64encode(content.encode()).decode()
        
        payload = {
            "message": message,
            "content": encoded_content,
        }
        
        if sha:
            payload["sha"] = sha
        
        try:
            response = requests.put(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully updated file: {path}")
                return True
            else:
                logger.error(f"GitHub error {response.status_code}: {response.text}")
                return False
                
        except requests.Timeout:
            logger.error(f"Timeout updating file: {path}")
            return False
        except Exception as e:
            logger.error(f"Error updating file {path}: {e}")
            return False
    
    def list_folder(self, path: str = "") -> Optional[list]:
        """List contents of a directory in the repo"""
        url = f"{self.api_url}/repos/{self.owner}/{self.repo}/contents/{path}"

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)

            if response.status_code == 200:
                items = response.json()
                logger.debug(f"Listed folder '{path}': {len(items)} items")
                return items
            elif response.status_code == 404:
                logger.warning(f"Folder not found: {path}")
                return None
            else:
                logger.error(f"GitHub error {response.status_code}: {response.text}")
                return None

        except requests.Timeout:
            logger.error(f"Timeout listing folder: {path}")
            return None
        except Exception as e:
            logger.error(f"Error listing folder {path}: {e}")
            return None

    def delete_file(self, path: str, message: str, sha: str) -> bool:
        """Delete file from GitHub"""
        url = f"{self.api_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        
        payload = {
            "message": message,
            "sha": sha,
        }
        
        try:
            response = requests.delete(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted file: {path}")
                return True
            else:
                logger.error(f"GitHub error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False
