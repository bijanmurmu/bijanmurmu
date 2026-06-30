import os
import re
import requests

GITHUB_TOKEN = os.environ.get('GH_TOKEN')
USERNAME = 'bijanmurmu'

def fetch_languages():
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    else:
        print("Warning: GH_TOKEN not set. Running unauthenticated (rate limits apply).")
    
    print("Fetching repositories for languages...")
    repos_res = requests.get(f'https://api.github.com/users/{USERNAME}/repos?per_page=100', headers=headers)
    
    if repos_res.status_code != 200:
        print("Error fetching repos:", repos_res.status_code)
        return
        
    repos = repos_res.json()
    
    if not isinstance(repos, list):
        print("Expected a list of repos, got:", repos)
        return
        
    language_bytes = {}
    
    for repo in repos:
        if repo.get('fork') == True: continue
        repo_name = repo['name']
        langs_res = requests.get(f'https://api.github.com/repos/{USERNAME}/{repo_name}/languages', headers=headers)
        if langs_res.status_code == 200:
            langs = langs_res.json()
            for lang, bytes_count in langs.items():
                if lang in language_bytes:
                    language_bytes[lang] += bytes_count
                else:
                    language_bytes[lang] = bytes_count
                    
    total_bytes = sum(language_bytes.values())
    
    if total_bytes == 0:
        print("No language data found.")
        return
        
    # Sort languages by bytes descending
    sorted_langs = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
    display_langs = sorted_langs[:5]
    
    other_langs = sorted_langs[5:]
    if other_langs:
        others_bytes = sum(b for _, b in other_langs)
        display_langs.append(("Others", others_bytes))
    
    # Generate table
    table_lines = []
    
    top_5_perc_sum = 0.0
    
    for lang, b in display_langs:
        # Format size in KB
        size_kb = b / 1024
        size_str = f"{size_kb:,.0f} KB"
        
        if lang == "Others":
            perc = max(0.0, 100.0 - top_5_perc_sum)
        else:
            perc = round((b / total_bytes) * 100, 1)
            top_5_perc_sum += perc
            
        perc_str = f"{perc:.1f}%"
        
        # Format row: Language (12 chars max), Size (8 chars), Usage (6 chars)
        row = f"    > {lang[:12]:<12} [ {size_str:>8} ] {perc_str:>6}"
        table_lines.append(row)
    
    langs_text = "<!-- START_LANGS -->\n" + "\n".join(table_lines) + "\n<!-- END_LANGS -->"
    
    print("Updating README.md with languages...")
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    new_readme = re.sub(r'<!-- START_LANGS -->.*?<!-- END_LANGS -->', langs_text, readme, flags=re.DOTALL)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme)
        
    print("Language stats updated!")

if __name__ == '__main__':
    fetch_languages()
