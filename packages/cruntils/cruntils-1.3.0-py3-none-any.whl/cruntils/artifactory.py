
# Core Python.
import os

# 3rd party.
import requests

class Artifactory:
    """Class for interfacing with Artifactory"""

    def __init__(self, username: str = "", password: str = ""):
        self.username = username
        self.password = password

    def deploy_artifact(self, path: str, url: str):
        """Deploy and artifact to Artifactory.

        https://jfrog.com/help/r/jfrog-rest-apis/deploy-artifact

        path: The path to the file to upload.

        url: The URL at which to place the file.
        """

        # Check if the file exists.
        if not(os.path.isfile(path)):
            print(f"File '{path}' does not exist, nothing to upload.")
            return

        # Attempt to upload the file.
        # By providing the file handle instead of reading the data ourselves,
        # requests will stream the data for us.
        with open(path, "rb") as file:
            response = requests.put(
                url,
                data = file,
                verify=False,
                auth=(self.username, self.password)
            )

    def retrieve_artifact(self, url: str):
        """Download a file from Artifactory.

        https://jfrog.com/help/r/jfrog-rest-apis/retrieve-artifact

        url: The URL of the file to download.
        """

        # Check artifact exists and get size.
        chunk_size = 8192
        file_info = self.get_file_info(url)
        if file_info != None:
            file_size = int(file_info["size"])
            if file_size < chunk_size:
                chunk_size = file_size

        # Get name of local file to save as.
        url_parts = url.split("/")
        file_name = url_parts[-1]

        # Attempt to download the file.
        with requests.get(
            url,
            verify=False,
            auth=(self.username, self.password),
            stream=True
        ) as response:
            
            # If an error occurred, raise it.
            response.raise_for_status()

            # Open local file to write to.
            with open(file_name, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

    def get_file_info(self, url: str):
        """Get Artifact file info"""

        # Replace artifact url with API storage URL.
        url = url.replace("artifactory/", "artifactory/api/storage/")

        # Request the file info.
        response = requests.get(
            url,
            verify=False,
            auth=(self.username, self.password),
        )

        # Return.
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Could not get file information for:\n{url}\nHTTP response code: {response.status_code}\n{response.text}")
            return None
