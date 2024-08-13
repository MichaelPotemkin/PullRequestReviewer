import os
import shutil
from typing import List, Optional
from urllib.parse import urlparse

import git
import requests
from git import Repo

from schemas import Difference


class GitProcessorService:
    """
    A class to compare git branches and get the differences between them.
    """

    REPO_ROOT_DIRECTORY = "repositories"

    def __init__(self) -> None:
        """
        Initializes the GitBranchComparator class.
        """
        self.repository: Optional[Repo] = None
        self.pr_details: Optional[dict] = None

    def clone_repository(self, url: str) -> None:
        """
        Clones the repository from the given URL to the local directory.
        If the directory already exists, it is removed before cloning.

        Args:
            url (str): The URL of the repository to clone

        Raises:
            Exception: If cloning the repository fails.
        """
        try:
            repo_name = self.get_repo_name_from_url(url)
            repo_path = os.path.join(self.REPO_ROOT_DIRECTORY, repo_name)

            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)

            self.repository = git.Repo.clone_from(url, repo_path)
        except Exception as e:
            raise Exception(f"Failed to clone repository: {str(e)}")

    def set_local_repository(self, path: str) -> None:
        """
        Sets the local repository path.

        Args:
            path (str): The path to the local repository.
        """
        self.repository = git.Repo(path)

    def fetch_all_branches(self) -> None:
        """
        Fetches all branches from the remote repository.

        Raises:
            Exception: If fetching all branches fails.
        """
        try:
            self.repository.git.fetch('--all')
        except Exception as e:
            raise Exception(f"Failed to fetch all branches: {str(e)}")

    def get_branch_diff(self, branch_name: str) -> List[Difference]:
        """
        Gets the differences between the master branch and the specified branch.

        Args:
            branch_name (str): Name of the branch to compare with the master branch.

        Returns:
            List[Difference]: A list of Difference objects containing the file path,
                              change type, and diff of each changed file.

        Raises:
            Exception: If the branch is not found or if getting the differences fails.
        """
        try:
            self.fetch_all_branches()
            origin = self.repository.remotes.origin
            master_commit = origin.refs.master.commit
            target_commit = origin.refs[branch_name].commit

            diffs = master_commit.diff(target_commit, create_patch=True)
            diff_details = []
            for diff in diffs:
                diff_detail = Difference(
                    file=diff.a_path or diff.b_path,
                    change_type=diff.change_type,
                    diff=diff.diff.decode('utf-8')
                )
                diff_details.append(diff_detail)
            return diff_details
        except IndexError:
            raise Exception(f"Branch '{branch_name}' not found in the repository.")
        except Exception as e:
            raise Exception(f"Failed to get branch differences: {str(e)}")

    def compare_pull_request(self, pull_request_url: str, token: Optional[str] = None) -> List[Difference]:
        """
        Processes the pull request by cloning the repository and getting the differences
        between the master branch and the pull request branch.

        Args:
            pull_request_url (str): The URL of the pull request.
            token (Optional[str]): The GitHub token for authentication (optional).

        Returns:
            List[Difference]: A list of Difference objects containing the file path,
                              change type, and diff of each changed file.
        """
        repository_url = pull_request_url.split("/pull/")[0] + ".git"
        self.clone_repository(repository_url)
        target_branch = self.get_branch_name_from_url(pull_request_url, token)
        differences = self.get_branch_diff(target_branch)
        return differences

    @staticmethod
    def parse_github_url(url: str) -> tuple:
        """
        Parses the GitHub URL to extract the repository owner, name, and pull request number.

        Args:
            url (str): The URL of the pull request.

        Returns:
            tuple: A tuple containing the owner, repo name, and pull request number.
        """
        path_parts = urlparse(url).path.split('/')
        owner = path_parts[1]
        repo = path_parts[2]
        pull_number = path_parts[4]
        return owner, repo, pull_number

    @staticmethod
    def get_pull_request_details(owner: str, repo: str, pull_number: str, token: Optional[str] = None) -> dict:
        """
        Fetches pull request details from the GitHub API.

        Args:
            owner (str): The owner of the repository.
            repo (str): The name of the repository.
            pull_number (str): The pull request number.
            token (Optional[str]): The GitHub token for authentication (optional).

        Returns:
            dict: The JSON response containing pull request details.
        """
        headers = {}
        if token:
            headers['Authorization'] = f'token {token}'

        api_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}'
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def checkout_branch(repo_path: str, branch_name: str) -> None:
        """
        Checks out the specified branch in the given repository path.

        Args:
            repo_path (str): The path to the local repository.
            branch_name (str): The name of the branch to checkout.
        """
        repo = Repo(repo_path)
        repo.git.checkout(branch_name)

    def get_branch_name_from_url(self, url: str, token: Optional[str] = None) -> str:
        """
        Extracts the branch name from the pull request URL using the GitHub API.

        Args:
            url (str): The URL of the pull request.
            token (Optional[str]): The GitHub token for authentication (optional).

        Returns:
            str: The name of the branch associated with the pull request.
        """
        owner, repo, pull_number = self.parse_github_url(url)
        self.pr_details = self.get_pull_request_details(owner, repo, pull_number, token)
        return self.pr_details['head']['ref']

    @staticmethod
    def get_repo_name_from_url(url: str) -> str:
        """
        Extracts the repository name from the given URL.

        Args:
            url (str): The URL of the repository.

        Returns:
            str: The name of the repository.
        """
        path_parts = urlparse(url).path.split('/')
        repo_name = path_parts[2]
        return repo_name

    @staticmethod
    def determine_position(diff: Difference) -> int:
        # place the comment after the last line for now
        return len(diff.diff.splitlines()) - 1



    def comment_on_diff(self, difference: Difference, token: str) -> None:
        """
        Comments on the pull request with the feedback provided for the diff.
        Args:
            difference (Difference): The Difference object containing the feedback.
            token (str): The GitHub token for authentication.
        """
        if not difference.comment:
            return

        # Extract details from the stored pull request details
        owner = self.pr_details['head']['repo']['owner']['login']
        repo = self.pr_details['head']['repo']['name']
        pull_number = self.pr_details['number']
        commit_sha = self.pr_details['head']['sha']

        # GitHub API URL to create a comment on a commit in a pull request
        api_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments'

        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        data = {
            'body': difference.comment,
            'commit_id': commit_sha,
            'path': difference.file,
            'position': self.determine_position(difference)
        }
        response = requests.post(api_url, headers=headers, json=data)
        try:
            response.raise_for_status()  # This will raise an error if the request fails
        except requests.exceptions.HTTPError as e:
            print(f"Failed to post comment: {str(e)}")  # Handling the exception to avoid crashing and provide error feedback
