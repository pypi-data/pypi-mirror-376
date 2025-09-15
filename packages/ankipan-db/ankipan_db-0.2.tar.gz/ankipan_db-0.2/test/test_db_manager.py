from ankipan_db import DBManager

db = DBManager('jp')
a = db.get_source_list('wikipedia')
print(a)
# import ankipan_db
# ankipan_db.db_config['database'] = 'ankipan_test_db'
# from ankipan_db import DBManager


# db = DBManager('en')

# print("o")
# a = db.get_segments_for_lemmas([],['like'],'source_category_1', 'de')
# print("a")
# print(a)