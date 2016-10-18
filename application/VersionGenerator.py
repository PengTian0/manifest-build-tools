# Copyright 2015-2016, EMC, Inc.

"""
The script compute the version of a package, just like:

1.1-1-devel-20160809150908-7396d91

"""
import os
import sys
import re
import datetime
import subprocess
from RepositoryOperator import RepoOperator

class VersionGenerator(object):
    def __init__(self, repo_dir):
        """
        :return:
 
        """
        self._repo_dir = repo_dir
        self.repo_operator = RepoOperator()
 
    def generate_small_version(self):
        """
        generate the small version which consists of commit date and commit hash
        return: small version 
        """

        try:
            ts_str = self.repo_operator.get_lastest_commit_date(self._repo_dir)
            date = datetime.datetime.utcfromtimestamp(int(ts_str)).strftime('%Y%m%d%H%M%SZ')
            commit_id = self.repo_operator.get_lastest_commit_id(self._repo_dir)
            version = "{date}-{commit}".format(date=date, commit=commit_id[0:7])
            return version              
        except RuntimeError as error:
            print "Failed to generate small version for {0} due to error: \n{1}".format(self._repo_dir, error)
            return None

    def generate_big_version(self):
        """
        generate the big version according to changelog
        return: big version
        """
        try:
            cmd_args = ["dpkg-parsechangelog", "--show-field", "Version"]
            proc = subprocess.Popen(cmd_args,
                                    cwd=self._repo_dir,
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    shell=False)

            (out, err) = proc.communicate()
            if proc.returncode == 0:
                return out.strip()
            else:
                return None
        except subprocess.CalledProcessError as ex:
            print "Failed to generate big version for {0} due to error: \n{1}".format(self._repo_dir, error)
            return None

        
    def generate_candidate_version(self):
        """
        generate the candidate version according to branch
        return: devel ,if the branch is master
                rc, if the branch is not master
        """
        try:
            current_branch = self.repo_operator.get_current_branch(self._repo_dir)
            candidate_version = ""
            if "master" in current_branch:
                candidate_version = "devel"
            else:
                candidate_version = "rc"
            return candidate_version
        except RuntimeError as error:
            print "Failed to generate candidate version for {0} due to error: \n{1}".format(self._repo_dir, error)
            return None
        

