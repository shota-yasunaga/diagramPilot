import feedparser
import requests
import tarfile
import re
import glob
import os
import shutil


def query_arxiv(search_query, start=0, max_results=10):
    base_url = "http://export.arxiv.org/api/query?"
    query = f"search_query={search_query}&start={start}&max_results={max_results}"
    url = base_url + query
    response = feedparser.parse(url)
    return response

def main():
    search_query = "all:electron" # Change this to your desired search query
    max_results = 3 # Change this to the desired number of results
    response = query_arxiv(search_query, max_results=max_results)

    for entry in response.entries:
        try:
            source_url = entry.link.replace("abs", "e-print")

            response = requests.get(source_url)
            
            # Extract the filename from the URL
            filename = source_url.split("/")[-1]

            # Save the tar.gz file in the 'sources' folder
            full_filename = f"sources/{filename}.tar.gz"
            with open(full_filename, "wb") as f:
                f.write(response.content)
                # expand tar.gz file in python
            
            file = tarfile.open(full_filename)
            # make directory
            expand_path = f'sources/{filename}'
            os.makedirs(expand_path, exist_ok=True)
            # extracting file
            file.extractall(expand_path)
            file.close()
            os.remove(full_filename)
        except Exception as e:
            print(f"failed on file {full_filename}")


        # Delete files that are not .tex files
        for file_path in glob.glob(f"{expand_path}/*"):
            if file_path.lower().endswith(".tex"):
                sections = extract_tikz_sections(file_path)
                print(sections)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        shutil.rmtree(expand_path)
        


def extract_tikz_sections(tex_file):
    with open(tex_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    tikz_sections = re.findall(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', content, re.DOTALL)
    return tikz_sections

def delete_non_tex_files(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and not filename.endswith(".tex"):
            os.remove(file_path)


if __name__ == "__main__":
    main()

