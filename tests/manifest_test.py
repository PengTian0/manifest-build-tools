#!/usr/bin/env python

import os
import unittest
from application.manifest import Manifest


testDataFiles = dict()
baseDir = os.path.dirname(os.path.abspath(__file__))

class ManifestTest(unittest.TestCase):

    __local_manifest_folder = os.path.join(baseDir, 'test_manifests')
    __local_manifest_file = 'correct_manifest'

    
    def setUp(self):
        
        self.manifest_class = Manifest(os.path.join(self.__local_manifest_folder, self.__local_manifest_file))

    def tearDown(self):
        del self.manifest_class

    def test_read_manifest_file_nonexist_file_fails(self):
        """
        Manifest read_manifest_file throw an error with nonexistent file
        """
        test_file = os.path.join(self.__local_manifest_folder, "nonexist_test")
        with self.assertRaises(KeyError):
            self.manifest_class.read_manifest_file(test_file)
    
    def test_read_manifest_file_bad_json_fails(self):
        """
        Manifest read_manifest_file throw an error with a bad json file
        """
        test_file = os.path.join(self.__local_manifest_folder, "bad_json")
        with self.assertRaises(ValueError):
            self.manifest_class.read_manifest_file(test_file)

    def test_parse_manifest_successful(self):

        """
        Manifest parse_manifest parse a right manifest file
        """
        test_file = os.path.join(self.__local_manifest_folder, "correct_manifest")
        self.manifest_class.read_manifest_file(test_file)
        self.manifest_class.parse_manifest()
        self.assertTrue(self.manifest_class.get_build_name())
        self.assertTrue(self.manifest_class.get_build_requirements())
        self.assertTrue(self.manifest_class.get_repositories())
        self.assertTrue(self.manifest_class.get_downstream_jobs())
        self.assertTrue(self.manifest_class.get_changed() is False)

    def test_validate_manifest_fails(self):
        """
        Manifest validate_manifest throw error when validate a manifest file which misses required tags
        Manifest files whose name start with "bad_manifest" all miss some required tags
        """
        for filename in os.listdir(self.__local_manifest_folder):
            test_file = os.path.join(self.__local_manifest_folder, filename)
            if filename.startswith("bad_manifest"):
                self.manifest_class.read_manifest_file(test_file)
                self.manifest_class.parse_manifest()
                with self.assertRaises(KeyError):
                    self.manifest_class.validate_manifest()


    def test_validate_manifest_succeed(self):
        """
        Manifest validate_manifest successfully validate a manifest file which is a good json 
        and contains all the required tags.
        Manifest files whose name start with "correct_manifest" are correct manifest.
        """
        for filename in os.listdir(self.__local_manifest_folder):
            test_file = os.path.join(self.__local_manifest_folder, filename)
            if filename.startswith("correct_manifest"):
                self.manifest_class.read_manifest_file(test_file)
                self.manifest_class.parse_manifest()
                raised = False
                try:
                    self.manifest_class.validate_manifest()
                except:
                    raised = True

                self.assertFalse(raised, 'Exception raised')


    def test_update_manifest_unchanged(self):
        """
        Manifest update_manifest should not update manifest if repository is not changed
        """ 
        test_file = os.path.join(self.__local_manifest_folder, "correct_manifest")
        self.manifest_class.read_manifest_file(test_file)
        self.manifest_class.parse_manifest()
        self.manifest_class.update_manifest("https://github.com/RackHD/on-http.git","master","f524774e296e7e178af265a4a26d2fd77a7ffa2e")
        self.assertTrue(self.manifest_class.get_changed() is False)

        

if __name__ == '__main__':
    unittest.main()
