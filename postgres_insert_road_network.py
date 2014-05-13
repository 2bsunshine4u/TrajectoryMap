import glob
import string
import time
import psycopg2
import sys
import re
import uuid

global conn_from
global conn_to

def insert(road_i,i):
    ##INSERT INTO temp(road_id,road_geo,describe) values(%s,LINESTRING(%s,%s),%s)
    print "Connecting.."
    conn_to = psycopg2.connect(host='localhost',port='5432',database="postgis_test_new",
                               user='postgres',password='123456')
    print "Connected.\n"
    cursor_to = conn_to.cursor()

    for j in range(1, len(road_i)):
        #print "road_id:%s_%s (%s %s,%s %s)" % (i,j,road_i[j][0],road_i[j][1],road_i[j+1][0],road_i[j+1][1])
        road_id = "'%s-%s'" %(i,j)
        road_geo = "'LINESTRING(%s %s,%s %s)'" % (road_i[j-1][0],road_i[j-1][1],road_i[j][0],road_i[j][1])
        sql = "INSERT INTO road_network(road_id,road_geo,describe) values(%s,%s,%s)" % (road_id,road_geo,road_geo)
        #print sql 
        cursor_to.execute(sql)
    conn_to.commit()
    conn_to.close()

def create_road_network():

    conn_to = psycopg2.connect(host='localhost',port='5432',database="postgis_test_new",
                               user='postgres',password='123456')
    print "Connected.\n"
    cursor_to = conn_to.cursor()

    sql = '''
CREATE TABLE road_network
(
  road_id character varying(10),
  road_geo geometry,
  describe character varying(100)
)
''' 
    #print sql
    cursor_to.execute(sql)
    conn_to.commit()
    conn_to.close()

def read_road_network(filename):
    road_network_file = open(filename,'r')
    """0-1-0        116.410626883 40.0208176186     116.413615987 40.0208326965"""
    lines = map(lambda x: x.split(), road_network_file.readlines())
    roads = map(lambda x: [x[0], (float(x[1]), float(x[2])), (float(x[3]),float(x[4]))], lines)
    #while 1:
    #    lines = road_network_file.readlines(1000)
    #    if not lines:
    #        break
    #    for line in lines:
    before_num = ''
    road_point = []
    traj_map_roads = []
    for road in roads:
        road_num = road[0].split("-")[0]
        if road_num == before_num:
           road_point += [road[2]]
        else :
           before_num = road_num
           traj_map_roads += [road_point]
           road_point = [road[1],road[2]]
    traj_map_roads += [road_point]

    #create_road_network()
    for i in range(len(traj_map_roads)):
        insert(traj_map_roads[i],i)
        #for j in range(1,len(traj_map_roads[i])):
        #    print "%s-%s:LINESTRING(%s %s,%s %s)" % (i,j,traj_map_roads[i][j-1][0],traj_map_roads[i][j-1][1],traj_map_roads[i][j][0],traj_map_roads[i][j][1])

read_road_network("split.500.2")
