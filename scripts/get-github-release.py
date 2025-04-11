#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright Red Hat, Inc.

import argparse
import os
import json
import sys
import urllib.request
import urllib.error
import urllib.parse


CHUNK_SIZE = 8192


def _print(*args, **kwargs):
    """Wrap print to disable flake8 errors in one place"""
    print(*args, **kwargs)  # noqa: T201


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch GitHub releases")
    parser.add_argument("--prerelease", action="store_true", help="Include prereleases")
    parser.add_argument("--list", action="store_true", help="List all releases")
    parser.add_argument("--tag", type=str, help="Specific tag to fetch")
    parser.add_argument(
        "repo_url",
        nargs=1,
        help="GitHub repository URL (e.g., https://github.com/owner/repo)",
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    repo_url = args.repo_url[0]

    owner, repo = extract_owner_repo(repo_url)
    releases = fetch_releases(owner, repo)

    if args.list:
        list_all_releases(releases)
        return

    if args.tag:
        release_info = find_release_by_tag(releases, args.tag)
    elif args.prerelease:
        release_info = get_latest_prerelease(releases)
    else:
        release_info = get_latest_release(releases)

    if not release_info:
        _print("No matching release found.")
        return

    tag_name = release_info["tag_name"]
    output_dir = os.path.join("releases", tag_name)

    if os.path.exists(output_dir):
        _print(f"Release {tag_name} already exists in {output_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)

    download_assets(release_info["assets"])
    save_release_notes(release_info.get("body"))
    save_release_info(release_info)
    pass


def extract_owner_repo(repo_url):
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    parts = repo_url.split("/")
    owner = parts[-2]
    repo = parts[-1]
    return owner, repo


def fetch_releases(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req)  # nosemgrep
        body_bytes = response.read()
        body = body_bytes.decode("utf-8")
    except urllib.error.HTTPError as e:
        _print(
            f"Non-successful HTTP response code from server: [{e.code}]: {e}",
            file=sys.stderr,
        )
        exit(1)
    except urllib.error.URLError as e:
        _print(f"Unable to send request to server: [{e.reason}]: {e}", file=sys.stderr)
        exit(1)
    return json.loads(body)


def list_all_releases(releases):
    for release in sorted(releases, key=lambda x: x["published_at"], reverse=True):
        pick = {
            "published_at": release.get("published_at"),
            "tag_name": release.get("tag_name"),
            "name": release.get("name"),
            "prerelease": release.get("prerelease"),
        }
        _print(json.dumps(pick))


def find_release_by_tag(releases, tag):
    for release in releases:
        if release["tag_name"] == tag:
            return release
    return None


def get_latest_prerelease(releases):
    prereleases = [r for r in releases if r.get("prerelease", False)]
    if not prereleases:
        _print("No prereleases found.", file=sys.stderr)
        exit(1)
    return sorted(prereleases, key=lambda x: x["published_at"], reverse=True)[0]


def get_latest_release(releases):
    for release in releases:
        if not release.get("prerelease", False):
            return release
    _print("No stable release found.", file=sys.stderr)
    exit(1)


def download_assets(assets):
    for asset in assets:
        url = asset["browser_download_url"]

        try:
            with urllib.request.urlopen(url) as response:  # nosemgrep
                response_headers = response.info()
                filename = None
                if "Content-Disposition" in response_headers:
                    filename = get_filename_from_headers(response_headers)
                else:
                    parsed_url = urllib.parse.urlparse(url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename:
                        filename = "downloaded_file"

                with open(filename, "wb") as file:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        file.write(chunk)
                _print(f"Downloaded {filename}")
        except urllib.error.HTTPError as e:
            _print(
                f"Non-successful HTTP response code from server {asset['name']}: {e.code}: {e}",
                file=sys.stderr,
            )
            exit(1)
        except urllib.error.URLError as e:
            _print(
                f"Unable to send request to server {asset['name']}: [{e.reason}]: {e}",
                file=sys.stderr,
            )
            exit(1)


def get_filename_from_headers(headers):
    content_disposition = headers.get("Content-Disposition")
    if not content_disposition:
        return "downloaded_file"

    _, _, filename = content_disposition.partition("filename=")
    if filename.startswith('"') and filename.endswith('"'):
        filename = filename[1:-1]
    return filename


def save_release_notes(body):
    if body:
        with open("README.md", "w") as f:
            f.write(body)


def save_release_info(release_info):
    with open("release_info.json", "w") as f:
        json.dump(release_info, f, indent=2)


if __name__ == "__main__":
    main()
