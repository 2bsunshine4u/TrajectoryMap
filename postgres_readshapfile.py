import glob
import string
import time
#import psycopg2
import sys
import re
import shapefile
import uuid

global conn_from
global conn_to

def insert_output(road_i,i):

    f = open('road_network','a')
    for j in range(1, len(road_i)):
        road_id = "%s-%s" %(i,j)
        road_geo = "%s %s\t%s %s" % (road_i[j-1][0],road_i[j-1][1],road_i[j][0],road_i[j][1])
        print "%s\t%s" % (road_id,road_geo)
        f.write("%s\t%s\n" % (road_id,road_geo))
    f.close()

def clean_road(roads):
    roads_temp = roads
    clean_road = {}
    num = 0
    for i in range(0,len(roads_temp))[::-1]:
        if len(roads_temp[i]) >=2 :
            road_i = map(lambda x: (x[0],x[1]), roads_temp[i])
            for j in range(1,len(road_i))[::-1]:
                road_j = (road_i[j-1][0],road_i[j-1][1],road_i[j][0],road_i[j][1])
                if road_j in clean_road:
                    num += 1
                    print "same road! num:%d id:(%d,%d)" % (num,i,j)
                    del roads[i][j]
                    clean_road[road_j] += [(i,j)]
                else:
                    clean_road[road_j] = [(i,j)]

    for i in range(0,len(roads))[::-1]:
        if len(roads[i]) <= 2:
            del roads[i]
    print "%s" %  roads
    return roads

def load_roads(filenames):
    roads = []
    road_names = []
    shapeRecords = reduce(lambda x,y: x+y, map(lambda f: shapefile.Reader(f).shapeRecords(), filenames))
    roads += filter(lambda n: len(n)>1, map(lambda x: x.shape.points, shapeRecords))
    
    #delete same roads
    roads = clean_road(roads)
    #
    #f = open('roads','w')
    #f.write('%s\n' % roads) 
    #f.close()
    
    for i in range(len(roads)):
        road_i = map(lambda x: (x[0],x[1]), roads[i])
        insert_output(road_i,i) 
    return roads


filenames = []
filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polygon*.dbf"))
#filenames += map(lambda x: x[0:-4], glob.glob("bj-shapefiles-2006/highway_*.dbf"))
load_roads(filenames)


