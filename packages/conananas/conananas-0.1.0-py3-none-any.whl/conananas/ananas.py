""" ananas """
from conan.api.conan_api import ConanAPI
from conan.cli.cli import Cli

LOCAL_CACHE = "Local Cache"

# pylint: disable-next=too-many-public-methods,too-many-instance-attributes
class Ananas():
    """ conan(anas) operations and data """

    all_packages = {}
    remote = LOCAL_CACHE
    disabled_remotes = []
    name = None
    version = None
    revision = None
    package = None
    package_path = ""
    recipe_path = ""

    def __init__(self):
        self.api = ConanAPI()
        self.cli = Cli(self.api)
        self.cli.add_commands()

    def remote_available(self):
        """ check if remote is available """
        try:
            return self.remote is not None \
                and self.all_packages[self.remote] is not None
        except Exception as _ex:
            return False

    def name_available(self):
        """ check if a name is available """
        try:
            return self.remote_available() and self.name is not None \
                and self.all_packages[self.remote][self.name] is not None
        except Exception as _ex:
            return False

    def version_available(self):
        """ check if a version is available """
        try:
            return self.name_available() and self.version is not None \
                and self.all_packages[self.remote][self.name][self.version] is not None
        except Exception as _ex:
            return False

    def revision_available(self):
        """ check if a revision is available """
        try:
            return self.version_available() \
                and self.revision is not None \
                and self.all_packages \
                    [self.remote][self.name][self.version][self.revision] is not None
        except Exception as _ex:
            return False

    def package_available(self):
        """ check if a package is available """
        try:
            return self.revision_available() \
                and self.package is not None \
                and self.all_packages \
                    [self.remote][self.name][self.version][self.revision][self.package] is not None
        except Exception as _ex:
            return False

    # PACKAGES
    def get_package(self) -> dict:
        """ get current package """
        if self.package_available():
            package = (self.all_packages
                       [self.remote]
                       [self.name]
                       [self.version]
                       [self.revision]
                       [self.package])
            return package

        return {}

    def get_packages(self, revision=None, detailed=False):
        """ get details for a specific package name and version """
        if not revision:
            revision = self.revision

        if not revision:
            revisions = self.get_revisions(self.version)
            revision = revisions[0] if revisions and len(revisions) > 0 else None

        if not revision or revision == "":
            return []

        if revision not in self.all_packages[self.remote][self.name][self.version] \
            or self.all_packages[self.remote][self.name][self.version][revision] is None:
            self.revision = revision

            if self.all_packages[self.remote][self.name][self.version][self.revision] is None:
                self.all_packages[self.remote][self.name][self.version][self.revision] = {}

            args = ["list", f"{self.name}/{self.version}#{self.revision}:*"]
            args = self._add_remote(args)
            results = self.api.command.run(args)["results"]

            packages = results \
                [self.remote][f"{self.name}/{self.version}"]["revisions"][self.revision]
            for package in list(packages["packages"]):
                try:
                    info = packages["packages"][package]["info"]
                except Exception as _ex:
                    info = {}
                self.all_packages \
                    [self.remote][self.name][self.version][self.revision][package] = info

        if detailed:
            packages = []
            for package_hash in self.all_packages[self.remote][self.name][self.version][revision]:
                try:
                    package = self.all_packages \
                        [self.remote][self.name][self.version][revision][package_hash]
                    packages.append(f"{package['settings']['os']}, "
                                    f"{package['settings']['compiler']} "
                                    f"{package['settings']['compiler.version']}, "
                                    f"{package['settings']['build_type']} "
                                    f"[{package_hash}]")
                except Exception as _ex:
                    # fallback for packages without information
                    packages.append(f"- [{package_hash}]")
            return packages

        return list(self.all_packages[self.remote][self.name][self.version][revision])

    def set_package(self, package):
        """ set current package """
        if self.revision_available():
            self.package = package
            return True

        return False

    def get_packages_count(self) -> int:
        """ get number of available packages """
        if self.revision_available():
            return len(list(self.all_packages
                            [self.remote]
                            [self.name]
                            [self.version]
                            [self.revision]))

        return 0

    def get_package_path(self):
        """ get path of current package if local """
        self.package_path = ""
        self.recipe_path = ""

        if self.remote == LOCAL_CACHE:
            def read_package_path(package=True):
                path = ""
                package_string = self.get_package_string(package=package)
                if package_string:
                    args = ["cache", "path", package_string]
                    path = self.api.command.run(args)

                return path


            self.package_path = read_package_path()
            self.recipe_path = read_package_path(package=False)

    def get_package_string(self, version=True, revision=True, package=True) -> str|None:
        """ get package string """
        package_string = None

        try:
            if self.name:
                package_string = self.name
                if version:
                    if not self.version:
                        return None
                    package_string += f"/{self.version}"
                if revision:
                    if not self.revision:
                        return None
                    package_string += f"#{self.revision}"
                if package:
                    if not self.package:
                        return None
                    package_string += f":{self.package}"
        except Exception as _ex:
            pass

        return package_string

    # REVISIONS
    def set_revision(self, revision):
        """ set current name """
        if self.version_available():
            self.revision = revision
            self.package = None
            return True

        return False

    def get_revisions(self, version=None):
        """ get details for a specific package name and version """
        if version is None:
            version = self.version

        if version is None and not self.version_available():
            return []

        self.version = version

        if version in self.all_packages[self.remote][self.name] \
            and self.all_packages[self.remote][self.name][version] is not None:
            return list(self.all_packages[self.remote][self.name][version])

        if self.all_packages[self.remote][self.name][self.version] is None:
            self.all_packages[self.remote][self.name][self.version] = {}

        args = ["list", f"{self.name}/{self.version}#*"]
        args = self._add_remote(args)
        results = self.api.command.run(args)["results"]

        package = results[self.remote][f"{self.name}/{self.version}"]
        for revision in list(package["revisions"]):
            self.all_packages[self.remote][self.name][self.version][revision] = None

        return list(self.all_packages[self.remote][self.name][self.version])

    def get_revisions_count(self) -> int:
        """ get number of available revisions """
        if self.version_available():
            return len(list(self.all_packages
                            [self.remote]
                            [self.name]
                            [self.version]))

        return 0

    # VERSIONS
    def set_version(self, version):
        """ set current name """
        if self.name_available():
            self.version = version
            self.revision = None
            self.package = None
            return True

        return False

    def get_versions(self) -> list:
        """ get list of available versions """
        if self.name_available():
            return list(self.all_packages
                        [self.remote]
                        [self.name])

        return []

    def get_versions_count(self) -> int:
        """ get number of available versions """
        if self.name_available():
            return len(list(self.all_packages
                            [self.remote]
                            [self.name]))

        return 0

    # NAMES
    def set_name(self, name):
        """ set current name """
        if self.remote_available():
            self.name = name
            self.version = None
            self.revision = None
            self.package = None
            return True

        return False

    def get_names(self) -> list:
        """ get list of available packages """
        if self.remote_available():
            return list(self.all_packages[self.remote])

        return []

    def get_names_count(self) -> int:
        """ get number of available names """
        if self.remote_available():
            return len(list(self.all_packages[self.remote]))

        return 0

    # REMOTES
    def read_remotes(self):
        """ read conan remotes """
        self.all_packages = {}
        self.all_packages[LOCAL_CACHE] = None
        self.disabled_remotes = []
        args = ["remote", "list"]
        results = self.api.command.run(args)
        for remote in results:
            if remote.disabled:
                self.disabled_remotes.append(remote.name)
            else:
                self.all_packages[remote.name] = None

    def get_remotes(self) -> list:
        """ get list of available and enabled remotes """
        return list(self.all_packages) if self.all_packages else []

    def get_disabled_remotes(self) -> list:
        """ get list of disabled remotes """
        return self.disabled_remotes

    # ALL PACKAGES
    def read_all_packages(self, remote: str):
        """ read conan package names """
        if not remote:
            return

        if remote in self.all_packages and self.all_packages[remote] is not None:
            self.remote = remote
            return

        self.remote = remote

        self._reset_data()

        args = ["list", "*"]
        args = self._add_remote(args)
        results = self.api.command.run(args)["results"]

        for source in results:
            if source == remote:
                if self.all_packages[remote] is None:
                    self.all_packages[remote] = {}
                for package_full in results[source]:
                    name, version = package_full.split("/", 1)

                    if name not in self.all_packages[remote]:
                        self.all_packages[remote][name] = {}
                    self.all_packages[remote][name][version] = None

    def _add_remote(self, args):
        if self.remote != LOCAL_CACHE:
            args.extend(["-r", self.remote])

        return args

    def _reset_data(self):
        self.name = None
        self.version = None
        self.revision = None
        self.package = None
        self.package_path = ""
