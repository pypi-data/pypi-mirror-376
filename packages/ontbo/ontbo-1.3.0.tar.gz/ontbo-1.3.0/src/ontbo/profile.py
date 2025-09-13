from typing import List, Union
from urllib.parse import urljoin

from ontbo.i_ontbo_server import IOntboServer
from ontbo.scene import Scene
from ontbo.update_status import UpdateStatus
from ontbo.query_type import QueryType

import requests


class Profile:
    """
    Represents a user profile on the Ontbo server.

    Profiles represent a single individual (typically a user of the host system).
    Profiles can be created by calling:
        Ontbo.profile(profile_id)
    """

    def __init__(self, server: IOntboServer, id: str):
        """
        Initialize a Profile instance.

        Args:
            server (IOntboServer): The Ontbo server connection.
            id (str): The unique profile ID.
        """
        self._server = server
        self._id = id

    @property
    def id(self) -> str:
        """
        str: The profile UID.
        """
        return self._id

    @property
    def scene_ids(self) -> List[str]:
        """
        Retrieve the list of scene IDs associated with the current profile.

        Returns:
            List[str]: A list of scene IDs.
        """
        response = requests.get(
            urljoin(self._server.url, f"profiles/{self._id}/scenes"),
            headers=self._server.headers,
        )
        response.raise_for_status()
        return response.json()

    def scene(self, scene_id: str) -> Scene:
        """
        Create a Scene object for the given ID (does not fetch data yet).

        Args:
            scene_id (str): The scene identifier.

        Returns:
            Scene: The Scene object.
        """
        return Scene(self._server, self.id, scene_id)

    def create_scene(self, requested_id: str = "scene") -> Scene:
        """
        Create a new scene for the current profile.

        Args:
            requested_id (str, optional): The desired ID for the new scene.
                                          Defaults to "scene".

        Returns:
            Scene: The newly created Scene.
        """
        if not requested_id:
            requested_id = "scene"

        response = requests.post(
            urljoin(self._server.url, f"profiles/{self._id}/scenes"),
            params={"requested_id": requested_id},
            headers=self._server.headers,
        )
        response.raise_for_status()
        return Scene(self._server, self.id, response.json()["id"])

    def delete_scene(self, scene_id: str) -> bool:
        """
        Delete a scene from the server.

        Args:
            scene_id (str): The unique identifier of the scene to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        response = requests.delete(
            urljoin(self._server.url, f"profiles/{self._id}/scenes/{scene_id}"),
            headers=self._server.headers,
        )
        return response.status_code == 200

    def update(self) -> UpdateStatus:
        """
        Request an update of the profile by parsing recently uploaded scenes.

        Returns:
            UpdateStatus: The current update status.
        """
        response = requests.put(
            urljoin(self._server.url, f"profiles/{self._id}/update/run"),
            headers=self._server.headers,
        )
        response.raise_for_status()
        return UpdateStatus(response.json()["status"])

    def stop_update(self) -> UpdateStatus:
        """
        Stop the current profile update.

        Returns:
            UpdateStatus: The current update status after stopping.
        """
        response = requests.put(
            urljoin(self._server.url, f"profiles/{self._id}/update/stop"),
            headers=self._server.headers,
        )
        response.raise_for_status()
        return UpdateStatus(response.json())

    def update_status(self) -> UpdateStatus:
        """
        Get the current computation status of an ongoing profile update.

        Returns:
            UpdateStatus: The current update status.
        """
        response = requests.get(
            urljoin(self._server.url, f"profiles/{self._id}/update/status"),
            headers=self._server.headers,
        )
        response.raise_for_status()
        return UpdateStatus(response.json())

    def list_facts(
        self,
        fields: List[str] = ["id"],
        skip_items: int = 0,
        max_items: int = 0,
    ) -> List[dict]:
        """
        List all facts for the profile.

        Args:
            fields (List[str]): Fields to return for each fact.
                                Possible values: "id", "data", "timestamp", "source".
            skip_items (int): Skip the first N results (pagination).
            max_items (int): Limit the number of returned facts (0 = no limit).

        Returns:
            List[dict]: A list of facts.
        """
        response = requests.get(
            urljoin(self._server.url, f"profiles/{self._id}/facts"),
            params={"fields": fields, "skip_items": skip_items, "max_items": max_items},
            headers=self._server.headers,
        )
        response.raise_for_status()
        return response.json()

    def query_facts(
        self,
        query: str,
        query_type: QueryType = QueryType.FULL_DATA,
    ) -> str:
        """
        Ask a natural language question against the profile facts database.

        Args:
            query (str): The question.
            query_type (QueryType): The retrieval method.

        Returns:
            str: The answer string.
        """
        response = requests.get(
            urljoin(self._server.url, f"profiles/{self._id}/facts/query"),
            params={"query": query, "query_type": query_type.value},
            headers=self._server.headers,
        )
        response.raise_for_status()
        return response.json()["result"]

    def append_facts(self, feedback: str, source_id: str = "") -> None:
        """
        Append a new fact to the profile.

        Args:
            feedback (str): The fact text or feedback string.
            source_id (str): (Optional) The source identifier.
        """
        response = requests.post(
            urljoin(self._server.url, f"profiles/{self._id}/facts"),
            params={"feedback": feedback, "source_id": source_id},
            headers=self._server.headers,
        )
        response.raise_for_status()

    def get_fact_details(self, fact_id: str) -> dict:
        """
        Retrieve detailed information about a specific fact.

        Args:
            fact_id (str): The UID of the fact.

        Returns:
            dict: The fact details.
        """
        response = requests.get(
            urljoin(self._server.url, f"profiles/{self._id}/facts/{fact_id}"),
            headers=self._server.headers,
        )
        response.raise_for_status()
        return response.json()

    def delete_fact(self, fact_id: str) -> bool:
        """
        Delete a fact from the profile.

        Args:
            fact_id (str): The UID of the fact.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        response = requests.delete(
            urljoin(self._server.url, f"profiles/{self._id}/facts/{fact_id}"),
            headers=self._server.headers,
        )
        return response.status_code == 200

    def build_context(self, query: str) -> str:
        """
        Build a context string with relevant profile information for a query.

        Args:
            query (str): The user query.

        Returns:
            str: The contextual information string.
        """
        response = requests.get(
            urljoin(self._server.url, f"profiles/{self._id}/context"),
            params={"query": query},
            headers=self._server.headers,
        )
        response.raise_for_status()
        return response.json()["result"]

    def find_in_scenes(self, query: str):
        """
        Search within all scenes of this profile.

        Note: Not yet implemented.
        """
        raise NotImplementedError("This method is not implemented yet.")
