import glob
import string
import time
import psycopg2
import sys
import re
#import shapefile
import uuid


class ConnPostgreSQL:

    def __init__(self, host='localhost',port='5432',database="new_postgis_db",
                               user='postgres',password='123456'):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.pwd = password
        
        self.conn_to = psycopg2.connect(host=self.host, port=self.port, database=self.database,
                               user=self.user, password=self.pwd)
        #self.cursor_to = conn_to.cursor()
        #self.traj_partten = re.compile(r'LINESTRING(\(\d+.\d+\) \(\d+.\d+\),\(\d+.\d+\) \(\d+.\d+\))')
        self.traj_partten = re.compile(r"(\d+\.\d+)")
        
    def __del__(self):
        self.conn_to.commit()
        self.conn_to.close()
        
    def execute(self, sql):
        cursor_to = self.conn_to.cursor()
        cursor_to.execute(sql)
        rows = cursor_to.fetchall()
        return rows
        
    def extract_traj(self, traj_result):
        result = []
        for tr_point in traj_result:
            #print "tr_point[0]",tr_point[0]
            match = re.findall(self.traj_partten,tr_point[0])
            if match:
                #print "===\n", match.group(), "===\n"
                #id_list = map(lambda x:x[1],match)
                ##print "***\n", match, "***\n"
                result += [[match[0],match[1]]]
        #result += [[match[2],match[3]]]
        #print result
        return result
        
if __name__ == '__main__':
    con = ConnPostgreSQL(host='192.168.1.236')
    
    ###find traj id
    sql = '''
select t.traj_id
from traj_without_rid_line_%s t
where ST_DWithin(
        ST_Transform(GeomFromText('%s',4326),26986),
        ST_Transform(t.traj_point,26986),
        %s 
);
'''% ('10000','POINT(116.3427505 39.85953522)',100)
    print sql
    traj_id_result = con.execute(sql)
    print traj_id_result
    ###find traj by traj_id
    
    for traj in traj_id_result:
        sql = """
select astext(t.traj_point)
from traj_without_rid_line_%s t
where t.traj_id = '%s';
""" % ('10000',traj[0])
        result = con.execute(sql)
        print result
        
        con.extract_traj(result)
        
