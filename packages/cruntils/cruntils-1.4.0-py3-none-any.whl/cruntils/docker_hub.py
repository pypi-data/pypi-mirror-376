
"""
A script for downloading docker images without the use of a docker client.

Currently designed to work specifically with Docker Hub.

But the OCI distribution spec is a standard that should be implemented by
other image repositories. So, some of the code should be reusable.

I couldn't find a difinitive description of how to store an image on disk. I
cobbled together my understanding based on the resources listed below and a
manual inspection of the "docker image save" .tar format.

I used a few resources to figure this out:

- https://tech.michaelaltfield.net/2024/09/03/container-download-curl-wget/#docker-hub
    Initial inspiration.
    Of limited use since it's based on an older version of the API / standards.

- https://github.com/opencontainers/image-spec/releases
    OCI Image Specification.
    Downloaded as PDF.

- https://github.com/opencontainers/distribution-spec/releases
    OCI Distribution Specification.
    Downloaded as PDF.

Simple example usage:

# Establish instance.
dh = DockerHub()

# List image versions.
tag = "atlassian/jira-software"
ver = "10.4.1"
dh.list_versions(tag)

# List platform for specified tag / version.
dh.list_platforms(tag, ver)

# Pull the image to a local file.
dh.pull_image(
    tag,
    ver,
    "sha256:82029b36f9bcfb19c74a05b0d59048779bff98c8610471ec7feb92d28fcbe405"
)

"""

# Core Python.
import gzip
import hashlib
import json
import os
import shutil
import tarfile

# 3rd party.
import requests

class DockerHub:
    """
    Definitions:
        Tag: a custom, human-readable pointer to a manifest. A manifest digest
            may have zero, one, or many tags referencing it.
    """
    def __init__(self):
        self.server = "https://registry-1.docker.io/v2"
        self.json_token = None

    def _ensure_auth(self, tag):
        """Ensure we are correctly authorized"""

        # If we don't currently have a token, get one.
        if self.json_token == None:
            self._get_json_auth_token(tag)

    def _get_json_auth_token(self, tag):
        """Get a Docker Hub auth token for the given tag

        This could be expanded to cater for more types of authentication.
        """
        url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{tag}:pull"
        response = requests.get(url)
        self.json_token = response.json()

    def _get_token(self):
        return self.json_token["token"]

    def _authd_get(self, url: str, tag: str):
        """Convenience method to make an authenticated get to Docker Hub"""

        # Make sure we're correctly authorized.
        self._ensure_auth(tag)

        # Make the request.
        headers = {"Authorization": f"Bearer {self._get_token()}"}
        response = requests.get(url, headers = headers)

        # Handle errors.
        if response.status_code != 200:
            print(response.status_code)
            print(url)

        return response

    def _get_manifest(self, tag: str, id: str):
        """Get a manifest

        tag: The image tag.

        id: The manifest identifier. Can be a version or a hash.
        """
        url = f"{self.server}/{tag}/manifests/{id}"
        response = self._authd_get(url, tag)
        return response.json()

    def _get_blob(self, tag: str, id: str):
        """Get a blob

        tag: the image tag.

        id: the blob identifier.
        """
        url = f"{self.server}/{tag}/blobs/{id}"
        response = self._authd_get(url, tag)
        return response.content

    def _make_tree(self, tag: str, ver: str):
        """"""
        tree_root = f'{tag.replace("/", "__")}_{ver}'
        if os.path.isdir(tree_root):
            shutil.rmtree(tree_root)
        os.mkdir(tree_root)
        os.mkdir(f"{tree_root}/blobs")
        os.mkdir(f"{tree_root}/blobs/sha256")
        return tree_root

    def _make_oci(self, root):
        """Write the oci-layout file"""
        with open(f"{root}/oci-layout", "w") as ocifile:
            ocifile.write('{"imageLayoutVersion": "1.0.0"}')

    def _pull_layers(self, tag: str, image_manifest: dict, root: str):
        """Pull all layers in the manifest

        Gunzip layers (where required) and update manifest as we go.
        """
        for layer_json in image_manifest["layers"]:

            # Get blob data.
            blob_hash: str = layer_json["digest"]
            blob_hash_type, blob_hash_value = blob_hash.split(":")
            blob_data = self._get_blob(tag, blob_hash)

            # If it's gzipped, decompress it and update mediatype in json.
            if layer_json["mediaType"] == "application/vnd.oci.image.layer.v1.tar+gzip":
                layer_json["mediaType"] = "application/vnd.oci.image.layer.v1.tar"
                blob_data = gzip.decompress(blob_data)

            # Compute hash & size of blob data and update in json.
            layer_hash = hashlib.sha256(blob_data)
            layer_size = len(blob_data)
            layer_json["digest"] = f"sha256:{layer_hash.hexdigest()}"
            layer_json["size"] = layer_size

            # Write to blob file.
            with open(f"{root}/blobs/sha256/{layer_hash.hexdigest()}", "wb") as blob:
                blob.write(blob_data)

        # Return the updated image_manifest.
        return image_manifest

    def list_versions(self, tag):
        """Get the available tags for a given image.

        tag: the image tag e.g. atlassian/jira-software or postgres
        """

        # Get the list of versions.
        url = f"{self.server}/{tag}/tags/list"
        response = self._authd_get(url, tag)

        # Print them.
        for index, tag in enumerate(response.json()["tags"]):
            print(f"{index + 1}. {tag}")

    def list_platforms(self, tag: str, ver: str):
        """List the platforms available for the specified image tag version"""

        # Get the image index.
        image_index = self._get_manifest(tag, ver)
        if "manifests" in image_index:
            for index, manifest in enumerate(image_index["manifests"]):
                arch = manifest["platform"]["architecture"]
                opsys = manifest["platform"]["os"]
                digest = manifest["digest"]
                print(f"{index + 1}. {arch}/{opsys} - {digest}")

    def pull_image(self, tag: str, ver: str, platform_hash: str):
        """Pull the specified image from Docker Hub.

        tag: the image tag e.g. atlassian/jira-software or postgres

        ver: the version e.g. 10.4.1

        platform_hash: the hash digest for the requested image e.g.
            sha256:82029b36f9bcfb19c74a05b0d59048779bff98c8610471ec7feb92d28fcbe405
        """

        # Get the image index.
        image_index = self._get_manifest(tag, ver)

        # Get the image index section that has been requested.
        image_index_manifest_ref = None
        for manifest in image_index["manifests"]:
            if manifest["digest"] == platform_hash:
                image_index_manifest_ref = manifest
                break

        # Get the image manifest for the specified platform.
        image_manifest = self._get_manifest(tag, platform_hash)

        # Create a skeleton tree to store the image files in.
        tree_root = self._make_tree(tag, ver)

        # Make the oci-layout file.
        self._make_oci(tree_root)

        # Pull the image layers.
        image_manifest = self._pull_layers(tag, image_manifest, tree_root)

        # Write the image manifest.
        image_manifest_content = json.dumps(image_manifest, separators=(',', ':')).encode(encoding="utf-8")
        image_manifest_hash = hashlib.sha256(image_manifest_content)
        with open(f"{tree_root}/blobs/sha256/{image_manifest_hash.hexdigest()}", "wb") as image_manifest_file:
            image_manifest_file.write(image_manifest_content)

        # Write the image index to file.
        with open(f"{tree_root}/index.json", "w") as image_index_file:

            # Construct the content.
            image_index_json = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [
                    {
                        "mediaType": image_index_manifest_ref["mediaType"],
                        "digest": f"sha256:{image_manifest_hash.hexdigest()}",
                        "size": len(image_manifest_content)
                    }
                ]
            }

            # Not sure I need to do this.
            # Add annotations if there are any.
            # if "annotations" in plat_man:
            #     index_json["manifests"][0]["annotations"] = plat_man["annotations"]

            # Write to file.
            image_index_file.write(json.dumps(image_index_json, separators=(',', ':')))

        # Get the image config.
        image_config_blob_digest = image_manifest["config"]["digest"]
        image_config_blob_hash_type, image_config_blob_hash_value = image_config_blob_digest.split(":")
        image_config_data = self._get_blob(tag, image_config_blob_digest)

        # Write the image config file as a blob.
        with open(f"{tree_root}/blobs/{image_config_blob_hash_type}/{image_config_blob_hash_value}", "wb") as image_config_file:
            image_config_file.write(image_config_data)

        # Write the manifest.json file.
        layers_list = []
        layers_sources = {}
        for layer in image_manifest["layers"]:
            hash_digest = layer["digest"].replace("sha256:", "")
            layers_list.append(
                f'blobs/sha256/{hash_digest}'
            )
            layers_sources[layer["digest"]] = {
                "mediaType": layer["mediaType"],
                "size": layer["size"],
                "digest": layer["digest"],
            }
        manifest_json = [
            {
                "Config": f'blobs/{image_config_blob_digest.replace(":", "/")}',
                "RepoTags": [f"{tag}:{ver}"],
                "Layers": layers_list,
                "LayerSources": layers_sources
            }
        ]
        with open(f"{tree_root}/manifest.json", "w") as manifest_file:
            manifest_file.write(json.dumps(manifest_json, separators=(',', ':')))

        # Wrap image into tar.
        with tarfile.open(f"{tree_root}.tar", "w") as tar:
            tar.add(tree_root, arcname=os.path.sep)
