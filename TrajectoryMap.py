import glob
import math 
import shapefile
import sys 
import time
from TrajectoryUtils import map_dist, is_line_segment_intersects_box, line_segment_cross

class TrajectoryPoint(object):
    # timestamp, lon, lat, plon, plat, road_id, seg_id, dist
    def __init__(self, timestamp, lon, lat):
        self.timestamp, self.lon, self.lat = timestamp, lon, lat
        self.row = self.col = -1

class TrajectoryMap(object):
    def __init__(self, min_longitude, max_longitude, min_latitude, max_latitude, grid_interval=300):
        # grid_interval: grid size in meters
        self.min_longitude = min_longitude  # degree
        self.max_longitude = max_longitude
        self.min_latitude = min_latitude
        self.max_latitude = max_latitude
        # ignore the sphere effect since the city size is not that big comparing with the earth surface
        self.UNIT_LONGITUDE_DISTANCE = map_dist(self.min_longitude, self.min_latitude, self.max_longitude, self.min_latitude) / (self.max_longitude - self.min_longitude)
        self.UNIT_LATITUDE_DISTANCE = map_dist(0, self.min_latitude, 0, self.max_latitude) / (self.max_latitude - self.min_latitude)
        self.GRID_INTERVAL = grid_interval
        self.GRID_INTERVAL_LONGITUDE = grid_interval / self.UNIT_LONGITUDE_DISTANCE # grid size in longitude diff
        self.GRID_INTERVAL_LATITUDE = grid_interval / self.UNIT_LATITUDE_DISTANCE # grid size in latitude diff
        self.TOTAL_GRID_ROWS = int((max_latitude - min_latitude) / self.GRID_INTERVAL_LATITUDE + 1)
        self.TOTAL_GRID_COLS = int((max_longitude - min_longitude) / self.GRID_INTERVAL_LONGITUDE + 1)
  
        self.roads = []
        self.roads2 = []
        self.roads_point = []
        self.road_names = []
        self.trajectory_points = {}    # filename -> [TrajectoryPoint, ...]
        self.map_matched_trajectory_names = []
        self.grid_road_index = []
        self.intersections = []
        self.road_intersections = {}   # interestions according to road, {road_id -> set of intersection}

    def load_roads(self, filenames):  #load the shapefile
        shapeRecords = reduce(lambda x,y: x+y, map(lambda f: shapefile.Reader(f).shapeRecords(), filenames))
        self.roads += filter(lambda n: len(n)>2, map(lambda x: x.shape.points, shapeRecords))
        #self.roads += map(lambda x: x.shape.points, shapeRecords)
        self.road_names += map(lambda x: x.record[0], shapeRecords)
        #print "###self.roads: %s" % self.roads
        #print "###self.road_names: %s" % self.road_names
        min_lon = min(map(lambda x: min(map(lambda y: y[0], x)), self.roads[1:]))
        max_lon = max(map(lambda x: max(map(lambda y: y[0], x)), self.roads[1:]))
        min_lat = min(map(lambda x: min(map(lambda y: y[1], x)), self.roads[1:]))
        max_lat = max(map(lambda x: max(map(lambda y: y[1], x)), self.roads[1:]))
        self.min_longitude = min_lon  # degree
        self.max_longitude = max_lon
        self.min_latitude = min_lat
        self.max_latitude = max_lat

        return self.roads

 
    def stat_map_info(self):  #print the map_stat
        roads_number = len(self.roads)
        points_number = reduce(lambda x,y: x+y, map(lambda x: len(x), self.roads))
        print "Number of total roads: %d" % roads_number
        print "Number of total points: %d" % points_number
        print "Number of total road segments: %d" % (points_number - roads_number)
        #for i in range(roads_number):
        #    print "roads:%d:%s" % (i,self.roads[i])
 
        min_lon = min(map(lambda x: min(map(lambda y: y[0], x)), self.roads[1:]))
        max_lon = max(map(lambda x: max(map(lambda y: y[0], x)), self.roads[1:]))
        min_lat = min(map(lambda x: min(map(lambda y: y[1], x)), self.roads[1:]))
        max_lat = max(map(lambda x: max(map(lambda y: y[1], x)), self.roads[1:]))
        
        print "min_longitude =", min_lon
        print "max_longitude =", max_lon
        print "min_latitude =", min_lat
        print "max_latitude =", max_lat

    def load_trajectories(self, filenames):  #load the traj file
        map(lambda x: self.load_trajectory(x), filenames)

    def load_trajectory(self, filename):
        traj_file = open(filename, "r")
        lines = map(lambda x: x.split(), traj_file.readlines())
        self.trajectory_points[filename] = map(lambda x: TrajectoryPoint(time.mktime(time.strptime(x[0], "%Y%m%d%H%M%S")), float(x[1]), float(x[2])), lines)
        traj_file.close()

    def stat_trajectories(self):
        for i in self.trajectory_points.keys():
            print i, len(self.trajectory_points[i])

    def index_roads_on_grid(self):  #map the seg id in each grid cell
        '''
        FUNCTION:
            make index of all roads on grid
        INPUT:
        OUTPUT:
            grid_road_index: array of each grid cell, the cell of
            this array stores an array of road segment as [(road_id, seg_id),...]
            road_id is the index of the input roads array,
            seg_id is the index of the road segment in roads[road_id]
        '''
        # init grid_road_dict
        self.grid_road_index = []
        for row in range(0, self.TOTAL_GRID_ROWS):
            self.grid_road_index.append([])
            for col in range(0, self.TOTAL_GRID_COLS):
                self.grid_road_index[row].append([])
        # index each map segments to grid_road_index array.
        for i in range(0, len(self.roads)):
            for j in range(0, len(self.roads[i])-1):
                lon1, lat1 = self.roads[i][j][0], self.roads[i][j][1]
                lon2, lat2 = self.roads[i][j+1][0], self.roads[i][j+1][1]
                row1, col1 = self.lon_lat_to_grid_row_col(lon1, lat1)
                row2, col2 = self.lon_lat_to_grid_row_col(lon2, lat2)
        
                for row in range(min(row1, row2), max(row1, row2) + 1):
                    for col in range(min(col1, col2), max(col1, col2) + 1):
                        xTL, yTL = self.grid_row_col_to_lon_lat(row, col)
                        xBR, yBR = self.grid_row_col_to_lon_lat(row + 1, col + 1)
                        #if is_line_segment_intersects_box(lon1, lat1, lon2, lat2, xTL, yTL, xBR, yBR):
                        self.grid_road_index[row][col].append((i,j))
        return self.grid_road_index

    def lon_lat_to_grid_row_col(self, lon, lat):
        row = int((self.max_latitude - lat) / self.GRID_INTERVAL_LATITUDE)
        col = int((lon - self.min_longitude) / self.GRID_INTERVAL_LONGITUDE)
        return row, col

    def grid_row_col_to_lon_lat(self, row, col):
        # return Top Left corner longitude, latitude
        lon = self.min_longitude + col * self.GRID_INTERVAL_LONGITUDE
        lat =  self.max_latitude - row * self.GRID_INTERVAL_LATITUDE
        return lon, lat

    def dump_grid_road_index(self):
        # dump number of road segments in a grid_road_index array cell
        for row in range(0, self.TOTAL_GRID_ROWS):
            for col in range(0, self.TOTAL_GRID_COLS):
                sys.stdout.write("%3d " % (len(self.grid_road_index[row][col])))

    def gen_road_graph(self):  #handle all the intersections
        for row in range(0, self.TOTAL_GRID_ROWS):
            for col in range(0, self.TOTAL_GRID_COLS):
                self.gen_intersections_in_grid_cell(row, col)
                print "gen_road_graph: row=%d, col=%d" % (row, col)
        # dump road graph
        print "intersections: ", len(self.intersections)
        #for i in range(0, len(self.intersections)):
        #    lon, lat = self.intersections[i][0:2]
        #    iname = str(self.intersections[i][2])
        #    print "Intersection %4d: (%f, %f), road_segs=%s" % (i, lon, lat, iname)
        #for i in self.road_intersections.items():
            #print "Road %d has intersections: %s" % (i[0], str(i[1]))

    def gen_intersections_in_grid_cell(self, row, col):
        intersections = []   # interestions in this grid cell, [(lon, lat, set of (road_id, seg_id)), ...]
        segments = self.grid_road_index[row][col]
        for i in range(0, len(segments)-1):
            for j in range(i, len(segments)):
                road_id1, seg_id1 = segments[i]
                road_id2, seg_id2 = segments[j]
                if road_id1 == road_id2:
                    continue  # road doesn't intersect with itself
                x0, y0 = self.roads[road_id1][seg_id1]
                x1, y1 = self.roads[road_id1][seg_id1+1]
                x2, y2 = self.roads[road_id2][seg_id2]
                x3, y3 = self.roads[road_id2][seg_id2+1]
                ix, iy = line_segment_cross(x0, y0, x1, y1, x2, y2, x3, y3)
                if ix and iy:
                    #print "(%f,%f)-(%f,%f) intersects with (%f,%f)-(%f,%f) at (%f,%f)" % (x0, y0, x1, y1, x2, y2, x3, y3, ix, iy)
                    #print "(%d,%d) intersects with (%d,%d) at (%f,%f)" % (road_id1, seg_id1, road_id2, seg_id2, ix, iy)
                    if road_id1 not in self.road_intersections:
                        self.road_intersections[road_id1] = set()
                    if road_id2 not in self.road_intersections:
                        self.road_intersections[road_id2] = set()

                    new_intersection_flag = True
                    #for k in intersections:     # only search intersections in this cell
                    #    if map_dist(k[0], k[1], ix, iy) < 5:  # < 5 meters, check duplicated intersection
                    #        k[2].add((road_id1, seg_id1))
                    #        k[2].add((road_id2, seg_id2))
                    #        new_intersection_flag = False
                    #        break
                    if new_intersection_flag:
                        k = (ix, iy, [(road_id1, seg_id1), (road_id2, seg_id2)])
                        intersections.append(k)
                        self.intersections.append(k)

                    # update road_intersections
                    self.road_intersections[road_id1].add(self.intersections.index(k))
                    self.road_intersections[road_id2].add(self.intersections.index(k))


    def ShortestPath(self, filename):
        outfile = open(filename, 'w')

        for i in range(0, len(self.roads)):
                for j in range(0, len(self.roads[i]) - 1):
                    print "Processing the ShortestPath from %d-%d" % (i, j)
                    self.Dijkstra(i, j, self.roads, self.intersections, self.road_intersections, outfile)
    
        outfile.close()

    
    def Dijkstra(self, road_id, segment_id, roads, intersections, road_intersections, outfile):
        INF = 9999999
        
        S = []
        U = []
    
        row, col = self.lon_lat_to_grid_row_col(roads[road_id][segment_id][0], (roads[road_id][segment_id][1] + roads[road_id][segment_id+1][1])/2)

        SegmentDistance = {}

        for i in range(0, len(self.grid_road_index[row-1][col-1])):
            SegmentDistance[(self.grid_road_index[row-1][col-1][i][0], self.grid_road_index[row-1][col-1][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row-1][col-1][i][0], self.grid_road_index[row-1][col-1][i][1]))

        for i in range(0, len(self.grid_road_index[row-1][col])):
            SegmentDistance[(self.grid_road_index[row-1][col][i][0], self.grid_road_index[row-1][col][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row-1][col][i][0], self.grid_road_index[row-1][col][i][1]))

        for i in range(0, len(self.grid_road_index[row-1][col+1])):
            SegmentDistance[(self.grid_road_index[row-1][col+1][i][0], self.grid_road_index[row-1][col+1][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row-1][col+1][i][0], self.grid_road_index[row-1][col+1][i][1]))

        for i in range(0, len(self.grid_road_index[row][col-1])):
            SegmentDistance[(self.grid_road_index[row][col-1][i][0], self.grid_road_index[row][col-1][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row][col-1][i][0], self.grid_road_index[row][col-1][i][1]))

        for i in range(0, len(self.grid_road_index[row][col])):
            SegmentDistance[(self.grid_road_index[row][col][i][0], self.grid_road_index[row][col][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row][col][i][0], self.grid_road_index[row][col][i][1]))

        for i in range(0, len(self.grid_road_index[row][col+1])):
            SegmentDistance[(self.grid_road_index[row][col+1][i][0], self.grid_road_index[row][col+1][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row][col+1][i][0], self.grid_road_index[row][col+1][i][1]))

        for i in range(0, len(self.grid_road_index[row+1][col-1])):
            SegmentDistance[(self.grid_road_index[row+1][col-1][i][0], self.grid_road_index[row+1][col-1][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row+1][col-1][i][0], self.grid_road_index[row+1][col-1][i][1]))

        for i in range(0, len(self.grid_road_index[row+1][col])):
            SegmentDistance[(self.grid_road_index[row+1][col][i][0], self.grid_road_index[row+1][col][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row+1][col][i][0], self.grid_road_index[row+1][col][i][1]))

        for i in range(0, len(self.grid_road_index[row+1][col+1])):
            SegmentDistance[(self.grid_road_index[row+1][col+1][i][0], self.grid_road_index[row+1][col+1][i][1])] = [INF, INF, INF]
            U.append((self.grid_road_index[row+1][col+1][i][0], self.grid_road_index[row+1][col+1][i][1]))

        SegmentDistance[(road_id,segment_id)] = [0, road_id, segment_id]

        while len(U) != 0:
            minimum = INF
            for seg in U:
                if SegmentDistance[seg][0] < minimum:
                    minimum = SegmentDistance[seg][0]
                    minidx = seg

            if minimum == INF:
                break

            S.append(minidx)
            U.remove(minidx)
            
            #print "to %d-%d" % (minidx[0], minidx[1])

            if minidx[0] in road_intersections:
                for n in road_intersections[minidx[0]]:
                    neighbor = (minidx[0], minidx[1])
                    if intersections[n][2][0] == minidx:
                        neighbor = intersections[n][2][1]
                    elif intersections[n][2][1] == minidx:
                        neighbor = intersections[n][2][0]
                    else:
                        continue

                    if not SegmentDistance.has_key(neighbor):
                        continue

                    lon11 = roads[minidx[0]][minidx[1]][0]
                    lon12 = roads[minidx[0]][minidx[1] + 1][0]
                    lat11 = roads[minidx[0]][minidx[1]][1] 
                    lat12 = roads[minidx[0]][minidx[1] + 1][1]
                    lon21 = roads[neighbor[0]][neighbor[1]][0] 
                    lon22 = roads[neighbor[0]][neighbor[1] + 1][0]
                    lat21 = roads[neighbor[0]][neighbor[1]][1] 
                    lat22 = roads[neighbor[0]][neighbor[1] + 1][1]
                    dist = (map_dist(lon11, lat11, lon12, lat12) + map_dist(lon21, lat21, lon22, lat22))/2
                    if dist + minimum < SegmentDistance[neighbor][0]:
                        SegmentDistance[neighbor][0] = dist + minimum
                        SegmentDistance[neighbor][1] = minidx[0]
                        SegmentDistance[neighbor][2] = minidx[1]

            if SegmentDistance.has_key((minidx[0], minidx[1] - 1)) and minidx[1] > 0:
                lon11 = roads[minidx[0]][minidx[1]][0]
                lon12 = roads[minidx[0]][minidx[1] + 1][0]
                lat11 = roads[minidx[0]][minidx[1]][1] 
                lat12 = roads[minidx[0]][minidx[1] + 1][1]
                lon21 = roads[minidx[0]][minidx[1] - 1][0]
                lon22 = roads[minidx[0]][minidx[1]][0]
                lat21 = roads[minidx[0]][minidx[1] - 1][1]
                lat22 = roads[minidx[0]][minidx[1]][1]
                dist = (map_dist(lon11, lat11, lon12, lat12) + map_dist(lon21, lat21, lon22, lat22))/2
                if dist + minimum < SegmentDistance[(minidx[0], minidx[1] - 1)][0]:
                    SegmentDistance[(minidx[0], minidx[1] - 1)][0] = dist + minimum
                    SegmentDistance[(minidx[0], minidx[1] - 1)][1] = minidx[0]
                    SegmentDistance[(minidx[0], minidx[1] - 1)][2] = minidx[1]

            if SegmentDistance.has_key((minidx[0], minidx[1] + 1)) and minidx[1] < len(roads[minidx[0]]) - 2:
                lon11 = roads[minidx[0]][minidx[1]][0]
                lon12 = roads[minidx[0]][minidx[1] + 1][0]
                lat11 = roads[minidx[0]][minidx[1]][1] 
                lat12 = roads[minidx[0]][minidx[1] + 1][1]
                lon21 = roads[minidx[0]][minidx[1] + 1][0]
                lon22 = roads[minidx[0]][minidx[1] + 2][0]
                lat21 = roads[minidx[0]][minidx[1] + 1][1]
                lat22 = roads[minidx[0]][minidx[1] + 2][1]
                dist = (map_dist(lon11, lat11, lon12, lat12) + map_dist(lon21, lat21, lon22, lat22))/2
                if dist + minimum < SegmentDistance[(minidx[0], minidx[1] + 1)][0]:
                    SegmentDistance[(minidx[0], minidx[1] + 1)][0] = dist + minimum
                    SegmentDistance[(minidx[0], minidx[1] + 1)][1] = minidx[0]
                    SegmentDistance[(minidx[0], minidx[1] + 1)][2] = minidx[1]

        for seg in S:
            if SegmentDistance[seg][0] <= INF:
                outfile.write("%d-%d %d-%d %d %d-%d\n" % (road_id, segment_id, seg[0], seg[1], SegmentDistance[seg][0], SegmentDistance[seg][1], SegmentDistance[seg][2]))

    
    def simple_map_matching_trajectory(self, filename):  #match the gps points with roads and segments
        for p in self.trajectory_points[filename]:
            p.plon, p.plat, p.road_id, p.seg_id, p.dist = self.simple_map_matching_point(p.lon, p.lat)
        self.map_matched_trajectory_names.append(filename)

    def simple_map_matching_point(self, lon, lat):
        '''
        FUNCTION:
            matching px,py to one of road segment in roads array
            with simple algorithm: search road segment with the smallest distance to (lon, lat)
        INPUT:
            roads: array of roads, each cell is in format [[x1,y1],[x2,y2],...]
            grid_road_index: array of roads index
            lon, lat: point to be matched
        OUTPUT:
            plon, plat: map matching position of the input point
            road_id, seg_id: map matched road segment in roads array
            dist: distance from input point to map matched position 
        '''         
        dist = float("inf")
        plon = plat = -1  # projection point on road
        road_id = seg_id = -1
 
        # search all road segment in 9 nearest grid cells
        row, col = self.lon_lat_to_grid_row_col(lon, lat)
        row_l = max(0, row - 1)
        row_h = min(self.TOTAL_GRID_ROWS, row + 1)
        col_l = max(0, col - 1)
        col_h = min(self.TOTAL_GRID_COLS, col + 1)
        search_range = []
        for i in range(row_l, row_h + 1):
            for j in range(col_l, col_h + 1):
                search_range += self.grid_road_index[i][j]
  
        for i, j in search_range:
            lon1, lat1 = self.roads[i][j][0], self.roads[i][j][1]
            lon2, lat2 = self.roads[i][j+1][0], self.roads[i][j+1][1]
            tdist, tlon, tlat = self.distance_point_to_line(lon, lat, lon1, lat1, lon2, lat2)
            if tdist < dist:
                dist = tdist
                plon, plat = tlon, tlat
                road_id = i
                seg_id = j
        #print "(%f, %f) matching to (%f, %f), dist=%f, segment=(%d,%d), (%f,%f)-(%f,%f)" % (lon, lat, plon, plat, dist, road_id, seg_id, roads[road_id][seg_id][0], roads[road_id][seg_id][1], roads[road_id][seg_id+1][0], roads[road_id][seg_id+1][1])
        return plon, plat, road_id, seg_id, dist

    def line_magnitude (self, lon1, lat1, lon2, lat2):
        return math.sqrt(math.pow((lon2 - lon1) * self.UNIT_LONGITUDE_DISTANCE, 2) + math.pow((lat2 - lat1) * self.UNIT_LATITUDE_DISTANCE, 2))
 
    def distance_point_to_line (self, lon, lat, lon1, lat1, lon2, lat2):
        '''
        FUNCTION:
            Calc minimum distance from a point and a line segment (i.e. consecutive vertices in a polyline).
            (see http://local.wasp.uwa.edu.au/~pbourke/geometry/pointline/source.vba)
        INPUT:
            all inputs are in longitude or latitude
        OUTPUT:
            dist: distance from point to segment
            plon, plat: projection point on the segment
        '''
 
        line_mag = self.line_magnitude(lon1, lat1, lon2, lat2)
        if line_mag < 0.00000001:
            return float("inf"), lon1, lon2  # segment is a point
 
        u1 = (lon - lon1) * (lon2 - lon1) * math.pow(self.UNIT_LONGITUDE_DISTANCE, 2)
        u2 = (lat - lat1) * (lat2 - lat1) * math.pow(self.UNIT_LATITUDE_DISTANCE, 2)
        u = (u1 + u2) / (line_mag * line_mag)
        if (u < 0.00001) or (u > 1):
            #// closest point does not fall within the line segment, take the shorter distance
            #// to an endpoint
            dist1 = self.line_magnitude(lon, lat, lon1, lat1)
            dist2 = self.line_magnitude(lon, lat, lon2, lat2)
            if dist1 < dist2:
                return dist1, lon1, lat1
            else:
                return dist2, lon2, lat2
        else:
            # Intersecting point is on the line, use the formula
            plon = lon1 + u * (lon2 - lon1)
            plat = lat1 + u * (lat2 - lat1)
            dist = self.line_magnitude(lon, lat, plon, plat)
            #dist = map_dist(lon, lat, plon, plat)
            return dist, plon, plat

    def dump_trajectory_points(self):
        for f in self.trajectory_points:
            print "------------------- ", f, " -----------------------"
            for p in self.trajectory_points[f]:
                print p.timestamp, p.lon, p.lat, p.row, p.col
            
if __name__ == '__main__':
    # full map
    beijingmap = TrajectoryMap(115.2, 117.5, 39.40, 41.10, 10)
    # city center
    #map = Map(116.1, 116.7, 39.65, 40.1)

    #min_longitude = 120.86702
    #max_longitude = 121.97395
    #min_latitude = 30.69477
    #max_latitude = 31.84318
    #shanghaimap = TrajectoryMap(120.86, 121.98, 30.69, 31.85)
    #shanghaimap.load_graph("shanghai.region.graph")
    #shanghaimap.stat_map_info()
    #filenames = glob.glob("MM_GPS_SH_2007-11-01/TAXI-9914/*.csv")
    #shanghaimap.load_shanghai_trajectories(filenames)
    #shanghaimap.stat_trajectories()

    # load map 
    #filenames = []
    #filenames += ["beijingmap/polyline_0x1"]
    #filenames += ["beijingmap/polyline_0x2"]
    #filenames += ["beijingmap/polyline_0x3"]
    #filenames += ["beijingmap/polyline_0x5"]
    #filenames += ["beijingmap/polyline_0x9"]
    #filenames += ["beijingmap/polyline_0x14"]

    filenames = map(lambda x: x[0:-4], glob.glob("/home/ss/Traj/beijingmap/polyline*.dbf"))
    filenames = map(lambda x: x[0:-4], glob.glob("/home/ss/Traj/beijingmap/polygon*.dbf"))
    beijingmap.load_roads(filenames)

    # stat map roads
    beijingmap.stat_map_info()

    # load trajectory
    beijingmap.load_trajectory("/home/ss/Traj/13301104001.traj")
    beijingmap.stat_trajectories()
    beijingmap.match_trajectory_to_grid() 
    beijingmap.dump_trajectory_points()

    # make road index
    beijingmap.index_roads_on_grid()
    beijingmap.dump_grid_road_index()
    
    # generate road graph
    #beijingmap.gen_intersections_in_grid_cell(60, 49)
    #beijingmap.gen_intersections_in_grid_cell(60, 50)
    #beijingmap.gen_intersections_in_grid_cell(60, 51)
    #beijingmap.gen_intersections_in_grid_cell(60, 52)
    #beijingmap.gen_intersections_in_grid_cell(60, 53)
    beijingmap.gen_road_graph()

    # map matching
    print beijingmap.simple_map_matching_trajectory("/home/ss/Traj/13301104001.traj")

