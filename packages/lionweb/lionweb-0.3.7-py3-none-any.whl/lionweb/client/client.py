from typing import TYPE_CHECKING, List, Optional

import requests
from pydantic import BaseModel

from lionweb.lionweb_version import LionWebVersion
from lionweb.model.node import Node
from lionweb.serialization import create_standard_json_serialization
from lionweb.serialization.json_serialization import JsonSerialization
from lionweb.serialization.unavailable_node_policy import UnavailableNodePolicy

if TYPE_CHECKING:
    from lionweb.model import ClassifierInstance

    from .bulk_import import BulkImport


class RepositoryConfiguration(BaseModel):
    name: str
    lionweb_version: LionWebVersion
    history: bool


class Client:

    def __init__(
        self,
        lionweb_version=LionWebVersion.current_version(),
        server_url="http://localhost:3005",
        client_id="lwpython",
        repository_name: Optional[str] = "default",
        serialization: Optional[JsonSerialization] = None,
        unavailable_parent_policy: UnavailableNodePolicy = UnavailableNodePolicy.PROXY_NODES,
        unavailable_children_policy: UnavailableNodePolicy = UnavailableNodePolicy.PROXY_NODES,
    ):
        if not isinstance(client_id, str):
            raise ValueError(f"client_id should be a string, but it is {client_id}")
        if not isinstance(repository_name, str):
            raise ValueError(
                f"repository_name should be a string, but it is {repository_name}"
            )
        self._lionweb_version = lionweb_version
        self._server_url = server_url
        self._client_id = client_id
        self._repository_name = repository_name
        if serialization is None:
            self._serialization = create_standard_json_serialization(
                self._lionweb_version
            )
        else:
            self._serialization = serialization
        self._serialization.unavailable_parent_policy = unavailable_parent_policy
        self._serialization.unavailable_children_policy = unavailable_children_policy

    def serialization(self) -> JsonSerialization:
        return self._serialization

    def set_repository_name(self, repository_name):
        self._repository_name = repository_name

    #####################################################
    # DB Admin APIs                                     #
    #####################################################

    def create_database(self):
        url = f"{self._server_url}/createDatabase"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "clientId": self._client_id,
        }
        response = requests.post(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)

    def list_repositories(self):
        url = f"{self._server_url}/listRepositories"
        headers = {"Content-Type": "application/json"}
        query_params = {"clientId": self._client_id}
        response = requests.post(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)
        return [
            RepositoryConfiguration(
                name=r["name"],
                lionweb_version=LionWebVersion.from_value(r["lionweb_version"]),
                history=r["history"],
            )
            for r in response.json()["repositories"]
        ]

    def create_repository(self, repository_configuration: RepositoryConfiguration):
        url = f"{self._server_url}/createRepository"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "clientId": self._client_id,
            "repository": repository_configuration.name,
            "lionWebVersion": repository_configuration.lionweb_version.value,
            "history": str(repository_configuration.history).lower(),
        }
        response = requests.post(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)

    def delete_repository(self, repository_name: str):
        url = f"{self._server_url}/deleteRepository"
        headers = {"Content-Type": "application/json"}
        query_params = {"clientId": self._client_id, "repository": repository_name}
        response = requests.post(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)

    #####################################################
    # Bulk APIs                                         #
    #####################################################

    def list_partitions(self):
        url = f"{self._server_url}/bulk/listPartitions"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        response = requests.post(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)
        return response.json()["chunk"]["nodes"]

    def create_partition(self, node: Node):
        self.create_partitions([node])

    def create_partitions(self, nodes: List["Node"]):
        for n in nodes:
            if len(n.get_children(containment=None)) > 0:
                raise ValueError("Cannot store a node with children as a new partition")

        url = f"{self._server_url}/bulk/createPartitions"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        data = self._serialization.serialize_trees_to_json_element(nodes)
        response = requests.post(url, params=query_params, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)

    def delete_partitions(self, node_ids: List[str]):
        if len(node_ids) == 0:
            return

        url = f"{self._server_url}/bulk/deletePartitions"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        response = requests.post(
            url, params=query_params, json=node_ids, headers=headers
        )
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)

    def ids(self, count: Optional[int] = None) -> List[str]:
        url = f"{self._server_url}/bulk/ids"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        if count:
            query_params["count"] = str(count)
        response = requests.post(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)
        return response.json()["ids"]

    def store(self, nodes: List["ClassifierInstance"]):
        url = f"{self._server_url}/bulk/store"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        data = self._serialization.serialize_trees_to_json_element(nodes)
        response = requests.post(url, params=query_params, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)

    def retrieve(self, ids: List[str], depth_limit: Optional[int] = None):
        if not self._is_list_of_strings(ids):
            raise ValueError(f"ids should be a list of strings, but we got {ids}")
        data = self._retrieve_raw(ids, depth_limit=depth_limit)
        nodes = self._serialization.deserialize_json_to_nodes(data["chunk"])
        return nodes

    def _retrieve_raw(self, ids: List[str], depth_limit: Optional[int] = None):
        if not self._is_list_of_strings(ids):
            raise ValueError(f"ids should be a list of strings, but we got {ids}")
        url = f"{self._server_url}/bulk/retrieve"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        if depth_limit is not None:
            if not isinstance(depth_limit, int):
                raise ValueError(
                    f"depth_limit should be an int, but it is {depth_limit}"
                )
            query_params["depthLimit"] = str(depth_limit)
        response = requests.post(
            url, params=query_params, json={"ids": ids}, headers=headers
        )
        # Check response
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise ValueError("Error:", response.status_code, response.text)

    def _is_list_of_strings(self, value):
        return isinstance(value, list) and all(isinstance(item, str) for item in value)

    #####################################################
    # Inspection APIs                                   #
    #####################################################

    def nodes_by_classifier(self):
        url = f"{self._server_url}/inspection/nodesByClassifier"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        response = requests.get(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)
        # return an array of language, classifier, ids, size
        return response.json()

    def nodes_by_language(self):
        url = f"{self._server_url}/inspection/nodesByLanguage"
        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }
        response = requests.get(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)
        # return an array of language, ids, size
        return response.json()

    #####################################################
    # Convenience methods                               #
    #####################################################

    def retrieve_partition(self, id: str, depth_limit: Optional[int] = None):
        res = self.retrieve([id], depth_limit=depth_limit)
        roots = [n for n in res if res.get_parent() is None]
        if len(roots) != 1:
            raise ValueError()
        return roots[0]

    def retrieve_node(self, id: str, depth_limit: Optional[int] = None):
        from lionweb.model.impl.proxy_node import ProxyNode

        retrieved_nodes = self.retrieve([id], depth_limit=depth_limit)
        if not retrieved_nodes:
            raise ValueError(f"Node id {id} not found")
        roots = [
            n
            for n in retrieved_nodes
            if not isinstance(n, ProxyNode)
            and (n.get_parent() is None or isinstance(n.get_parent(), ProxyNode))
        ]
        if len(roots) != 1:
            raise ValueError(f"Expected one root, but found {len(roots)}")
        return roots[0]

    def get_ancestors_ids(self, node_id: str) -> List[str]:
        """
        Retrieve the list of ancestor node IDs for a given node ID.
        """
        result = []
        current_node_id: Optional[str] = node_id

        while current_node_id:
            current_node_id = self.get_parent_id(current_node_id)
            if current_node_id:
                result.append(current_node_id)

        return result

    def containing_partition_id(self, node_id: str) -> str:
        ancestors = self.get_ancestors_ids(node_id)
        if len(ancestors) == 0:
            return node_id
        else:
            return ancestors[-1]

    def get_parent_id(self, node_id: str) -> Optional[str]:
        """
        Retrieve the parent node ID of a given node ID.
        """
        nodes = self._retrieve_raw([node_id], depth_limit=0)["chunk"]["nodes"]
        if len(nodes) != 1:
            raise ValueError()
        node = nodes[0]
        return node["parent"]

    #####################################################
    # Additional APIs                                   #
    #####################################################

    def bulk_import_using_json(self, bulk_import: "BulkImport"):

        body_attach_points = []

        for attach_point in bulk_import.get_attach_points():
            j_containment = {
                "language": attach_point.containment.language,
                "version": attach_point.containment.version,
                "key": attach_point.containment.key,
            }
            j_el = {
                "container": attach_point.container,
                "root": attach_point.root_id,
                "containment": j_containment,
            }
            body_attach_points.append(j_el)

        from lionweb.serialization import LowLevelJsonSerialization

        serialized_chunk_as_json = (
            LowLevelJsonSerialization().serialize_to_json_element(
                LowLevelJsonSerialization.group_nodes_into_serialization_block(
                    bulk_import.get_nodes(), self._lionweb_version
                )
            )
        )

        body_nodes = serialized_chunk_as_json["nodes"]
        body = {"attachPoints": body_attach_points, "nodes": body_nodes}

        headers = {"Content-Type": "application/json"}
        query_params = {
            "repository": self._repository_name,
            "clientId": self._client_id,
        }

        url = f"{self._server_url}/additional/bulkImport"
        response = requests.post(url, params=query_params, json=body, headers=headers)
        if response.status_code != 200:
            raise ValueError("Error:", response.status_code, response.text)
