
# KinGit
Ever got credentials of gitlab account in your engagements?
This tool is made for red teamers and ethical hackers in order to extract all kinds of secrets from a gitlab instance.

## How it works?
The tool first enumerates all the projects in the gitlab instance using the compromised account (by it's api token).
It then can do one or more of the following:
1. Extract all the CICD secrets for every project that was found during the enumeration phase.
2. Scan the code of each commit of every project that was found during the enumeration phase and find pre-defined secrets in it. This includes every commit the project.

## Setup
Log in to the gitlab with the compromised user and create an api key.

## Usage
The tools takes a couple of arguments:
* ```username``` - The username of the compromised user. This is a mandatory value.
* ```key``` - The API Token of the compromised user. This is a mandatory value.
* ```instance``` - URL of the gitlab instance (e.g https://gitlab.local).
* ```threads``` - The number of threads to use when enumerating the projects and extracting the CICD variables of each project.
* ```patterns``` - The path of the .toml file that contains the regex patterns for the secrets to find (default is "CURRENT_WORKING_DIRECTORY\patterms.toml")
* ```mode``` - The operations to do when running:<br />
&emsp;A - All - Do all the possible operations (currently - Extract CICD variables + code secrets).<br />
&emsp;C - CICD - Extract CICD variables only.<br />
&emsp;S - Code Secrets - Extracts code secrets only.<br />
&emsp;The default value of this argument is "A". Notice that you can specify a couple of modes at once by using comma (e.g C,S).
* ```export-projects``` - export the projects list we enumerated to .txt file (default is False).
* ```ssl-verify``` - Use SSL certificates when interacting the gitlab api via HTTPS (default is False).
* ```verbose``` - Add printings for debugging and/or monitoring (default is False).<br />

All the default values for the arguments that are not required can be easily changed in the ```config.conf``` file in the project's folder.

### Example Usage
The following command extracts all kinds of secrets from the https://gitlab.local gitlab instance:<br />
```python KinGit.py -u root -k <API_TOKEN> -i https://gitlab.local -e -v```

## Notes
* You can change the configs as you wish in the ```config.conf``` file.
* The tool will find secrets only in the commit where they had been added in. This is done to keep the tool as efficient and fast as possible. Remember, this tool is not made for DevSecOps, but for ethical hackers and red teamers.

## Credits
[Roy Rahamim](https://twitter.com/0xRoyR) - Coding the tool.

[The gitleaks project](https://github.com/gitleaks/gitleaks) - The default regexes for sensitive information were taken from there
