#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# This script initializes RHEL products OSCAL content using the ComplyScribe CLI.
# Pre-requirements:
# 1. Git clone the ComplyScribe repo and setup complyscribe
# 2. Git clone CAC repository
# 3. Git clone OSCAL content reppository
# 4. Setup the OSCAL content branch
# Requirements:
# 1. Local path to the CAC repository
# 2. Local path to the OSCAL repository
# 3. OSCAL repository branch containing the initial updates
# Usage:
# sh scripts/init_rh_products_content.sh "/Users/huiwang/issue-743/content" "/Users/huiwang/issue-744/oscal-content" init_rh_products_content

cac_repo_path=$1
oscal_repo_path=$2
repo_branch=$3

if [ $# -lt 3 ]; then
    echo "Please provide the necessary inputs."
    exit 1
fi

RH_PRODUCTS=(rhel8 rhel9 rhel10 ocp4)
for product in "${RH_PRODUCTS[@]}"; do
    # Get the available policy_ids for a specific product
    echo "Get $product available policy_ids ......"
    python scripts/get_product_controls.py "$product" "$cac_repo_path" > "$product""_controls"  2>&1
    cat "$product""_controls"
    # Get the relationship of product's profile, policy_id and security level
    echo "Get $product profile, policy_id and level mapping ......"
    python scripts/get_mappings_profile_control_levels.py "$product" "$cac_repo_path" > "$product""_map.json"  2>&1
    cat "$product""_map.json"
    file="$product""_controls"
    if [ -f "$file" ] && [ -s "$file" ]; then
        controls_a=$(cat "$file") # Get all the available controls of the product
        IFS=' ' read -r -a product_controls <<< "$controls_a"
        # Output all the available controls for a specific product
        echo "The product controls: ${product_controls[*]}"
    fi
    # Generate OSCAL catalog and profile
    for policy_id in "${product_controls[@]}"; do
        poetry run complyscribe sync-cac-content catalog  --repo-path "$oscal_repo_path" --committer-email "openscap-ci@gmail.com" --committer-name "openscap-ci" --branch "$repo_branch" --cac-content-root "$cac_repo_path" --cac-policy-id "$policy_id" --oscal-catalog "$policy_id" --dry-run
        poetry run complyscribe sync-cac-content profile  --repo-path "$oscal_repo_path" --committer-email "openscap-ci@gmail.com" --committer-name "openscap-ci" --branch "$repo_branch" --cac-content-root "$cac_repo_path" --product "$product" --cac-policy-id "$policy_id" --oscal-catalog "$policy_id" --dry-run
    done
    # Generate OSCAL component-definition
    file="$product""_map.json"
    if [ -f "$file" ] && [ -s "$file" ]; then
        while IFS= read -r line; do
            map=${line//\'/\"}
            policy_id=$(echo "$map" | jq -r '.policy_id')
            profile=$(echo "$map" | jq -r '.profile_name')
            levels_a=$(echo "$map" | jq -r '.levels[]')
            IFS=' ' read -r -a levels <<< "$levels_a"
            for level in "${levels[@]}"; do
                oscal_profile=$product-$policy_id-$level
                if [[ "$product" == *'rhel'* ]] ; then
                    type="software"
                else
                    type="service"
                fi
                # For Mac
                # sed -i "" "/href/s|\(trestle://\)[^ ]*\(catalogs\)|\1\2|g" "$oscal_repo_path/profiles/$oscal_profile/profile.json"
                # For Linux
                sed -i "/href/s|\(trestle://\)[^ ]*\(catalogs\)|\1\2|g" "$oscal_repo_path/profiles/$oscal_profile/profile.json"
                poetry run complyscribe sync-cac-content component-definition --repo-path "$oscal_repo_path" --committer-email "openscap-ci@gmail.com" --committer-name "openscap-ci" --branch "$repo_branch" --cac-content-root "$cac_repo_path" --product "$product" --component-definition-type "$type" --cac-profile "$profile" --oscal-profile "$oscal_profile" --dry-run
                type="validation"
                poetry run complyscribe sync-cac-content component-definition --repo-path "$oscal_repo_path" --committer-email "openscap-ci@gmail.com" --committer-name "openscap-ci" --branch "$repo_branch" --cac-content-root "$cac_repo_path" --product "$product" --component-definition-type "$type" --cac-profile "$profile" --oscal-profile "$oscal_profile" --dry-run
            done
        done < "$product""_map.json"
    fi    
done
