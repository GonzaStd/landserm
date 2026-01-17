""" 
I'll test:
    * event mismatching
    * event matching
    * unexistent variable
    * unexistent script
"""
import unittest
import subprocess
from unittest.mock import patch
from landserm.core.events import Event
from landserm.core.policy_engine import evaluate
from landserm.core import actions

class TestEvents(unittest.TestCase):
    def test_mismatching(self):
        print("test_mismatching")
        # arrange
        validPolicy = {
            "name": "sshd-stopped",
            "data": {
                "when": {
                    "kind": "status",
                    "subject": "ssh.service",
                    "payload": "inactive",
                },
                "then":
                {
                    "script":{
                        "name": "start_and_check",
                        "args": ["$subject"]
                    }
                }
            }
        }

        
        validEvent = Event("services", "status", "ssh.service", "active") 
            # Hipotetically checked by landserm.observers.checkStatus because of getServiceStatus(tService)
        
        # act
        result = evaluate(validPolicy, validEvent) # Should return 0

        # assert
        self.assertEqual(result, 0, "Event and policy don't match, evaluate func should return 0")

    def test_matching(self):
        print("test_matching")
        # arrange
        validPolicy = {
            "name": "sshd-stopped",
            "data": {
                "when": {
                    "kind": "status",
                    "subject": "ssh.service",
                    "payload": "inactive",
                },
                "then":
                {
                    "script":{
                        "name": "start_and_check",
                        "args": ["$subject"]
                    }
                }
            }
        }

        validEvent = Event("services", "status", "ssh.service", "inactive") 

        result = evaluate(validPolicy, validEvent)

        self.assertIsInstance(result, tuple)

        context, actions = result

        self.assertEqual(context["subject"], "ssh.service")
        self.assertIn("script", actions)

    @patch("landserm.core.actions.subprocess.run")
    def test_unexistent_variable(self, mock_run):
        # arrange
        print("test_unexistent_variable")
        validContext = {
            "domain": "services",
            "kind": "status",
            "subject": "ssh.service",
            "payload": "inactive"
        }

        actionsData = {
            "script": {
                "name": "start_and_check",
                "args": ["$unexistent-var"]
            }
        }

        actions.executeActions(validContext, actionsData)

        

        if mock_run.assert_not_called():
            called_args = mock_run.call_args[0][0]
            self.assertNotIn("$unexistent-var", called_args)

    @patch("landserm.core.actions.subprocess.run")
    def test_unexistent_script(self, mock_run):
        # arrange
        print("test_unexistent_script")
        context = {
            "domain": "services",
            "kind": "status",
            "subject": "ssh.service",
            "payload": "inactive"
        }

        actionsData = {
            "script": {
                "name": "non_existent_script",
                "args": []
            }
        }

        actions.executeActions(context, actionsData)

        mock_run.assert_not_called()



