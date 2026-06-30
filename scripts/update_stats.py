import os
import re
import requests

GITHUB_TOKEN = os.environ.get('GH_TOKEN')
USERNAME = 'bijanmurmu' # Update this if your username changes

def fetch_stats():
    if not GITHUB_TOKEN:
        print("Error: GH_TOKEN environment variable not set.")
        return

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    print("Fetching user profile...")
    user_res = requests.get(f'https://api.github.com/users/{USERNAME}', headers=headers).json()
    followers = user_res.get('followers', 0)
    public_repos = user_res.get('public_repos', 0)
    
    print("Fetching issues...")
    issues_res = requests.get(f'https://api.github.com/search/issues?q=author:{USERNAME}+type:issue', headers=headers).json()
    issues_created = issues_res.get('total_count', 0)
    
    print("Fetching PRs...")
    prs_created_res = requests.get(f'https://api.github.com/search/issues?q=author:{USERNAME}+type:pr', headers=headers).json()
    prs_created = prs_created_res.get('total_count', 0)
    
    prs_merged_res = requests.get(f'https://api.github.com/search/issues?q=author:{USERNAME}+type:pr+is:merged', headers=headers).json()
    prs_merged = prs_merged_res.get('total_count', 0)
    
    print("Fetching commits...")
    commits_res = requests.get(f'https://api.github.com/search/commits?q=author:{USERNAME}', headers=headers).json()
    commits_count = commits_res.get('total_count', 0)
    
    print("Fetching contributed repos via GraphQL...")
    query = """
    query {
      user(login: "%s") {
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) {
          totalCount
        }
      }
    }
    """ % USERNAME
    gql_res = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers).json()
    try:
        contributed_repos = gql_res['data']['user']['repositoriesContributedTo']['totalCount']
    except Exception as e:
        print("Failed to parse GraphQL response:", e)
        contributed_repos = 0

    print("Fetching reviews...")
    reviews_res = requests.get(f'https://api.github.com/search/issues?q=reviewed-by:{USERNAME}', headers=headers).json()
    reviews_count = reviews_res.get('total_count', 0)

    print("Fetching LOC stats...")
    repos_res = requests.get(f'https://api.github.com/users/{USERNAME}/repos?per_page=100', headers=headers).json()
    additions = 0
    deletions = 0
    
    if isinstance(repos_res, list):
        for repo in repos_res:
            if repo.get('fork') == True: continue
            repo_name = repo['name']
            stats_res = requests.get(f'https://api.github.com/repos/{USERNAME}/{repo_name}/stats/contributors', headers=headers)
            if stats_res.status_code == 200:
                data = stats_res.json()
                if isinstance(data, list):
                    for contributor in data:
                        if contributor.get('author', {}).get('login') == USERNAME:
                            for week in contributor.get('weeks', []):
                                additions += week.get('a', 0)
                                deletions += week.get('d', 0)

    # Format the stats string
    stats_text = f"""<!-- START_STATS -->
    > Repos: ....... {public_repos:<12} {{Contributed: {contributed_repos}}}
    > Followers: ... {followers:<12}
    > Commits: ..... {commits_count:<12} (All-time)
    > Issues: ...... {issues_created:<12} (Created)
    > PRs: ......... {prs_created:<12} {{Merged: {prs_merged}}}
    > Code reviews:. {reviews_count:<12} (Conducted)
    > LOC: ......... (+{additions:,}, -{deletions:,})
<!-- END_STATS -->"""

    print("Updating README.md...")
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    new_readme = re.sub(r'<!-- START_STATS -->.*?<!-- END_STATS -->', stats_text, readme, flags=re.DOTALL)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme)
        
    print("Done!")

if __name__ == '__main__':
    fetch_stats()
