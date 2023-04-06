"""app/bbs/models/bbs.py
"""
from datetime import datetime
from bbs.models import db

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    article_count = db.Column(db.Integer, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False,
                                default=datetime.utcnow)
    userid = db.Column(db.String(20),nullable=False)
    name = db.Column(db.String(80))
    article = db.Column(db.Text())
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)

    def __init__(self,article_count,  pub_date, name, userid, article, thread_id):
        self.article_count = article_count
        self.pub_date = pub_date
        self.name = name
        self.userid = userid
        self.article = article
        self.thread_id = thread_id


class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    threadname = db.Column(db.String(80), unique=True)
    articles = db.relationship('Article', backref='thread', lazy=True)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'))

    def __init__(self, threadname, board_id, articles=[]):
        self.threadname = threadname
        self.board_id = board_id
        self.articles = articles


class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    boardname = db.Column(db.String(80), unique=True)
    thread = db.relationship('Thread', backref='board', lazy=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    def __init__(self, boardname, thread, category_id):
        self.boardname = boardname
        self.thread = thread
        self.category_id = category_id


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoryname = db.Column(db.String(80), unique=True)
    board = db.relationship('Board', backref='category', lazy=True)
    
    def __init__(self, categoryname, board):
        self.categoryname = categoryname
        self.board = board
