## Installation
1. Clone the repository
2. Create a virtual environment using ```python -m venv venv``` and activate it (tested with Python 3.11)
3. Install the required packages using ```pip install -r requirements.txt```
4. Create a .env file using an example file ```cp .env.example .env```
5. Add your OPENAI_API_KEY to the .env file and GH_TOKEN to the .env file. Make sure the GH_TOKEN has the necessary permissions to leave comments and has access to the repository.


## Usage
* If you want to process a pull request, run the script using ```python main.py --pull-request-url <url>``` 
* If you want to process a local repository, run the script using ```python main.py --local-repo-path <path> --branch <branch>```
* If you want to process a specific repository, run the script using ```python main.py --repo-url <url> --branch <branch>```