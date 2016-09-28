#!/usr/bin/env python

import json
import os
import unittest

from application.update_manifest import UpdateManifest

@unittest.skip("temporarily disabled")
class UpdateManifestTest(unittest.TestCase):

    __local_repo_to_change = "https://github.com/RackHD/on-tasks.git" 
    __local_manifest_repo = 'ssh://git@hwstashprd01.isus.emc.com:7999/hwimotools/manifest-build-tools.git'
    __local_manifest_file = 'correct_manifest.json'
    __local_manifest_folder = 'test_manifests'
    __local_branch = 'master'
    __real_repo = 'https://github.com/RackHD/on-taskgraph.git'
    __real_manifest_repo = 'ssh://git@hwstashprd01.isus.emc.com:7999/hwimotools/manifest.git'

    def setUp(self):
        self.um_class = UpdateManifest()
        self.um_class.quiet = True

    def tearDown(self):
        try:
            self.um_class.cleanup_and_exit()
        except SystemExit:
            pass
        del self.um_class


    def test_parse_args(self):
        """
        UpdateManifest.parse_args successfully parses arguments
        """
        parsed = self.um_class.parse_args([
            '--repo', 'www.google.com',
            '--branch', 'master',
            '--manifest_repo', 'www.xkcd.com',
            '--commit', 'abcdef',
            '--manifest_file', 'da_manifest'])
        self.assertEqual(parsed.repo, 'www.google.com')
        self.assertEqual(parsed.branch, 'master')
        self.assertEqual(parsed.manifest_repo, 'www.xkcd.com')
        self.assertEqual(parsed.commit, 'abcdef')
        self.assertEqual(parsed.manifest_file, 'da_manifest')


    def test_parsed_branch_fails(self):
        """
        UpdateManifest.__check_branch throws an error b/c provided with nonexistent branch name
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__real_repo,
            '--branch', 'masteer',
            '--manifest_repo', self.__real_manifest_repo
            ])
        with self.assertRaises(SystemExit):
            self.um_class.assign_args(parsed)


    def test_parsed_commit_fails(self):
        """
        UpdateManifest.assign_args throws an error b/c provided flawed commit-id
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__real_repo,
            '--branch', 'master',
            '--manifest_repo', self.__real_manifest_repo,
            '--commit', 'notfortycharactersofhex' ])
        with self.assertRaises(SystemExit):
            self.um_class.assign_args(parsed)


    def test_clone_manifest_repository_url(self):
        """
        UpdateManifest.clone_repo successfully clones a provided repository
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__real_repo,
            '--branch', 'master',
            '--manifest_repo', self.__real_manifest_repo
            ])
        self.um_class.assign_args(parsed)
        tmp_folder = self.um_class.clone_repo()
        self.assertTrue(os.path.isdir(tmp_folder))


    def test_clone_manifest_repository_url_bad_url_fails(self):
        """
        UpdateManifest.clone_repo throws an error b/c provided with nonexistent url to clone
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__real_repo,
            '--branch', 'master',
            '--manifest_repo', 'ssh://git@hwstashprd01.isus.emc.com:7999/hwimotools/mani.git'
            ])
        self.um_class.assign_args(parsed)
        tmp_folder = self.um_class.clone_repo()
        with self.assertRaises(TypeError):
            os.path(tmp_folder)


    def test_get_manifest_data_one_file(self):
        """
        UpdateManifest.get_manifest_files reads a target file
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__local_repo_to_change,
            '--branch', self.__local_branch,
            '--manifest_repo', self.__local_manifest_repo,
            '--manifest_file', self.__local_manifest_file
            ])
        self.um_class.assign_args(parsed)
        manifest_data = self.um_class.get_manifest_files(self.__local_manifest_folder)
        for filename in manifest_data:
            self.assertTrue(manifest_data[filename]['content']['repositories'])
            self.assertTrue(manifest_data[filename]['changed'] is False)


    def test_get_manifest_data_multiple_files(self):
        """
        UpdateManifest.get_manifest_files reads all files within a folder
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__local_repo_to_change,
            '--branch', self.__local_branch,
            '--manifest_repo', self.__local_manifest_repo,
            ])
        self.um_class.assign_args(parsed)
        manifest_data = self.um_class.get_manifest_files(self.__local_manifest_folder)
        for filename in manifest_data:
            self.assertTrue(manifest_data[filename]['content']['repositories'])
            self.assertTrue(manifest_data[filename]['changed'] is False)


    def test_get_manifest_data_has_bad_manifest_file_value(self):
        """
        UpdateManifest.get_manifest_files throws an error when target file does not exist
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__local_repo_to_change,
            '--branch', self.__local_branch,
            '--manifest_repo', self.__local_manifest_repo,
            '--manifest_file', 'doesnt-exist.json'
            ])
        self.um_class.assign_args(parsed)
        with self.assertRaises(IOError):
            self.um_class.get_manifest_files(self.__local_manifest_folder)


    def test_update_manifest_changed_is_true(self):
        """
        UpdateManifest.udpate_manifest successfully alters a provided manifest file
        """
        parsed = self.um_class.parse_args([
            '--repo', self.__local_repo_to_change,
            '--branch', self.__local_branch,
            '--manifest_repo', self.__local_manifest_repo,
            '--manifest_file', self.__local_manifest_file
            ])
        self.um_class.assign_args(parsed)
        manifest_data = self.um_class.get_manifest_files(self.__local_manifest_folder)
        for filename in manifest_data:
            manifest_data[filename] = self.um_class.update_manifest(manifest_data[filename])
            self.assertTrue(manifest_data[filename]['changed'])


#    def test_write_manifest_file(self):
#        """
#        UpdateManifest.write_manifest_file validates that a target manifest file has been written to
#        """
#        parsed = self.um_class.parse_args([
#            '--repo', self.__local_repo_to_change,
#            '--branch', self.__local_branch,
#            '--manifest_repo', self.__local_manifest_repo,
#            '--manifest_file', self.__local_manifest_file
#            ])
#        self.um_class.assign_args(parsed)
#        new_manifest_file = None
#        manifest_data = self.um_class.get_manifest_files(self.__local_manifest_folder)
#        for filename in manifest_data:
#            manifest_data[filename] = self.um_class.update_manifest(manifest_data[filename])
#            if manifest_data[filename]['changed']:
#                new_manifest_file = self.um_class.write_manifest_file(filename, self.__local_manifest_folder, manifest_data[filename]['content'])
#        self.assertTrue(os.path.isfile(new_manifest_file))
#        with open(new_manifest_file, 'r+') as new_file:
#            new_content = json.load(new_file)
#        found = False
#        for repo in new_content['repositories']:
#            if repo['repository'] == self.__local_repo_to_change and\
#                            repo['branch'] == self.__local_branch and\
#                            repo['commit-id'] == None:
#                found = True
#                repo['commit-id'] = '0000000000000000000000000000000000000000'
#                break
#        self.assertTrue(found)



if __name__ == '__main__':
    unittest.main()
