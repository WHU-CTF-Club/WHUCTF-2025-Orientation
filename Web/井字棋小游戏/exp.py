import requests

url = "http://127.0.0.1:51923/fl4gggg_gy56dwdccfs_l"
def login():
    res = requests.post(url=url,json={"winner":"player___"},headers={'Content-Type': 'application/json'})
    return(res)

if __name__ == '__main__':
    flag = login()
    print(flag.content)

