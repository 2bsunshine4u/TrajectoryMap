import re
import math
import sys
import string

def distance(long1, lat1, long2, lat2):
    '''distance between 2 points on sphere surface, in meter'''
    if long1 == long2 and lat1 == lat2:
        return 0
    else:
        return 6378137*math.acos(math.sin(math.radians(lat1))*math.sin(math.radians(lat2))+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.cos(math.radians(long2-long1)))

def split_line(start_point,end_point,num):
    delta_x = (end_point[0]-start_point[0])/num;
    delta_y = (end_point[1]-start_point[1])/num;
    point_list = []
    point_list += [start_point]
    for i in range(1,num):
        point_list += [[start_point[0]+delta_x*i,start_point[1]+delta_y*i]]
    point_list += [end_point]
    return point_list

def readfile(filename,dist_max):
    f = open(filename,'r')
    outfile = open("split_result", 'w')
    prevrid = ''
    offset = 0
    while 1:
        lines = f.readlines(1000)
        if not lines:
            break
        for line in lines:
            line = line.strip()
            words = line.split('\t')
            if len(words) == 4:
                start_point = map(lambda x:float(x),words[1].split(" "))
                end_point = map(lambda x:float(x),words[2].split(" "))
                dist = distance(start_point[0],start_point[1],end_point[0],end_point[1])
                #print "dist:%s;dist_max:%s" %(dist,dist_max)
                if dist < dist_max:
                    #print line
                    #print "%s\t%s %s\t%s %s\tdist:%s\n" % (words[0],start_point[0],start_point[1],end_point[0],end_point[1], dist)
                    word = words[0].split('-')
                    if word[0] != prevrid:
                        prevrid = word[0]
                        offset = 0
                    word[1] = str(int(word[1]) + offset)
                    outfile.write("%s-%s\t%s %s\t%s %s\tdist:%s\n" % (word[0], word[1],start_point[0],start_point[1],end_point[0],end_point[1], dist))
                else:
                    #print "old#%s" % line
                    num = int(dist-1)/dist_max + 1
                    #print "num:%s" % num
                    point_list = split_line(start_point,end_point,num)
                    for i in range(1,len(point_list)):
                        #print "%s-%s:LINESTRING(%s %s,%s %s)" % (words[0],i-1,point_list[i-1][0],point_list[i-1][1],point_list[i][0],point_list[i][1])
                        #pprint "%s-%s\t%s %s\t%s %s\tdist:%s\n" % (words[0],i-1,point_list[i-1][0],point_list[i-1][1],point_list[i][0],point_list[i][1], distance(point_list[i-1][0],point_list[i-1][1],point_list[i][0],point_list[i][1]))
                        word = words[0].split('-')
                        if word[0] != prevrid:
                            prevrid = word[0]
                            offset = 0
                        word[1] = str(int(word[1]) + offset)
                        outfile.write("%s-%s\t%s %s\t%s %s\tdist:%s\n" % (word[0], word[1],point_list[i-1][0],point_list[i-1][1],point_list[i][0],point_list[i][1], distance(point_list[i-1][0],point_list[i-1][1],point_list[i][0],point_list[i][1])))
                        if not i == len(point_list) - 1:
                            offset = offset + 1

'''
def readfile(filename,dist_max):
    f=open(filename,'r')
    while 1:
        lines = f.readlines(1000)
        if not lines:
            break
        for line in lines:
            line = line.strip()
            words = line.split(':')
            if len(words) == 2:
                if words[1].startswith('LINESTRING'):
                    #print before_line
                    point_line = re.split(r"\(|,|\)",words[1])
                    start_point = map(lambda x:float(x),point_line[1].split(" "))
                    end_point = map(lambda x:float(x),point_line[2].split(" "))
                    dist = distance(start_point[0],start_point[1],end_point[0],end_point[1])
                    #print "dist:%s;dist_max:%s" %(dist,dist_max)
                    if dist < dist_max:
                        #print line
                        print "%s\t%s %s\t%s %s" % (words[0],start_point[0],start_point[1],end_point[0],end_point[1])
                    else:
                        #print "old#%s" % line
                        num = int(dist-1)/dist_max + 1
                        #print "num:%s" % num
                        point_list = split_line(start_point,end_point,num)
                        for i in range(1,len(point_list)):
                            #print "%s-%s:LINESTRING(%s %s,%s %s)" % (words[0],i-1,point_list[i-1][0],point_list[i-1][1],point_list[i][0],point_list[i][1])
                            print "%s-%s\t%s %s\t%s %s" % (words[0],i-1,point_list[i-1][0],point_list[i-1][1],point_list[i][0],point_list[i][1])
'''

if __name__ == "__main__":
    if len(sys.argv)!=2:
        print 'useby "python split_network.py dist"'
        exit(1)
    else:
        dist = sys.argv[1]
        print dist

        readfile("merge_roads",int(dist))
