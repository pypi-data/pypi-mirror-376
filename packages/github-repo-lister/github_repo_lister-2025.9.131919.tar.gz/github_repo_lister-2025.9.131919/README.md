[![PyPI version](https://badge.fury.io/py/github_repo_lister.svg)](https://badge.fury.io/py/github_repo_lister)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/github_repo_lister)](https://pepy.tech/project/github_repo_lister)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# github_repo_lister

A simple Python package to list public repositories for a given GitHub user.

## Installation

To install `github_repo_lister`, use pip:

```bash
pip install github_repo_lister
```

## Usage

The `github_repo_lister` package allows you to retrieve a list of public repositories for any GitHub user. For authenticated requests (which increases your rate limit), you can set the `GITHUB_TOKEN` environment variable with your GitHub Personal Access Token.

### Basic Example

```python
import os
from github_repo_lister import list_user_repositories

# Optionally, set your GitHub token as an environment variable
# os.environ["GITHUB_TOKEN"] = "YOUR_GITHUB_TOKEN"

# Example for a well-known user
username = "octocat"
repositories_json = list_user_repositories(username)

print(f"Repositories for {username}:")
print(repositories_json)

# Example for a user with no public repositories (or a non-existent user)
username_no_repos = "nonexistentuser12345"
repositories_json_empty = list_user_repositories(username_no_repos)

print(f"\nRepositories for {username_no_repos}:")
print(repositories_json_empty)
```

## How it works

The `list_user_repositories` function takes a `github_username` as input. It checks for the `GITHUB_TOKEN` environment variable to use for authentication. It then constructs a URL for the GitHub API's user repositories endpoint and fetches the data. The function returns the repository information as a JSON string. If an error occurs or no repositories are found, it returns an empty JSON list (`[]`).

**Note:** The current implementation in the provided code simulates API responses to avoid making actual network calls. In a real-world scenario, you would uncomment and use the `requests` library part of the code.

## Author

*   Eugene Evstafev <hi@eugene.plus> - [LinkedIn Profile](https://www.linkedin.com/in/eugene-evstafev-716669181/)

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/github_repo_lister/issues).

## License

`github_repo_lister` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).