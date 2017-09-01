#!/usr/bin/env python
import collections
import os


class SyscallTable:

    def __init__(self, filename):
        self.source = filename
        self.entries = collections.OrderedDict()

        self.parse_table(filename)

    def getEntryDict(self, parts, identifiers):
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
            self.entries[parts[1]] = self.getEntryDict(
                line.split("\t"), identifiers)

    def getEntryByID(self, idx):
        for entry in self.entries:
            if self.entries[entry]["#"] == str(idx):
                return self.entries[entry]

        return None

    def getEntryByName(self, name):
        if name in self.entries:
            return self.entries[name]

        return None

    def getInfoMessage(self, entry):
        if entry:
            msg = ""

            for part in entry:
                msg += "{0:15} : {1}\n".format(part, entry[part])

            return msg

        return None

    def getInfoMessageByID(self, idx):
        entry = self.getEntryByID(idx)
        return self.getInfoMessage(entry)

    def getInfoMessageByName(self, name):
        entry = self.getEntryByName(name)
        return self.getInfoMessage(entry)


class SyscallInfo:

    def __init__(self, basedir):
        self.tables = {}

        for table in os.listdir(basedir):
            filename = os.path.join(basedir, table)

            self.tables[table] = SyscallTable(filename)

    def getAvailableArchitectures(self):
        return self.tables.keys()

    def getArch(self, arch):
        if arch in self.tables:
            return self.tables[arch]

        return None
