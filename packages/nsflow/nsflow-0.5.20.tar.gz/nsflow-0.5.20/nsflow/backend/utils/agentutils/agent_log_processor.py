
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

import json
from typing import Any
from typing import Dict
import logging

from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.message_processing.message_processor import MessageProcessor
from nsflow.backend.utils.logutils.websocket_logs_registry import LogsRegistry
from nsflow.backend.trust.rai_service import RaiService


class AgentLogProcessor(MessageProcessor):
    """
    Tells the UI there's an agent message to process.
    """

    def __init__(self, agent_name: str, sid: str):
        """
        Constructor
        """
        self.logs_manager = LogsRegistry.register(agent_name)
        self.sid: str = sid
        self.agent_name = agent_name

    async def async_process_message(self, chat_message_dict: Dict[str, Any], message_type: ChatMessageType):
        """
        Process the message to:
          - Log the message
          - Highlight the agent in the network diagram
          - Display the message in the Agents Communication panel
        :param chat_message_dict: The chat message
        :param message_type: The type of message
        """
        # initialize different items in response
        internal_chat = None
        otrace = None
        sly_data = None
        token_accounting: Dict[str, Any] = {}
        
        # Log the original chat_message_dict in full only for debugging on client interface
        # await self.logs_manager.log_event(f"{'='*50}\n{chat_message_dict}")
        # To just print on terminal, uncomment the below 3 lines
        # logging.info("\n"+"="*30 + "chat_message_dict incoming" + "="*30+"\n")
        # logging.info(chat_message_dict)
        # logging.info("\n"+"x"*30 + "End of chat_message_dict" + "x"*30+"\n")

        if message_type not in (ChatMessageType.AGENT,
                                ChatMessageType.AI,
                                ChatMessageType.AGENT_TOOL_RESULT):
            # These are framework messages that contain chat context, system prompts or consolidated messages etc.
            # Don't log them. And there's no agent to highlight in the network diagram.
            return
        # Get the token accounting information
        if message_type == ChatMessageType.AGENT:
            token_accounting = chat_message_dict.get("structure", token_accounting)

        # # Discard empty messages, don't need it for now
        # log_text = chat_message_dict.get("text", "").strip()
        # if log_text == "":
        #     return

        # Get the list of agents that participated in the message
        otrace = chat_message_dict.get("origin", [])
        otrace = [i.get("tool") for i in otrace]

        if message_type in (ChatMessageType.AGENT, ChatMessageType.AGENT_TOOL_RESULT):
            # Get the internal chat message between agents
            internal_chat = chat_message_dict.get("text", "")

        otrace_str = json.dumps({"otrace": otrace})
        # Always send longs with a key "text" to any web socket
        internal_chat_str = {"otrace": otrace, "text": internal_chat}
        token_accounting_str = json.dumps({"token_accounting": token_accounting})
        await self.logs_manager.log_event(f"{otrace_str}", "NeuroSan")
        await self.logs_manager.internal_chat_event(internal_chat_str)

        if token_accounting:
            await self.logs_manager.log_event(f"{token_accounting_str}", "NeuroSan")
            await RaiService.get_instance().update_metrics_from_token_accounting(token_accounting, self.agent_name)
