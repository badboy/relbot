# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/


from util import *


def _update_ac_version(fenix_repo, branch, old_ac_version, new_ac_version, author):
    contents = fenix_repo.get_contents("buildSrc/src/main/java/AndroidComponents.kt", ref=branch)
    content = contents.decoded_content.decode("utf-8")
    new_content = content.replace(f'VERSION = "{old_ac_version}"', f'VERSION = "{new_ac_version}"')
    if content == new_content:
        raise Exception("Update to AndroidComponents.kt resulted in no changes: maybe the file was already up to date?")
    fenix_repo.update_file(contents.path, f"Update to Android-Components {new_ac_version}.",
                     new_content, contents.sha, branch=branch, author=author)


#
# For the current Fenix release and beta version, find out if there is
# a newer android-components that can be pulled in.
#

def update_android_components(ac_repo, fenix_repo, author, debug):
    for channel in ("beta", "release"):
        fenix_major_version = discover_fenix_major_version(channel)
        release_branch_name = f"releases/v{fenix_major_version}.0.0"

        print(f"{ts()} Looking at Fenix {channel.capitalize()} on {release_branch_name}")

        current_ac_version = get_current_ac_version_in_fenix(fenix_repo, release_branch_name)
        print(f"{ts()} Current A-C version is {current_ac_version}")

        ac_major_version = int(current_ac_version[0:2]) # TODO Util & Test!
        latest_ac_version = get_latest_ac_version_for_major_version(ac_repo, ac_major_version)

        raise Exception("TODO This should look in Maven and not in GitHub")

        # For testing on st3fan/fenix
        #if channel == "beta":
        #    latest_ac_version = "63.0.2"

        if compare_ac_versions(current_ac_version, latest_ac_version) >= 0:
            print(f"{ts()} No need to upgrade; Fenix {channel.capitalize()} is on A-C {current_ac_version}")
            continue

        print(f"{ts()} Should upgrade to {latest_ac_version}")

        pr_branch_name = f"relbot/AC-{latest_ac_version}"

        try:
            pr_branch = fenix_repo.get_branch(pr_branch_name)
            if pr_branch:
                raise Exception(f"The PR branch {pr_branch_name} already exists. Exiting.")
        except GithubException as e:
            pass

        release_branch = fenix_repo.get_branch(release_branch_name)
        print(f"{ts()} Last commit on {release_branch_name} is {release_branch.commit.sha}")

        print(f"{ts()} Creating branch {pr_branch_name} on {release_branch.commit.sha}")
        fenix_repo.create_git_ref(ref=f"refs/heads/{pr_branch_name}", sha=release_branch.commit.sha)

        print(f"{ts()} Updating AndroidComponents.kt from {current_ac_version} to {latest_ac_version} on {pr_branch_name}")
        _update_ac_version(fenix_repo, pr_branch_name, current_ac_version, latest_ac_version, author)

        print(f"{ts()} Creating pull request")
        pr = fenix_repo.create_pull(title=f"Update to Android-Components {latest_ac_version}.",
                                 body=f"This (automated) patch updates Android-Components to {latest_ac_version}.",
                                 head=pr_branch_name, base=release_branch_name)
        print(f"{ts()} Pull request at {pr.html_url}")



def create_release(ac_repo, fenix_repo, author, debug):
    print("Creating Fenix Release")