
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# nsflow SDK Software in commercial settings.
#
# END COPYRIGHT
import os
import re
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from pyhocon import ConfigFactory

logging.basicConfig(level=logging.INFO)

# Define the registry directory and other constants
# Ensure the environment variable is set
# if not os.getenv("AGENT_MANIFEST_FILE"):
#     raise ValueError("Environment variable AGENT_MANIFEST_FILE is not set. "
#                      "Please set it to the path of the agent manifest file.")

AGENT_MANIFEST_FILE = os.getenv("AGENT_MANIFEST_FILE")
if not AGENT_MANIFEST_FILE:
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, "../../../../.."))
    AGENT_MANIFEST_FILE = os.path.join(ROOT_DIR, "registries", "manifest.hocon")

REGISTRY_DIR = os.path.dirname(AGENT_MANIFEST_FILE)
ROOT_DIR = os.path.dirname(REGISTRY_DIR)
CODED_TOOLS_DIR = os.path.join(ROOT_DIR, "coded_tools")
FIXTURES_DIR = os.path.join(ROOT_DIR, "tests", "fixtures")
TEST_NETWORK = os.path.join(FIXTURES_DIR, "test_network.hocon")


@dataclass
class AgentData:
    """Dataclass to encapsulate agent processing parameters."""
    agent: Dict
    nodes: List[Dict]
    edges: List[Dict]
    agent_details: Dict
    node_lookup: Dict
    parent: Optional[str] = None
    depth: int = 0


class AgentNetworkUtils:
    """
    Encapsulates utility methods for agent network operations.
    This class is to be used only for locally located hocon files.
    """

    def __init__(self):
        self.registry_dir = REGISTRY_DIR
        self.fixtures_dir = FIXTURES_DIR

    def get_test_manifest_path(self):
        """Returns the manifest.hocon path."""
        return os.path.join(self.fixtures_dir, "manifest.hocon")

    def get_network_file_path(self, network_name: str):
        """
        Securely returns the absolute path for a given agent network name.
        Validates to prevent directory traversal or malformed names.
        """
        # Step 1: Sanitize input to strip any path-like behavior
        sanitized_name = os.path.basename(network_name)

        # Step 2: Ensure only safe characters are used (alphanumeric, _, -)
        if not re.match(r'^[\w\-]+$', sanitized_name):
            raise HTTPException(status_code=400,
                                detail="Invalid network name. Only alphanumeric, underscores, and hyphens are allowed.")

        # Step 3: Build full path inside safe REGISTRY_DIR
        raw_path = os.path.join(REGISTRY_DIR, f"{sanitized_name}.hocon")

        # Step 4: Normalize and resolve to handle ../ or symlinks
        resolved_path = os.path.realpath(os.path.normpath(str(raw_path)))
        allowed_dir = os.path.realpath(str(REGISTRY_DIR))

        # Step 5: Ensure resolved path stays inside allowed dir
        if not resolved_path.startswith(allowed_dir + os.sep):
            raise HTTPException(status_code=403, detail="Access denied: Path is outside allowed directory")

        # Step 6: Check if file exists and is a file (not a directory)
        # final_path = Path(resolved_path)
        # if not final_path.is_file():
        #     raise HTTPException(status_code=404, detail=f"Network file not found: {sanitized_name}.hocon")

        return resolved_path

    def list_available_networks(self):
        """Lists available networks from the manifest file."""
        manifest_path = AGENT_MANIFEST_FILE
        if not os.path.exists(manifest_path):
            return {"networks": []}

        config = ConfigFactory.parse_file(str(manifest_path))
        networks = [
            os.path.splitext(os.path.basename(file))[0].replace('"', "").strip()
            for file, enabled in config.items()
            if enabled is True
        ]

        return {"networks": networks}

    @staticmethod
    def load_hocon_config(file_path: str, base_dir: str = ROOT_DIR):
        """
        Load a HOCON file from the given directory and parse it safely.
        Prevents path traversal by ensuring the resolved path stays within the base_dir.
        """
        try:
            # Ensure base_dir is an absolute, normalized path
            base_dir_str = os.path.abspath(str(base_dir))
            file_path_str = os.path.abspath(os.path.join(base_dir_str, str(file_path)))

            # Ensure the final path is inside base_dir
            if not file_path_str.startswith(base_dir_str + os.sep):
                raise HTTPException(status_code=403, detail="Access to this file is not allowed")

            # Now it is safe to use as a Path
            safe_path = file_path_str

            if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
                raise HTTPException(status_code=404, detail="Config file not found")

            # Safe to parse
            config = ConfigFactory.parse_file(str(safe_path))
            return config

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing HOCON: {str(e)}") from e

    def parse_agent_network(self, file_path: str):
        """Parses an agent network from a HOCON configuration file."""
        config = self.load_hocon_config(file_path)

        nodes = []
        edges = []
        agent_details = {}
        node_lookup = {}

        tools = config.get("tools", [])

        # Ensure all tools have a "command" key
        for tool in tools:
            if "command" not in tool:
                tool["command"] = ""

        # Build lookup dictionary for agents
        for tool in tools:
            agent_id = tool.get("name", "unknown_agent")
            node_lookup[agent_id] = tool

        front_man = self.find_front_man(file_path)

        if not front_man:
            raise HTTPException(status_code=400, detail="No front-man agent found in network.")

        agent_data = AgentData(front_man, nodes, edges, agent_details, node_lookup)
        self.process_agent(agent_data)

        return {"nodes": nodes, "edges": edges, "agent_details": agent_details}

    def find_front_man(self, file_path: str):
        """Finds the front-man agent from the tools list.
        1. First, check if an agent has a function **without parameters**.
        2. If all agents have parameters, **fallback to the first agent** in the HOCON file.
        """
        front_men: List[str] = []
        config = self.load_hocon_config(file_path)
        tools = config.get("tools", [])

        # Ensure all tools have a "command" key
        for tool in tools:
            if "command" not in tool:
                tool["command"] = ""

        # Try to find an agent with a function **without parameters**
        for tool in tools:
            if isinstance(tool.get("function"), dict) and "parameters" not in tool["function"]:
                front_men.append(tool)

        # If no such agent is found, fallback to the **first agent in HOCON**
        if tools:
            front_men.append(tools[0])

        if len(front_men) == 0:
            raise ValueError("No front-man found. "
                             "One entry's function must not have any parameters defined to be the front man")

        front_man = front_men[0]
        return front_man

    def process_agent(self, data: AgentData):
        """Recursively processes each agent in the network, capturing hierarchy details."""
        agent_id = data.agent.get("name", "unknown_agent")

        child_nodes = []
        dropdown_tools = []
        sub_networks = []  # Track sub-network tools

        for tool_name in data.agent.get("tools", []):
            if tool_name.startswith("/"):  # Identify sub-network tools
                sub_networks.append(tool_name.lstrip("/"))  # Remove leading `/`
            elif tool_name in data.node_lookup:
                child_agent = data.node_lookup[tool_name]
                if child_agent.get("class", "No class") == "No class":
                    child_nodes.append(tool_name)
                else:
                    dropdown_tools.append(tool_name)

        # Add the agent node
        data.nodes.append({
            "id": agent_id,
            "type": "agent",
            "data": {
                "label": agent_id,
                "depth": data.depth,
                "parent": data.parent,
                "children": child_nodes,
                "dropdown_tools": dropdown_tools,
                "sub_networks": sub_networks,  # Store sub-networks separately
            },
            "position": {"x": 100, "y": 100},
        })

        data.agent_details[agent_id] = {
            "instructions": data.agent.get("instructions", "No instructions"),
            "command": data.agent.get("command", "No command"),
            "class": data.agent.get("class", "No class"),
            "function": data.agent.get("function"),
            "dropdown_tools": dropdown_tools,
            "sub_networks": sub_networks,  # Add sub-network info
        }

        # Add edges and recursively process normal child nodes
        for child_id in child_nodes:
            data.edges.append({
                "id": f"{agent_id}-{child_id}",
                "source": agent_id,
                "target": child_id,
                "animated": True,
            })

            child_agent_data = AgentData(
                agent=data.node_lookup[child_id],
                nodes=data.nodes,
                edges=data.edges,
                agent_details=data.agent_details,
                node_lookup=data.node_lookup,
                parent=agent_id,
                depth=data.depth + 1
            )
            self.process_agent(child_agent_data)

        # Process sub-network tools as separate green nodes
        for sub_network in sub_networks:
            data.nodes.append({
                "id": sub_network,
                "type": "sub-network",  # Differentiate node type
                "data": {
                    "label": sub_network,
                    "depth": data.depth + 1,
                    "parent": agent_id,
                    "color": "green",  # Mark sub-network nodes as green
                },
                "position": {"x": 200, "y": 200},
            })

            # Connect sub-network tool to its parent agent
            data.edges.append({
                "id": f"{agent_id}-{sub_network}",
                "source": agent_id,
                "target": sub_network,
                "animated": True,
                "color": "green",  # Mark sub-network edges as green
            })

    def extract_connectivity_info(self, file_path: str):
        """Extracts connectivity details from an HOCON network configuration file."""
        logging.info("utils file_path: %s", file_path)

        config = self.load_hocon_config(file_path)
        tools = config.get("tools", [])

        connectivity = []
        processed_tools = set()

        for tool in tools:
            tool_name = tool.get("name", "unknown_tool")

            if tool_name in processed_tools:
                continue

            entry = {"origin": tool_name}

            if "tools" in tool and tool["tools"]:
                entry["tools"] = tool["tools"]

            if "class" in tool:
                entry["origin"] = tool["class"]

            connectivity.append(entry)
            processed_tools.add(tool_name)

        return {"connectivity": connectivity}

    def extract_coded_tool_class(self, file_path: str):
        """Extract all the coded tool classes in a list"""
        config = self.load_hocon_config(file_path)
        tools = config.get("tools", [])
        coded_tool_classes: List[str] = []
        for tool in tools:
            class_name = tool.get("class", None)
            if class_name:
                coded_tool_classes.append(class_name)
        return coded_tool_classes

    def get_agent_details(self, config_path: str, agent_name: str) -> Dict[str, Any]:
        """
        Retrieves the entire details of an Agent from a HOCON network configuration file.
        :param config_path: Path to the HOCON configuration file.
        :param agent_name: Name of the agent to retrieve details for.
        :return: A dictionary containing the agent's details.
        """
        config = self.load_hocon_config(config_path)

        empty_dict = {}
        empty_list = []

        if "tools" not in config:
            raise HTTPException(status_code=400, detail="Missing tools section")

        tools = config.get("tools", empty_list)
        commondefs = config.get("commondefs", empty_dict)
        agent_data = next((tool for tool in tools if tool.get("name") == agent_name), None)

        if not agent_data:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        # Start with the agent_data as-is
        agent_details = dict(agent_data)

        # Merge global and agent-level llm_config
        merged_llm_config = dict(config.get("llm_config", empty_dict))
        if "llm_config" in agent_data:
            merged_llm_config.update(agent_data["llm_config"])
        agent_details["llm_config"] = merged_llm_config

        # Check if commondefs are referenced
        all_values = AgentNetworkUtils.flatten_values(agent_data)

        uses_commondefs = AgentNetworkUtils.detect_commondefs_usage(
            all_values,
            commondefs.get("replacement_strings", empty_dict),
            commondefs.get("replacement_values", empty_dict)
        )

        if uses_commondefs:
            agent_details["common_defs"] = commondefs

        return agent_details

    @staticmethod
    def flatten_values(obj: Any) -> list:
        """
        Flattens the values of a nested dictionary or list into a single list.
        :param obj: The object to flatten (can be a dict, list, or string).
        :return: A flat list of values.
        """
        flat = []
        if isinstance(obj, dict):
            for v in obj.values():
                flat.extend(AgentNetworkUtils.flatten_values(v))
        elif isinstance(obj, list):
            for i in obj:
                flat.extend(AgentNetworkUtils.flatten_values(i))
        elif isinstance(obj, str):
            flat.append(obj)
        return flat

    @staticmethod
    def detect_commondefs_usage(values: list, replacement_strings: dict, replacement_values: dict) -> bool:
        """
        Detects if any of the values use commondefs replacement strings or values.
        :param values: List of values to check.
        :param replacement_strings: Dictionary of replacement strings.
        :param replacement_values: Dictionary of replacement values.
        :return: True if any value uses commondefs, False otherwise.
        """
        pattern = re.compile(r"\{(\w+)\}")
        for val in values:
            if not isinstance(val, str):
                continue

            # Check {replacement_string} markers
            matches = pattern.findall(val)
            if any(match in replacement_strings for match in matches):
                return True

            # Check if value is directly one of the replacement_values
            if val in replacement_values:
                return True

        return False
