from manager import Manager
import os


def get_url(filename:str) -> list:
    urls = []
    with open(filename, 'r') as file:
        urls = file.readlines()
    for i_url in range(len(urls)):
        urls[i_url] = urls[i_url].replace('\n','')
    return urls

def main():
    urls_path = os.path.dirname(__file__) + '/urls.txt'
    if not os.path.exists(urls_path):
        raise Exception("Invalid path urls.txt or urls.txt not found in directory")
    urls = get_url(urls_path)
    print(urls)
    manager = Manager(urls)
    manager.manage()

if __name__ == "__main__":
    main()