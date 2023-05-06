import feedparser
import requests
import tarfile
import re
import glob
import os
import shutil
import threading
import queue
from threading import Thread



def query_arxiv(search_query, start=0, max_results=10):
    base_url = "http://export.arxiv.org/api/query?"
    query = f"search_query={search_query}&start={start}&max_results={max_results}"
    url = base_url + query
    response = feedparser.parse(url)
    return response

metadata_file = "metadata.txt"

def process_entry(entry):
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

        # Delete files that are not .tex files
        for file_path in glob.glob(f"{expand_path}/*"):
            if file_path.lower().endswith(".tex"):
                sections = extract_tikz_sections(file_path)
                if len(sections) > 0:
                    with open(metadata_file, "a", encoding="utf-8") as f:
                        f.write(f"{source_url}\n")
                    print(sections)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        shutil.rmtree(expand_path)
        # print("success")
    except Exception as e:
        # print(e)
        # print(f"failed on file {full_filename}")
        try:
            os.remove(full_filename)
        except:
            pass

    


def main():
    search_query = "all:electron" # Change this to your desired search query
    max_results = 5000 # Change this to the desired number of results
    response = query_arxiv(search_query, max_results=max_results)
    max_threads = 10
    
    job_queue = queue.Queue()
    for entry in response.entries:
        job_queue.put(entry)


    def worker():
        """Thread worker function"""
    
        while not job_queue.empty():
            job = job_queue.get()
            if job is None:
                # The queue is empty and has been closed, so exit the thread
                break
            process_entry(job)
            job_queue.task_done()

    threadpool = [Thread(target=worker) for _ in range(max_threads)]
    [t.start() for t in threadpool]
    [t.join() for t in threadpool]

    print("All workers completed")


def extract_tikz_sections(tex_file):
    with open(tex_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    tikz_sections = re.findall(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', content, re.DOTALL)
    write_tikz_sections_to_files(tikz_sections)
    return tikz_sections

def write_tikz_sections_to_files(tikz_sections):
    filename = "section.txt"
    for section in tikz_sections:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(section+"\n")

        print(f"Wrote section {i} to file {filename}")


if __name__ == "__main__":
    main()

