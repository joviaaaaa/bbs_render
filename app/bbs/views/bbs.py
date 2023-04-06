from flask import Blueprint, Flask, request, render_template, redirect, url_for, session

import json
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import request
from flask import jsonify
import ipwhois
import hashlib
from sqlalchemy import and_, or_

import psycopg2
import configparser

from flask import Markup
from ipwhois import IPWhois
from bbs.models import db
from bbs.models.bbs import Article, Thread, Board, Category
import os
import re
import errno
from enum import Enum, IntEnum, auto

THREAD_FIRST_POST = 1
THREAD_LAST_POST = 1000

DATA_USER = os.environ['DATABASE_USER']
DATA_PASS = os.environ['DATABASE_PASS']
DATA_HOST = os.environ['DATABASE_HOST']
DATA_NAME = os.environ['DATABASE_NAME']

bbs = Blueprint('bbs', __name__)

Hex_list = \
['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o',\
 'p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N',\
 'O','P','Q','R','S','T','U','V','W','X','Y','Z']

class atcl(IntEnum):
    id = 0
    article_count = auto()
    pub_date = auto()
    userid = auto()
    name = auto()
    article = auto()
    thread_id = auto()

@bbs.route("/")
def main():
    category_list, board_list = board_menu_imt()
    threads = Thread.query.all()
    return render_template("index.html", threads = threads, categories = category_list, boards = board_list)

@bbs.route("/search_result", methods=["GET"])
def search():
    search_get = request.args.get("search")
    notstr = '' 
    if search_get == notstr:
       return redirect("/")

    search_get = "%{}%".format(search_get) 
    search_hit = Thread.query.filter(Thread.threadname.like(search_get)).all()
    search_list = []
    for seth in search_hit:
       search_list.append(seth.threadname)
    
    return render_template("search_result.html",search=search_list)

@bbs.route("/thread_json/<thread_get>/<range_nmb>", methods=["POST"])
def thred_json_return(thread_get,range_nmb):
    if thread_search(thread_get) == False:
        return "not exist thread"
    thread = thread_search(thread_get) 
    return_article = article_acq(mode="ONLY_NUM", thread_arg = thread, range1 = range_nmb)
    
    for r in return_article:
        rejson = {
                    "Article": {
                        "id": r.id, 
                        "article_count": r.article_count, 
                        "pub_date": str(r.pub_date), 
                        "userid": r.userid, 
                        "name": r.name, 
                        "article": r.article
                        }
                 }
    #e = json.dumps(rejson)
    return jsonify(rejson)

@bbs.route("/create", methods=["POST"])
def create():
    thread_list = []
    threads = Thread.query.all()
    date = datetime.now()
    thread_get = request.form["thread"]
    article = request.form["article"]
    name = request.form["name"]
    userid = shorthash(((request.remote_addr[1] + date.strftime('%Y%m%d'))),8)
    message = ""
    article_count_first = 1
    name = threadpost_name_check(thread=thread_get, name=name)
    
    session['date'] = date
    session['article'] = request.form["article"]
    session['userid'] = shorthash((request.remote_addr[1] + date.strftime('%Y%m%d')),8)
    session['name'] = name
    session['thread'] = thread_get
    session['article_count'] = article_count_first

    for th in threads:
        thread_list.append(th.threadname)

    if thread_get in thread_list:
        thread = Thread.query.filter_by(threadname=thread_get).first()
        article_count = Article.query.filter_by(thread_id=thread.id).count() + 1
        session['article_count'] = article_count
        session['thread'] = thread

        if(threadpost_error_check(thread=thread_get, article_count=article_count, article=article, name=name, date=date, userid=userid)):
            message = threadpost_error_log(thread=thread_get, article_count=article_count, article=article, name=name, date=date, userid=userid)
            session['message'] = message
            return redirect(url_for('bbs.error_direct'))

        admin = Article(article_count, pub_date=date, name=name, article=article, userid=userid, thread_id=thread.id)
        db.session.add(admin)
        db.session.commit()
        articles = article_acq(mode="ALL", thread_arg=thread)
        return redirect(url_for('bbs.result_direct'))

    else:
        board_id = request.form["board_id"]
        thread_new = Thread(thread_get,board_id)

        if(threadpost_error_check(thread=thread_get, article_count=article_count_first, article=article, name=name, date=date, userid=userid)):
            message = threadpost_error_log(thread=thread_get, article_count=article_count_first, article=article, name=name, date=date, userid=userid)
            session['message'] = message
            return redirect(url_for('bbs.error_direct'))

        db.session.add(thread_new)
        db.session.commit()

        thread = Thread.query.filter_by(threadname=thread_get).first()
        article_count = Article.query.filter_by(thread_id=thread.id).count() + 1
        session['thread'] = thread.threadname
        session['article_count'] = article_count

        admin = Article(article_count, pub_date=date, name=name, article=article, userid=userid, thread_id=thread.id)
        db.session.add(admin)
        db.session.commit()
        #articles = article_acq(mode="ALL", thread_arg=thread_new)
        return redirect(url_for('bbs.result_direct_thread'))

@bbs.route("/result_direct_thread/")
def result_direct_thread():
    if 'article_count' not in session and 'article' not in session and 'name' not in session and 'date' not in session and 'thread' not in session and 'userid' not in session:
        return redirect(url_for('/'))
    
    date = session['date']
    article = session['article']
    name    = session['name']
    userid = session['userid']
    thread = session['thread'] 
    thread = Thread.query.filter_by(threadname=thread).first()
    article_count = session['article_count'] 

    return render_template("bbs_result.html", article_count=article_count, article=article, name=name, now=date,thread=thread, userid=userid, threadinit='True')


@bbs.route("/thread/<thread_get>/")
def thread_defo(thread_get):
    return thread(thread_get,"dummy")

@bbs.route("/thread/<thread_get>/<range_nmb>")
def thread(thread_get,range_nmb):
    thread_list = []
    start_point_temp = []
    
    threads = Thread.query.all()
    for th in threads:
        thread_list.append(th.threadname)
    if thread_get in thread_list:
        thread = Thread.query.filter_by(threadname=thread_get).first()
    else:
        print("error")
        return render_template("index.html")
    
    start_point_temp.append(range_nmb.find('l')) if range_nmb.find('l') >= 0 else False
    start_if_number = ((re.search('.*\d.*',range_nmb).start())) if re.search('.*\d.*',range_nmb) != None else False
    start_point_temp.append(range_nmb.find('-')) if range_nmb.find('-') >= 0 else False
    
    if  start_point_temp != [] and start_if_number != None:
        if min(start_point_temp) > start_if_number  and range_nmb[min(start_point_temp)] != '-':
            start_point_temp.append((re.search('.*\d.*',range_nmb).start()))

    else:
        start_point_temp.append(0)

    start_point = min(start_point_temp)
    
    bo = Board.query.filter_by(id=thread.board_id).first()

    if range_nmb[start_point] == 'l':
        range_temp1 = range_nmb.split('-')
        range_temp = range_temp1[0].split('l')
        if re.sub(r"\D","",range_temp[1]) == None or len(re.sub(r"\D","",range_temp[1])) == 0:
            articles = article_acq(mode="ALL", thread_arg = thread)

        else:
            display_range = int(re.sub(r"\D","",range_temp[1]))
            articles = article_acq(mode="L", thread_arg=thread, range1=display_range)
            
    elif range_nmb[start_point] == '-':
        range_temp1 = range_nmb.split('l')
        range_temp = range_temp1[0].split('-')
        display_range_start = THREAD_FIRST_POST      
        display_range_end = THREAD_LAST_POST     
        
        if ((range_temp[0] is not None) and (not len(range_temp[0]) == 0)):
            display_range_start = int(re.sub(r"\D","",range_temp[0]))
        
        if ((range_temp[1] is not None) and (not len(range_temp[1]) == 0)):
            display_range_end = int(re.sub(r"\D","",range_temp[1]))     
        
        if display_range_start == THREAD_FIRST_POST and display_range_end == THREAD_LAST_POST:
            articles = article_acq(mode="ALL", thread_arg = thread)

        else:
            articles = article_acq(mode="-", thread_arg=thread, range1=display_range_start, range2=display_range_end)
    
    else:
        range_temp1 = range_nmb.split('-')
        range_temp = range_temp1[0].split('l')
        
        if len(re.sub(r"\D","",range_temp[0])) == 0:
            articles = article_acq(mode="ALL", thread_arg = thread)
        
        else:
            display_range = int(re.sub(r"\D","",range_temp[0]))
            articles = article_acq(mode="ONLY_NUM", thread_arg = thread, range1 = display_range)
    
    if len(articles) == 0:
        return redirect(url_for('bbs.thread_defo', thread_get=thread_get))

    return render_template("thread.html",
                             articles=articles,
                             thread=thread_get,
                             board=bo
                             )


@bbs.route("/result", methods=["POST"])
def result():
    date = datetime.now()
    session['date'] = date
    session['article'] = request.form["article"]
    session['userid'] = shorthash((request.remote_addr[1] + date.strftime('%Y%m%d')),8)
    session['thread'] = request.form["thread"]
    thread = Thread.query.filter_by(threadname=(request.form["thread"])).first()
    session['article_count'] = Article.query.filter_by(thread_id=thread.id).count() + 1

    date = datetime.now()
    article = request.form["article"]
    name = request.form["name"]
    userid = shorthash((request.remote_addr[1] + date.strftime('%Y%m%d')),8)
    thread = request.form["thread"]
    thread = Thread.query.filter_by(threadname=thread).first()
    article_count = Article.query.filter_by(thread_id=thread.id).count() + 1

    error = False
    message = ""

    name = threadpost_name_check(thread=thread, name=name)
    session['name'] = name

    if(threadpost_error_check(thread=thread, article_count=article_count, article=article, name=name, date=date, userid=userid)):
        message = threadpost_error_log(thread=thread, article_count=article_count, article=article, name=name, date=date, userid=userid)
        session['message'] = message
        return redirect(url_for('bbs.error_direct'))

    admin = Article(article_count, pub_date=date, name=name, article=article, userid=userid, thread_id=thread.id)
    db.session.add(admin)
    db.session.commit()
    
    if article_count == 1000:
        max_comment = Article(1001, pub_date=date, name="ラスト", article="1000だよ", userid="admin", thread_id=thread.id)
        db.session.add(max_comment)
        db.session.commit()

    return redirect(url_for('bbs.result_direct'))

@bbs.route("/error_direct/")
def error_direct():
    if 'article_count' not in session and\
       'article' not in session and \
       'name' not in session and \
       'date' not in session and \
       'thread' not in session and \
       'userid' not in session and \
       'messagge' not in session:
       
        return redirect(url_for('/'))

    date = session['date']
    article = session['article']
    name    = session['name']
    userid = session['userid']
    thread = session['thread'] 
    thread = Thread.query.filter_by(threadname=thread).first()
    article_count = session['article_count'] 
    message = session['message']

    session_delete()

    return render_template("bbs_error.html", article_count=article_count, article=article, name=name, now=date,thread=thread, userid=userid, message=message)

@bbs.route("/result_direct/")
def result_direct():
    if 'article_count' not in session and 'article' not in session and 'name' not in session and 'date' not in session and 'thread' not in session and 'userid' not in session:
        return redirect(url_for('/'))
    
    date = session['date']
    article = session['article']
    name    = session['name']
    userid = session['userid']
    thread = session['thread'] 
    thread = Thread.query.filter_by(threadname=thread).first()
    article_count = session['article_count'] 

    session_delete()

    return render_template("bbs_result.html", article_count=article_count, article=article, name=name, now=date,thread=thread, userid=userid, threadinit='False')


@bbs.route("/board_menu")
def board_menu():
    category_list, board_list = board_menu_imt()
    return render_template("board_menu.html", categories = category_list, boards = board_list)

def board_menu_imt():
    category_list :str = []
    categories = Category.query.all()
    board_list :str = [[]]
    
    for ca in categories:
        category_list.append(str(ca.categoryname))
        board = Board.query.filter_by(category_id = ca.id).all()
        board_list_temp :str = []
        for bo in board:
            board_list_temp.append(bo)
        board_list.append(board_list_temp)

    return category_list, board_list

def article_acq(mode, thread_arg=None, range1=THREAD_FIRST_POST, range2=THREAD_LAST_POST):
    if mode is "ALL":
        articles = Article.query.filter_by(thread_id=thread_arg.id).order_by(Article.article_count).all()

    elif mode is "L":
        cnt_article = Article.query.filter_by(thread_id=thread_arg.id).count()
        display_range = cnt_article - range1 + 1
        articles = Article.query.filter(or_(and_(Article.article_count==THREAD_FIRST_POST,Article.thread_id==thread_arg.id),and_(Article.thread_id==thread_arg.id,Article.article_count>=display_range))).order_by(Article.article_count).all()
    
    elif mode is "-":
        display_range_init =  max(1,range1)
        display_range = display_range_init + max(0,range2 - range1)
        articles = Article.query.filter(or_(and_(Article.thread_id==thread_arg.id, Article.article_count>=display_range_init, Article.article_count<=display_range),and_(Article.thread_id==thread_arg.id, Article.article_count==THREAD_FIRST_POST))).order_by(Article.article_count).all()
    
    elif mode is "ONLY_NUM":
        articles = Article.query.filter(Article.thread_id==thread_arg.id,Article.article_count==range1).all()
    
    else:
        print("error")
        return None
        
    return articles    

@bbs.route("/board/<board_name>/")
def board(board_name):
    Thread_ID = 1
    Thread_NAME = 2
    i = 0

    next_jump = []
    prev_jump = []
    thread_list :str = []
    article_list :str = [[]]
    article_total_posts = []

    bo = Board.query.filter_by(boardname=board_name).first()
    SQL_STATE = """SELECT date_desc,t_id,threadname FROM thread as t2 INNER JOIN ( \
                   SELECT MAX(pub_date) as date_desc, a.thread_id as t_id from article as a \
                   WHERE a.thread_id IN \
                   (SELECT t.id as In_thread_id FROM thread AS t \
                   INNER JOIN board as b ON t.board_id = b.id WHERE b.boardname = %s) \
                   GROUP BY a.thread_id ORDER BY MAX(pub_date) \
                   DESC LIMIT 20) \
                   AS s ON t2.id = s.t_id ORDER BY date_desc DESC;"""

    try:
        cnn = psycopg2.connect(dbname=DATA_NAME,host=DATA_HOST,user=DATA_USER,password=DATA_PASS)
        cur = cnn.cursor()
        cur.execute(SQL_STATE, (board_name,))
        rows = cur.fetchall()
        cur.close()
        cnn.close()

    except (psycopg2.OperationalError) as e:
        print (e)
    
    th_t = len(rows)
    
    for row in rows:
        thread = Thread(threadname=row[Thread_NAME],board_id=None)
        thread.id = row[Thread_ID]
        thread_list.append(str(row[Thread_NAME]))
        article = article_acq(mode="L", thread_arg=thread, range1=10)
        article_list_temp :str = []
        for al in article:
            article_list_temp.append(al)
        article_list.append(article_list_temp)

        article_total_posts.append(Article.query.filter(Article.thread_id==row[Thread_ID]).count()) 
        next_jump.append((i + 1) % th_t)
        prev_jump.append((i + (th_t - 1)) % th_t)
        i += 1

    return render_template("board.html", boards=bo,threads=thread_list,articles=article_list,a_to=article_total_posts,next_jp=next_jump,prev_jp=prev_jump)
    
def base10to(n,b):
    if(int(n/b)):
      return base10to(int(n/b),b) + (Hex_list[n%b])
    return str(n%b)

def base10from(n,b):
    m = 0
    numlist = list(n)
    while(numlist):
     m *= b
     m += int(numlist.pop(0))
    return m     
    
def Hash_Id(id):
    return hashlib.md5(id.encode()).hexdigest()    

def shorthash(id,len):
    hashed_id = Hash_Id(id) 
    str = (base10to(int(hashed_id,16),62))
    return str[0:len]

def tojson(obj):
    n = json.dumps(obj)
    o = json.loads(n)
    return o

def thread_search(threadname):
    thread_list = []
    threads = Thread.query.all()
    for th in threads:
        thread_list.append(th.threadname)
    
    if threadname in thread_list:
        thread = Thread.query.filter_by(threadname=threadname).first()
    
    else:
        return False

    return thread


def threadpost_error_check(thread, article_count, article, name, date, userid):
    error = False
    message = ""

    if article == "":
        error = True;
        
    if article_count >= 1001:
        error = True;
    
    if thread == "":
        error = True;

    return error;   

def threadpost_error_log(thread, article_count, article, name, date, userid):
    error = False
    message = ""

    if article == "":
        message += "コメント内容が空です。何か入力して投稿してください。\n"
        
    if article_count >= 1001:
        message += "投稿内容が1000に達しています\n"

    if thread == "":
        message += "スレッド名が空です。何か入力して投稿してください。\n"

    return message; 

def threadpost_name_check(thread, name):
    
    if name == "":
        name = "名無しさん"
    
    return name;   

def session_delete():
    if 'article_count'  in session:
        session.pop('article_count', None)
    
    if 'article'  in session:
        session.pop('article', None)

    if 'name'  in session:
        session.pop('name', None)

    if 'date'  in session:
        session.pop('date', None)

    if 'thread'  in session:
        session.pop('thread', None)

    if 'userid'  in session:
        session.pop('userid', None)

    if 'message'  in session:
        session.pop('message', None)
    
    session.clear()

    return None;

@bbs.context_processor
def add_staticfile():
    def staticfile_cp(fname):
        path = os.path.join(bbs.root_path, '../static/css/', fname)
        #mtime =  str(int(os.stat(path).st_mtime))
        return '/static/css/' + fname# + '?v=' + str(mtime)
    return dict(staticfile=staticfile_cp)