import subprocess
import requests
import json
import re
from constants import *


def verbose_print(message: str, verbose: bool):
    """
    This function is getting a message to print and a verbosity flag. If the verbose flag is turned on, the function
    will print the message.
    :param message: String. The message to print.
    :param verbose: Boolean. Indicates if the user want to display the message.
    :return: None.
    """

    if verbose:
        print(message)


def extract_added_content(diff: str):
    """
    This function gets commit diff data (which contains added and removed content) and extracts the added content
    from it.
    In addition, we also get the file which content was added to, for each time we find added content. This helps us
    later in documenting where exactly in the commit the secret was found.
    :param diff: String. A commit diff data.
    :return:
    """

    # Split the diff into lines
    lines = re.split('\\\\n', diff)

    file_path = 'nulled_file_path'
    start_line = None

    for i, line in enumerate(lines):
        if line.startswith('+++ '):
            file_path = line[6:]
        if line.startswith("@@"):
            start_line = i + 1
            break

    added_content = []
    for line in lines[start_line:]:
        if line.startswith('+') and not line.startswith('+++'):
            added_content.append(line[1:])

    return file_path, '\\n'.join(added_content)


class Project:
    def __init__(self, proj_name: str, proj_id: int, instance: str, verify_ssl: bool, patterns: dict, verbose: bool):
        """
        Initialization method for the 'Project' class.
        :param proj_name: String. The url of the current gitlab project.
        :param proj_id: Integer. The id of the current project.
        :param instance: String. The url to the gitlab instance in which this project is in.
        :param verify_ssl: Boolean. Indicates if we should or should not use ssl when interacting with the gitlab api.
        :param patterns: Dictionary. Contains all the secrets' regex patterns, and some metadata on each secret.
        :param verbose: Boolean. Indicates if we should print status messages or not.
        """

        self.proj_name: str = proj_name
        self.proj_id: int = proj_id
        self.instance: str = instance
        self.verify_ssl: bool = verify_ssl
        self.patterns: dict = patterns
        self.verbose: bool = verbose

        self.cicd_secrets: list[tuple] = []
        self.code_secrets: list[list[str, str, str, int]] = []

    def get_cicd_variables(self, private_token):
        """
        This function gets the cicd variables for the current Project instace.
        :return:
        """

        # Get the cicd variables through gitlab apis
        r = requests.get(VARIABLES_API_URL_FORMAT.format(self.instance, self.proj_id, private_token),
                         verify=self.verify_ssl)
        if r.status_code == 200 and r.content != b'[]':
            json_cicd_secrets = json.loads(r.content.decode(UTF_8_ENCODING))
            for secret in json_cicd_secrets:
                self.cicd_secrets.append((secret['key'], secret['value']))

    def inspect_code(self):
        """
        This function enumerates all the commits for each project.
        For each commit, the function will get all the data that was added and look for the presence of secrets in it.
        Because the only thing that is checked is the added data, if secret is present in the added data of one commit
        and is not changed in later commits, it will NOT show up in the results of the later commits.
        This makes our code to miss duplications, but we don't need to get the same secret twice - we just want to find
        all the secrets as fast as possible.
        :return:
        """

        # Get all the modifications in the commit.
        r = subprocess.Popen(GIT_GET_ALL_PROJECT_HISTORY.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=False)
        out, err = r.communicate()
        if err:
            print('(-) Error inspecting {0}. Skipping.'.format(self.proj_name))
            print(err)
            return
        out = str(out)[2:-1]

        # Split the output of the 'GIT_GET_ALL_PROJECT_HISTORY' command into chunks. Each chunk is a commit.
        splitted_out = re.split(RE_SPLIT_TO_COMMITS, out)
        splitted_out = [commit_data for commit_data in splitted_out if commit_data]
        splitted_tup_out = []
        for i in range(0, len(splitted_out), 3):
            splitted_tup_out.append((splitted_out[i], '{0}{1}'.format(splitted_out[i + 1], splitted_out[i + 2])))

        # From each commit, extract only its added content and then look for secrets in it.
        for commit_hash, commit_data in splitted_tup_out:
            # Split the output into chunks containing the diffs in each file in the commit.
            diffs = re.split(RE_SPLIT_TO_DIFFS, commit_data)
            for diff in diffs:
                file_path, curr_added_content = extract_added_content(diff)
                if curr_added_content:
                    for pattern, metadata in self.patterns.items():
                        try:
                            res = re.findall(pattern, curr_added_content)
                        except re.error:
                            print('The pattern {0} is invalid. Skipping.'.format(pattern))
                            continue

                        # If secrets were found, add the info about them to the 'self.code_secrets' list of the current
                        # instance.
                        if res:
                            times_found = len(res)
                            # This variable is important. Before that line, we tried to use
                            # metadata += [additional_data], but it destroyed changed the metadata in the patterns
                            # array, which caused an unexpected behavior in the results.
                            secret_row = metadata + ['{0}/-/tree/{1}/{2}'.format(self.proj_name, commit_hash,
                                                                                 file_path), times_found]
                            self.code_secrets.append(secret_row)
                            res.clear()

        if self.code_secrets:
            verbose_print(FOUND_CODE_SECRETS_VERBOSE, self.verbose)

        # Delete all the commit data that we got for better handling the memory, as this data can be quite big.
        del out
        del splitted_out
        del splitted_tup_out

    def clone_project(self, username, private_token, temp_folder):
        """
        This function is responsible of cloning a gitlab project to a predefined location in the file system.
        :return:
        """

        # Add the username and the private token of the username to the url in order to have access to clone the
        # project.
        clone_url = self.proj_name.split(r'://')
        clone_url[1] = r'{0}:{1}@'.format(username, private_token) + clone_url[1]
        clone_url = r'://'.join(clone_url)
        verbose_print(CLONE_PROJECT_VERBOSE.format(clone_url), self.verbose)

        # Clone the project into the 'temp_folder' directory. 'temp_folder' is a subdirectory of the current directory.
        if not self.verify_ssl:
            r = subprocess.Popen(GIT_CLONE_NOSSL.format(clone_url, temp_folder).split(' '),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        else:
            r = subprocess.Popen(GIT_CLONE.format(clone_url, temp_folder).split(' '),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        out, err = r.communicate()

        # Make sure there are no errors
        err = err.decode()
        if err and 'redirecting to http' not in err:
            print('(+) Error cloning {}. Skipping.'.format(clone_url))
            print(err)
