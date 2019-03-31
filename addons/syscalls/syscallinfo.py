#!/usr/bin/env python
import collections
import os


class SyscallTable:

    def __init__(self, filename):
        self.source = filename
        self.entries = collections.OrderedDict()

        self.parse_table(filename)

    def get_entry_dict(self, parts, identifiers):
        entry = collections.OrderedDict()

        for i in range(len(parts)):
            if identifiers[i] == "Definition":
                parts[i] = parts[i].split(":")[0]

            entry[identifiers[i]] = parts[i]

        return entry

    def parse_table(self, filename):
        lines = []

        with open(filename) as f:
            lines = f.readlines()

        # retrieve identifiers from first line
        identifiers = lines[0].strip().split("\t")

        for line in lines[1:]:
            parts = line.split("\t")
            self.entries[parts[1]] = self.get_entry_dict(
                line.split("\t"), identifiers)

    def get_entry_by_id(self, idx):
        for entry in self.entries:
            if self.entries[entry]["#"] == str(idx):
                return self.entries[entry]

        return None

    def get_entry_by_name(self, name):
        if name in self.entries:
            return self.entries[name]

        return None

    def get_info_message(self, entry):
        if entry:
            msg = ""

            for part in entry:
                msg += "{0:15} : {1}\n".format(part, entry[part])

            return msg

        return None

    def get_info_message_by_id(self, idx):
        entry = self.get_entry_by_id(idx)
        return self.get_info_message(entry)

    def get_info_message_by_name(self, name):
        entry = self.get_entry_by_name(name)
        return self.get_info_message(entry)


class SyscallInfo:

    def __init__(self, basedir):
        self.tables = {}

        for table in os.listdir(basedir):
            filename = os.path.join(basedir, table)

            self.tables[table] = SyscallTable(filename)

    def get_available_architectures(self):
        return self.tables.keys()

    def get_arch(self, arch):
        if arch in self.tables:
            return self.tables[arch]

        return None
