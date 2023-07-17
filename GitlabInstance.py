import stat
import time
import threading
import urllib3
import csv
import os
import shutil
import datetime
import tomli
from Project import *


urllib3.disable_warnings()


def on_error_deleting_clone_path(func, path, exc_info):
    """
    This function is responsible for trying once again to delete a git clone before raising an error
    :param func:
    :param path:
    :param exc_info:
    :return:
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)
    except FileNotFoundError:
        pass
    except PermissionError:
        print('Some permission error. Giving it one more chance after sleeping for five seconds')
        time.sleep(5)
        shutil.rmtree(path)


class GitlabInstance:
    def __init__(self, username: str, private_token: str, instance: str, mode: str, threads_count: int,
                 verify_ssl: bool, save_projects: bool, verbose: bool, patterns_path: str, output: str):
        """
        Initialization function for the 'GitlabInstance' class.
        :param instance: String. The URL of the gitlab instance.
        :param threads_count: Integer. The number of threads to use in getting the projects and the cicd secrets.
        :param verify_ssl: Boolean. Indicates if we need to use SSL when interacting with the gitlab api of the current
        instance.
        :param patterns_path: String. The path to the toml file which contains the regex patterns to find the secrets in
        the code of the projects.
        :param output: String. The path to the directory that will contain the outputs for each run
        """

        # Gitlab specifics.
        self.username: str = username
        self.private_token: str = private_token
        self.instance: str = instance
        self.verify_ssl: bool = verify_ssl

        # Defines operations does the user want to do:
        # A = All
        # C = CICD Vars
        # S = Code Secres
        self.mode: str = ''
        if MODE_ALL in mode.upper().split(','):
            self.mode = MODE_ALL
        else:
            if MODE_CICD_VARIABLES in mode.upper().split(',') and MODE_CICD_VARIABLES not in self.mode:
                self.mode += MODE_CICD_VARIABLES
            if MODE_CODE_SECRETS in mode.upper().split(',') and MODE_CODE_SECRETS not in self.mode:
                self.mode += MODE_CODE_SECRETS
        if not self.mode:
            raise INVALID_MODE_ERROR

        # File system specifics.
        self.cwd: str = os.getcwd()

        # Define the path of the directory that will contain the output directories for each run.
        if not output:
            self.results_root_directory: str = os.path.join(self.cwd, RESULTS_FOLDER_NAME_DEFAULT)
        else:
            self.results_root_directory: str = output

        # Define the output directory for the current run. The name of this directory will be the current time.
        self.output_path: str = os.path.join(self.results_root_directory,
                                             datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))

        # The name of the temp folder to create when cloning a project
        self.temp_folder: str = TEMP_FOLDER_NAME_DEFAULT
        self.clone_path: str = os.path.join(self.cwd, self.temp_folder)

        # Make sure that the path that the projects will be cloned to does not exist. If it exists, we will run into an
        # error.
        if os.path.isdir(self.clone_path):
            shutil.rmtree(self.clone_path, onerror=on_error_deleting_clone_path)

        self.threads: list[threading.Thread] = []
        self.threads_counter: int = threads_count
        self.pages_counter: int = 0

        self.response: list[dict] = []

        self.ids: list[int] = []
        self.projects: list[Project] = []
        self.projects_counter: int = 0

        self.secrets: list = []

        self.patterns: dict = {}
        if patterns_path == PATTERNS_PATH_DEFAULT:
            self.patterns_path: str = os.path.join(self.cwd, PATTERNS_PATH_DEFAULT)
        else:
            self.patterns_path: str = patterns_path
        if not os.path.isfile(self.patterns_path):
            raise PATTERNS_FILE_NOT_FOUND_ERROR

        self.save_projects: bool = save_projects

        self.verbose: bool = verbose

    def caller(self):
        """
        This function is responsible for calling the different functions in the 'GitlabInstance' class, based on the
        client preferences (which are specified in the 'mode' :argument).
        :return: None
        """

        # Create the output directory, if it does not already exist.
        os.makedirs(self.output_path, exist_ok=True)

        # Enumerate all the projects. That should happen in any mode.
        self.enum_projects()

        # Do the operations that the client had specified in the 'mode' argument.
        if MODE_ALL in self.mode:
            self.extract_all_cicd_secrets()
            self.extract_code_secrets()
        else:
            if MODE_CICD_VARIABLES in self.mode:
                self.extract_all_cicd_secrets()
            if MODE_CODE_SECRETS in self.mode:
                self.extract_code_secrets()

    def enum_projects_at_page(self, page: int):
        """
        This function sends a request to gitlab's api in order to get all the projects in the current page.
        Furthermore, this funtion then create a 'Project' class instance for each project found, and appends it
        to the 'self.projects' list
        :param page: Integer. The number of the current page.
        :return: None
        """

        # response is a list that contains json objects. Each json is a project.
        self.response = requests.get(PROJECTS_API_URL_FORMAT.format(self.instance, self.private_token, page + 1),
                                     verify=self.verify_ssl).json()

        # Avoid duplications by:
        # 1. Saving each new project's id in the 'self.ids' list.
        # 2. Before creating new Project instance for the current project, check that it's id is not already present
        # in the 'self.ids' list (indicates that this project is new).
        for project in self.response:
            if project['id'] not in self.ids:
                # Remove the ".git" extention from the project url if it exists.
                curr_url = project['http_url_to_repo']
                curr_url = curr_url[:-4] if curr_url.endswith('.git') else curr_url

                # Create a 'Project' instance for the current project and append it to the 'self.projects' list.
                new_project = Project(proj_name=curr_url, proj_id=project['id'], instance=self.instance,
                                      verify_ssl=self.verify_ssl, patterns=self.patterns, verbose=self.verbose)
                self.projects.append(new_project)
                self.ids.append(project['id'])

    def enum_projects(self):
        """
        This function enumerates all the projects in the current gitlab instance
        :return: None
        """

        verbose_print(ENUM_PROJECTS_START_VERBOSE.format(self.instance), self.verbose)

        # While the gitlab api returns a list of projects, it means that there are more projects to enumerate.
        # Once we enumerate all the gitlab projects, the response will be an empty array (b'[]').
        self.response = [1, 2, 3]
        while self.response:
            # Get the next chunk of pages, create a thread for each page and start the thread.
            # the size of each chunk of pages equals to the number of threads ('self.threads_counter').
            for i in range(self.pages_counter, self.pages_counter + self.threads_counter):
                curr_thread = threading.Thread(target=self.enum_projects_at_page, args=(self.pages_counter,))
                self.threads.append(curr_thread)
            for thread in self.threads:
                thread.start()
            for thread in self.threads:
                thread.join()
            self.threads.clear()
            # Update the number of the current page.
            self.pages_counter += self.threads_counter
            # Update the number of projects discovered so far.
            self.projects_counter = len(self.projects)
            verbose_print(ENUM_PROJECTS_STATUS_VERBOSE.format(
                self.threads_counter, self.pages_counter, self.projects_counter), self.verbose)

        verbose_print(ENUM_PROJECTS_FINISH_VERBOSE.format(self.instance), self.verbose)

        # Save the projects urls in the output directory if the client had specified it.
        if self.save_projects:
            projects_urls_output_path = os.path.join(self.output_path, SAVE_PROJECTS_URLS_FILE_NAME_DEFAULT)
            with open(projects_urls_output_path, MODE_WRITE) as file:
                for project in self.projects:
                    file.write(project.proj_name + '\n')

            verbose_print(EXTRACT_PROJECTS_URLS_FINISH.format(projects_urls_output_path), self.verbose)

    def extract_all_cicd_secrets(self):
        """
        This function is responsible to go through all the enumerated projects, and for each project, the function will
        call it's 'get_cicd_variables' which returns the cicd variables of the current projects.
        :return: None
        """

        verbose_print(EXTRACT_CICD_START_VERBOSE, self.verbose)
        # Enumerate all the projects.
        for i in range(0, self.projects_counter, self.threads_counter):
            self.threads.clear()
            # Create 'self.threads_counter' amount of threads each iteration.
            for t in range(i, i + self.threads_counter):
                # Make sure we didn't go higher than the amount of projects in the instance.
                if t < self.projects_counter:
                    curr_project = self.projects[t]
                    # Create a thread to the current project's 'get_cicd_variables' method.
                    curr_thread = threading.Thread(target=curr_project.get_cicd_variables, args=(self.private_token,))
                    self.threads.append(curr_thread)
            for curr_thread in self.threads:
                curr_thread.start()
            for curr_thread in self.threads:
                curr_thread.join()

        verbose_print(EXTRACT_CICD_FINISH_VERBOSE, self.verbose)

        # Export the cicd variables.
        self.export_cicd_secrets()

    def export_cicd_secrets(self):
        """
        This function is responsible to export collected cicd secrets into a csv file.
        :return: None
        """

        verbose_print(EXPORT_CICD_START_VERBOSE, self.verbose)

        # Write to the output file all the current cicd variables.
        cicd_vars_output_path = os.path.join(self.output_path, CICD_VARS_FILE_NAME_DEFAULT)
        with open(cicd_vars_output_path, MODE_WRITE, encoding=UTF_8_ENCODING, newline='') as file:
            writer = csv.writer(file)
            writer.writerow(COLUMNS_HEADERS_CICD_VARIABLES)
            for project in self.projects:
                if project.cicd_secrets:
                    for cicd_secret in project.cicd_secrets:
                        writer.writerow([project.proj_id, project.proj_name, cicd_secret[0], cicd_secret[1]])

        verbose_print(EXPORT_CICD_FINISH_VERBOSE, self.verbose)

    def load_patterns(self):
        """
        This function is used for loading all the possible regex patterns of the secrets to be found.
        :return: None
        """

        # Load the data of the toml file that contains the regex patterns for the secrets.
        with open(self.patterns_path, 'rb') as file:
            toml_dict = tomli.load(file)

        # Convert the toml into an easy-iteratable dictionary
        for category_name, category_value in toml_dict.items():
            for sub_category in category_value:

                # Make sure that there is a description (sub_category_name) and at least one regex pattern for the
                # current sub category
                if PATTERNS_VALUE_SUB_CATEGORY_NAME not in sub_category.keys() or \
                        PATTERNS_VALUE_REGEX not in sub_category.keys():
                    print(PATTERNS_INCOMPLETE_PATTERN_IN_TOML_FILE)
                    continue

                # Get the regex/es of the current sub category
                regex = sub_category[PATTERNS_VALUE_REGEX]

                # Add the pattern/s to the keys of the 'self.patterns' dictionary and the metadata ('category_name',
                # sub_category[PATTERNS_VALUE_SUB_CATEGORY_NAME]) to the value of this key (value type: list).
                # If the regex (or one of the regexes we got in a list) is not of type 'str', it's an invalid regex and
                # we should skip it and continue to the next iteration.
                if type(regex) == str:
                    self.patterns[regex] = [category_name, sub_category[PATTERNS_VALUE_SUB_CATEGORY_NAME]]
                elif type(regex) == list:
                    for r in regex:
                        if type(r) != str:
                            print(PATTERNS_INVALID_REGEX_IN_TOML_FILE.format(category_name, sub_category))
                            continue
                        self.patterns[r] = [category_name, sub_category[PATTERNS_VALUE_SUB_CATEGORY_NAME]]
                else:
                    print(PATTERNS_INVALID_REGEX_IN_TOML_FILE.format(category_name, sub_category))
                    continue

        # Delete the loaded toml content. We do not need it anymore because we got the dictionary representation of it
        # in the previous step.
        del toml_dict

        verbose_print(LOAD_PATTERNS_FINISH_VERBOSE.format(self.patterns_path), self.verbose)

    def write_code_secrets(self, secrets: list[list[str, str, str, int]]):
        """
        This function writes a list of secrets to a desired output file.
        :param secrets: List<List>. A list containing a list of metadata
        :return: None
        """

        # Open the output file and append to it the current secrets.
        with open(os.path.join(self.output_path, SECRETS_FILE_NAME_DEFAULT), MODE_APPEND, encoding=UTF_8_ENCODING,
                  newline='') as file:
            writer = csv.writer(file)
            for secret_metadata in secrets:
                writer.writerow(secret_metadata)

    def extract_code_secrets(self):
        """
        This function iterates a given projects list 'projects_urls' and checks for secrets in all the commits of each
        one of them. Each url in the list must be a project that was scanned with the tool in the 'enum_projects'
        method.
        :param projects_urls: A list that contains URLs to gitlab projects
        :return: None
        """

        verbose_print(EXTRACT_CODE_SECRETS_START_VERBOSE, self.verbose)

        # Prepare the output file with column headers
        self.write_code_secrets([COLUMNS_HEADERS_CODE_SECRETS])

        # Load all the secrets regex patterns.
        self.load_patterns()

        secrets_to_write = []
        # For every project, clone it and call it's 'inspect_code' method.
        for i, proj in enumerate(self.projects):
            proj.clone_project(self.username, self.private_token, self.temp_folder)
            os.chdir(self.clone_path)

            proj.inspect_code()

            # If secrets were found, add them to the secrets list.
            if proj.code_secrets:
                secrets_to_write += proj.code_secrets

            # If the number of secrets is equal or greater than 'MAX_SECRETS_BEFORE_SAVING_DEFAULT', save the secrets
            # to the desired output file.
            if len(secrets_to_write) >= MAX_SECRETS_BEFORE_SAVING_DEFAULT:
                self.write_code_secrets(secrets_to_write)
                secrets_to_write.clear()
            os.chdir(self.cwd)

            shutil.rmtree(self.clone_path, onerror=on_error_deleting_clone_path)

        # Write the remained secrets to the desired output file.
        self.write_code_secrets(secrets_to_write)
        secrets_to_write.clear()

        verbose_print(EXTRACT_CODE_SECRETS_FINISH_VERBOSE, self.verbose)
