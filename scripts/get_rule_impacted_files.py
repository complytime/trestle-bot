import os
import logging
import sys
from typing import List

"""
Description:
    This module is designed to get the controls and profiles which are impacted by
    the rule. It is particularly useful to determine how to sync the updated rule
    to OSCAL component-definition.

    The output is a set of controls or profiles which is easy used in shell.
    How to run it:
    $python get_rule_impacted_files.py "rhel8" "cac-content_root" "$rule" "control"
Output Format:
    "cis_sle15 stig_ol9 cis_rhel10 cis_rhel8 ccn_ol9 ccn_rhel9"
"""

logging.basicConfig(level=logging.INFO, format="%(message)s")


def find_files_with_string(directory, search_string) -> List:
    matching_files = []
    # Walk through the directory and its subdirectories
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # Open each file and search for the string
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if search_string in content:
                        matching_files.append(file_path)
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                continue
    items = []
    for file in matching_files:
        filename = file.split('/')[-1]
        name = filename.split('.')[0]
        items.append(name)
    return items


def main(product, content_root_dir, search_rule, file_type="control"):
    if file_type == "control":
        directory = f"{content_root_dir}/controls/"
    else:
        directory = f"{content_root_dir}/products/{product}/profiles"
    files = find_files_with_string(directory, search_rule)
    files = set(files)
    logging.info(" ".join(files))


if __name__ == "__main__":
    # Ensure that the script is run with the correct number of arguments
    if len(sys.argv) != 5:
        USAGE_MESSAGE = """
Usage: python get_rule_impacted_files.py '<product>' \
'<content_root_dir>' '<rule>' '<file_type>'"
"""
        logging.warning(USAGE_MESSAGE)
        sys.exit(1)
    try:
        # Extract arguments
        product = sys.argv[1]  # First argument is product
        content_root_dir = sys.argv[2]  # Second argument is content_root_dir
        search_rule = sys.argv[3]  # Third argument is the updated rule
        file_type = sys.argv[4]  # Fourth argument is the control flag
        # Call the main function
        main(product, content_root_dir, search_rule, file_type)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
