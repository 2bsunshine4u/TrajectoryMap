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

def is_line_segment_intersects_box(x1, y1, x2, y2, xTL, yTL, xBR, yBR):
    #Let the segment endpoints be p1=(x1 y1) and p2=(x2 y2). 
    #Let the rectangle's corners be (xTL yTL) and (xBR yBR).
    #All in lon lat

    # test 4 corners of the rectangle to see whether they are all above or below the lin
    #print 'x1, y1, x2, y2, xTL, yTL, xBR, yBR:',x1, y1, x2, y2, xTL, yTL, xBR, yBR

    f = lambda x,y: (y2-y1)*x + (x1-x2)*y + (x2*y1-x1*y2)
    f1 = f(xTL, yTL)
    f2 = f(xTL, yBR)
    f3 = f(xBR, yTL)
    f4 = f(xBR, yBR)
    if f1 > 0 and f2 > 0 and f3 > 0 and f4 > 0:
        return False # no intersection (rectangle if above line).
    if f1 < 0 and f2 < 0 and f3 < 0 and f4 < 0:
        return False # no intersection (rectangle if below line).
    if x1 > xBR and x2 > xBR:
        return False # no intersection (line is to right of rectangle). 
    if x1 < xTL and x2 < xTL:
        return False # no intersection (line is to left of rectangle). 
    #if y1 < yBR and y2 < yBR:
    if y1 > yBR and y2 > yBR:
        return False # no intersection (line is below rectangle). 
    #if y1 > yTL and y2 > yTL:
    if y1 < yTL and y2 < yTL:
        return False # no intersection (line is above rectangle). 
    return True

def rand_color():
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    return "#%02x%02x%02x" % (r, g, b)

def line_segment_cross(x0, y0, x1, y1, x2, y2, x3, y3):
    if (x0 == x2 and y0 == y2) or (x0 == x3 and y0 == y3): 
        return x0, y0
    if (x1 == x2 and y1 == y2) or (x1 == x3 and y1 == y3): 
        return x1, y1
    # http://en.wikipedia.org/wiki/Line-line_intersection
    p = (x0-x1)*(y2-y3)-(y0-y1)*(x2-x3)
    if p == 0:
        return None, None   # parallel

    px = ((x0*y1 - y0*x1) * (x2 - x3) - (x0 - x1) * (x2 * y3 - y2 * x3)) / p
    py = ((x0*y1 - y0*x1) * (y2 - y3) - (y0 - y1) * (x2 * y3 - y2 * x3)) / p
    if x1 != x0:
        t = (px - x0) / (x1 - x0)
    else:
        t = (py - y0) / (y1 - y0)
    if x2 != x3:
        u = (px - x2) / (x3 - x2)
    else:
        u = (py - y2) / (y3 - y2)
    if t<0 or t>1 or u<0 or u>1:
        return None, None   # intersection point is not on the segment
    return px, py

def is_in_bbox(bbox, x, y):
    return bbox[0] <= x and bbox[2] > x and bbox[1] <= y and bbox[3] > y

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

#=============================
#
#=============================
class MapMatching(object):
        
    def __init__(self, filename):
        road_network_file = open(filename,'r')
        """0-1-0	116.410626883 40.0208176186	116.413615987 40.0208326965"""
        roads = []
        while 1:
            lines = road_network_file.readlines(1000)
            if not lines:
                break
            lines = map(lambda x: x.split(), lines)
            roads += map(lambda x: [x[0], (float(x[1]), float(x[2])), (float(x[3]),float(x[4]))], lines)

        before_num = ''
        road_point = []
        traj_map_roads = []
        for road in roads:
            road_num = road[0].split("-")[0]
            if road_num == before_num:
               road_point += [road[2]]
            else :
                before_num = road_num
                if not road_point == []:
                    traj_map_roads += [road_point]
                road_point = [road[1],road[2]]

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

        #return self.roads
 
 
    def canvas_xy_to_grid_row_col(self, x, y):
        # x, y in canvas coord
        #print x,y
        #print 'self.CANVAS_MIN_Y:',self.CANVAS_MIN_Y
        #print 'self.CANVAS_MIN_X:',self.CANVAS_MIN_X
        #print 'self.GRID_INTERVAL:',self.GRID_INTERVAL
        #print 'self.RESOLUTION',self.RESOLUTION
        return int ( (y - self.CANVAS_MIN_Y) / self.GRID_INTERVAL ), \
                int( (x - self.CANVAS_MIN_X) / self.GRID_INTERVAL) 

#        return int( (y - self.CANVAS_MIN_Y) / self.GRID_INTERVAL/self.RESOLUTION), \
#                int( (x - self.CANVAS_MIN_X) / self.GRID_INTERVAL/self.RESOLUTION)

    def grid_row_col_to_canvas_xy(self, row, col):
        # return Top Left corner coord
        return self.CANVAS_MIN_X + col * self.GRID_INTERVAL, \
                self.CANVAS_MIN_Y + row * self.GRID_INTERVAL

    
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
        
        
    def split_roads_to_grid(self):
        #self.roads = [y.shape.self.roads for x in self.map_shapes.values() for y in x[1]]
        # init grid_road_dict
        self.grid_road_index = []
        print "self.TOTAL_GRID_ROWS,self.TOTAL_GRID_COLS",self.TOTAL_GRID_ROWS,self.TOTAL_GRID_COLS
        #self.canvas_xy_to_grid_row_col(x1, y1)
        #self.canvas_xy_to_grid_row_col(x2, y2)
        #print ""
        for row in range(0, self.TOTAL_GRID_ROWS+1):
            self.grid_road_index.append([])
            for col in range(0, self.TOTAL_GRID_COLS+1):
                self.grid_road_index[row].append([])
        # index map segments to self.grid_road_index array. key=(row,col) of a grid; value=array of (road_id, seg_id)
        for i in range(0, len(self.roads)):
            for j in range(0, len(self.roads[i])-1):
                #print "i,j",i,j
                x1, y1 = self.to_canvas_xy(self.roads[i][j][0], self.roads[i][j][1])
                x2, y2 = self.to_canvas_xy(self.roads[i][j+1][0], self.roads[i][j+1][1])
                #print "x1,y1,x2,y2",x1,y1,x2,y2
                row1, col1 = self.canvas_xy_to_grid_row_col(x1, y1)
                row2, col2 = self.canvas_xy_to_grid_row_col(x2, y2)
                #print "row1, col1, row2, col2",row1, col1, row2, col2
                
                for row in range(min(row1, row2), max(row1, row2) + 1):
                    for col in range(min(col1, col2), max(col1, col2) + 1):
                        xTL, yTL = self.grid_row_col_to_canvas_xy(row, col)
                        xBR, yBR = self.grid_row_col_to_canvas_xy(row + 1, col + 1)
                        if is_line_segment_intersects_box(x1, y1, x2, y2, xTL, yTL, xBR, yBR):
                            #print "row,col:i,j|",row,col,i,j
                            self.grid_road_index[row][col].append((i,j))
        
    def simple_map_matching(self, search_range, px, py):
        px, py = self.to_canvas_xy(px, py)
        #search_range: [(road_id, seg_id),...]
        # get all min_type
        mindist = 9999999.0
        minlx = minly = -1  # projection point on road
        min_road_id = min_segment_id = -1
        minx1, miny1, minx2, miny2 = -1, -1, -1, -1
        #print "search_range:%s" % search_range
        for i, j in search_range:
            x1, y1 = self.to_canvas_xy(self.roads[i][j][0], self.roads[i][j][1])
            x2, y2 = self.to_canvas_xy(self.roads[i][j+1][0], self.roads[i][j+1][1])
            dist, lx, ly = DistancePointLine(px, py, x1, y1, x2, y2)
            #print "segment:%s-%s dist:%s" % (i,j,dist)
            if dist < mindist:
                mindist = dist
                minx1, miny1 = (self.roads[i][j][0], self.roads[i][j][1])
                minx2, miny2 = (self.roads[i][j+1][0], self.roads[i][j+1][1])
                #minx1, miny1 = to_canvas_xy(roads[i][j][0], roads[i][j][1])
                #minx2, miny2 = to_canvas_xy(roads[i][j+1][0], roads[i][j+1][1])
                minlx, minly = lx, ly
                min_road_id = i
                min_segment_id = j
    
        lon, lat = self.to_lon_lat(px,py)
        llon, llat = self.to_lon_lat(minlx,minly)
        rdist = map_dist(lon, lat, llon, llat)
        #print "(%f, %f) matching to (%f, %f), dist=%f, segment=(%d,%d), (%f,%f)-(%f,%f)"\
        #     % (lon,lat,llon,llat, rdist, min_road_id, min_segment_id,minx1, miny1, minx2, miny2)
    
        #draw_line(minx1, miny1, minx2, miny2,fill="yellow") 
        return px, py, minlx, minly, min_road_id, min_segment_id, minx1, miny1, minx2, miny2, rdist       

 
    def get_map_matching_point(self, px, py):
        #yxy#roads = [y.shape.points for x in self.map_shapes.values() for y in x[1]]
        # get searching range
        cpx, cpy = self.to_canvas_xy(px, py)
        row, col = self.canvas_xy_to_grid_row_col(cpx, cpy)
        row_l = max(0, row - 1)
        row_h = min(self.TOTAL_GRID_ROWS, row + 1)
        col_l = max(0, col - 1)
        col_h = min(self.TOTAL_GRID_COLS, col + 1)
        
        search_range = []
        #print 'row_l,row_h,col_l,col_h',row_l,row_h,col_l,col_h
        for i in range(row_l, row_h + 1):
            for j in range(col_l, col_h + 1):
                search_range += self.grid_road_index[i][j]

        px, py, minlx, minly, min_road_id, min_segmenet_id, minx1, miny1, minx2, miny2, dist = \
            self.simple_map_matching(search_range, px, py)

        print minx1, miny1, minx2, miny2


        return min_road_id*1000+min_segmenet_id,dist



    def get_map_matching_trajectory(self, filename):
        '''readfile "13301104001 20101101000157 116.3428345 39.85949707 0 332 0 4 50#" '''
        traj_file = open(filename, "r")
        output_file = open(filename+'_roadid', 'w')
        while 1:
            lines = traj_file.readlines(1000)
            if not lines:
                break
            for line in lines:
                line = line.strip()
                words = line.split(' ')
                point = words[1:3]
                #print point
                road_id,dist = self.get_map_matching_point(float(point[0]), float(point[1]))
                output_file.write("%s %s %s\n" % (line,road_id,dist))
        traj_file.close()
        output_file.close()

        
if __name__ == '__main__':
    # full map
    #beijingmap = TrajectoryMap(115.2, 117.5, 39.40, 41.10, 10)
    # city center
    #map = Map(116.1, 116.7, 39.65, 40.1)

    #min_longitude = 120.86702
    #max_longitude = 121.97395
    #min_latitude = 30.69477
    #max_latitude = 31.84318
    mymapmatch = MapMatching("split_result")
    mymapmatch.split_roads_to_grid()
    mymapmatch.get_map_matching_trajectory("13301104001.20101101.traj")
    #mymapmatch.get_map_matching_trajectory("x02")
    #mymapmatch.get_map_matching_trajectory("x03")
    #mymapmatch.get_map_matching_trajectory("x04")
    #mymapmatch.get_map_matching_trajectory("x05")
    #mymapmatch.get_map_matching_trajectory("x06")
    #mymapmatch.get_map_matching_trajectory("x07")
    #mymapmatch.get_map_matching_trajectory("x08")
    #mymapmatch.get_map_matching_trajectory("x09")
    #mymapmatch.get_map_matching_trajectory("x10")
    
