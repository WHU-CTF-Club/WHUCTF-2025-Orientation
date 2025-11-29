import os
from flask import Flask, request
# --- 配置 Flask 应用程序 ---
app = Flask(__name__)

@app.route('/')
def game():
    return app.send_static_file('game.html')

@app.route('/fl4gggg_gy56dwdccfs_l',methods=['POST'])
def flag():
    print(request.json.get('winner'))
    if request.json.get('winner') == 'player___':
        return open("/flag.txt", "r").read()
    else:
        return 'WHUCTF{fake_flag}'

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)