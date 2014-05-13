import glob
import math
import sys
import time

def map_dist(long1, lat1, long2, lat2):
    '''distance between 2 points on sphere surface, in meter'''
    if long1 == long2 and lat1 == lat2:
        return 0
    else:
        try:
            return 6378137*math.acos(math.sin(math.radians(lat1))*math.sin(math.radians(lat2))+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.cos(math.radians(long2-long1)))
        except Exception,ex:
            print Exception,":",ex
            return 1000000

def lineMagnitude (x1, y1, x2, y2):
    lineMagnitude = math.sqrt(math.pow((x2 - x1), 2)+ math.pow((y2 - y1), 2)) 
    return lineMagnitude

def DistancePointLine (px, py, x1, y1, x2, y2):
    #http://local.wasp.uwa.edu.au/~pbourke/geometry/pointline/source.vba
    LineMag = lineMagnitude(x1, y1, x2, y2) 
    if LineMag < 0.00000001:
        DistancePointLine = 9999999.0
        return DistancePointLine, x1, y1

    u1 = (((px - x1) * (x2 - x1)) + ((py - y1) * (y2 - y1)))
    u = u1 / (LineMag * LineMag)
    if (u < 0.00001) or (u > 1): 
        #// closest point does not fall within the line segment, take the shorter distance
        #// to an endpoint
        ix = lineMagnitude(px, py, x1, y1) 
        iy = lineMagnitude(px, py, x2, y2) 
        if ix > iy: 
            return iy, x2, y2
        else:
            return ix, x1, y1
    else:
        # Intersecting point is on the line, use the formula
        ix = x1 + u * (x2 - x1) 
        iy = y1 + u * (y2 - y1) 
        DistancePointLine = lineMagnitude(px, py, ix, iy) 
    return DistancePointLine, ix, iy

class Merge_road(object):
    
    def __init__(self,filename):
        road_network_file = open(filename,'r')
        '''13301156449 20101104050807 116.1870651 40.22826004 0 22 0 4 50# 1468000 287.481676418 (116.1850565, 40.225909375000001)'''
        lines = map(lambda x: x.split(), road_network_file.readlines())
        points = map(lambda x: (float(x[2]),float(x[3]),int(x[4]),float(x[11][1:-1]),float(x[12][:-1])),lines)
        mm_points = map(lambda x: (float(x[11][1:-1]),float(x[12][:-1])),lines)
        '''
        roads = map(lambda x: [x[0], (float(x[1]), float(x[2])), (float(x[3]),float(x[4]))], lines)
        
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
    
        self.roads = traj_map_roads
        '''
        traj_map_roads = [points]
        self.roads = traj_map_roads
        self.mm_roads = mm_points

        min_lon = min(map(lambda x: min(map(lambda y: y[0], x)), self.roads))
        max_lon = max(map(lambda x: max(map(lambda y: y[0], x)), self.roads))
        min_lat = min(map(lambda x: min(map(lambda y: y[1], x)), self.roads))
        max_lat = max(map(lambda x: max(map(lambda y: y[1], x)), self.roads))
        self.min_longitude = min_lon  # degree
        self.max_longitude = max_lon
        self.min_latitude = min_lat
        self.max_latitude = max_lat

        resolution = 0.01
        self.RESOLUTION = resolution

        self.CANVAS_WIDTH = resolution * map_dist(self.min_longitude, self.min_latitude, \
                self.max_longitude, self.min_latitude)
        self.CANVAS_HEIGHT = resolution * map_dist(self.min_longitude, self.min_latitude, \
                self.min_longitude, self.max_latitude)
        self.CANVAS_MIN_X, self.CANVAS_MIN_Y = self.to_canvas_xy(self.min_longitude, self.max_latitude)
        self.CANVAS_MAX_X, self.CANVAS_MAX_Y = self.to_canvas_xy(self.max_longitude, self.min_latitude)
        self.GRID_INTERVAL_KM = 0.5 # grid size in km
        self.GRID_INTERVAL = self.GRID_INTERVAL_KM * 1000 * self.RESOLUTION

        self.TOTAL_GRID_ROWS = int((self.CANVAS_MAX_Y - self.CANVAS_MIN_Y) / self.GRID_INTERVAL + 1)
        self.TOTAL_GRID_COLS = int((self.CANVAS_MAX_X - self.CANVAS_MIN_X) / self.GRID_INTERVAL + 1)
   
    def to_lon_lat(self, x, y):
        lon = x * (self.max_longitude - self.min_longitude) / \
                self.CANVAS_WIDTH + self.min_longitude
        lat = (self.CANVAS_HEIGHT - y) * (self.max_latitude - self.min_latitude) / \
                self.CANVAS_HEIGHT + self.min_latitude
        return lon, lat
 
    def to_canvas_xy(self, lon, lat):
        x = (lon - self.min_longitude) * self.CANVAS_WIDTH / \
                (self.max_longitude - self.min_longitude)
        y = self.CANVAS_HEIGHT - (lat - self.min_latitude) * self.CANVAS_HEIGHT / \
                (self.max_latitude - self.min_latitude)
        return x, y

    def find_crossing(self):
        self.coress_dict = {}
        for i in range(0, len(self.roads)):
            #p = map(lambda x: self.to_canvas_xy(x[0], x[1]), self.traj_map.roads[i])
            p = map(lambda x: (x[0], x[1]), self.roads[i])
            #print "point: %s" % p
            if len(p) >= 2:
                #a = map(lambda x: `x`,p)#point_dict[`x`]
                for point in p:
                    if point in self.coress_dict:
                        if i not in self.coress_dict[point]:
                            self.coress_dict[point] = self.coress_dict[point] + [i]
                    else:
                        self.coress_dict[point] = [i]
        #cross = [x for x in self.coress_dict if len(self.coress_dict[x])>1]
    
    def is_delete_point(self, now_point, before_point, after_point):
        if len(self.coress_dict[now_point[:2]])>1:
            return True #don't delete
    
        px, py = self.to_canvas_xy(now_point[0],now_point[1])
        x1, y1 = self.to_canvas_xy(before_point[0],before_point[1])
        x2, y2 = self.to_canvas_xy(after_point[0],after_point[1])

        now_speed = now_point[2]
        before_speed = before_point[2]
        after_speed = after_point[2]
        #print now_speed,before_speed
 
        dist, lx, ly = DistancePointLine(px, py, x1, y1, x2, y2)
        lon, lat = self.to_lon_lat(px,py)
        llon, llat = self.to_lon_lat(lx,ly)
        rdist = map_dist(lon, lat, llon, llat)
        #print rdist
        if (rdist > 150) or ((before_speed - now_speed) > 18 or (before_speed - now_speed) < -18):
           #print rdist,now_speed,before_speed
           return True,rdist,now_speed,before_speed #don't delete
        else:
           #print rdist,now_speed,before_speed
           return False,rdist,now_speed,before_speed #delete
        
    def merge_roads(self):
        self.merge_roads = []
        for road in self.roads:
            if len(road) < 3: ##3 is the max error
                continue
            merge_road = [road[0]]
            before_point = road[0]
            max_speed = 0
            max_dist = 0
            for i in range(1,len(road)-1):
                after_point = road[i+1]
                now_point = road[i]
                #print now_point
                key,rdist,now_speed,before_speed = self.is_delete_point(now_point,before_point,after_point)
                if key:
                    merge_road += [road[i]]
                    before_point = road[i]
                    print rdist
                else:
                    if (max_dist < rdist):
                        max_dist = rdist
                    if (max_speed < (now_speed-before_speed)*(now_speed-before_speed)):
                        max_speed = (now_speed-before_speed)*(now_speed-before_speed)
                    #print rdist,now_speed,before_speed
            merge_road += [road[-1]]
            #print max_dist,math.sqrt(max_speed)
            self.merge_roads += [merge_road]
        #print self.merge_roads
            #print max_dist,max_speed
    def map_match(self):
        for j in range(len(self.mm_roads)):
                point = self.mm_roads[j]
                px,py = self.to_canvas_xy(point[0],point[1])
                mindist = 9999999.0
                for i in range(1,len(self.merge_roads[0])):
                    x1,y1 = self.to_canvas_xy(self.merge_roads[0][i-1][0], self.merge_roads[0][i-1][1])
                    x2, y2 = self.to_canvas_xy(self.merge_roads[0][i][0], self.merge_roads[0][i][1])
                    dist,lx,ly = DistancePointLine(px, py, x1, y1, x2, y2)
                    if dist < mindist:
                        mindist = dist
                        minlx, minly = lx, ly
                lon, lat = self.to_lon_lat(px,py)
                llon, llat = self.to_lon_lat(minlx,minly)
                rdist = map_dist(lon, lat, llon, llat)
                #if rdist > 100:
                print j,rdist
                #print rdist
        
    def output_mergefile(self,file_name):
        output_file = open(file_name, 'w')
        for i in range(len(self.merge_roads)):
            for j in range(1,len(self.merge_roads[i])):
                long1, lat1, long2, lat2, speed = (self.merge_roads[i][j-1][0],self.merge_roads[i][j-1][1],self.merge_roads[i][j][0],self.merge_roads[i][j][1],self.merge_roads[i][j][2])
                dist = map_dist(long1, lat1, long2, lat2)
                output_file.write("%s-%s\t%s %s\t%s %s\tdist:%s speed:%d\n" % (i,j,long1, lat1, long2, lat2, dist, speed))

        output_file.close()

if __name__ == '__main__':
    if len(sys.argv)!=2:
        print 'useby "python point_line_DP.py file"'
        exit(1)
    else:
        file_name = sys.argv[1]
        #print file_name
    mymergeroad = Merge_road(file_name)
    mymergeroad.find_crossing()
    mymergeroad.merge_roads()
    #mymergeroad.map_match()
    mymergeroad.output_mergefile(file_name+"_100")
 
