# SPDX-License-Identifier: LGPL-3.0-or-later

"""
This module handles API requests for creating new chat sessions.

It uses the ChatSessionManager to manage session creation and optionally integrates
with user management through Flask-Login's current_user.
"""

from maeser.chat.chat_session_manager import ChatSessionManager
from flask import request
from flask_login import current_user


def controller(
    session_handler: ChatSessionManager, user_management: bool = False
) -> dict[str, str]:
    """
    Handle session requests and return the response from **session_handler**.

    The response is formatted like so:

    - ``{'response': '<response>'}``, if successful.
    - ``{'response': 'invalid', 'details': 'Requested session type is not valid'}`` if unsuccessful.

    Args:
        session_handler (ChatSessionManager): The session handler instance.
        user_management (bool): Flag to indicate if user management is enabled.

    Returns:
        dict: The response from **session_handler**.
    """
    posty = request.get_json()
    branch_action = posty["action"]
    if posty["type"] == "new":
        if user_management:
            return {
                "response": session_handler.get_new_session_id(
                    branch_action, current_user
                )
            }  # type: ignore
        return {"response": session_handler.get_new_session_id(branch_action)}
    return {"response": "invalid", "details": "Requested session type is not valid"}
