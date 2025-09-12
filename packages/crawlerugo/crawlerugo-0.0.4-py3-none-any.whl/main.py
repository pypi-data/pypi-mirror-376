from crawlerugo.crawler import crawl
import os


base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def main():
    result = crawl(base_dir, lambda f: f)
    print("Crawled Data:", result)




if __name__ == "__main__":
    main()
