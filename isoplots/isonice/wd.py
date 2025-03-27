"""
WIP ISOFIT Output Parser
"""
from pathlib import Path

from isofit.radiative_transfer import luts


class LUTs:
    lut_regex = r"(\w+)-(\d*\.?\d+)_?"

    def __init__(self, path):
        self.path = Path(path)
        self.data = {}

        self.luts = {}
        for file in self.path.glob("*.nc"):
            self.luts[file.name] = file

        # Try to parse any additional files
        self.parseSixS()
        self.parseModtran()

    def __repr__(self):
        return f"<{self.__class__.__name__}/{self.path.name}>"

    def parseSixS(self):
        self.sixs = {}
        for file in self.path.glob("*.inp"):
            matches = re.findall(self.lut_regex, file.stem[4:])
            for (name, value) in matches:
                quant = self.sixs.setdefault(name, set())
                quant.add(float(value))

    def parseModtran(self):
        self.modtran = {}
        for file in self.path.glob("*.json"):
            matches = re.findall(self.lut_regex, file.stem[4:])
            for (name, value) in matches:
                quant = self.modtran.setdefault(name, set())
                quant.add(float(value))

    def load(self, name):
        if not name.endswith(".nc"):
            name += ".nc"

        if name not in self.data:
            self.data[name] = luts.load(self.luts[name])

        return self.data[name]


class IsofitWD:
    _dirs = ("config", "data", "input", "lut_full", "lut_h2o", "output")

    def __init__(self, path, invalid=False):
        """
        TODO

        Parameters
        ----------
        path : str
            Path to either an ISOFIT configuration file or an output directory. If a
            config file, will attempt to detect the output directory from it.
        invalid : bool, default=False
            Allow an invalid path. This may be used to initialize an empty object and
            change it via changePath()
        """
        self.dirs = {}
        self.path = Path(path)
        self.data = None
        self._logs = None
        self.logFile = None
        self.invalid = invalid

        if self.path.is_file():
            for parent in self.path.parents:
                dirs = self.findSubdirs(parent)
                if any(dirs.values()):
                    self.path = parent
                    self.data = IsofitData(self.path)
                    break
            else:
                self._error("Could not find a valid working directory given the configuration file")

        elif any((dirs := self.findSubdirs(self.path)).values()):
            self.data = IsofitData(self.path)

        else:
            self._error("Could not find a valid working directory")

        self.createChildren()

    def createChildren(self):
        for path in self.path.glob("*lut*"):
            self.dirs[path.name] = LUTs(path)

        self.dirs["config"] = IsofitConfigs(self.path / "config")
        self.dirs["output"] = IsofitOutputs(self.path / "output")
        self.dirs["data"]   = IsofitData(self.path / "data")
        self.dirs["input"]  = IsofitInputs(self.path / "input")


    def __repr__(self):
        return f"<IsofitOutput: {self.path}>"

    def changePath(self, *args, **kwargs):
        """
        Re-initializes the existing object by simply calling __init__. Useful for
        maintaining a single object that must change working directories

        Parameters
        ----------
        *args : list
            Passthrough arguments
        **kwargs : dict
            Passthrough key-word arguments
        """
        self.__init__(*args, **kwargs)
        return self

    def findSubdirs(self, path):
        return {
            subdir: (path / subdir).exists()
            for subdir in self._dirs
        }

    def makeTree(self):
        tree = []
        for _dir, data in IsofitFiles.items():
            subpath = self.path / _dir
            children = []
            if subpath.exists():
                tree.append({"id": _dir, "desc": data["desc"], "children": children})
                for name, desc in data["files"].items():
                    if files := list(subpath.glob(name)):
                        for file in files:
                            children.append({"id": file.name, "desc": desc})

        return tree

    def parseLogs(self, file=None):
        if file:
            self.logs = IsofitLogs(file)
        else:
            if not self.logs:
                files = list(self.path.rglob("*.log"))
                if files:
                    self.logs = IsofitLogs(files[0])
                else:
                    print("No log file found")
                    return

    def setLogFile(self, file=None):
        """
        Sets the log file

        Parameters
        ----------
        file : str, default=None
            Filepath to a log file to parse. If None, resets the stored log file and
            will attempt to automatically find one on the next access of the `logs`
            attribute

        Raises
        -------
        FileNotFoundError
            If the provided log file does not exist
        """
        if file:
            if not Path(file).exists():
                return self._error(f"Log file does not exist: {file}")
        self.logFile = file

    @property
    def logs(self):
        if self._logs is None:
            if self.logFile is None:
                files = list(self.path.rglob("*.log"))
                if files:
                    self.logFile = files[0]

            if self.logFile:
                self._logs = IsofitLogs(self.logFile)
            else:
                self._error("No log file found. Please set one via setLogFile()")
        return self._logs

    def _error(self, message):
        if not self.invalid:
            raise FileNotFoundError(message)
        print(message)


# wd = IsofitWD("/Users/jamesmo/projects/isofit/research/NEON.bak/output/NIS01_20210403_173647")
# wd.dirs
#
#%
#
l = LUTs("/Users/jamesmo/projects/isofit/research/jemit/lut_full")
l = LUTs("/Users/jamesmo/projects/isofit/research/NEON.bak/output/NIS01_20210403_173647/lut_full")
#%%
path = Path("/Users/jamesmo/projects/isofit/extras/examples/20171108_Pasadena/configs")
list(path.rglob("*.json"))

#%%

for file in path.rglob("*.json"):
    break

#%%


class IsofitConfigs:
    def __init__(self, path):
        self.path = Path(path)

    def getTree(self, *, path=None, tree={'': []}):
        """
        Recursively finds the JSON files under a directory as a dict tree

        Parameters
        ----------
        path : pathlib.Path
            Directory to search
        tree : dict, default={'': []}
            Tree structure of discovered JSONS

        Returns
        -------
        tree : dict
            Tree structure of discovered JSONS. The keys are the directory names and
            the list values are the found JSONS
        """
        if path is None:
            path = self.path

        for item in path.glob("*"):
            if item.is_dir():
                self.getTree(path=item, tree=tree.setdefault(item.name, {'': []}))
            elif item.suffix == ".json":
                tree[''].append(item.name)

        return tree

    def getFlat(self):
        files = []
        for file in path.rglob("*.json"):
            name = str(file).replace(f"{path}/", "")
            files.append(name)
        return files

    def get(self, name):
        found = []
        for file in files:
            if name in file:
                found.append(file)
        if len(found) > 1:
            print(f"{len(found)} configuration files were found containing the provided name {name!r}, try being more specific. Returning just the first instance")
        return found[0]

io = IsofitConfigs(path)
io.getTree()
files = io.getFlat()
files
name = "surface"

#%%

parents = list(file.parents)
if path in parents:
    parents.pop(parents.index(path))

#%%




files
