from config import settings
from git_processor_service import GitProcessorService
from review_agent import MistralReviewer, OpenAIReviewer
import argparse

parser = argparse.ArgumentParser(description='Review a pull request')

parser.add_argument('--pull-request-url', type=str, help='The URL of the pull request')
parser.add_argument('--repo-url', type=str, help='The URL of the repository')
parser.add_argument('--local-repo-path', type=str, help='The path to the local repository')
parser.add_argument('--branch', type=str, help='The branch name to checkout')

args = parser.parse_args()

git_processor = GitProcessorService()
reviewer = OpenAIReviewer()

if args.pull_request_url:
    differences = git_processor.compare_pull_request(args.pull_request_url, settings.GH_TOKEN)
    for difference in differences:
        reviewed_diff = reviewer.review_diff(difference)
        print(reviewed_diff)
        git_processor.comment_on_diff(reviewed_diff, settings.GH_TOKEN)
elif args.repo_url and args.branch:
    git_processor.clone_repository(args.repo_url)
    differences = git_processor.get_branch_diff(args.branch)
    result = reviewer.review_diffs(differences)
    with open('reviewed_diffs.txt', 'w') as f:
        for diff in result:
            print(diff)
            f.write(str(diff) + '\n')
elif args.local_repo_path and args.branch:
    git_processor.set_local_repository(args.local_repo_path)
    differences = git_processor.get_branch_diff(args.branch)
    result = reviewer.review_diffs(differences)
    with open('reviewed_diffs.txt', 'w') as f:
        for diff in result:
            print(diff)
            f.write(str(diff) + '\n')
else:
    raise ValueError("Please provide either a pull request URL or a repository URL and branch name")

