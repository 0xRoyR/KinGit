import argparse
from GitlabInstance import *


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description=DESCRIPTION_ARGPARSE)
    parser.add_argument(USERNAME_PARAM_ARGPARSE[0], USERNAME_PARAM_ARGPARSE[1],
                        help=USERNAME_PARAM_ARGPARSE[2], type=str, required=True)
    parser.add_argument(KEY_PARAM_ARGPARSE[0], KEY_PARAM_ARGPARSE[1],
                        help=KEY_PARAM_ARGPARSE[2], type=str, required=True)
    parser.add_argument(INSTANCE_PARAM_ARGPARSE[0], INSTANCE_PARAM_ARGPARSE[1],
                        help=INSTANCE_PARAM_ARGPARSE[2], type=str, required=True)
    parser.add_argument(THREADS_PARAM_ARGPARSE[0], THREADS_PARAM_ARGPARSE[1],
                        help=THREADS_PARAM_ARGPARSE[2], type=int, required=False, default=NUMBER_OF_THREADS_DEFAULT)
    parser.add_argument(PATTERNS_PARAM_ARGPARSE[0], PATTERNS_PARAM_ARGPARSE[1],
                        help=PATTERNS_PARAM_ARGPARSE[2], type=str, required=False, default=PATTERNS_PATH_DEFAULT)
    parser.add_argument(MODE_PARAM_ARGPARSE[0], MODE_PARAM_ARGPARSE[1],
                        help=MODE_PARAM_ARGPARSE[2], type=str, required=False, default=MODE_ALL)
    parser.add_argument(SSL_PARAM_ARGPARSE[0], SSL_PARAM_ARGPARSE[1],
                        help=SSL_PARAM_ARGPARSE[2], required=False, action=STORE_TRUE_ARGPARSE, default=False)
    parser.add_argument(EXPORT_PROJECTS_PARAM_ARGPARSE[0], EXPORT_PROJECTS_PARAM_ARGPARSE[1],
                        help=EXPORT_PROJECTS_PARAM_ARGPARSE[2], required=False, action=STORE_TRUE_ARGPARSE,
                        default=False)
    parser.add_argument(VERBOSE_PARAM_ARGPARSE[0], VERBOSE_PARAM_ARGPARSE[1],
                        help=VERBOSE_PARAM_ARGPARSE[2], required=False, action=STORE_TRUE_ARGPARSE, default=False)

    args = parser.parse_args()

    local_instance = GitlabInstance(username=args.username, private_token=args.key, instance=args.instance,
                                    mode=args.mode, threads_count=args.threads, verify_ssl=args.ssl_verify,
                                    save_projects=args.export_projects, verbose=args.verbose,
                                    patterns_path=args.patterns, output=OUTPUT_FOLDER_PATH_DEFAULT)
    local_instance.caller()


if __name__ == '__main__':
    main()
