#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright Red Hat, Inc.

me="$(basename "$0")"
usage() {
cat <<EOF
$me: get a release from github
$me [--prerelease|--list] [--tag=<TAG>] [<REPO>]
EOF
exit "$1"
}

main() {
    prerelease=0
    list=0
    user_tag=
    remote_url='https://github.com/complytime/complytime.git'
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --help)
                usage 0
                ;;
            --prerelease)
                prerelease=1
                shift
                ;;
            --list)
                list=1
                shift
                ;;
            --tag=*)
                user_tag="${1#--tag=}"
                shift
                ;;
            --tag)
                user_tag="$2"
                shift 2
                ;;
            *)
                remote_url="$1"
                shift
                break
                ;;
        esac
    done

    case "$remote_url" in
        https://github.com/*)
            github
            ;;
        *)
            echo 'Not a github remote'
            exit 1
            ;;
    esac
}

github() {
    repo="${remote_url:19}"
    repo="${repo%.git}"
    if [[ "$list" -eq 1 ]]; then
        release_info_url="https://api.github.com/repos/$repo/releases"
        curl -s -H "Accept: application/vnd.github+json" "$release_info_url" | jq -c '[.[] | {published_at, tag_name, name}] | sort_by(.published_at) | .[]'
        exit
    elif [[ -n "$user_tag" ]]; then
        release_info_url="https://api.github.com/repos/$repo/releases"
        release_info="$(curl -H "Accept: application/vnd.github+json" "$release_info_url" | jq --arg user_tag "$user_tag" 'map(select(.tag_name == $user_tag)) | sort_by(.published_at) | last')"
    elif [[ "$prerelease" -eq 1 ]]; then
        release_info_url="https://api.github.com/repos/$repo/releases"
        release_info="$(curl -H "Accept: application/vnd.github+json" "$release_info_url" | jq 'map(select(.draft == false)) | sort_by(.published_at) | last')"
    else
        release_info_url="https://api.github.com/repos/$repo/releases/latest"
        release_info="$(curl -H "Accept: application/vnd.github+json" "$release_info_url")"
    fi
    if [[ "$(jq <<<"$release_info" -r '.message')" = 'Moved Permanently' ]]; then
        printf >&2 '%s: %s\n' "$repo" "$(jq <<<"$release_info" -cr)"
        if [[ "$prerelease" -eq 1 ]]; then
            release_info="$(curl -L -H "Accept: application/vnd.github+json" "$release_info_url" | jq 'map(select(.draft == false)) | sort_by(.published_at) | last')"
        else
            release_info="$(curl -L -H "Accept: application/vnd.github+json" "$release_info_url")"
        fi
    fi
    tag="$(jq <<<"$release_info" -r '.tag_name')"
    if [[ -e "releases/$tag" ]]; then
        exit 0
    fi
    mkdir -p "releases/$tag"
    cd "releases/$tag"
    jq <<<"$release_info" -r '.assets[]? | .browser_download_url' | while IFS= read -r url; do
    wget --content-disposition --xattr "$url"
    done
    if [[ "$(jq <<<"$release_info" -r 'has("body")')" = true ]]; then
        jq <<<"$release_info" -r .body >README.md
    fi
    ( set -C; printf '%s\n' "$release_info" >release_info.json )
}

main "$@"


