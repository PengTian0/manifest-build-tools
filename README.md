# manifest-build-tools


## purpose

The content of this repository revolves around the automated maintenance of manifest files and system build procedures. 

## files

###update_manifest.py

This program takes a number of arguments and uses them to update target manifest files. Using a CI service like Jenkins or
Travis this should follow the successful build of a repository mentioned within a manifest file.
    
Given a repository url, a branch name, and a commit-id this will update the commit-id in all appropriate manifest files.
    
    Requires
        * --repo <The repository url being updated in the manifest>
        * --branch <The branch name for the --repo tag to match within the manifest file>
        * --manifest_repository_url <The repository url the points to the collection of manifest files>
    Optional
        * --commit <The commit id associated with the --repo and --branch that we want to update>
        * --manifest_file <The desired manifest file to update which resides in --manifest_repository_url>
        
        
###reprove.py

This file is under construction

Given a path to a manifest file and a directory name this will checkout all repositories within a manifest into that build
directory. When --force is added it will override a builddir name even if it already exists.

When performing a system build this will follow update_manifest.py

    Requires
        * --manifest <The repository manifest file>
        * --builddir <The destination for checked out repositories>
    Optional
        * --force

# build-manifests

## background
RackHD code is,for a variety of reasons, kept in multiple Git repositories. This is not likely to change, except that the number of repositories will almost certainly increase as functionality is added to the system.

Today, a Debian .deb package is built for each of the separate repositories (except for a couple of library repos that are used by multiple installed programs).  Those packages are built by Jenkins any time the repository is updated, and then the .deb files are uploaded to Artifactory.  From there, packages are installed onto the base operating system and the ORA is ready for use.

This works, provided everybody wants to install packages from the Debian repositories in Artifactory. Unfortunately, that's not always the case.

For example, someone with a new feature in onserve might want to test run in an ORA with that feature available.   We don't have a way to do that, except by the developer manually installing the new onserve in an ORA.   It's even worse if the new code is in a library used by many packages (say, logging).   Every package that uses the new library version would need to be rebuilt, and all of those packages installed into an ORA.

## purpose

In order to build the entire system at one go, instead of package by package, the repository is created.
We checkout everything needed for a release, perform a set of builds, and then install from this tree into a suitable base OS image, and then create an OVA snapshot of the result.   
The confusion of the package overhead is eliminated.

## files
Files in this repository are all in json format.
For each release branch, there is a json file.

### example
There are 3 elements in a json file:

```
{
    "build-name": "project-devel", 
    "repositories": [
        {
            "branch": "master", 
            "commit-id": "ba7c08be02e1482d3f16a33a8e0282e46e6f7398", 
            "repository": "https://github.com/RackHD/on-core.git"
        }, 
        {
            "branch": "master", 
            "repository": "https://github.com/RackHD/on-dhcp-proxy.git"
        }, 
        {
            "commit-id": "0a7b2fd6eabd2c5821de3a3b9ab64fdad4350f63", 
            "repository": "https://github.com/RackHD/on-http.git",
            "checked-out-directory-name": "onrack"
        } 
    ],
     "downstream-jobs": [
        {
            "branch": "master",
            "command": "./HWIMO-BUILD",
            "commit-id": "cc480b840dad20413abcf9d3823c03be5a9ad1b8",
            "purpose": "Make Updater",
            "repository": "https://github.com/RackHD/testrepo1.git",
            "running-label": "xxx",
            "working-directory": "testrepo1/updater"
        },
        {
            "branch": "master",
            "command": "./HWIMO-BUILD",
            "commit-id": "cc29159cf58bfbbe4c95e638767943aa594024a2",
            "purpose": "Build Onrack OVA",
            "repository": "https://github.com/RackHD/testrepo2.git",
            "running-label": "vmworkstation12",
            "working-directory": "testrepo2/packer",
            "downstream-jobs": [
                {
                    "branch": "master",
                    "command": "./HWIMO-BUILD",
                    "commit-id": "cc480b840dad20413abcf9d3823c03be5a9ad1b8",
                    "purpose": "Autotest Smoke Test",
                    "repository": "https://github.com/RackHD/testrepo3.git",
                    "running-label": "ci-director",
                    "working-directory": "testrepo3/autotest"
                }
            ]
        }
    ]
}
```

##### build-name 
  - **semantic**:
      The repository of the build system is prefix by the value of this element.
  - **syntactic**:
```
"build-name": "onrack-xxx"
```
##### repositories 
  - **semantic**: 
      A Jenkins job will checkout all repositories within the field 
      and build a debian repository with the repositories. 
  - **syntactic**:
```
repositories: [
   {
       "branch": "xxx",                                           
       "checked-out-directory-name": "xxx", 
       "commit-id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
       "repository": "https://eos2git.cec.lab.emc.com/xxx/xxx.git" 
   }
   ...
]
```
  - **semantic for each field**:
    
   Requires
    * **repository**: the url of the repository. 

   Optional
    * **branch**: the branch name for the repository. If commit-id is not provided, it is required. 
    * **commit-id**: the commit id associated with the repository and branch. If branch is not provided, it is required. If it is not provided, the job update-manifest run for this entry would add a commit-id field to the entry. 
   
        So, branch and commit-id should be provided at least one. Below is an invalid example:
        ```
        {
            "repository": "https://eos2git.cec.lab.emc.com/xxx/xxx.git"
        }
        ```

    * **checked-out-directory-name**: the local directory name for check out the repository, such as "onrack" for repository "https://eos2git.cec.lab.emc.com/OnRack/onrack-base.git"



##### downstream-jobs 
  - **semantic**: 
      Support branching the tool repositories for OVA building, update bundle building 
      and smoke test aginst built OVA. 
      This field support nest.
      For each entry of the field,the Bounce-Job will start a building with the items in the entry as parameters.
  - **syntactic**:
```
"downstream-jobs": [
    {
        "branch": "xxx",
        "command": "xxx",
        "commit-id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "purpose": "xxx",
        "repository": "https://eos2git.cec.lab.emc.com/xxx/xxx.git",
        "running-label": "xxx", 
        "working-directory": "xxx",
        "downstream-jobs": [
                {
                    "branch": "xxx",
                    "command": "xxx",
                    "commit-id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "purpose": "xxx",
                    "repository": "https://github.com/RackHD/testrepo3.git",
                    "running-label": "xxx",
                    "working-directory": "xxx"
                }
            ]
    },
    ...
]
```
  - **semantic for each field**:

   Requires
    * **repository**: the url of the repository.
    * **command**: the command that the Jenkins job will run, typically a script to do the building, such as: ./HWIMO-BUILD
    * **working-directory**: where the Jenkins job run command.
    * **running-label**: the name or label of the Jenkins slave node where the job runs.

   Optional
    * **branch**: the branch name for the repository. If commit-id is not provided, it is required.
    * **commit-id**: the commit id associated with the repository and branch. If branch is not provided, it is required. If it is not provided, the job update-manifest run for this entry would add a commit-id field to the entry.
    * **purpose**: what the Jenkins job are doing and the job will add it to build name and notification message.
                   If it is not set, the Jenkins job will use the default value: null
    * **downstream-jobs**: the triggered build of Jenkins job will accept the field as a string parameter and the build can trigger another build by parsing the parameter.

### onrack-devel
File for master branch.
The file keeps pace with the example both in syntactic and semantic.
     
### onrack-release-1.2.0
File for release branch 1.2.0.
The file keeps pace with the example both in syntactic and semantic.

### onrack-release-1.1.0
File for release branch 1.1.0.
The file keeps pace with the example both in syntactic and semantic.

