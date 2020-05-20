#!/usr/bin/env python3
from unittest import TestCase
from tests.slackwrapper_mock import SlackWrapperMock
import unittest
from util.loghandler import log, logging
from server.botserver import BotServer
from bottypes.invalid_command import InvalidCommand


class BotBaseTest(TestCase):
    def setUp(self):
        self.botserver = BotServer()

        self.botserver.config = {
            "bot_name": "unittest_bot",
            "api_key": "unittest_apikey",
            "send_help_as_dm": "1",
            "admin_users": [
                "admin_user"
            ],
            "auto_invite": [],
            "wolfram_app_id": "wolfram_dummyapi"
        }

        self.botserver.slack_wrapper = SlackWrapperMock("testapikey")
        self.botserver.init_bot_data()

        # replace set_config_option to avoid overwriting original bot configuration.
        self.botserver.set_config_option = self.set_config_option_mock

    def set_config_option_mock(self, option, value):
        if option in self.botserver.config:
            self.botserver.config[option] = value
        else:
            raise InvalidCommand("The specified configuration option doesn't exist: {}".format(option))

    def create_slack_wrapper_mock(self, api_key):
        return SlackWrapperMock(api_key)

    def exec_command(self, msg, exec_user="normal_user"):
        """Simulate execution of the specified message as the specified user in the test environment."""
        testmsg = [{'type': 'message', 'user': exec_user, 'text': msg, 'client_msg_id': '738e4beb-d50e-42a4-a60e-3fafd4bd71da',
                    'team': 'UNITTESTTEAMID', 'channel': 'UNITTESTCHANNELID', 'event_ts': '1549715670.002000', 'ts': '1549715670.002000'}]
        self.botserver.handle_message(testmsg)

    def exec_reaction(self, reaction, exec_user="normal_user"):
        """Simulate execution of the specified reaction as the specified user in the test environment."""
        testmsg = [{'type': 'reaction_added', 'user': exec_user, 'item': {'type': 'message', 'channel': 'UNITTESTCHANNELID', 'ts': '1549117537.000500'},
                    'reaction': reaction, 'item_user': 'UNITTESTUSERID', 'event_ts': '1549715822.000800', 'ts': '1549715822.000800'}]

        self.botserver.handle_message(testmsg)

    def check_for_response_available(self):
        return len(self.botserver.slack_wrapper.message_list) > 0

    def check_for_response(self, expected_result):
        """ Check if the simulated slack responses contain an expected result. """
        for msg in self.botserver.slack_wrapper.message_list:
            if expected_result in msg.message:
                return True

        return False


class TestSyscallsHandler(BotBaseTest):
    def test_available(self):
        self.exec_command("!syscalls available")
        self.assertTrue(self.check_for_response("Available architectures"),
                        msg="Available architectures didn't respond correct.")

    def test_show_x86_execve(self):
        self.exec_command("!syscalls show x86 execve")
        self.assertTrue(self.check_for_response("execve"), msg="Didn't receive execve syscall from bot")
        self.assertTrue(self.check_for_response("0x0b"),
                        msg="Didn't receive correct execve syscall no for x86 from bot")

    def test_show_amd64_execve(self):
        self.exec_command("!syscalls show x64 execve")
        self.assertTrue(self.check_for_response("execve"), msg="Didn't receive execve syscall from bot")
        self.assertTrue(self.check_for_response("0x3b"),
                        msg="Didn't receive correct execve syscall no for x64 from bot")

    def test_syscall_not_found(self):
        self.exec_command("!syscalls show x64 notexist")
        self.assertTrue(self.check_for_response("Specified syscall not found"),
                        msg="Bot didn't respond with expected response on non-existing syscall")


class TestBotHandler(BotBaseTest):
    def test_ping(self):
        self.exec_command("!bot ping")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.check_for_response("Pong!"), msg="Ping command didn't reply with pong.")

    def test_intro(self):
        self.exec_command("!bot intro")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response(
            "Unknown handler or command"), msg="Intro didn't execute properly.")

    def test_version(self):
        self.exec_command("!bot version")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response(
            "Unknown handler or command"), msg="Version didn't execute properly.")


class TestAdminHandler(BotBaseTest):
    def test_show_admins(self):
        self.exec_command("!admin show_admins", "admin_user")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="ShowAdmins didn't execute properly.")
        self.assertTrue(self.check_for_response("Administrators"),
                        msg="ShowAdmins didn't reply with expected result.")

    def test_add_admin(self):
        self.exec_command("!admin add_admin test", "admin_user")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response(
            "Unknown handler or command"), msg="AddAdmin didn't execute properly.")

    def test_remove_admin(self):
        self.exec_command("!admin remove_admin test", "admin_user")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RemoveAdmin didn't execute properly.")

    def test_as(self):
        self.exec_command("!admin as @unittest_user1 addchallenge test pwn", "admin_user")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response(
            "Unknown handler or command"), msg="As didn't execute properly.")


class TestChallengeHandler(BotBaseTest):
    def test_addctf_name_too_long(self):
        ctf_name = "unittest_{}".format("A"*50)
        
        self.exec_command("!ctf addctf {} unittest_ctf".format(ctf_name))

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.check_for_response("CTF name must be <= {} characters.".format(40)),
                        msg="Challenge handler didn't respond with expected result for name_too_long.")

    def test_addctf_success(self):
        self.exec_command("!ctf addctf test_ctf test_ctf")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.check_for_response("Created channel #test_ctf"),
                        msg="Challenge handler failed on creating ctf channel.")

    def test_addchallenge(self):
        self.exec_command("!ctf addchall testchall pwn")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="AddChallenge command didn't execute properly.")

    def test_addtag(self):
        self.exec_command("!ctf tag laff lawl lull")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="AddChallenge command didn't execute properly.")

    def test_removetag(self):
        self.exec_command("!ctf tag laff lawl lull")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="AddChallenge command didn't execute properly.")

    def test_workon(self):
        self.exec_command("!ctf workon test_challenge")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="Workon command didn't execute properly.")

    def test_status(self):
        self.exec_command("!ctf status")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="Status command didn't execute properly.")

    def test_solve(self):
        self.exec_command("!ctf solve testchall")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="Solve command didn't execute properly.")

    def test_solve_support(self):
        self.exec_command("!ctf solve testchall supporter")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="Solve with supporter didn't execute properly.")

    def test_rename_challenge_name(self):
        self.exec_command("!ctf renamechallenge testchall test1")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RenameChallenge didn't execute properly.")

    def test_renamectf(self):
        self.exec_command("!ctf renamectf testctf test2")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RenameCTF didn't execute properly.")

    def test_reload(self):
        self.exec_command("!ctf reload", "admin_user")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.check_for_response(
            "Updating CTFs and challenges"), msg="Reload didn't execute properly.")

    def test_addcreds(self):
        self.exec_command("!ctf addcreds user pw url")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RenameCTF didn't execute properly.")

    def test_endctf(self):
        self.exec_command("!ctf endctf", "admin_user")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response(
            "Unknown handler or command"), msg="EndCTF didn't execute properly.")

    def test_showcreds(self):
        self.exec_command("!ctf showcreds")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RenameCTF didn't execute properly.")

    def test_unsolve(self):
        self.exec_command("!ctf unsolve testchall")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RenameCTF didn't execute properly.")

    def test_removechallenge(self):
        self.exec_command("!ctf removechallenge testchall", "admin_user")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RenameCTF didn't execute properly.")

    def test_roll(self):
        self.exec_command("!ctf roll")

        self.assertTrue(self.check_for_response_available(),
                        msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.check_for_response("Unknown handler or command"),
                         msg="RenameCTF didn't execute properly.")


def run_tests():
    # borrowed from gef test suite (https://github.com/hugsy/gef/blob/dev/tests/runtests.py)
    test_instances = [
        TestSyscallsHandler,
        TestBotHandler,
        TestAdminHandler,
        TestChallengeHandler
    ]

    # don't show bot debug messages for running tests
    log.setLevel(logging.ERROR)

    runner = unittest.TextTestRunner(verbosity=3)
    total_failures = 0

    for test in [unittest.TestLoader().loadTestsFromTestCase(x) for x in test_instances]:
        res = runner.run(test)
        total_failures += len(res.errors) + len(res.failures)

    return total_failures


if __name__ == "__main__":
    run_tests()
