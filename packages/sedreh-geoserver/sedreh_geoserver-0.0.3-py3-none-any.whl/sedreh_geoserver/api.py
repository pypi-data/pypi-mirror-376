import requests
from requests.auth import HTTPBasicAuth


class GeoserverManager:
    def __init__(self, geoserver_username: str, geoserver_password: str, geoserver_url: str) -> None:
        self.auth = HTTPBasicAuth(geoserver_username, geoserver_password)
        self.geoserver_url = geoserver_url

    def check_or_create_workspace(self, workspace: str) -> None:
        """Check if a GeoServer workspace exists; if not, create it."""
        check_url = f"{self.geoserver_url}/workspaces/{workspace}"
        headers = {"Accept": "application/json"}

        response = requests.get(check_url, headers=headers, auth=self.auth)

        if response.status_code == 200:
            print(f"Workspace '{workspace}' already exists.")
            return
        if response.status_code == 404:
            # Workspace does not exist, so create it
            create_url = f"{self.geoserver_url}/workspaces"
            headers = {"Content-type": "application/xml"}
            workspace_xml = f"<workspace><name>{workspace}</name></workspace>"

            create_response = requests.post(create_url, headers=headers, data=workspace_xml, auth=self.auth)

            if create_response.status_code not in [200, 201]:
                raise Exception(f"Failed to create workspace '{workspace}': {create_response.text}")
        else:
            raise Exception(f"Error checking workspace '{workspace}': {response.status_code} - {response.text}")

    def create_layer_with_store(self, workspace: str, store_name: str, minio_path: str) -> None:
        """Create a GeoServer store if it doesn't already exist."""

        request_url = f"{self.geoserver_url}/workspaces/{workspace}/coveragestores"
        headers = {"content-type": "application/xml"}
        store_xml = f"""<coverageStore><name>{store_name}</name><type>GeoTIFF</type><enabled>true</enabled><workspace>{workspace}</workspace><url>{minio_path}</url><metadata><entry key="CogSettings.Key"><cogSettings><useCachingStream>false</useCachingStream><rangeReaderSettings>HTTP</rangeReaderSettings></cogSettings></entry></metadata></coverageStore>"""
        try:
            requests.post(request_url, headers=headers, data=store_xml, auth=self.auth)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create store: {e}")

    def publish_layer(self, workspace: str, store_name: str) -> None:
        """Publish a layer in GeoServer."""

        request_url = f"{self.geoserver_url}/workspaces/{workspace}/coveragestores/{store_name}/coverages/"
        headers = {"content-type": "application/xml"}
        layer_xml = f"""<coverage><name>{store_name}</name><title>{store_name}</title><nativeName>geotiff_coverage</nativeName><enabled>true</enabled></coverage>"""
        try:
            create_layer_response = requests.post(request_url, headers=headers, data=layer_xml, auth=self.auth)
            if not create_layer_response.status_code == 201:
                raise Exception(f"Failed to publish layer: {create_layer_response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create layer: {e}")
