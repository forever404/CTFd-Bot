from config import logininfo
import re,json,time,configparser,logging,sys,os,requests,asyncio

def login(login_url, username, password):
    #请求头
    my_headers = {
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding' : 'gzip',
        'Accept-Language' : 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4'
    }

    #获取token
    sss = requests.Session()
    try:
        r = sss.get(login_url, headers = my_headers)
    except:
        logging.error('[error]fail to login,check your config and network')
        return
    reg = r'<input type="hidden" name="nonce" value="(.*)">'
    pattern = re.compile(reg)
    result = pattern.findall(r.content.decode('utf-8'))
    token = result[0]
    
    #postdata
    my_data = {
    'name' : username,
    'password' : password,
    'nonce' : token,
    }
    
    #登录后
    try:
        r = sss.post(login_url, headers = my_headers, data = my_data)
    except:
        logging.error('[error]fail to login,check your config and network')
        return
    if r.ok == True:
        logging.info('[success]login ok,start the robot...')
        return sss
    else:
        logging.error('[error]fail to login,check your config and network')

#取配置文件
def readConf(configFile,subject,key):
    cf = configparser.ConfigParser()
    filename = cf.read(configFile)
    return cf.get(subject,key)

#取用户列表
def get_user_list():
    theSession = login(logininfo.login_url,logininfo.username,logininfo.password)
    try:
        responseJson = theSession.get(logininfo.apiUrl)
    except:
        logging.error('[error]fail to get api info,continue.')
        return []
    jsonInfo = json.loads(responseJson.text)
    if jsonInfo['success'] != True:
        logging.error("error to get userlist")
        return []
    userList = eval(str(jsonInfo['data']))
    return userList

#取提交flag信息
def get_attempt_info():
    theSession = login(logininfo.login_url,logininfo.username,logininfo.password)
    try:
        responseJson = theSession.get(logininfo.apiUrl)
    except:
        logging.error('[error]fail to get api info,continue.')
        return []
    jsonInfo = json.loads(responseJson.text)
    if jsonInfo['success'] != True:
        logging.error("error to get attemptlist")
        return []
    allList = eval(str(jsonInfo['data']))
    return allList

#异步循环发送请求
async def deal_user_list():
    global userLen,userList
    while True:
        try:
            tmpList = get_user_list()
            tmpLen = len(tmpList)
            if tmpLen == 0:
                continue
            if userLen < tmpLen:
                for i in range(userLen,tmpLen):
                    message = tmpList[i]['name']+"成功注册"
                    requests.get(logininfo.group_api+message)
                userLen = tmpLen
                userList = tmpList
            else:
                userLen = tmpLen
                userlist = tmpList
        except TypeError:
            logging.error('[error]fail to get api info,continue.')
            continue         
        await asyncio.sleep(5)
        logging.info("complete one time dectect of users.")

async def deal_attemp_list():
    global userLen,userList,allLen,allList
    while True:
        try:
            tmpallList = get_attempt_info()
            tmpallLen = len(tmpallList)
            if tmpallLen == 0:
                continue
            if allLen < tmpallLen:
                for i in range(allLen,tmpallLen):
                    if tmpallList[i]['type'] == "correct":
                        chaname = ""
                        for s in userList:
                            if str(s['id']) == str(tmpallList[i]['user_id']):
                                chaname = s['name']
                                if chaname == "":
                                    continue
                        message = "恭喜" + chaname + "做出" + str(tmpallList[i]['challenge']['category'])+"题目-" + str(tmpallList[i]['challenge']['name'])
                        #requests.get(logininfo.url_api+message)
                        requests.get(logininfo.group_api+message)
                allLen = tmpallLen
                allList = tmpallList
            else:
                allLen = tmpallLen
                allList = tmpallList
        except TypeError:
            logging.error('[error]fail to get api info,continue.')
            continue         
        await asyncio.sleep(5)
        logging.info("complete one time dectect of challenge.")
if __name__ == ("__main__"):
    logging.basicConfig(filename='err.log',level=logging.ERROR,format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',datefmt='%Y-%m-%d')

# 全局变量声明
    userList = get_user_list()
    userLen = len(userList)
    allList = get_attempt_info()
    allLen = len(allList)
    #allLen = 0

    loop = asyncio.get_event_loop()
    tasks = [deal_user_list(),deal_attemp_list()]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()