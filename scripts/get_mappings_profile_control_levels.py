# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Red Hat, Inc.
import os
import sys
from typing import Dict
from ssg.profiles import _load_yaml_profile_file, get_profiles_from_products

from complyscribe.utils import load_controls_manager

import logging

"""
Description:
    This module is designed to handle the mapping of CAC profile names,
    their corresponding available control files, and the selected security levels.

    It is particularly useful to determine which profiles are mapped when detecting
    updates of CAC control files. We could according to the mapped profiles to update
    the related component-definition.

    The output is a dictionary containing information about the profile,
    policy ID, and the associated security levels.
How to use it:
    python get_mappings_profile_control_levels.py '<product>' '<content_root_dir>'"
    E.g., $python get_mappings_profile_control_levels.py "rhel10" "/path/of/cac-content"
Output Format:
    The module produces an output dictionary with the following structure:

    {
        'profile_name': 'stig',
        'policy_id': 'stig_rhel9',
        'levels': ['high', 'medium', 'low']
    }
"""

logging.basicConfig(level=logging.INFO, format="%(message)s")


def get_controls(cac_profile, cac_content_root, product) -> Dict:
    """Get the policy and levels"""
    controls_manager = load_controls_manager(cac_content_root, product)
    policies = controls_manager.policies
    profile_yaml = _load_yaml_profile_file(cac_profile)
    # Initialize an empty dictionary to store policy IDs and their corresponding levels
    policy_levels = {}
    # Get the selections from the profile
    selections = profile_yaml.get("selections", [])
    # Process each selected policy
    for selected in selections:
        # Split the selected item into parts based on ":"
        if ":" in selected:
            parts = selected.split(":")
            policy_id = parts[0]  # The policy ID is the first part
            # Retrieve the policy object
            policy = policies.get(policy_id)
            if policy is not None:
                # If there are three parts, use the third as a specific level
                if len(parts) == 3:
                    levels = [parts[2]]
                else:
                    # Otherwise, include all levels associated with the policy
                    levels = [level.id for level in policy.levels]
                # Store the policy_id and its corresponding levels
                policy_levels[policy_id] = levels
            else:
                # Handle case where policy doesn't exist
                logging.warning(f"Warning: Policy '{policy_id}' not found.")
        else:
            # If there are no available controls, bypass it.
            # The CPLYTM-228 will improve this part.
            pass
    return policy_levels


def main(product, content_root_dir):
    profiles = get_profiles_from_products(content_root_dir, [f"{product}"], sorted=True)
    for profile in profiles:
        profile_name = profile.profile_id + ".profile"
        cac_profile = os.path.join(
            content_root_dir,
            "products",
            product,
            "profiles",
            profile_name
        )
        policy_levels = get_controls(cac_profile, content_root_dir, product)
        relationship = {}
        relationship["profile_name"] = profile.profile_id
        if len(policy_levels) > 0:
            for key, value in policy_levels.items():
                # Update the relation_ship with the policy_id and levels
                relationship["policy_id"] = key
                relationship["levels"] = value
                logging.info(relationship)


if __name__ == "__main__":
    # Ensure that the script is run with the correct number of arguments
    if len(sys.argv) != 3:
        logging.warning("Usage: \
            python get_mappings_profile_control_levels.py '<product>' '<content_root_dir>'")
        sys.exit(1)
    try:
        # Extract arguments
        product = sys.argv[1]  # First argument is product
        content_root_dir = sys.argv[2]  # Second argument is content_root_dir
        # Call the main function
        main(product, content_root_dir)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
