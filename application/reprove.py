#!/usr/bin/env python
# see http://stackoverflow.com/questions/1783405/checkout-remote-git-branch
# and http://stackoverflow.com/questions/791959/download-a-specific-tag-with-git

# check out a set of repositories to match the manifest file

# Copyright 2015-2016, EMC, Inc.

import argparse
import json
import os
import shutil
import sys

import config

from urlparse import urlparse, urlunsplit
from RepositoryOperator import RepoOperator
from manifest import Manifest


def strip_suffix(text, suffix):
    """
    Cut a set of the last characters from a provided string
    :param text: Base string to cut
    :param suffix: String to remove if found at the end of text
    :return: text without the provided suffix
    """
    if text is not None and text.endswith(suffix):
        return text[:len(text) - len(suffix)]
    else:
        return text


def strip_prefix(text, prefix):
    if text is not None and text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text


class ManifestActions(object):

    valid_actions = ['checkout', 'tag', 'packagerefs', 'branch']

    def __init__(self):
        """
        __force - Overwrite a directory if it exists
        __manifest - Repository manifest contents
        __builddir - Destination for checked out repositories
        __tagname - Tagname to be applied to all repos
        :return:
        """
        self._force = False
        self._git_credentials = None
        self._builddir = None
        self._manifest = None
        self._tagname = None
        self._jobs = 1
        self.actions = []
        self._map = {}
       
        self.repo_operator = RepoOperator()
 
        self.__parse_command_line()
       

    def add_mapping(self, mapping):
        url_from, url_to = mapping

        url_from = urlparse(url_from)
        url_to = urlparse(url_to)
        self._map[url_from] = url_to


    def get_manifest(self):
        """
        Standard getter for manifest
        :return: None
        """
        return self._manifest


    def get_tagname(self):
        """
        Standard getter for tagname
        : return: None
        """
        return self._tagname

    def get_branchname(self):
        """
        Standard getter for tagname
        : return: None
        """
        return self._branchname

    def add_action(self, action):
        if action not in self.valid_actions:
            print "Unknown action '{0}' requested".format(action)
            print "Valid actions are:"
            for op in self.valid_actions:
                print "  {0}".format(op)
            sys.exit(1)
        else:
            self.actions.append(action)


    def __parse_command_line(self):
        """
        Parse script arguments.
        :return: Parsed args for assignment
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("--manifest",
                            required=True,
                            help="repository manifest file",
                            action="store")
        parser.add_argument("--builddir",
                            required=True,
                            help="destination for checked out repositories",
                            action="store")
        parser.add_argument("--force",
                            help="use destination dir, even if it exists",
                            action="store_true")
        parser.add_argument("--git-credential",
                            help="Git credentials for CI services",
                            action="append")
        parser.add_argument("--tagname",
                            help="tagname applied to repos",
                            action="store")
        parser.add_argument("--branchname",
                            help="branchname applied to repos",
                            action="store")
        parser.add_argument("--jobs",
                            default=1,
                            help="Number of parallel jobs to run",
                            type=int)
        parser.add_argument("--map",
                            nargs=2,
                            help="Remap repository URLs",
                            action="append")
        parser.add_argument('action',
                            nargs="+")

        args = parser.parse_args()

        ## first, check & handle all of the command line options

        if args.force:
            self._force = True

        for action in args.action:
            self.add_action(action)

        self._builddir = args.builddir
        if 'checkout' in args.action and self._builddir is not None:
            self.check_builddir()

        if args.git_credential:
            self._git_credentials = args.git_credential
            self.repo_operator.setup_gitbit(credentials=self._git_credentials)

        if args.tagname:
            self._tagname = args.tagname
        
        if args.branchname:
            self._branchname = args.branchname

        if args.jobs:
            self._jobs = args.jobs

        if self._jobs < 1:
            print "--jobs value must be an integer >=1"
            sys.exit(1)

        if args.map:
            for mapping in args.map:
                self.add_mapping(mapping)

        # and then finally do some actual work, which might depend upon the command line
        # option values

        if args.manifest:
            try:
                self._manifest = Manifest(args.manifest)
                self._manifest.validate_manifest()
            except KeyError as error:
                print "Failed to create a Manifest instance for the manifest file {0} \nERROR:\n{1}"\
                      .format(args.manifest, error.message)
                sys.exit(1)

            for repo in self._manifest.get_repositories():
                repo['directory-name'] = self.directory_for_repo(repo)


    def check_builddir(self):
        """
        Checks the given builddir name and force flag. Deletes exists directory if one already
        exists and --force is set
        :return: None
        """
        if os.path.exists(self._builddir):
            if self._force:
                shutil.rmtree(self._builddir)
                print "Removing existing data at {0}".format(self._builddir)
            else:
                print "Unwilling to overwrite destination builddir of {0}".format(self._builddir)
                sys.exit(1)

        os.makedirs(self._builddir)


    @staticmethod
    def print_command_summary(name, results):
        """
        Print the results of running commands.
          first the command line itself
            and the error code if it's non-zero
          then the stdout & stderr values from running that command

        :param name:
        :param results:
        :return: True if any command exited with an error condition
        """

        error_found = False

        print "============================"
        print "Command output for {0}".format(name)

        if 'commands' in results[name]:
            commands = results[name]['commands']
            for command in commands:
                for key in ['command', 'stdout', 'stderr']:
                    if key in command:
                        if command[key] != '':
                            print command[key]
                        if key == 'command':
                            if command['return_code'] != 0:
                                error_found = True
                                print "EXITED: {0}".format(command['return_code'])

        return error_found

        
    def get_repositories(self):
        """
        Issues checkout commands to dictionaries within a provided manifest
        :return: None
        """
        repo_list = self._manifest.get_repositories()
        try:
            self.repo_operator.clone_repo_list(repo_list, self._builddir, jobs=self._jobs)
        except RuntimeError as error:
            print "Exiting due to error: {0}".format(error)
            sys.exit(1)
            

    def create_repo_branch(self, repo):
        """
        create branch  on the repos in the manifest file
        :param repo: A dictionary
        :return: None
        """

        repo_url = repo['repository']
        basename = strip_suffix(os.path.basename(repo_url), ".git")
        work_dir = "{0}/{1}".format(self._builddir, basename)

        try:
            self.repo_operator.create_repo_branch(repo_url, work_dir, self._branchname)
        except RuntimeError as error:
            print "Exiting due to error: {0}".format(error)
            sys.exit(1)

    def branch_existing_repositories(self):
        """
        Issues create branch commands to repos in a provided manifest
        :return: None
        """
        repo_list = self._manifest.get_repositories()
        if repo_list is None:
            print "No repository list found in manifest file"
            sys.exit(2)
        else:
            # Loop through list of repos and create specified tag on each
            for repo in repo_list:
                self.create_repo_branch(repo)

    def set_repo_tagname(self, repo):
        """
        Sets tagname on the repos in the manifest file
        :param repo: A dictionary
        :return: None
        """

        repo_url = repo['repository']
        basename = strip_suffix(os.path.basename(repo_url), ".git")
        work_dir = "{0}/{1}".format(self._builddir, basename)

        try:
            self.repo_operator.set_repo_tagname(repo_url, work_dir, self._tagname)
        except RuntimeError as error:
            print "Exiting due to error: {0}".format(error)
            sys.exit(1)


    def tag_existing_repositories(self):
        """
        Issues set_tagname commands to repos in a provided manifest
        :return: None
        """
        repo_list = self._manifest.get_repositories()
        if repo_list is None:
            print "No repository list found in manifest file"
            sys.exit(2)
        else:
            # Loop through list of repos and create specified tag on each
            for repo in repo_list:
                self.set_repo_tagname(repo)


    def directory_for_repo(self, repo):
        if 'checked-out-directory-name' in repo:
            repo_directory = repo['checked-out-directory-name']
        else:
            if 'repository' in repo:
                repo_url = repo['repository']
                repo_directory = strip_suffix(os.path.basename(repo_url), ".git")
            else:
                raise ValueError("no way to find basename")

        repo_directory = os.path.join(self._builddir, repo_directory)
        return repo_directory


    def match_url(self, url_string, url_from, url_to):
        current_url = urlparse(url_string)

        if (current_url.scheme == url_from.scheme and
                current_url.netloc == url_from.netloc and
                current_url.path.startswith(url_from.path + "/")):

            new_path = current_url.path.replace(url_from.path, url_to.path)

            new_urlbits = (url_to.scheme, url_to.netloc, new_path, current_url.query, None)

            new_url = urlunsplit(new_urlbits)
            print "new url is"
            print new_url
            if 'branch' not in self.actions:
                for repo in self._manifest.get_repositories():
                    if new_url == repo['repository']:
                        if 'directory-name' in repo:
                            new_url = os.path.abspath(repo['directory-name'])
                            return new_url


    def _update_dependency(self, version):
        """
        Check the specified package & version, and return a new package version if
        the package is listed in the manifest.

        :param version:
        :return:
        """

        if not version.startswith("git+"):
            return version

        url = strip_prefix(version, "git+")

        for r_from, r_to in self._map.items():
            new_url = self.match_url(url, r_from, r_to)
            if new_url is not None:
                return new_url

        return version


    def update_repo_package_list(self, repo):
        """

        :param repo: a manifest repository entry
        :return:
        """
        repo_dir = repo['directory-name']

        package_json_file = os.path.join(repo_dir, "package.json")
        if not os.path.exists(package_json_file):
            # if there's no package.json file, there is nothing more for us to do here
            return

        changes = False
        log = ""

        with open(package_json_file, "r") as fp:
            package_data = json.load(fp)

            #git_version_info = self._get_repo_url(repo)
            #package_data['version'] = git_version_info

            if 'dependencies' in package_data:
                for package, version in package_data['dependencies'].items():
                    new_version = self._update_dependency(version)
                    if new_version != version:
                        log += "  {0}:\n    WAS {1}\n    NOW {2}\n".format(package,
                                                                           version,
                                                                           new_version)
                        package_data['dependencies'][package] = new_version
                        changes = True

        if changes:
            print "There are changes to dependencies for {0}\n{1}".format(package_json_file, log)

            os.rename(package_json_file, package_json_file + ".orig")

            new_file = package_json_file
            with open(new_file, "w") as newfile:
                json.dump(package_data, newfile, indent=4, sort_keys=True)

        else:
            print "There are NO changes to data for {0}".format(package_json_file)


    def update_package_references(self):
        print "Update internal package lists"

        repo_list = self._manifest.get_repositories()
        if repo_list is None:
            print "No repository list found in manifest file"
            sys.exit(2)
        else:
            # Loop through list of repos and create specified tag on each
            for repo in repo_list:
                self.update_repo_package_list(repo)


def main():
    manifest_actions = ManifestActions()

    if 'checkout' in manifest_actions.actions:
        manifest_actions.get_repositories()

    if 'tag' in manifest_actions.actions:
        if manifest_actions.get_tagname() is not None:
            print "Setting tags for the repos..."
            manifest_actions.tag_existing_repositories()
        else:
            print "No setting for --tagname"
            sys.exit(1)

    if 'packagerefs' in manifest_actions.actions:
        manifest_actions.update_package_references()

    if 'branch' in manifest_actions.actions:
        manifest_actions.create_branch()

if __name__ == "__main__":
    main()
    sys.exit(0)
