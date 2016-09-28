#test_manifests


## purpose

The files in this folder are used to test functions which use or deal with manifest.

## files

###bad_json

The file is a bad json file which omit a "," after the 3 line: 
```
"build-requirements": "test"
```

###bad_manifest1

The file omit "branch" and "commit-id" in an entry of "repositories":

```
        {
            "repository": "https://github.com/leachim6/hello-world.git"
        }
```

###bad_manifest2

The file omit "repository" in an entry of "repositories":
```
        {
            "branch": "master",
            "commit-id": null
        }
```

###bad_manifest3
The file omit "branch" and "commit-id" in an entry of "downstream-jobs":
```
        {
            "command": "./HWIMO-BUILD",
            "purpose": "Smoke Test",
            "repository": "https://github.com/RackHD/on-http.git",
            "running-label": "ci-test",
            "working-directory": "on-http"
        }
```
###bad_manifest4
The file omit "command" in an entry of "downstream-jobs":
```
        {
            "branch": "master",
            "commit-id": "f524774e296e7e178af265a4a26d2fd77a7ffa2e",
            "purpose": "Smoke Test",
            "repository": "https://github.com/RackHD/on-http.git",
            "running-label": "ci-test",
            "working-directory": "on-http"
        }
```

###bad_manifest5
The file omit "repository" in an entry of "downstream-jobs":
```
        {
            "branch": "master",
            "command": "./HWIMO-BUILD",
            "commit-id": "f524774e296e7e178af265a4a26d2fd77a7ffa2e",
            "purpose": "Smoke Test",
            "running-label": "ci-test",
            "working-directory": "on-http"
        }
```

###bad_manifest6
The file omit "running-label" in an entry of "downstream-jobs":
```
        {
            "branch": "master",
            "command": "./HWIMO-BUILD",
            "commit-id": "f524774e296e7e178af265a4a26d2fd77a7ffa2e",
            "purpose": "Smoke Test",
            "repository": "https://github.com/RackHD/on-http.git",
            "working-directory": "on-http"
        }
```

###bad_manifest7
The file omit "working-directory" in an entry of "downstream-jobs":
```
       {
            "branch": "master",
            "command": "./HWIMO-BUILD",
            "commit-id": "f524774e296e7e178af265a4a26d2fd77a7ffa2e",
            "purpose": "Smoke Test",
            "repository": "https://github.com/RackHD/on-http.git",
            "running-label": "ci-test"
        }
```

###bad_manifest8
The file omit "working-directory" and "command" in an nested "downstream-jobs":
```
        "downstream-jobs": [
              {
                    "branch": "master",
                    "commit-id": "f524774e296e7e178af265a4a26d2fd77a7ffa2e",
                    "purpose": "Smoke Test",
                    "repository": "https://github.com/RackHD/on-http.git",
                    "running-label": "ci-test"
              }
        ]
```

###correct_manifest
The file is an example for a correct manifest.

Both "branch" and "commit-id" are set.

###correct_manifest.json
The file is an example for a correct manifest.

Only "branch" is set:
```
        {
            "branch": "master", 
            "commit-id": null, 
            "repository": "https://github.com/leachim6/hello-world.git"
        }
```

Only "commit-id" is set:
```
        {
            "commit-id": "c05c9de9f6f318cdd57156f827f9c198cbde0c84",
            "repository": "https://github.com/RackHD/on-tasks.git"
        }
```
