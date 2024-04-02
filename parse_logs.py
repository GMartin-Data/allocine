import re


url_pattern = r"https://www.allocine.fr/film/fichefilm-(\d+)/casting/"

logfile_path = "allocine/logs/logfile.log"

def extract_urls_from_log(file_path):
    urls = set()  # Use a set to avoid duplicate URLs
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            matches = re.findall(url_pattern, line)
            urls.update(matches)
    return urls

urls = extract_urls_from_log(logfile_path)

print(len(urls))
