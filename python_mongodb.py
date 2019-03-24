#coding:utf-8
import pymongo as pm
from bson import objectid
def connect_to_mongodb(host,post):
    """

    :param host:
    :param post:
    :return:
    """
    client = pm.MongoClient(host,post)
def insert_to_db(db):
    message_1 = {
        'id':'0922',
        'name':'Mike',
        'age':21,
        'gender':'male'
    }
    message_2 = {
        'id': '0923',
        'name': 'Mike',
        'age': 21,
        'gender': 'male'
    }
    message_3 = {
        'id': '0924',
        'name': 'Mike',
        'age': 21,
        'gender': 'male'
    }
    result_1 = db.insert(message_1)
    result_2 = db.insert([message_1,message_2])
    # 返回的是ObjectId类型的_id属性值
    print result_1,result_2
    result_1 = db.insert_one(message_1)
    print result_1.inserted_id
    result_2 = db.insert_many([message_1,message_2])
    print result_2.inserted_ids

def search_collections(db,collections):
    result = db[collections].find_one({'name':'Mike'})
    result = db[collections].find_one({'_id':objectid('593278c115c2602667ec6bae')})
    #大于查询语句
    result = db[collections].find({'age':{'$gt':20}})
    # > $gt
    # < $lt
    # <= $lte
    # >= $gte
    # != $ne
    # '$in':[20,23]
    # '$nin':[20,23]
    #正则匹配查询
    # $regex:'^M.*' 以M开头的正则表达式
    # $exists: True
    # $type :'int'
    # {$text :{'$search':'Mike'}}
    # {$where:'obj.fans_count==obj.follows_count'}
    # 计数
def insert_test(db):
    db.food.insert({"_id": 1, "fruit": ["apple", "banana", "peach"]})
    db.food.insert({"_id": 2, "fruit": ["apple", "orange"]})
    db.food.insert({"_id": 3, "fruit": ["banana", "peach", "orange"]})
def find_test(db):
    # 匹配fruit中包含banana的文档
    db.food.find({"fruit": "banana"})
    # 必须匹配所有
    reseult = db.food.find({"fruit": {"$all": ["apple", "peach"]}})
    for item in reseult:
        print item
    # 精确匹配
    reseult= db.food.find({"fruit": ["apple", "orange"]})
    for item in reseult:
        print item
    # 指定下标 key.index
    db.food.find({"fruit.2": "peach"})
    # 查询指定长度的数组
    db.food.find({"fruit": {"$size": 3}})
if __name__ == "__main__":
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.test
    #insert_test(db)
    find_test(db)