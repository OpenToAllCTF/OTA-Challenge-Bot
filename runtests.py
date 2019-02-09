#!/usr/bin/env python3
from unittest import TestCase
from unittest.mock import patch
from tests.botserver_mock import BotServerMock
import unittest
from util.loghandler import log, logging


class TestSyscallsHandler(TestCase):
    def setUp(self):
        self.botserver = BotServerMock()

    def test_available(self):
        self.botserver.test_command("!syscalls available")
        self.assertTrue(self.botserver.check_for_response("Available architectures"),
                        msg="Available architectures didn't respond correct.")

    def test_show_x86_execve(self):
        self.botserver.test_command("!syscalls show x86 execve")
        self.assertTrue(self.botserver.check_for_response("execve"), msg="Didn't receive execve syscall from bot")
        self.assertTrue(self.botserver.check_for_response("0x0b"),
                        msg="Didn't receive correct execve syscall no for x86 from bot")

    def test_show_amd64_execve(self):
        self.botserver.test_command("!syscalls show x64 execve")
        self.assertTrue(self.botserver.check_for_response("execve"), msg="Didn't receive execve syscall from bot")
        self.assertTrue(self.botserver.check_for_response("0x3b"),
                        msg="Didn't receive correct execve syscall no for x64 from bot")

    def test_syscall_not_found(self):
        self.botserver.test_command("!syscalls show x64 notexist")
        self.assertTrue(self.botserver.check_for_response("Specified syscall not found"),
                        msg="Bot didn't respond with expected response on non-existing syscall")


class TestBotHandler(TestCase):
    def setUp(self):
        self.botserver = BotServerMock()

    def test_ping(self):
        self.botserver.test_command("!bot ping")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.botserver.check_for_response("Pong!"), msg="Ping command didn't reply with pong.")

    def test_intro(self):
        self.botserver.test_command("!bot intro")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="Intro didn't execute properly.")

    def test_version(self):
        self.botserver.test_command("!bot version")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="Version didn't execute properly.")


class TestAdminHandler(TestCase):
    def setUp(self):
        self.botserver = BotServerMock()

    def test_show_admins(self):
        self.botserver.test_command("!admin show_admins", "admin_user")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="ShowAdmins didn't execute properly.")
        self.assertTrue(self.botserver.check_for_response("Administrators"), msg="ShowAdmins didn't reply with expected result.")

    def test_add_admin(self):
        self.botserver.test_command("!admin add_admin test", "admin_user")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="AddAdmin didn't execute properly.")

    def test_remove_admin(self):
        self.botserver.test_command("!admin remove_admin test", "admin_user")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RemoveAdmin didn't execute properly.")

    def test_as(self):
        self.botserver.test_command("!admin as @unittest_user1 addchallenge test pwn", "admin_user")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="As didn't execute properly.")


class TestChallengeHandler(TestCase):
    def setUp(self):
        self.botserver = BotServerMock()

    def test_addctf_name_too_long(self):
        self.botserver.test_command("!ctf addctf unittest_ctf unittest_ctf")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.botserver.check_for_response("CTF name must be <= 10 characters."), msg="Challenge handler didn't respond with expected result for name_too_long.")

    def test_addctf_success(self):
        self.botserver.test_command("!ctf addctf test_ctf test_ctf")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.botserver.check_for_response("Created channel #test_ctf"), msg="Challenge handler failed on creating ctf channel.")

    def test_addchallenge(self):
        self.botserver.test_command("!ctf addchall testchall pwn")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="AddChallenge command didn't execute properly.")

    def test_workon(self):
        self.botserver.test_command("!ctf workon test_challenge")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="Workon command didn't execute properly.")

    def test_status(self):
        self.botserver.test_command("!ctf status")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="Status command didn't execute properly.")

    def test_solve(self):
        self.botserver.test_command("!ctf solve testchall")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="Solve command didn't execute properly.")

    def test_solve_support(self):
        self.botserver.test_command("!ctf solve testchall supporter")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="Solve with supporter didn't execute properly.")

    def test_rename_challenge_name(self):
        self.botserver.test_command("!ctf renamechallenge testchall test1")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RenameChallenge didn't execute properly.")

    def test_renamectf(self):
        self.botserver.test_command("!ctf renamectf testctf test2")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RenameCTF didn't execute properly.")

    def test_reload(self):
        self.botserver.test_command("!ctf reload")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertTrue(self.botserver.check_for_response("Updating CTFs and challenges"), msg="Reload didn't execute properly.")

    def test_addcreds(self):
        self.botserver.test_command("!ctf addcreds user pw url")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RenameCTF didn't execute properly.")

    def test_endctf(self):
        self.botserver.test_command("!ctf endctf", "admin_user")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="EndCTF didn't execute properly.")

    def test_showcreds(self):
        self.botserver.test_command("!ctf showcreds")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RenameCTF didn't execute properly.")

    def test_unsolve(self):
        self.botserver.test_command("!ctf unsolve testchall")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RenameCTF didn't execute properly.")

    def test_removechallenge(self):
        self.botserver.test_command("!ctf removechallenge testchall", "admin_user")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RenameCTF didn't execute properly.")

    def test_roll(self):
        self.botserver.test_command("!ctf roll")

        self.assertTrue(self.botserver.check_for_response_available(), msg="Bot didn't react on unit test. Check for possible exceptions.")
        self.assertFalse(self.botserver.check_for_response("Unknown handler or command"), msg="RenameCTF didn't execute properly.")


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
