from configparser import ConfigParser

config = ConfigParser()
config.read('config.conf')

# ------------------------------
# Config Defaults
# ------------------------------
PATTERNS_PATH_DEFAULT = config['PATHS']['PATTERNS_PATH_CONF']
TEMP_FOLDER_NAME_DEFAULT = config['PATHS']['TEMP_FOLDER_NAME_CONF']
RESULTS_FOLDER_NAME_DEFAULT = config['PATHS']['RESULTS_FOLDER_NAME_CONF']
SECRETS_FILE_NAME_DEFAULT = config['PATHS']['SECERTS_FILENAME_CONF']
CICD_VARS_FILE_NAME_DEFAULT = config['PATHS']['CICD_VARS_FILENAME_CONF']
MAX_SECRETS_BEFORE_SAVING_DEFAULT = int(config['EFFICIENCY']['MAX_SECRETS_BEFORE_SAVING_CONF'])
NUMBER_OF_THREADS_DEFAULT = int(config['EFFICIENCY']['NUMBER_OF_THREADS_CONF'])
SAVE_PROJECTS_URLS_FILE_NAME_DEFAULT = config['PATHS']['SAVE_PROJECTS_URLS_FILE_NAME_CONF']
OUTPUT_FOLDER_PATH_DEFAULT = config['PATHS']['OUTPUT_FOLDER_PATH']

# ------------------------------
# Gitlab API Constants
# ------------------------------
PROJECTS_API_URL_FORMAT = '{0}/api/v4/projects?private_token={1}&per_page=100&page={2}'
VARIABLES_API_URL_FORMAT = '{0}/api/v4/projects/{1}/variables?private_token={2}'
COMMITS_API_URL_FORMAT = '{0}/api/v4/projects/{1}/repository/commits?all=true'
DIFF_API_URL_FORMAT = '{0}/api/v4/projects/{1}/repository/compare?from={2}&to={3}'

# ------------------------------
# Git CLI commands
# ------------------------------
GIT_CLONE = 'git clone {0} {1}'
GIT_CLONE_NOSSL = 'git clone -c http.sslVerify=false {0} {1}'
GIT_GET_ALL_PROJECT_HISTORY = 'git log -p -U0 --full-history --all --diff-filter=AM'

# ------------------------------
# Modes Options
# ------------------------------
MODE_CICD_VARIABLES = 'C'
MODE_CODE_SECRETS = 'S'
MODE_ALL = 'A'

# ------------------------------
# Regex patterns
# ------------------------------
RE_SPLIT_TO_COMMITS = 'commit ([a-z0-9]{40})(\\\\nAuthor:)'
RE_SPLIT_TO_DIFFS = '\\\\ndiff --git'

# ------------------------------
# File system constants
# ------------------------------
MODE_READ = 'r'
MODE_WRITE = 'w'
MODE_APPEND = 'a'
UTF_8_ENCODING = 'utf-8'

# ------------------------------
# Patterns Loading
# ------------------------------
PATTERNS_VALUE_SUB_CATEGORY_NAME = 'sub_category_name'
PATTERNS_VALUE_REGEX = 'regex'
PATTERNS_INCOMPLETE_PATTERN_IN_TOML_FILE = '(-) A sub_category_name and regex variables must be present for every ' \
                                           'sub category in the toml file. Skipping.'
PATTERNS_INVALID_REGEX_IN_TOML_FILE = '(-) Invalid regex at {0}[{1}]. Skipping.'

# ------------------------------
# Errors Raising
# ------------------------------
PATTERNS_FILE_NOT_FOUND_ERROR = '(-) Patterns file not found!'
INVALID_MODE_ERROR = '(-) Invalid mode'

# ------------------------------
# Verbose
# ------------------------------
ENUM_PROJECTS_START_VERBOSE = '(+) Starting to enumerate the projects in {0}'
ENUM_PROJECTS_STATUS_VERBOSE = '\tScanned +{0} pages (Total: {1} pages, {2} projects - before removing duplicates)'
ENUM_PROJECTS_FINISH_VERBOSE = '(+) Successfully enumerated all the projects in {0}'
EXTRACT_PROJECTS_URLS_FINISH = '(+) Successfully extracted all the projects urls to {0}'
EXTRACT_CICD_START_VERBOSE = '(+) Extracting the CICD secrets of every project.'
EXTRACT_CICD_FINISH_VERBOSE = '(+) Successfully extracted the CICD secrets of every project.'
EXPORT_CICD_START_VERBOSE = '(+) Exporting the CICD secrets to a csv file'
EXPORT_CICD_FINISH_VERBOSE = '(+) Done Exporting'
EXTRACT_CODE_SECRETS_START_VERBOSE = '(+) Starting to extract all the code secrets of each project'
EXTRACT_CODE_SECRETS_FINISH_VERBOSE = '(+) Successfully extracted all the code secrets of each project'
LOAD_PATTERNS_FINISH_VERBOSE = '(+) Successfully loaded all the regex patterns from {}'
CLONE_PROJECT_VERBOSE = '\tCloning {}'
FOUND_CODE_SECRETS_VERBOSE = '\t\tSecrets were found in the current project\'s code!'

# ------------------------------
# Argparse
# ------------------------------
DESCRIPTION_ARGPARSE = 'This tool was created for read teamers to easily and efficiently enumerate gitlab instance and ' \
                       'extract all sorts of secrets in it.'
STORE_TRUE_ARGPARSE = 'store_true'
USERNAME_PARAM_ARGPARSE = [
    '-u',
    '--username',
    'The username of the user we got on gitlab'
]
KEY_PARAM_ARGPARSE = [
    '-k',
    '--key',
    'The API key of the user we got on gitlab'
]
INSTANCE_PARAM_ARGPARSE = [
    '-i',
    '--instance',
    'URL of the gitlab instance.'
]
THREADS_PARAM_ARGPARSE = [
    '-t',
    '--threads',
    'Number of threads for enumerating the projects.'
]
SSL_PARAM_ARGPARSE = [
    '-s',
    '--ssl_verify',
    'Use SSL certificates.'
]
VERBOSE_PARAM_ARGPARSE = [
    '-v',
    '--verbose',
    'Add verbosity. Might slow the program.'
]
PATTERNS_PARAM_ARGPARSE = [
    '-p',
    '--patterns',
    'Define a custom path to the yaml file containing the regex patterns'
]
MODE_PARAM_ARGPARSE = [
    '-m',
    '--mode',
    'Do a specific task(/s): C (CICD): Get only the cicd secrets. S (Code Secrets): Get the code secrets. A (All) '
    'Get all the secrets.'
]
EXPORT_PROJECTS_PARAM_ARGPARSE = [
    '-e',
    '--export-projects',
    'Export the projects list that we have access to in the current instance.'
]

# ------------------------------
# Misc
# ------------------------------
COLUMNS_HEADERS_CICD_VARIABLES = ['Project ID', 'Project URL', 'Variable Name', 'Variable Value']
COLUMNS_HEADERS_CODE_SECRETS = ['Category', 'Sub Category', 'Location', 'Times Found']

# ------------------------------
# Banner
# ------------------------------
BANNER = r'                                         ' + '\n'\
r'____  __.__         ________.__  __               ' + '\n'\
r'|    |/ _|__| ____  /  _____/|__|/  |_            '+ '\n'\
r'|      < |  |/    \/   \  ___|  \   __\  ' + 'Twitter: @0xRoyR' + '\n'\
r'|    |  \|  |   |  \    \_\  \  ||  |             ' + '\n'\
r'|____|__ \__|___|  /\______  /__||__|    ' + 'Github: 0xRoyR' + '\n'\
r'        \/       \/        \/                     '+ '\n'\
r'Become the king of gitlab                             '+ '\n'\
r'                                                  '
