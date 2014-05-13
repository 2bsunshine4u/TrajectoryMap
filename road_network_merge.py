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
        """0-1-0	116.410626883 40.0208176186	116.413615987 40.0208326965"""
        lines = map(lambda x: x.split(), road_network_file.readlines())
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
        min_lon = min(map(lambda x: min(map(lambda y: y[0], x)), self.roads[1:]))
        max_lon = max(map(lambda x: max(map(lambda y: y[0], x)), self.roads[1:]))
        min_lat = min(map(lambda x: min(map(lambda y: y[1], x)), self.roads[1:]))
        max_lat = max(map(lambda x: max(map(lambda y: y[1], x)), self.roads[1:]))
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
            print "point: %s" % p
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
        if len(self.coress_dict[now_point])>1:
            return True #don't delete
    
        px, py = self.to_canvas_xy(now_point[0],now_point[1])
        x1, y1 = self.to_canvas_xy(before_point[0],before_point[1])
        x2, y2 = self.to_canvas_xy(after_point[0],after_point[1])
    
        dist, lx, ly = DistancePointLine(px, py, x1, y1, x2, y2)
        lon, lat = self.to_lon_lat(px,py)
        llon, llat = self.to_lon_lat(lx,ly)
        rdist = map_dist(lon, lat, llon, llat)
        print rdist
        if rdist > 10:
           return True #don't delete
        else:
           return False #delete
        
    def merge_roads(self):
        self.merge_roads = []
        for road in self.roads:
            if len(road) < 3:
                continue
            merge_road = [road[0]]
            before_point = road[0]
            for i in range(1,len(road)-1):
                after_point = road[i+1]
                now_point = road[i]
                if self.is_delete_point(now_point,before_point,after_point):
                    merge_road += [road[i]]
                    before_point = road[i]
            merge_road += [road[-1]]
            self.merge_roads += [merge_road]
        #print self.merge_roads

    def output_mergefile(self):
        output_file = open('merge_roads', 'w')
        for i in range(len(self.merge_roads)):
            for j in range(1,len(self.merge_roads[i])):
                long1, lat1, long2, lat2 = (self.merge_roads[i][j-1][0],self.merge_roads[i][j-1][1],self.merge_roads[i][j][0],self.merge_roads[i][j][1])
                dist = map_dist(long1, lat1, long2, lat2)
                print "%s-%s\t%s %s\t%s %s\tdist:%s\n" % (i,j,long1, lat1, long2, lat2, dist)
                output_file.write("%s-%s\t%s %s\t%s %s\tdist:%s\n" % (i,j,long1, lat1, long2, lat2, dist))

        output_file.close()

if __name__ == '__main__':
    if len(sys.argv)!=2:
        print 'useby "python road_network_merge.py file"'
        exit(1)
    else:
        file_name = sys.argv[1]
        print file_name
    mymergeroad = Merge_road(file_name)
    mymergeroad.find_crossing()
    mymergeroad.merge_roads()
    mymergeroad.output_mergefile()
 
