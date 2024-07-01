from flask import (
    Flask,request,abort,make_response,jsonify,redirect
)
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent,TextMessage,TextSendMessage,QuickReply,
    QuickReplyButton,MessageAction,CameraAction,CameraRollAction,
    LocationAction,FlexSendMessage,LocationMessage,TemplateSendMessage,
    CarouselTemplate,CarouselColumn,PostbackTemplateAction,MessageTemplateAction,
    URITemplateAction,ButtonsTemplate,PostbackAction,URIAction,DatetimePickerTemplateAction,
    PostbackEvent,ConfirmTemplate
)
import pymssql
import time
import datetime



app = Flask(__name__)

line_bot_api = LineBotApi('Os2+EY32XtFny0iRzIxqRf4OY0Kw9SSNo1D9+iRyGKB58MLlaEfst0THYvvIKyG+jlFh9gS1Ob9CAScosaevLYYezm/XCZJKzJqdpS7uTapD5h+WGGT1kw2q7WTp9KXQWs8dKRVuT1rOk/V4nqd2DwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('04bc2982521b007bd6306e49fd1ac3db')

conn = pymssql.connect(
        host = 'localhost:62859',
        port = '1433',
        user = 'Test',
        password = '123',
        database = 'recallBotDB'
        )

#API的IP
webhookURL = "https://5aec-123-205-67-194.ngrok.io"

cursor = conn.cursor(as_dict=True)



@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'



@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    name = profile.display_name #使用者名稱
    uid = profile.user_id # 發訊者ID
    user_talk = event.message.text
    print(user_talk)
    
    action(name,uid,user_talk)



@handler.add(PostbackEvent)
def handle_postback_event(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    name = profile.display_name #使用者名稱
    uid = profile.user_id # 發訊者ID
    datetime = event.postback.params['datetime'].replace("T"," ") + ":00"
    
    action(name,uid,datetime)



"""建立全域變數"""
service = ""
talk = ["",""] #talk[0]為系統對話,talk[1]為使用者對話



def action(name,uid,user_talk):
    sign_in(name,uid)
    account(name,uid,user_talk)
    select(uid,user_talk)
    remind(uid,user_talk)
    goal(uid,user_talk)
    note(uid, user_talk)
    bookmark(uid,user_talk)



"""時間選擇(V)"""
def datetimepicker(uid,mod):
    line_bot_api.push_message(uid,TemplateSendMessage(alt_text='DatetimePickerTemplate',template=ButtonsTemplate(
            title=mod,text=mod,
            actions=[
                DatetimePickerTemplateAction(
                    label = "設定時間",
                    data = "action=buy&itemid=1",
                    mode = "datetime",                        
                    initial = "2022-05-01T00:00",
                    min = "2022-01-01T00:00",
                    max = "2032-12-31T23:59"
                )
    ])))



"""登入(V)"""
def sign_in(name,uid):
    cursor.execute('SELECT * FROM [user]')
    user_uid = []
    datalist = cursor.fetchall()
    
    for row in datalist:
        user_uid.append(row['user_uid'])
    
    exist = 0
    
    for i in range(len(user_uid)):
        if uid == user_uid[i]:
            exist = 1
            break
    
    if exist == 0:
        sql = "INSERT INTO [user](user_name,user_uid) VALUES('{}','{}')".format(name,uid)
        cursor.execute(sql)
        conn.commit()



"""帳號(V)"""
def account(name,uid,user_talk):
    global service
    
    if user_talk == "!查看帳號所有功能":
        line_bot_api.push_message(uid,TemplateSendMessage(alt_text='ButtonsTemplate',template=ButtonsTemplate(
                title="帳號功能",text="使用帳號功能",
                actions=[
                    MessageAction(label="查看帳號",text="!查看帳號"),
                    MessageAction(label="編輯帳號",text="!編輯帳號"),
                    MessageAction(label="繼承帳號",text="!繼承帳號"),
                    MessageAction(label="刪除帳號",text="!刪除帳號")
        ])))
        
    elif user_talk == "!查看帳號":
        serch_account(uid)
    
    elif user_talk == "!編輯帳號":
        line_bot_api.push_message(uid,TemplateSendMessage(alt_text='ButtonsTemplate',template=ButtonsTemplate(
                title="編輯帳號",text="選擇要編輯的功能",
                actions=[
                    MessageAction(label="編輯暱稱",text="!編輯帳號暱稱"),
                    MessageAction(label="編輯信箱",text="!編輯帳號信箱")
        ])))
    
    elif user_talk == "!編輯帳號暱稱":
        talk[0] = "輸入新的暱稱："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "編輯帳號暱稱"
    
    elif user_talk == "!編輯帳號信箱":
        talk[0] = "輸入新的信箱："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "編輯帳號信箱"
    
    elif user_talk == "!繼承帳號":
        talk[0] = "輸入原有的暱稱："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "繼承帳號"
    
    elif user_talk == "!刪除帳號":
        talk[0] = "如刪除帳號，儲存的內容可能會全部遺失，是否確定刪除？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
        ])))
        service = "刪除帳號"
        
    #--------------------------------------------------------------------------
    
    elif service == "編輯帳號暱稱":
        edit_account_nickname(uid,user_talk)
    
    elif service == "編輯帳號信箱":
        edit_account_mail(uid,user_talk)
    
    elif service == "繼承帳號":
        inherit_account(uid,user_talk)
    
    elif service == "刪除帳號":
        del_account(uid,user_talk)



"""查看帳號(V)"""
def serch_account(uid):
    cursor.execute("SELECT * FROM [user] Where user_uid = '{}'".format(uid))
    datalist = cursor.fetchone()
    
    user_name = datalist['user_name']
    user_nickname = datalist['user_nickname']
    user_mail = datalist['user_mail']
    
    if user_nickname == None:
        user_nickname = "尚未填寫"
    if user_mail == None:
        user_mail = "尚未填寫"
    
    result = "===========================\n"
    result += "帳號姓名：" + user_name + '\n'
    result += "帳號暱稱：" + user_nickname + '\n'
    result += "帳號信箱：" + user_mail + '\n'
    result += "==========================="
    line_bot_api.push_message(uid,TextSendMessage(result))



"""編輯帳號暱稱"""
def edit_account_nickname(uid,user_talk):
    global service
   
    if talk[0] == "輸入新的暱稱：":
        
        cursor.execute("UPDATE [user] SET user_nickname = %(n1)s Where user_uid = %(n2)s",{'n1':user_talk,'n2':uid})
        conn.commit()
        
        line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
        talk[0] = ""
        talk[1] = ""
        service = ""



"""編輯帳號信箱"""
def edit_account_mail(uid,user_talk):
    global service
   
    if talk[0] == "輸入新的信箱：":
        cursor.execute("UPDATE [user] SET user_mail = %(n1)s Where user_uid = %(n2)s",{'n1':user_talk,'n2':uid})
        conn.commit()
            
        line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
        talk[0] = ""
        talk[1] = ""
        service = ""



"""繼承帳號(V)"""
def inherit_account(uid,user_talk):
    global service
    tmp = ["",""]
    
    if talk[0] == "輸入原有的暱稱：":
        talk[1] = user_talk
        talk[0] = "輸入原有的電子信箱："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
    
    elif talk[0] == "輸入原有的電子信箱：":
        talk[1] += '|' + user_talk
        tmp = talk[1].split("|")
        
        result = "===========================\n"
        result += "原有帳號暱稱：" + tmp[0] + '\n'
        result += "原有電子信箱：" + tmp[1] + '\n'
        result += "==========================="
        line_bot_api.push_message(uid,TextSendMessage(result))
        
        talk[0] = "是否確認繼承？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
                ])))
    
    elif talk[0] == "是否確認繼承？":
        if user_talk == "是":
            line_bot_api.push_message(uid,TextSendMessage("已繼承！"))
            tmp = talk[1].split("|")
            
            cursor.execute("SELECT user_uid FROM [user] Where user_nickname = '{}' and user_mail = '{}'".format(tmp[0],tmp[1]))
            datalist = cursor.fetchone()
            user_uid = datalist['user_uid']
            
            cursor.execute("UPDATE remind SET user_uid = %(n1)s Where user_uid = %(n2)s",{'n1':uid,'n2':user_uid})
            conn.commit()
            cursor.execute("UPDATE goal SET user_uid = %(n1)s Where user_uid = %(n2)s",{'n1':uid,'n2':user_uid})
            conn.commit()
            cursor.execute("UPDATE note SET user_uid = %(n1)s Where user_uid = %(n2)s",{'n1':uid,'n2':user_uid})
            conn.commit()
            cursor.execute("UPDATE bookmark SET user_uid = %(n1)s Where user_uid = %(n2)s",{'n1':uid,'n2':user_uid})
            conn.commit()
            
            sql = "DELETE FROM [user] Where user_nickname = '{}' and user_mail = '{}'".format(tmp[0],tmp[1])
            cursor.execute(sql)
            conn.commit()
            
            talk[0] = ""
            talk[1] = ""
            service = ""
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""刪除帳號(V)"""
def del_account(uid,user_talk):
    global service
    
    if talk[0] == "如刪除帳號，儲存的內容可能會全部遺失，是否確定刪除？":
        if user_talk == "是":
            cursor.execute("DELETE FROM remind WHERE user_uid = '{}'".format(uid))
            conn.commit()
            cursor.execute("DELETE FROM goal WHERE user_uid = '{}'".format(uid))
            conn.commit()
            cursor.execute("DELETE FROM note WHERE user_uid = '{}'".format(uid))
            conn.commit()
            cursor.execute("DELETE FROM bookmark WHERE user_uid = '{}'".format(uid))
            conn.commit()
            cursor.execute("DELETE FROM [user] WHERE user_uid = '{}'".format(uid))
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已刪除！"))
            talk[0] = ""
            service = ""
        
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            service = ""



"""所有選單(V)"""
def select(uid,user_talk):
    if user_talk == "!查看所有功能":
        line_bot_api.push_message(uid,TemplateSendMessage(alt_text='CarouselTemplate',template=CarouselTemplate(
            columns = [
                CarouselColumn(title="書籤",text="使用書籤功能",actions=[
                    MessageAction(label="建立書籤",text="!建立書籤"),
                    MessageAction(label="查詢書籤",text="!查詢書籤"),
                    MessageAction(label="查看所有功能",text="!查看書籤所有功能")
                ]),
            
                CarouselColumn(title = "筆記",text = "使用筆記功能",actions=[
                    MessageAction(label="建立筆記",text="!建立筆記"),
                    MessageAction(label="查詢筆記",text="!查詢筆記"),
                    MessageAction(label="查看所有功能",text="!查看筆記所有功能")
                ]),
            
                CarouselColumn(title = "提醒",text = "使用提醒功能",actions=[
                    MessageAction(label="建立提醒",text="!建立提醒"),
                    MessageAction(label="查詢提醒",text="!查詢提醒"),
                    MessageAction(label="查看所有功能",text="!查看提醒所有功能")
                ]),
            
                CarouselColumn(title = "目標",text = "使用目標功能",actions=[
                    MessageAction(label="建立目標",text="!建立目標"),
                    MessageAction(label="查詢目標",text="!查詢目標"),
                    MessageAction(label="查看所有功能",text="!查看目標所有功能")
                ]),
                
                CarouselColumn(title = "分享",text = "分享儲存的記錄",actions=[
                    MessageAction(label="分享書籤",text="!分享書籤"),
                    MessageAction(label="分享筆記",text="!分享筆記"),
                    MessageAction(label="查看所有功能",text="!查看分享所有功能")
                ]),
                
                CarouselColumn(title = "帳號",text = "使用帳號功能",actions=[
                    MessageAction(label="查看帳號",text="!查看帳號"),
                    MessageAction(label="編輯帳號",text="!編輯帳號"),
                    MessageAction(label="查看所有功能",text="!查看帳號所有功能")
                ])
        ])))



"""提醒(V)"""
def remind(uid,user_talk):
    global service
    
    if user_talk == "!查看提醒所有功能":
        line_bot_api.push_message(uid,TemplateSendMessage(alt_text='ButtonsTemplate',template=ButtonsTemplate(
                title="帳號功能",text="使用帳號功能",
                actions=[
                    MessageAction(label="建立提醒", text="!建立提醒"),
                    MessageAction(label="查詢提醒", text="!查詢提醒"),
                    MessageAction(label="編輯提醒", text="!編輯提醒"),
                    MessageAction(label="刪除提醒", text="!刪除提醒")
        ])))
        
    elif user_talk == "!建立提醒":
        talk[0] = "輸入要建立的提醒標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "建立提醒"
        
    elif user_talk == "!查詢提醒":
        serch_remind(uid)
        
    elif user_talk == "!編輯提醒":
        talk[0] = "輸入要編輯的提醒標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "編輯提醒"
        
    elif user_talk == "!刪除提醒":
        talk[0] = "輸入要刪除的提醒標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "刪除提醒"
        
    #--------------------------------------------------------------------------
    
    elif service == "建立提醒":
        set_remind(uid,user_talk)
        
    elif service == "編輯提醒":
        edit_remind(uid,user_talk)
        
    elif service == "刪除提醒":
        del_remind(uid,user_talk)



"""建立提醒(V)"""
def set_remind(uid,user_talk):
    global service
    tmp = ["","",""] #暫存陣列
                
    if talk[0] == "輸入要建立的提醒標題：":
        talk[1] = user_talk
        talk[0] = "輸入要建立的提醒內容："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
                
    elif talk[0] == "輸入要建立的提醒內容：":
        talk[1] += '|' + user_talk
        talk[0] = "輸入要建立的提醒時間"
        datetimepicker(uid,talk[0])
        
    elif talk[0] == "輸入要建立的提醒時間":
        talk[1] += '|' + user_talk
        talk[0] = "建立完成，是否要儲存？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
                ])))
        
    elif talk[0] == "建立完成，是否要儲存？":
        if user_talk == "是":
            line_bot_api.push_message(uid,TextSendMessage("已建立！"))
            tmp = talk[1].split("|")
            
            sql = "INSERT INTO remind(remind_name,remind_detail,remind_time,user_uid) VALUES('{}','{}','{}','{}')".format(tmp[0],tmp[1],tmp[2],uid)
            cursor.execute(sql)
            conn.commit()
            
            talk[0] = ""
            talk[1] = ""
            service = ""
            
            result = "===========================\n"
            result += "提醒標題：" + tmp[0] + '\n' 
            result += "提醒內容：" + tmp[1] + '\n' 
            result += "提醒時間：" + tmp[2] + '\n' 
            result += "==========================="
            line_bot_api.push_message(uid,TextSendMessage(result))
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已捨棄！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""查詢提醒(V)"""
def serch_remind(uid):
    cursor.execute("SELECT * FROM remind WHERE user_uid = '{}'".format(uid))
    remind_name = []
    remind_detail = []
    remind_time = []
    user_uid = []
    datalist = cursor.fetchall()  
    
    if cursor.rowcount == 0:
        result = "查無結果"
        line_bot_api.push_message(uid,TextSendMessage(result))
    
    for row in datalist:
        remind_name.append(row['remind_name'])
        remind_detail.append(row['remind_detail'])
        remind_time.append(row['remind_time'])
        user_uid.append(row['user_uid'])
        
    for i in range(len(remind_name)):
        result = "===========================\n"
        result += '提醒標題：' + remind_name[i] + '\n'
        result += '提醒內容：' + remind_detail[i] + '\n'
        result += '提醒時間：' + remind_time[i] + '\n'
        result += "==========================="
        line_bot_api.push_message(user_uid[i],TextSendMessage(result))



"""編輯提醒(V)"""
def edit_remind(uid,user_talk):
   global service
   tmp = ["",""]
   
   if talk[0] == "輸入要編輯的提醒標題：":
        talk[1] = user_talk
        talk[0] = "輸入要編輯的提醒功能："
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="標題", text="標題")),
                QuickReplyButton(action=MessageAction(label="內容", text="內容")),
                QuickReplyButton(action=MessageAction(label="時間", text="時間"))
                ])))
                
   elif talk[0] == "輸入要編輯的提醒功能：":
       talk[1] += '|' + user_talk
       talk[0] = "輸入要修改的提醒內容：" 
       line_bot_api.push_message(uid,TextSendMessage(talk[0]))
       
   elif talk[0] == "輸入要修改的提醒內容：":
       tmp = talk[1].split("|")
       
       if tmp[1] == "標題":
            cursor.execute("UPDATE remind SET remind_name = %(n1)s Where remind_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "內容":
            cursor.execute("UPDATE remind SET remind_detail = %(n1)s Where remind_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "時間":
            cursor.execute("UPDATE remind SET remind_time = %(n1)s Where remind_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""刪除提醒(V)"""
def del_remind(uid,user_talk):
    global service
    
    if talk[0] == "輸入要刪除的提醒標題：":
        talk[1] = user_talk
        
        cursor.execute("SELECT * FROM remind WHERE remind_name = '{}' and user_uid = '{}'".format(user_talk,uid))
        remind_name = []
        remind_detail = []
        remind_time = []
        user_uid = []
        datalist = cursor.fetchall()
            
        for row in datalist:
            remind_name.append(row['remind_name'])
            remind_detail.append(row['remind_detail'])
            remind_time.append(row['remind_time'])
            user_uid.append(row['user_uid'])
            
        for i in range(len(remind_name)):
            result = "===========================\n"
            result += '提醒標題：' + remind_name[i] + '\n'
            result += '提醒內容：' + remind_detail[i] + '\n'
            result += '提醒時間：' + remind_time[i] + '\n'
            result += "==========================="
            line_bot_api.push_message(user_uid[i],TextSendMessage(result))
                
        talk[0] = "是否要刪除提醒？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="是", text="是")),
            QuickReplyButton(action=MessageAction(label="否", text="否"))
        ])))
        
    elif talk[0] == "是否要刪除提醒？":
        if user_talk == "是":
            sql = "DELETE FROM remind WHERE remind_name = '{}'".format(talk[1])
            cursor.execute(sql)
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已刪除！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""目標(V)"""
def goal(uid,user_talk):
    global service
    
    if(user_talk == "!查看目標所有功能"):
        line_bot_api.push_message(uid,TemplateSendMessage(alt_text='ButtonsTemplate',template=ButtonsTemplate(
                title="目標功能",text="使用目標功能",
                actions=[
                    MessageAction(label="建立目標", text="!建立目標"),
                    MessageAction(label="查詢目標", text="!查詢目標"),
                    MessageAction(label="編輯目標", text="!編輯目標"),
                    MessageAction(label="刪除目標", text="!刪除目標")
        ])))
    
    elif user_talk == "!建立目標":
        talk[0] = "輸入要建立的目標標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "建立目標"
        
    elif user_talk == "!查詢目標":
        serch_goal(uid)
        
    elif user_talk == "!編輯目標":
        talk[0] = "輸入要編輯的目標標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "編輯目標"
        
    elif user_talk == "!刪除目標":
        talk[0] = "輸入要刪除的目標標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "刪除目標"
        
    #--------------------------------------------------------------------------
    
    elif service == "建立目標":
        set_goal(uid,user_talk)
        
    elif service == "編輯目標":
        edit_goal(uid,user_talk)
        
    elif service == "刪除目標":
        del_goal(uid,user_talk)



"""建立目標(V)"""
def set_goal(uid,user_talk):
    global service
    tmp = ["","",""] #暫存陣列
                
    if talk[0] == "輸入要建立的目標標題：":
        talk[1] = user_talk
        talk[0] = "輸入要建立的目標內容："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
                
    elif talk[0] == "輸入要建立的目標內容：":
        talk[1] += '|' + user_talk
        talk[0] = "輸入要建立的目標時間"
        datetimepicker(uid,talk[0])
        
    elif talk[0] == "輸入要建立的目標時間":
        talk[1] += '|' + user_talk
        talk[0] = "建立完成，是否要儲存？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
                ])))
        
    elif talk[0] == "建立完成，是否要儲存？":
        if user_talk == "是":
            line_bot_api.push_message(uid,TextSendMessage("已建立！"))
            tmp = talk[1].split("|")
            
            sql = "INSERT INTO goal(goal_name,goal_detail,goal_time,user_uid) VALUES('{}','{}','{}','{}')".format(tmp[0],tmp[1],tmp[2],uid)
            cursor.execute(sql)
            conn.commit()
            
            talk[0] = ""
            talk[1] = ""
            service = ""
            
            result = "===========================\n"
            result += "目標標題：" + tmp[0] + '\n' 
            result += "目標內容：" + tmp[1] + '\n' 
            result += "目標時間：" + tmp[2] + '\n' 
            result += "==========================="
            line_bot_api.push_message(uid,TextSendMessage(result))
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""查詢目標(V)"""
def serch_goal(uid):
    cursor.execute("SELECT * FROM goal WHERE user_uid = '{}'".format(uid))
    goal_name = []
    goal_detail = []
    goal_time = []
    user_uid = []
    datalist = cursor.fetchall()  
    
    if cursor.rowcount == 0:
        result = "查無結果"
        line_bot_api.push_message(uid,TextSendMessage(result))
    
    for row in datalist:
        goal_name.append(row['goal_name'])
        goal_detail.append(row['goal_detail'])
        goal_time.append(row['goal_time'])
        user_uid.append(row['user_uid'])
        
    for i in range(len(goal_name)):
        t = str(datetime.datetime.strptime(goal_time[i],"%Y-%m-%d %H:%M:%S") - datetime.datetime.now())
        t = t.replace(" days, ","日")
        t = t.replace(":","時",1)
        t = t.replace(":","分",1)
        t = t[:-9]
        
        result = "===========================\n"
        result += '目標標題：' + goal_name[i] + '\n'
        result += '目標內容：' + goal_detail[i] + '\n'
        result += '剩餘時間：' + t + '\n'
        result += "==========================="
        line_bot_api.push_message(user_uid[i],TextSendMessage(result))



"""編輯目標(V)"""
def edit_goal(uid,user_talk):
   global service
   tmp = ["",""]
   
   if talk[0] == "輸入要編輯的目標標題：":
        talk[1] = user_talk
        talk[0] = "輸入要編輯的目標功能："
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="標題", text="標題")),
                QuickReplyButton(action=MessageAction(label="內容", text="內容")),
                QuickReplyButton(action=MessageAction(label="時間", text="時間"))
                ])))
                
   elif talk[0] == "輸入要編輯的目標功能：":
       talk[1] += '|' + user_talk
       talk[0] = "輸入要修改的目標內容：" 
       line_bot_api.push_message(uid,TextSendMessage(talk[0]))
       
   elif talk[0] == "輸入要修改的目標內容：":
       tmp = talk[1].split("|")
       
       if tmp[1] == "標題":
            cursor.execute("UPDATE goal SET goal_name = %(n1)s Where goal_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "內容":
            cursor.execute("UPDATE goal SET goal_detail = %(n1)s Where goal_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "時間":
            cursor.execute("UPDATE goal SET goal_time = %(n1)s Where goal_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""刪除目標(V)"""
def del_goal(uid,user_talk):
    global service
    
    if talk[0] == "輸入要刪除的目標標題：":
        talk[1] = user_talk
        
        cursor.execute("SELECT * FROM goal WHERE user_uid = '{}'".format(uid))
        goal_name = []
        goal_detail = []
        goal_time = []
        user_uid = []
        datalist = cursor.fetchall()  
        
        for row in datalist:
            goal_name.append(row['goal_name'])
            goal_detail.append(row['goal_detail'])
            goal_time.append(row['goal_time'])
            user_uid.append(row['user_uid'])
            
        for i in range(len(goal_name)):
            result = "===========================\n"
            result += '目標標題：' + goal_name[i] + '\n'
            result += '目標內容：' + goal_detail[i] + '\n'
            result += '目標時間：' + goal_time[i] + '\n'
            result += "==========================="
            line_bot_api.push_message(user_uid[i],TextSendMessage(result))
            
        talk[0] = "是否要刪除目標？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
        ])))
        
    elif talk[0] == "是否要刪除目標？":
        if user_talk == "是":
            sql = "DELETE FROM goal WHERE goal_name = '{}'".format(talk[1])
            cursor.execute(sql)
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已刪除！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""筆記"""
def note(uid,user_talk):
    global service
    
    if user_talk == "!查看筆記所有功能":
        line_bot_api.push_message(uid,TemplateSendMessage(alt_text='ButtonsTemplate',template=ButtonsTemplate(
                title="筆記功能",text="使用筆記功能",
                actions=[
                    MessageAction(label="建立筆記", text="!建立筆記"),
                    MessageAction(label="查詢筆記", text="!查詢筆記"),
                    MessageAction(label="編輯筆記", text="!編輯筆記"),
                    MessageAction(label="刪除筆記", text="!刪除筆記")
        ])))
    
    elif user_talk == "!建立筆記":
        talk[0] = "輸入要建立的筆記標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "建立筆記"
        
    elif user_talk == "!查詢筆記":
        talk[0] = "選擇查詢方式："
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="查詢標題", text="查詢筆記標題")),
                QuickReplyButton(action=MessageAction(label="查詢分類", text="查詢筆記分類"))
        ])))
    
    elif user_talk == "!查詢筆記標題":
        talk[0] = "輸入要查詢的筆記標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "查詢筆記標題"
    
    elif user_talk == "!查詢筆記分類":
        talk[0] = "輸入要查詢的筆記分類："
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="筆記", text="筆記")),
                QuickReplyButton(action=MessageAction(label="記事", text="記事")),
                QuickReplyButton(action=MessageAction(label="記帳", text="記帳")),
                QuickReplyButton(action=MessageAction(label="其他", text="其他"))
                ])))
        service = "查詢筆記分類"
    
    elif user_talk == "!編輯筆記":
        talk[0] = "輸入要編輯的筆記標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "編輯筆記"
        
    elif user_talk == "!刪除筆記":
        talk[0] = "輸入要刪除的筆記標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "刪除筆記"
    
    #--------------------------------------------------------------------------
    
    elif service == "建立筆記":
        set_note(uid,user_talk)
        
    elif service == "查詢筆記標題":
        serch_note_name(uid,user_talk)
        
    elif service == "查詢筆記分類":
        serch_note_title(uid,user_talk)
        
    elif service == "編輯筆記":
        edit_note(uid,user_talk)
        
    elif service == "刪除筆記":
        del_note(uid,user_talk)



"""建立筆記(V)"""
def set_note(uid,user_talk):
    global service
    tmp = ["","",""]
    time_tmp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
    if talk[0] == "輸入要建立的筆記標題：":
        talk[1] = user_talk
        talk[0] = "選擇筆記分類："
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="筆記", text="筆記")),
                QuickReplyButton(action=MessageAction(label="記事", text="記事")),
                QuickReplyButton(action=MessageAction(label="記帳", text="記帳")),
                QuickReplyButton(action=MessageAction(label="其他", text="其他"))
                ])))
    
    elif talk[0] == "選擇筆記分類：":
        talk[1] += '|' + user_talk
        talk[0] = "輸入要建立的筆記內容："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
    
    elif talk[0] == "輸入要建立的筆記內容：":
        talk[1] += '|' + user_talk
        talk[0] = "建立完成，是否要儲存？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
                ])))
        
    elif talk[0] == "建立完成，是否要儲存？":
        if user_talk == "是":
            line_bot_api.push_message(uid,TextSendMessage("已建立！"))
            tmp = talk[1].split("|")
            
            sql = "INSERT INTO note(note_name,note_title,note_content,note_time,user_uid) VALUES('{}','{}','{}','{}','{}')".format(tmp[0],tmp[1],tmp[2],time_tmp,uid)
            cursor.execute(sql)
            conn.commit()
            
            talk[0] = ""
            talk[1] = ""
            service = ""
            
            result = "===========================\n"
            result += "筆記標題：" + tmp[0] + '\n'
            result += "筆記分類：" + tmp[1] + '\n'
            result += "筆記內容：" + tmp[2] + '\n'
            result += "==========================="
            line_bot_api.push_message(uid,TextSendMessage(result))
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            
            talk[0] = ""
            talk[1] = ""
            service = ""



"""查詢筆記標題(V)"""
def serch_note_name(uid,user_talk):
    global service
    cnt = 0
    
    if talk[0] == "輸入要查詢的筆記標題：":
        talk[1] = user_talk
        
        cursor.execute("SELECT * FROM note WHERE user_uid = '{}'".format(uid))
        note_name = []
        note_title = []
        note_content = []
        user_uid = []
        datalist = cursor.fetchall()
        
        for row in datalist:
            note_name.append(row['note_name'])
            note_title.append(row['note_title'])
            note_content.append(row['note_content'])
            user_uid.append(row['user_uid'])
        
        for i in range(len(note_name)):
            if talk[1] in note_name[i]:
                result = "===========================\n"
                result += '筆記標題：' + note_name[i] + '\n'
                result += '筆記分類：' + note_title[i] + '\n'
                result += '筆記內容：' + note_content[i] + '\n'
                result += "==========================="
                line_bot_api.push_message(user_uid[i],TextSendMessage(result))
                cnt += 1
        
        if cnt == 0:
            line_bot_api.push_message(uid,TextSendMessage("查無結果"))
    
    talk[0] = ""
    talk[1] = ""
    service = ""



"""查詢筆記分類(V)"""
def serch_note_title(uid,user_talk):
    global service
    
    if talk[0] == "輸入要查詢的筆記分類：":
        talk[1] = user_talk
        
        cursor.execute("SELECT * FROM note WHERE note_title = '{}'".format(talk[1]))
        note_name = []
        note_title = []
        note_content = []
        user_uid = []
        datalist = cursor.fetchall()  
        
        if cursor.rowcount == 0:
            result = "查無結果"
            line_bot_api.push_message(uid,TextSendMessage(result))
        
        for row in datalist:
            note_name.append(row['note_name'])
            note_title.append(row['note_title'])
            note_content.append(row['note_content'])
            user_uid.append(row['user_uid'])
        
        for i in range(len(note_name)):
            if user_uid[i] == uid: 
                result = "===========================\n"
                result += '筆記標題：' + note_name[i] + '\n'
                result += '筆記分類：' + note_title[i] + '\n'
                result += '筆記內容：' + note_content[i] + '\n'
                result += "==========================="
                line_bot_api.push_message(user_uid[i],TextSendMessage(result))
    
    talk[0] = ""
    talk[1] = ""
    service = ""



"""編輯筆記(V)"""
def edit_note(uid,user_talk):
   global service
   tmp = ["",""]
   
   if talk[0] == "輸入要編輯的筆記標題：":
        talk[1] = user_talk
        talk[0] = "輸入要編輯的筆記功能："
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="標題", text="標題")),
                QuickReplyButton(action=MessageAction(label="內容", text="內容"))
                ])))
                
   elif talk[0] == "輸入要編輯的筆記功能：":
       talk[1] += '|' + user_talk
       talk[0] = "輸入要修改的筆記內容：" 
       line_bot_api.push_message(uid,TextSendMessage(talk[0]))
       
   elif talk[0] == "輸入要修改的筆記內容：":
       tmp = talk[1].split("|")
       
       if tmp[1] == "標題":
            cursor.execute("UPDATE note SET note_name = %(n1)s Where note_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "內容":
            cursor.execute("UPDATE note SET note_detail = %(n1)s Where note_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""刪除筆記(V)"""
def del_note(uid,user_talk):
    global service
    
    if talk[0] == "輸入要刪除的筆記標題：":
        talk[1] = user_talk
        
        cursor.execute("SELECT * FROM note WHERE note_name = '{}' and user_uid = '{}'".format(talk[1],uid))
        note_name = []
        note_title = []
        note_content = []
        note_time = []
        user_uid = []
        datalist = cursor.fetchall()
        
        for row in datalist:
            note_name.append(row['note_name'])
            note_title.append(row['note_title'])
            note_content.append(row['note_content'])
            note_time.append(row['note_time'])
            user_uid.append(row['user_uid'])
        
        for i in range(len(note_name)):
            result = "===========================\n"
            result += '筆記標題：' + note_name[i] + '\n'
            result += '筆記分類：' + note_title[i] + '\n'
            result += '筆記內容：' + note_content[i] + '\n'
            result += '筆記時間：' + note_time[i] + '\n'
            result += "==========================="
            line_bot_api.push_message(user_uid[i],TextSendMessage(result))
        
        talk[0] = "是否要刪除筆記？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
                ])))
        
    elif talk[0] == "是否要刪除筆記？":
        if user_talk == "是":
            sql = "DELETE FROM note WHERE note_name = '{}'".format(talk[1])
            cursor.execute(sql)
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已刪除！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""書籤"""
def bookmark(uid,user_talk):
    global service
    
    if(user_talk == "!查看書籤所有功能"):
        line_bot_api.push_message(uid,TemplateSendMessage(alt_text='ButtonsTemplate',template=ButtonsTemplate(
                title="書籤功能",text="使用書籤功能",
                actions=[
                    MessageAction(label="建立書籤", text="!建立書籤"),
                    MessageAction(label="查詢書籤", text="!查詢書籤"),
                    MessageAction(label="編輯書籤", text="!編輯書籤"),
                    MessageAction(label="刪除書籤", text="!刪除書籤"),
                    #MessageAction(label="分享書籤", text="!分享書籤")
        ])))
        
    elif user_talk == "!建立書籤":
        talk[0] = "輸入要建立的書籤標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "建立書籤"
        
    elif user_talk == "!查詢書籤":
        talk[0] = "選擇查詢方式"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="標題查詢", text="!查詢書籤標題")),
                QuickReplyButton(action=MessageAction(label="分類查詢", text="!查詢書籤分類")),
                QuickReplyButton(action=MessageAction(label="全部查詢", text="!查詢全部書籤"))
        ])))
        
    elif user_talk == "!查詢書籤標題":
        talk[0] = "輸入要查詢的書籤標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "查詢書籤標題"
        
    elif user_talk == "!查詢書籤分類":
        talk[0] = "輸入要查詢的書籤分類："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "查詢書籤分類"
    
    elif user_talk == "!查詢全部書籤":
        serch_bookmark_all(uid)
        
    elif user_talk == "!編輯書籤":
        talk[0] = "輸入要編輯的書籤標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "編輯書籤"
        
    elif user_talk == "!刪除書籤":
        line_bot_api.push_message(uid,TextSendMessage("選擇刪除方式" , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="標題查詢", text="!刪除書籤標題")),
                QuickReplyButton(action=MessageAction(label="分類查詢", text="!刪除書籤分類"))
        ])))
        
    elif user_talk == "!刪除書籤標題":
        talk[0] = "輸入要刪除的書籤標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "刪除書籤標題"
        
    elif user_talk == "!刪除書籤分類":
        talk[0] = "輸入要刪除的書籤分類："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "刪除書籤分類"
    
    elif user_talk == "!分享書籤":
        talk[0] = "輸入要分享的書籤標題："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "分享書籤"
    
    #--------------------------------------------------------------------------
    
    elif service == "建立書籤":
        set_bookmark(uid,user_talk)
        
    elif service == "查詢書籤標題":
        serch_bookmark_name(uid,user_talk)
        
    elif service == "查詢書籤分類":
        serch_bookmark_title(uid, user_talk)
        
    elif service == "編輯書籤":
        edit_bookmark(uid,user_talk)
    
    elif service == "重複書籤":
        edit_bookmark_by_URL(uid,user_talk)
        
    elif service == "刪除書籤標題":
        del_bookmark_name(uid,user_talk)
        
    elif service == "刪除書籤分類":
        del_bookmark_title(uid, user_talk)
    
    elif service == "分享書籤":
        share_bookmark(uid,user_talk)



"""建立書籤(V)"""
def set_bookmark(uid,user_talk):
    global service
    tmp = ["","",""] #暫存陣列
    
    cursor.execute('SELECT * FROM bookmark')
    bookmark_URL = []
    datalist = cursor.fetchall()
    
    for row in datalist:
        bookmark_URL.append(row['bookmark_URL'])
                
    if talk[0] == "輸入要建立的書籤標題：":
        talk[1] = user_talk
        talk[0] = "輸入要建立的書籤網址："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
                
    elif talk[0] == "輸入要建立的書籤網址：":
        exist = 0
        
        for i in range(len(bookmark_URL)):
            if user_talk == bookmark_URL[i].replace(" ",""):
                exist = 1
                break
        
        if exist == 0:
            talk[1] += '|' + user_talk
            talk[0] = "輸入要建立的書籤分類："
            line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        
        elif exist == 1:
            talk[1] = user_talk
            talk[0] = "已有重複的網址，是否移至編輯？"
            line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
                ])))
            
    elif talk[0] == "已有重複的網址，是否移至編輯？":
        if user_talk == "是":
            service = "重複書籤"
            edit_bookmark_by_URL(uid,talk[1])
            
        elif user_talk == "否":
            talk[0] = "已取消！"
            line_bot_api.push_message(uid,TextSendMessage(talk[0]))
            
            talk[0] = ""
            talk[1] = ""
            service = ""
    
    elif talk[0] == "輸入要建立的書籤分類：":
        talk[1] += '|' + user_talk
        talk[0] = "建立完成，是否要儲存？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
                ])))
        
    elif talk[0] == "建立完成，是否要儲存？":
        if user_talk == "是":
            line_bot_api.push_message(uid,TextSendMessage("已建立！"))
            tmp = talk[1].split("|")
            
            sql = "INSERT INTO bookmark(bookmark_name,bookmark_URL,bookmark_title,user_uid) VALUES('{}','{}','{}','{}')".format(tmp[0],tmp[1],tmp[2],uid)
            cursor.execute(sql)
            conn.commit()
            
            talk[0] = ""
            talk[1] = ""
            service = ""
            
            result = "===========================\n"
            result += "書籤標題：" + tmp[0] + '\n' 
            result += "書籤網址：" + tmp[1] + '\n' 
            result += "書籤分類：" + tmp[2] + '\n' 
            result += "==========================="
            line_bot_api.push_message(uid,TextSendMessage(result))
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""查詢書籤標題(V)"""
def serch_bookmark_name(uid,user_talk):
    global service
    cnt = 0
    
    if talk[0] == "輸入要查詢的書籤標題：":
        talk[1] = user_talk
        
        cursor.execute("SELECT * FROM bookmark WHERE user_uid = '{}'".format(uid))
        bookmark_name = []
        bookmark_URL = []
        bookmark_title = []
        user_uid = []
        datalist = cursor.fetchall()
        
        for row in datalist:
            bookmark_name.append(row['bookmark_name'])
            bookmark_URL.append(row['bookmark_URL'])
            bookmark_title.append(row['bookmark_title'])
            user_uid.append(row['user_uid'])
        
        for i in range(len(bookmark_name)):
            if talk[1] in bookmark_name[i]:
                result = "===========================\n"
                result += '書籤標題：' + bookmark_name[i] + '\n'
                result += '書籤網址：' + bookmark_URL[i] + '\n'
                result += '書籤分類：' + bookmark_title[i] + '\n'
                result += "==========================="
                line_bot_api.push_message(user_uid[i],TextSendMessage(result))
                cnt += 1
        
        if cnt == 0:
            line_bot_api.push_message(uid,TextSendMessage("查無結果"))
    
    talk[0] = ""
    talk[1] = ""
    service = ""



"""查詢書籤分類(V)"""
def serch_bookmark_title(uid, user_talk):
    global service
    cnt = 0
    
    if talk[0] == "輸入要查詢的書籤分類：":
        talk[1] = user_talk
        
        cursor.execute("SELECT * FROM bookmark WHERE user_uid = '{}'".format(uid))
        bookmark_name = []
        bookmark_URL = []
        bookmark_title = []
        user_uid = []
        datalist = cursor.fetchall()
        
        for row in datalist:
            bookmark_name.append(row['bookmark_name'])
            bookmark_URL.append(row['bookmark_URL'])
            bookmark_title.append(row['bookmark_title'])
            user_uid.append(row['user_uid'])
        
        for i in range(len(bookmark_name)):
            if talk[1] in bookmark_title[i]:
                result = "===========================\n"
                result += '書籤標題：' + bookmark_name[i] + '\n'
                result += '書籤網址：' + bookmark_URL[i] + '\n'
                result += '書籤分類：' + bookmark_title[i] + '\n'
                result += "==========================="
                line_bot_api.push_message(user_uid[i],TextSendMessage(result))
                cnt += 1
        
        if cnt == 0:
            line_bot_api.push_message(uid,TextSendMessage("查無結果"))
    
    talk[0] = ""
    talk[1] = ""
    service = ""



"""查詢全部書籤(V)"""
def serch_bookmark_all(uid):
    cursor.execute("SELECT * FROM bookmark WHERE user_uid = '{}'".format(uid))
    bookmark_name = []
    bookmark_URL = []
    bookmark_title = []
    user_uid = []
    datalist = cursor.fetchall()  
    
    if cursor.rowcount == 0:
        result = "查無結果"
        line_bot_api.push_message(uid,TextSendMessage(result))
    
    for row in datalist:
        bookmark_name.append(row['bookmark_name'])
        bookmark_URL.append(row['bookmark_URL'])
        bookmark_title.append(row['bookmark_title'])
        user_uid.append(row['user_uid'])
        
    for i in range(len(bookmark_name)):
        result = "===========================\n"
        result += '書籤標題：' + bookmark_name[i] + '\n'
        result += '書籤網址：' + bookmark_URL[i] + '\n'
        result += '書籤分類：' + bookmark_title[i] + '\n'
        result += "==========================="
        line_bot_api.push_message(user_uid[i],TextSendMessage(result))



"""編輯書籤(V)"""
def edit_bookmark(uid,user_talk):
   global service
   tmp = ["",""]
   
   if talk[0] == "輸入要編輯的書籤標題：":
        talk[1] = user_talk
        talk[0] = "輸入要編輯的書籤功能："
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="標題", text="標題")),
                QuickReplyButton(action=MessageAction(label="網址", text="網址")),
                QuickReplyButton(action=MessageAction(label="分類", text="分類"))
                ])))
                
   elif talk[0] == "輸入要編輯的書籤功能：":
       talk[1] += '|' + user_talk
       talk[0] = "輸入要修改的書籤內容：" 
       line_bot_api.push_message(uid,TextSendMessage(talk[0]))
       
   elif talk[0] == "輸入要修改的書籤內容：":
       tmp = talk[1].split("|")
       
       if tmp[1] == "標題":
            cursor.execute("UPDATE bookmark SET bookmark_name = %(n1)s Where bookmark_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "網址":
            cursor.execute("UPDATE bookmark SET bookmark_URL = %(n1)s Where bookmark_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "分類":
            cursor.execute("UPDATE bookmark SET bookmark_title = %(n1)s Where bookmark_name = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""重複書籤(V)"""
def edit_bookmark_by_URL(uid,user_talk):
   global service
   tmp = ["",""]
   
   if talk[0] == "已有重複的網址，是否移至編輯？":
       talk[0] = "輸入要編輯的書籤功能："
       line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
           QuickReplyButton(action=MessageAction(label="標題", text="標題")),
           QuickReplyButton(action=MessageAction(label="分類", text="分類"))
       ])))
   
   elif talk[0] == "輸入要編輯的書籤功能：":
       talk[1] += '|' + user_talk
       talk[0] = "輸入要修改的書籤內容：" 
       line_bot_api.push_message(uid,TextSendMessage(talk[0]))
       
   elif talk[0] == "輸入要修改的書籤內容：":
       tmp = talk[1].split("|")
       
       if tmp[1] == "標題":
            cursor.execute("UPDATE bookmark SET bookmark_name = %(n1)s Where bookmark_URL = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
       elif tmp[1] == "分類":
            cursor.execute("UPDATE bookmark SET bookmark_title = %(n1)s Where bookmark_URL = %(n2)s",{'n1':user_talk,'n2':tmp[0]})
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已編輯！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""刪除書籤標題(V)"""
def del_bookmark_name(uid,user_talk):
    global service
    
    if talk[0] == "輸入要刪除的書籤標題：":
        talk[1] = user_talk
        talk[0] = "該標題有："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        
        cursor.execute("SELECT * FROM bookmark WHERE bookmark_name = '{}' and user_uid = '{}'".format(talk[1],uid))
        bookmark_name = []
        bookmark_URL = []
        bookmark_title = []
        user_uid = []
        datalist = cursor.fetchall()  
    
        for row in datalist:
            bookmark_name.append(row['bookmark_name'])
            bookmark_URL.append(row['bookmark_URL'])
            bookmark_title.append(row['bookmark_title'])
            user_uid.append(row['user_uid'])
        
        for i in range(len(bookmark_name)):
            result = "===========================\n"
            result += '書籤標題：' + bookmark_name[i] + '\n'
            result += '書籤內容：' + bookmark_URL[i] + '\n'
            result += '書籤時間：' + bookmark_title[i] + '\n'
            result += "==========================="
            line_bot_api.push_message(user_uid[i],TextSendMessage(result))
        
        talk[0] = "是否全部刪除？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
        ])))
        
    elif talk[0] == "是否全部刪除？":
        if user_talk == "是":
            sql = "DELETE FROM bookmark WHERE bookmark_name = '{}'".format(talk[1])
            cursor.execute(sql)
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已刪除！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""刪除書籤分類(V)"""
def del_bookmark_title(uid,user_talk):
    global service
    
    if talk[0] == "輸入要刪除的書籤分類：":
        talk[1] = user_talk
        talk[0] = "該分類有："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        
        cursor.execute("SELECT * FROM bookmark WHERE bookmark_title = '{}' and user_uid = '{}'".format(talk[1],uid))
        bookmark_name = []
        bookmark_URL = []
        bookmark_title = []
        user_uid = []
        datalist = cursor.fetchall()  
    
        for row in datalist:
            bookmark_name.append(row['bookmark_name'])
            bookmark_URL.append(row['bookmark_URL'])
            bookmark_title.append(row['bookmark_title'])
            user_uid.append(row['user_uid'])
        
        for i in range(len(bookmark_name)):
            result = "===========================\n"
            result += '書籤標題：' + bookmark_name[i] + '\n'
            result += '書籤內容：' + bookmark_URL[i] + '\n'
            result += '書籤時間：' + bookmark_title[i] + '\n'
            result += "==========================="
            line_bot_api.push_message(user_uid[i],TextSendMessage(result))
        
        talk[0] = "是否全部刪除？"
        line_bot_api.push_message(uid,TextSendMessage(talk[0] , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
        ])))
        
    elif talk[0] == "是否全部刪除？":
        if user_talk == "是":
            sql = "DELETE FROM bookmark WHERE bookmark_title = '{}'".format(talk[1])
            cursor.execute(sql)
            conn.commit()
            
            line_bot_api.push_message(uid,TextSendMessage("已刪除！"))
            talk[0] = ""
            talk[1] = ""
            service = ""
            
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消！"))
            talk[0] = ""
            talk[1] = ""
            service = ""



"""分享書籤(V)"""
def share_bookmark(uid,user_talk):
    global service
    tmp =["","",""] #標題,寄件人,收件人uid
    
    if talk[0] == "輸入要分享的書籤標題：":
        talk[0] = "輸入要查詢的書籤標題："
        serch_bookmark_name(uid,user_talk)
        
        talk[1] = user_talk
        talk[0] = "輸入分享對象的LINE名字："
        line_bot_api.push_message(uid,TextSendMessage(talk[0]))
        service = "分享書籤"
    
    elif talk[0] == "輸入分享對象的LINE名字：":
        cursor.execute("SELECT user_name FROM [user] WHERE user_uid = '{}'".format(uid))
        datalist = cursor.fetchone()
        talk[1] += '|' + datalist['user_name']
        
        cursor.execute("SELECT user_uid FROM [user] WHERE user_name = '{}'".format(user_talk))
        datalist = cursor.fetchone()
        
        if cursor.rowcount == 0:
            result = "查無結果"
            line_bot_api.push_message(uid,TextSendMessage(result))
            
            talk[0] = ""
            talk[1] = ""
            service = ""
        
        talk[1] += '|' + datalist['user_uid']
        
        talk[0] = "是否要傳送書籤給 "
        line_bot_api.push_message(uid,TextSendMessage(talk[0] + user_talk , quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="是", text="是")),
                QuickReplyButton(action=MessageAction(label="否", text="否"))
        ])))
    
    elif talk[0] == "是否要傳送書籤給 ":
        if user_talk == "是":
            tmp = talk[1].split("|")
            
            cursor.execute("SELECT * FROM bookmark WHERE user_uid = '{}'".format(uid))
            bookmark_name = []
            bookmark_URL = []
            datalist = cursor.fetchall()
            
            for row in datalist:
                bookmark_name.append(row['bookmark_name'])
                bookmark_URL.append(row['bookmark_URL'])
            
            for i in range(len(bookmark_name)):
                if tmp[0] in bookmark_name[i]:
                    result = "===========================\n"
                    result += '書籤標題：' + bookmark_name[i] + '\n'
                    result += '書籤網址：' + bookmark_URL[i] + '\n'
                    result += '傳送自：' + tmp[1] + '\n'
                    result += "==========================="
                    line_bot_api.push_message(tmp[2],TextSendMessage(result))
                
            line_bot_api.push_message(uid,TextSendMessage("已分享書籤"))
        
        elif user_talk == "否":
            line_bot_api.push_message(uid,TextSendMessage("已取消"))
            
            talk[0] = ""
            talk[1] = ""
            service = ""



if __name__ == "__main__":
    app.run(port=5500)