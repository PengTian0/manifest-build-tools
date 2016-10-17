#!/usr/bin/env python

import argparse
import sys
import os
import shutil
from RepositoryOperator import RepoOperator
from reprove import ManifestActions
from VersionGenerator import VersionGenerator
import deb822
import subprocess

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

class UpdateRackhdVersion(object):
    def __init__(self, manifest_url, manifest_commit, manifest_name, builddir):
        """
        __force - Overwrite a directory if it exists
        __git_credential - url, credentials pair for the access to github repos
        __manifest_url - The url of Repository manifest
        __manifest_commit - The commit of Repository manifest
        __manifest_name - The file name of manifest
        __builddir - Destination for checked out repositories
        __is_official_release - True if the official is official release
        :return:
        """
        self._force = False
        self._git_credentials = None
        self._manifest_url = manifest_url
        self._manifest_commit = manifest_commit
        self._manifest_name = manifest_name
        self._builddir = builddir
        
        self._is_official_release = False
        
        self._manifest_path = None
        self._manifest_builddir = None
        self._manifest_repo_dir = None
        self.manifest_actions = None

        self.repo_operator = RepoOperator()
        
        
    def set_git_credentials(self, git_credential):
        """
        Standard setter for git_credentials
        :return: None
        """
        self._git_credentials = git_credential
        self.repo_operator.setup_gitbit(credentials=self._git_credentials)

    def set_force(self, force):
        """
        Standard setter for force
        :return: None
        """
        self._force = force

    def set_is_official_release(self, is_official_release):
        """
        Standard setter for is_official_release
        :return: None
        """
        self._is_official_release = is_official_release

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

    def clone_manifest(self):
        if self._manifest_url and self._manifest_commit:
            manifest_repo_dir = self.repo_operator.clone_repo(self._manifest_url, self._builddir, repo_commit=self._manifest_commit)
            self._manifest_repo_dir =  manifest_repo_dir
            self._initial_manifest_actions()

        else:
            print "manifest url or manifest commit can not be null"
            sys.exit(1)


    def _initial_manifest_actions(self):
        self._manifest_path = os.path.join(self._manifest_repo_dir, self._manifest_name)
        self._manifest_builddir = os.path.join(self._builddir, self._builddir)
        self.manifest_actions = ManifestActions(self._manifest_path, self._manifest_builddir)
        if self._git_credentials:
            self.manifest_actions.set_git_credentials(self._git_credentials)
        self.manifest_actions.set_jobs(8)

        self.manifest_actions.check_builddir()
        self.manifest_actions.get_repositories()


    def _get_RackHD_dir(self):
        repo_list = self.manifest_actions.get_manifest().get_repositories()
        for repo in repo_list:
            if 'repository' in repo:
                repo_url = repo['repository']
                repo_name = strip_suffix(os.path.basename(repo_url), ".git")
                if repo_name == "RackHD":
                    if 'directory-name' in repo:
                        rackhd_dir = repo['directory-name']
                    else:
                        rackhd_dir = self.manifest_actions.directory_for_repo(repo)
                    return rackhd_dir
            else:
                print "no way to find basename"
                sys.exit(1)
        print "Failed to find repository RackHD at {0}".format(self._manifest_builddir)
        sys.exit(1)


    def generate_RackHD_version(self):
        rackhd_dir = self._get_RackHD_dir()
        version_generator = VersionGenerator(rackhd_dir)
        big_version = version_generator.generate_big_version()
        if big_version is None:
            print "Failed to generate big version for {0}".format(rackhd_dir)
            sys.exit(1)
        if self._is_official_release:
            return big_version
        else:
            candidate_version = version_generator.generate_candidate_version()
            small_version_generator = VersionGenerator(self._manifest_repo_dir)
            small_version = small_version_generator.generate_small_version()
            if big_version is None or candidate_version is None or small_version is None:
                print "Failed to generate version for RackHD, Exiting now..."
                sys.exit(1)
            version = "{0}-{1}-{2}".format(big_version, candidate_version, small_version)
            return version        

    def generate_package_version(self, repo_dir):
        try:
            repo_name = os.path.basename(repo_dir)
            print repo_name
            if repo_name == "on-http":
                cmd_args = ["rsync", "-ar", "debianstatic/on-http/", "debian"]
                proc = subprocess.Popen(cmd_args,
                                    cwd=repo_dir,
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    shell=False)

                (out, err) = proc.communicate()
                if proc.returncode != 0:
                    print "Failed to sync on-http/debianstatic/on-http to on-http/debian, exiting now..."
                    sys.exit(1)

            version_generator = VersionGenerator(repo_dir)
            big_version = version_generator.generate_big_version()
            if big_version is None:
                print "Failed to generate big version, maybe the {0} doesn't contain debian directory".format(repo_dir)
                return None

            if self._is_official_release:
                return big_version
            else:
                candidate_version = version_generator.generate_candidate_version()
                small_version = version_generator.generate_small_version()

                if big_version is None or candidate_version is None or small_version is None:
                    print "Failed to generate version for {0}, Exiting now...".format(repo_dir)
                    sys.exit(1)
                version = "{0}-{1}-{2}".format(big_version, candidate_version, small_version)
                return version                
        except Exception,e:
            print e
            sys.exit(1)

    def _get_control_depends(self, control_path):
        """
        Parse debian control file
        :param control_path: the path of control file
        :return: a dictionay which contains all the package in field Depends
        """
        if not os.path.isfile(control_path):
            raise RuntimeError("Can't parse {0} because it is not a file".format(control))

        for paragraph in deb822.Deb822.iter_paragraphs(open(control_path)):
            for item in paragraph.items():
                if item[0] == 'Depends':
                    packages = item[1].split("\n")
                    return packages
        return None

    def _update_dependency(self, debian_dir, version_dict):
        control = os.path.join(debian_dir, "control")
        
        if not os.path.isfile(control):
            raise RuntimeError("Can't update dependency of {0} because it is not a file".format(control))

        new_control = os.path.join(debian_dir, "control_new")
        new_control_fp = open(new_control , "wb")

        packages = self._get_control_depends(control)

        with open(control) as fp:
            package_count = 0
            is_depends = False
            for line in fp:
                if line.startswith('Depends'):
                    package_count += 1
                    is_depends = True
                    new_control_fp.write("Depends: ")
                    for package in packages:
                        package_name = package.split(',',)[0].strip()
                        if ' ' in package_name:
                            package_name = package_name.split(' ')[0]
                        if package_name in version_dict:
                            if ',' in package:
                                depends_str = "         {0} (= {1}),{2}".format(package_name, version_dict[package_name], os.linesep)
                            else:
                                depends_str = "         {0} (= {1}){2}".format(package_name, version_dict[package_name], os.linesep)
                            new_control_fp.write(depends_str)
                        else:
                            new_control_fp.write("{0}{1}".format(package, os.linesep))
                else:
                    if not is_depends or package_count >= len(packages):
                        new_control_fp.write(line)
                    else:
                        package_count += 1

        new_control_fp.close()
        os.remove(control)
        os.rename(new_control, control)


    def update_RackHD_control(self):
        try:
            rackhd_dir = self._get_RackHD_dir()
            debian_dir = os.path.join(rackhd_dir, "debian")

            repo_list = self.manifest_actions.get_manifest().get_repositories()
            version_dict = {}
            for repo in repo_list:
                if 'directory-name' in repo:
                    repo_dir = repo['directory-name']
                else:
                    repo_dir = self.manifest_actions.directory_for_repo(repo)

                version = self.generate_package_version(repo_dir)
                if version != None:
                    if 'repository' in repo:
                        repo_url = repo['repository']
                        repo_name = strip_suffix(os.path.basename(repo_url), ".git")
                        version_dict[repo_name] = version
                    else:
                        print "The repo should be invalid..No way to find repository in {0}".format(json.dumps(repo, indent=True))
                        sys.exit(1)
            if "on-http" in version_dict:
                version_dict["python-on-http-redfish-1.0"] = version_dict["on-http"]
                version_dict["python-on-http-api1.1"] = version_dict["on-http"]
                version_dict["python-on-http-api2.0"] = version_dict["on-http"]
            self._update_dependency(debian_dir, version_dict)
        except Exception, e:
            print e
            sys.exit(1)

        

def parse_command_line(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-repo-url",
                        required=True,
                        help="the url of repository manifest",
                        action="store")
    
    parser.add_argument("--manifest-repo-commit",
                        default="HEAD",
                        help="the commit of repository manifest",
                        action="store")

    parser.add_argument("--manifest-name",
                        required=True,
                        help="repository manifest file",
                        action="store")

    parser.add_argument("--builddir",
                        required=True,
                        help="destination for checked out repositories",
                        action="store")

    parser.add_argument('--parameter-file',
                        help="The jenkins parameter file that will used for succeeding Jenkins job",
                        action='store',
                        default="downstream_parameters")

    parser.add_argument("--force",
                        help="use destination dir, even if it exists",
                        action="store_true")

    parser.add_argument("--git-credential",
                        help="Git credentials for CI services",
                        action="append")

    parser.add_argument("--is-official-release",
                        help="This release if official",
                        action="store_true")

    parsed_args = parser.parse_args(args)
    return parsed_args


def write_downstream_parameters(filename, params):
    """
    Add/append downstream parameter (java variable value pair) to the given
    parameter file. If the file does not exist, then create the file.

    :param filename: The parameter file that will be used for making environment
     variable for downstream job.
    :param params: the parameters dictionary

    :return:
            None on success
            Raise any error if there is any
    """
    if filename is None:
        return

    with open(filename, 'w') as fp:
        try:
            for key in params:
                entry = "{key}={value}\n".format(key=key, value=params[key])
                fp.write(entry)
        except IOError:
            print "Unable to write parameter(s) for next step(s), exit"
            exit(2)

def main():
    # parse arguments
    args = parse_command_line(sys.argv[1:])

    updater = UpdateRackhdVersion(args.manifest_repo_url, args.manifest_repo_commit, args.manifest_name, args.builddir)
    if args.force:
        updater.set_force(args.force)
        updater.check_builddir()

    if args.is_official_release:
        updater.set_is_official_release(args.is_official_release)

    if args.git_credential:
        updater.set_git_credentials(args.git_credential)

    updater.check_builddir()
    updater.clone_manifest()
    RackHD_version = updater.generate_RackHD_version()
    updater.update_RackHD_control()

    if os.path.isfile(args.parameter_file):  # Delete existing parameter file
        os.remove(args.parameter_file)

    downstream_parameters = {}
    downstream_parameters['RACKHD_VERSION'] = RackHD_version
    write_downstream_parameters(args.parameter_file, downstream_parameters)

if __name__ == "__main__":
    main()
    sys.exit(0)
