from Tkinter import *
import random
import math
import shapefile
import glob
import time
import thread
import sys

# full map
min_longitude = 115.2  # degree
max_longitude = 117.5  # degree
min_latitude = 39.40   # degree
max_latitude = 41.10   # degree

# city center
#min_longitude = 116.1  # degree
#max_longitude = 116.7  # degree
#min_latitude = 39.65   # degree
#max_latitude = 40.1   # degree

def map_dist(long1, lat1, long2, lat2):
    '''distance between 2 points on sphere surface, in meter'''
    if long1 == long2 and lat1 == lat2:
        return 0
    else:
        return 6378137*math.acos(math.sin(math.radians(lat1))*math.sin(math.radians(lat2))+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.cos(math.radians(long2-long1)))

RESOLUTION = 0.01 # pixcel/m
CANVAS_WIDTH = RESOLUTION * map_dist(min_longitude, min_latitude, max_longitude, min_latitude)
CANVAS_HEIGHT = RESOLUTION * map_dist(min_longitude, min_latitude, min_longitude, max_latitude)

def to_lon_lat(x, y):
    lon = x * (max_longitude - min_longitude) / CANVAS_WIDTH + min_longitude
    lat = (CANVAS_HEIGHT - y) * (max_latitude - min_latitude) / CANVAS_HEIGHT + min_latitude
    return lon, lat

def to_canvas_xy(lon, lat):
    x = (lon - min_longitude) * CANVAS_WIDTH / (max_longitude - min_longitude)
    y = CANVAS_HEIGHT - (lat - min_latitude) * CANVAS_HEIGHT / (max_latitude - min_latitude)
    return x, y

GRID_INTERVAL_KM = 0.3 # grid size in km
GRID_INTERVAL = GRID_INTERVAL_KM * 1000 * RESOLUTION

CANVAS_MIN_X, CANVAS_MIN_Y = to_canvas_xy(min_longitude, max_latitude)
CANVAS_MAX_X, CANVAS_MAX_Y = to_canvas_xy(max_longitude, min_latitude)
TOTAL_GRID_ROWS = int((CANVAS_MAX_Y - CANVAS_MIN_Y) / GRID_INTERVAL + 1)
TOTAL_GRID_COLS = int((CANVAS_MAX_X - CANVAS_MIN_X) / GRID_INTERVAL + 1)

def rand_color():
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    return "#%02x%02x%02x" % (r, g, b)

class MapCanvas(Frame):

    CHECK_BUTTON_STATES = ["hidden", "normal"]

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)

        f_main = Frame(self)
        f_main.pack(expand=YES, fill=BOTH)

        canv = Canvas(f_main)
        canv.config(width=1024, height=600)
        self.select_rect_top = 0
        self.select_rect_bottom = 0
        self.select_rect_left = 0
        self.select_rect_right = 0
        self.select_rect_id = canv.create_rectangle(0, 0, 0, 0, state="hidden")
        canv.config(highlightthickness=0)

        self.drag_last_x = 0
        self.drag_last_y = 0

        self.f_panel = Frame(f_main)
        self.f_panel.pack(side=RIGHT, fill=Y)

        Label(self.f_panel, text="Map Layers").pack()
        self.var_cb_map = IntVar()
        cb_map = Checkbutton(self.f_panel, text="Map", variable=self.var_cb_map, \
                 onvalue=1, offvalue=0, height=5, width=20, \
                 command=lambda: self.onLayerRedraw("map", self.var_cb_map))
        cb_map.select()
        cb_map.pack()
        
        self.var_cb_map_matching = IntVar()
        cb_map_matching = Checkbutton(self.f_panel, text="Map Matching", variable=self.var_cb_map_matching, \
                 onvalue=1, offvalue=0, height=5, width=20, \
                 command=lambda: self.onLayerRedraw("map-matching", self.var_cb_map_matching))
        cb_map_matching.select()
        cb_map_matching.pack()

        self.var_cb_grid = IntVar()
        cb_grid = Checkbutton(self.f_panel, text="Grid", variable=self.var_cb_grid, \
                 onvalue=1, offvalue=0, height=5, width=20, \
                 command=lambda: self.onLayerRedraw("grid", self.var_cb_grid))
        cb_grid.select()
        cb_grid.pack()

        self.bar_y = bar_y = Scrollbar(f_main)
        bar_y.config(command=canv.yview)
        canv.config(yscrollcommand=bar_y.set)
        bar_y.pack(side=RIGHT, fill=Y)
        
        canv.pack(side=LEFT, expand=YES, fill=BOTH)
        canv.bind('<Motion>', self.onCanvasMotion)
        canv.bind('<MouseWheel>', self.onCanvasMouseWheel)
        canv.bind('<ButtonPress-1>', self.onCanvasDragBegin)
        canv.bind('<ButtonRelease-1>', self.onCanvasDragEnd)
        canv.bind('<B1-Motion>', self.onCanvasDrag)
        canv.bind('<ButtonPress-2>', self.onCanvasSelectBegin)
        canv.bind('<ButtonRelease-2>', self.onCanvasSelectEnd)
        canv.bind('<B2-Motion>', self.onCanvasSelectDrag)
        canv.bind("<Double-Button-1>", self.onCanvasLeftDoubleClick)
        canv.bind("<Double-Button-2>", self.onCanvasRightDoubleClick)
        self.canvas = canv

        self.bar_x = bar_x = Scrollbar(self, orient=HORIZONTAL)
        bar_x.config(command=canv.xview)
        canv.config(xscrollcommand=bar_x.set)
        bar_x.pack(fill=BOTH)

        f_start = Frame(self)
        f_start.pack(fill=BOTH)
        Label(f_start, text="Start Time:", width=12).pack(side=LEFT)
        self.var_start_time = StringVar()
        en_start = Entry(f_start, textvariable=self.var_start_time)
        en_start.pack(side=LEFT)
        self.scale_start = Scale(f_start, showvalue=0, orient=HORIZONTAL, command=self.onStartTimeScaleChanged)
        self.scale_start.pack(anchor=CENTER, fill=X)

        f_end = Frame(self)
        f_end.pack(fill=BOTH)
        Label(f_end, text="End Time:", width=12).pack(side=LEFT)
        self.var_end_time = StringVar()
        en_end = Entry(f_end, textvariable=self.var_end_time)
        en_end.pack(side=LEFT)
        self.scale_end = Scale(f_end, showvalue=0, orient=HORIZONTAL, command=self.onEndTimeScaleChanged)
        self.scale_end.pack(anchor=CENTER, fill=X)

        bt_redraw = Button(self, text="Redraw", command=self.onRedrawPressed)
        bt_redraw.pack(fill=BOTH, padx=5, pady=5)

        bt_zoomout = Button(self, text="Zoom Out", command=self.onZoomoutPressed)
        bt_zoomout.pack(side=RIGHT, padx=5, pady=5)
        bt_zoomin = Button(self, text="Zoom In", command=self.onZoominPressed)
        bt_zoomin.pack(side=RIGHT, padx=5, pady=5)

        self.var_pos = StringVar()
        footer = Label(self, textvariable=self.var_pos)
        footer.pack(fill=BOTH)

        self.scale = 1.0       # zoomin/zoomout scale
        self.map_shapes = {}   # map_name -> <timestamp, lon, lat>
        self.traj_shapes = {}   # traj_name -> list of <timestamp, lon, lat>
        self.traj_var_cb = {}   # traj_name -> var for checkbutton state
        self.max_time = 0
        self.min_time = sys.maxint

    # draw map in shapefile format
    def draw_map_shapes(self, filename, shape_type='polyline'):
        if filename in self.map_shapes:
            shape_type, shapeRecords = self.map_shapes[filename]
        else:
            sf = shapefile.Reader(filename)
            shapeRecords = sf.shapeRecords()
            self.map_shapes[filename] = (shape_type, shapeRecords)
        draw_shape_funcs = {
            'polyline' : self.canvas.create_line,
            'polygon'  : self.canvas.create_polygon
        }
        for s in shapeRecords:
            p = map(lambda x: to_canvas_xy(x[0], x[1]), s.shape.points)
            draw_shape_funcs[shape_type](p, fill="#000000", tag="map")#rand_color())
            #self.canvas.create_text(p[0][0],p[0][1],text=unicode(s.record[0],"gbk"))
        self.canvas.itemconfig("map", state=MapCanvas.CHECK_BUTTON_STATES[self.var_cb_map.get()])
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))

    # draw trajectory in format:
    # <timestamp> <longitude> <latitude>
    # start_time, end_time: float
    def draw_trajectory(self, filename, traj_color="red", start_time=None, end_time=None):
        if filename in self.traj_shapes:
            traj_color, points = self.traj_shapes[filename]
        else:
            # not loaded before, load it!
            traj_file = open(filename, "r")
            lines = map(lambda x: x.split(), traj_file.readlines())
            points = map(lambda x: [time.mktime(time.strptime(x[0], "%Y%m%d%H%M%S")), float(x[1]), float(x[2])], lines)
            self.traj_shapes[filename] = (traj_color, points)
            self.min_time = min(min(map(lambda x: x[0], points)), self.min_time)
            self.max_time = max(max(map(lambda x: x[0], points)), self.max_time)
            self.scale_start["from"] = self.min_time
            self.scale_end["from"] = self.min_time
            self.scale_start["to"] = self.max_time
            self.scale_end["to"] = self.max_time
            # add map layer check box
            var_cb_traj = IntVar()
            self.traj_var_cb[filename] = var_cb_traj
            cb_traj = Checkbutton(self.f_panel, text=filename, \
                 variable=var_cb_traj, onvalue=1, offvalue=0, height=5, width=20, \
                 command=lambda: self.onLayerRedraw("traj-" + filename, var_cb_traj))
            cb_traj.select()
            cb_traj.pack()

        if start_time:
            points = filter(lambda x: x[0] >= start_time, points)
            self.scale_start.set(start_time)
        else:
            self.scale_start.set(0)
        if end_time:
            points = filter(lambda x: x[0] < end_time, points)
            self.scale_end.set(end_time)
        else:
            self.scale_end.set(self.scale_end["to"])

        p = map(lambda x: to_canvas_xy(x[1], x[2]), points)
        if len(p) > 0:
            map_canvas.canvas.create_line(p, fill=traj_color, tag=("traj", "traj-" + filename), \
                state=MapCanvas.CHECK_BUTTON_STATES[self.traj_var_cb[filename].get()])

        # reset zoom scale
        self.scale = 1.0

    def draw_point(self, x, y):
        self.canvas.create_oval(x,y,x,y,fill="red", tag="map-matching")

    def draw_line(self, x1, y1, x2, y2, fill="red", width=10.0, dash=""):
        self.canvas.create_line(x1, y1, x2, y2, fill=fill, width=width, dash=dash, tag="map-matching")

    def draw_map_matching_point(self, obj_id, timestamp, px, py):
        roads = [y.shape.points for x in self.map_shapes.values() for y in x[1]]
        # get searching range
        cpx, cpy = to_canvas_xy(px, py)
        row, col = canvas_xy_to_grid_row_col(cpx, cpy)
        row_l = max(0, row - 1)
        row_h = min(TOTAL_GRID_ROWS, row + 1)
        col_l = max(0, col - 1)
        col_h = min(TOTAL_GRID_COLS, col + 1)
        
        search_range = []
        for i in range(row_l, row_h + 1):
            for j in range(col_l, col_h + 1):
                search_range += self.grid_road_index[i][j]
	px, py, minlx, minly, min_road_id, min_segmenet_id, minx1, miny1, minx2, miny2 = simple_map_matching(roads, search_range, px, py) 
	print timestamp, px, py, minlx, minly, min_road_id, min_segmenet_id
        
        self.draw_point(px, py)
        self.draw_point(minlx, minly)
        self.draw_line(px, py, minlx, minly, fill="green", dash=(3,3), width=1)
        self.draw_line(minx1, miny1, minx2, miny2)

    def draw_map_matching_trajectory(self, filename):
        traj_color, points = self.traj_shapes[filename]
        map(lambda x: self.draw_map_matching_point(filename, x[0], x[1], x[2]), points)

    def onCanvasMotion(self, event):
        lon, lat = to_lon_lat(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self.var_pos.set("(%4.4f, %4.4f), scale=%.2f" % (lon, lat, self.scale))

    def onCanvasDragBegin(self, event):
        # change cursor to hand
        self.canvas['cursor'] = 'closedhand'
        self.drag_bar_x_fraction = self.bar_x.get()[0]
        self.drag_bar_y_fraction = self.bar_y.get()[0]
        self.drag_last_x = event.x
        self.drag_last_y = event.y

    def onCanvasDragEnd(self, event):
        # change cursor back to arrow
        self.canvas['cursor'] = 'arrow'

    def onCanvasDrag(self, event):
        dx = event.x - self.drag_last_x
        dy = event.y - self.drag_last_y
        sr = self.canvas['scrollregion'].split()
        rx = (self.bar_x.winfo_width() - 36) / (float(sr[2]) - float(sr[0]))
        ry = (self.bar_y.winfo_height() - 36) / (float(sr[3]) - float(sr[1]))
        self.canvas.xview_moveto(self.drag_bar_x_fraction - self.bar_x.delta(dx, 0)*rx)
        self.canvas.yview_moveto(self.drag_bar_y_fraction - self.bar_y.delta(0, dy)*ry)

    def onCanvasSelectBegin(self, event):
        # change cursor back to arrow
        self.canvas['cursor'] = 'tcross'
        self.select_rect_left = left  = self.canvas.canvasx(event.x)
        self.select_rect_top = top = self.canvas.canvasy(event.y)
        self.canvas.coords(self.select_rect_id, left, top, left, top)
        self.canvas.itemconfigure(self.select_rect_id, state="normal")

    def onCanvasSelectEnd(self, event):
        # change cursor back to arrow
        self.canvas['cursor'] = 'arrow'
        self.canvas.itemconfigure(self.select_rect_id, state="hidden")
        # zoom to this view
        left = self.select_rect_left
        top = self.select_rect_top
        self.select_rect_right = right  = self.canvas.canvasx(event.x)
        self.select_rect_bottom = bottom = self.canvas.canvasy(event.y)
        width = right - left
        height = bottom - top
        if width > 0 and height > 0:
            scale = min(self.canvas.winfo_width()/abs(width), self.canvas.winfo_height()/abs(height))
            self.zoomIn(event.x-width/2, event.y-height/2, scale)

    def onCanvasSelectDrag(self, event):
        self.select_rect_right = right  = self.canvas.canvasx(event.x)
        self.select_rect_bottom = bottom = self.canvas.canvasy(event.y)
        self.canvas.coords(self.select_rect_id, self.select_rect_left, self.select_rect_top, right, bottom)

    def onCanvasMouseWheel(self, event):
        if (event.delta < 0): self.canvas.yview("scroll", 1, "units")
        elif (event.delta > 0): self.canvas.yview("scroll", -1, "units")

    #Zoom In
    def onCanvasLeftDoubleClick(self, event):
        self.zoomIn(event.x, event.y)

    #Zoom Out
    def onCanvasRightDoubleClick(self, event):
        self.zoomOut(event.x, event.y)

    def onZoominPressed(self):
        self.zoomIn(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2)

    def onZoomoutPressed(self):
        self.zoomOut(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2)

    def zoomIn(self, x, y, scale=1.2):
        self.scale *= scale
        cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
        self.canvas.scale(ALL, cx, cy, scale, scale)
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))

    def zoomOut(self, x, y, scale=1.2):
        self.scale /= scale
        cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
        self.canvas.scale(ALL, cx, cy, 1.0/scale, 1.0/scale)
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))

    def onRedrawPressed(self):
        self.canvas.delete("map")
        self.canvas.delete("traj")
        for i in self.map_shapes.keys():
            self.draw_map_shapes(i)
        for i in self.traj_shapes.keys():
            self.draw_trajectory(i, start_time=self.scale_start.get(), end_time=self.scale_end.get())

    def onStartTimeScaleChanged(self, event):
        self.var_start_time.set(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.scale_start.get())))

    def onEndTimeScaleChanged(self, event):
        self.var_end_time.set(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.scale_end.get())))

    def onLayerRedraw(self, tag, var):
        self.canvas.itemconfig(tag, state=MapCanvas.CHECK_BUTTON_STATES[var.get()])

    def stat_map_info(self):
        # count number of all shapes
        shapes = [y.shape for x in self.map_shapes.values() for y in x[1]]
        shapes_number = len(shapes)
        points = map(lambda x: x.points, shapes)
        points_number =  reduce(lambda x,y: x+y, map(lambda x: len(x), points))
        
        print "Number of total polylines: %d" % shapes_number
        print "Number of total points: %d" % points_number
        print "Number of total segments: %d" % (points_number - shapes_number)
        
    def draw_grid(self):
        for i in range(1, TOTAL_GRID_ROWS):
            self.canvas.create_line(CANVAS_MIN_X, CANVAS_MIN_Y + i * GRID_INTERVAL, CANVAS_MAX_X, CANVAS_MIN_Y + i * GRID_INTERVAL, fill="grey", tag="grid")
        for i in range(1, TOTAL_GRID_COLS):
            self.canvas.create_line(CANVAS_MIN_X + i * GRID_INTERVAL, CANVAS_MIN_Y, CANVAS_MIN_X + i * GRID_INTERVAL, CANVAS_MAX_Y, fill="grey", tag="grid")
        for i in range(0, TOTAL_GRID_ROWS):
            for j in range(0, TOTAL_GRID_COLS):
                self.canvas.create_text(CANVAS_MIN_X + j * GRID_INTERVAL, CANVAS_MIN_Y + i * GRID_INTERVAL, text="%d, %d" % (i ,j), anchor=NW, tag="grid")

    def split_roads_to_grid(self):
        points = [y.shape.points for x in self.map_shapes.values() for y in x[1]]
        # init grid_road_dict
        self.grid_road_index = []
        for row in range(0, TOTAL_GRID_ROWS):
            self.grid_road_index.append([])
            for col in range(0, TOTAL_GRID_COLS):
                self.grid_road_index[row].append([])
        # index map segments to self.grid_road_index array. key=(row,col) of a grid; value=array of (road_id, seg_id)
        for i in range(0, len(points)):
            for j in range(0, len(points[i])-1):
                x1, y1 = to_canvas_xy(points[i][j][0], points[i][j][1])
                x2, y2 = to_canvas_xy(points[i][j+1][0], points[i][j+1][1])
                row1, col1 = canvas_xy_to_grid_row_col(x1, y1)
                row2, col2 = canvas_xy_to_grid_row_col(x2, y2)
                
                for row in range(min(row1, row2), max(row1, row2) + 1):
                    for col in range(min(col1, col2), max(col1, col2) + 1):
                        xTL, yTL = grid_row_col_to_canvas_xy(row, col)
                        xBR, yBR = grid_row_col_to_canvas_xy(row + 1, col + 1)
                        if is_line_segment_intersects_box(x1, y1, x2, y2, xTL, yTL, xBR, yBR):
                            self.grid_road_index[row][col].append((i,j))

        # dump grid_road_index array
        for row in range(0, TOTAL_GRID_ROWS):
            for col in range(0, TOTAL_GRID_COLS):
                sys.stdout.write("%3d " % (len(self.grid_road_index[row][col])))
            print

    def highlight_grid_cell(self, row, col):
        print self.grid_road_index[row][col]
        print len(self.grid_road_index[row][col])
        points = [y.shape.points for x in self.map_shapes.values() for y in x[1]]
        print map(lambda x: points[x[0]][x[1]], self.grid_road_index[row][col])
        # highlight grid cell border
        xTL, yTL = grid_row_col_to_canvas_xy(row, col)
        xBR, yBR = grid_row_col_to_canvas_xy(row + 1, col + 1)
        self.canvas.create_rectangle(xTL,yTL,xBR,yBR, width=3)
        # highlight trajectories in grid cell
        for road_id, seg_id in self.grid_road_index[row][col]:
            x1, y1 = to_canvas_xy(points[road_id][seg_id][0], points[road_id][seg_id][1])
            x2, y2 = to_canvas_xy(points[road_id][seg_id+1][0], points[road_id][seg_id+1][1])
            self.canvas.create_text(x1, y1, text="(%d,%d)" % (road_id, seg_id))
            self.canvas.create_line(x1, y1, x2, y2, fill="red", tag="map")

        segments = self.grid_road_index[row][col]
        print segments
        for i in range(0, len(segments)-1):
            for j in range(i, len(segments)):
                road_id1, seg_id1 = segments[i]
                road_id2, seg_id2 = segments[j]
                x0, y0 = points[road_id1][seg_id1]
                x1, y1 = points[road_id1][seg_id1+1]
                x2, y2 = points[road_id2][seg_id2]
                x3, y3 = points[road_id2][seg_id2+1]
                ix, iy = line_segment_cross(x0, y0, x1, y1, x2, y2, x3, y3)
                if ix and iy:
                    #print "(%f,%f)-(%f,%f) intersects with (%f,%f)-(%f,%f) at (%f,%f)" % (x0, y0, x1, y1, x2, y2, x3, y3, ix, iy)
                    print "(%d,%d) intersects with (%d,%d) at (%f,%f)" % (road_id1, seg_id1, road_id2, seg_id2, ix, iy)
                    cix, ciy = to_canvas_xy(ix, iy)
                    self.canvas.create_oval(cix-0.01, ciy-0.01, cix+0.01, ciy+0.01, fill="yellow")
                    self.canvas.create_text(cix, ciy+0.02, text="(%d,%d)x(%d,%d)" % (road_id1, seg_id1, road_id2, seg_id2), fill="red")

def canvas_xy_to_grid_row_col(x, y):
    # x, y in canvas coord
    return int((y - CANVAS_MIN_Y) / GRID_INTERVAL), int((x - CANVAS_MIN_X) / GRID_INTERVAL)

def grid_row_col_to_canvas_xy(row, col):
    # return Top Left corner coord
    return CANVAS_MIN_X + col * GRID_INTERVAL, CANVAS_MIN_Y + row * GRID_INTERVAL
    
def simple_map_matching(roads, search_range, px, py):
    px, py = to_canvas_xy(px, py)
    #search_range: [(road_id, seg_id),...]
    # get all min_type
    mindist = 9999999.0
    minlx = minly = -1  # projection point on road
    min_road_id = min_segment_id = -1
    for i, j in search_range:
        x1, y1 = to_canvas_xy(roads[i][j][0], roads[i][j][1])
        x2, y2 = to_canvas_xy(roads[i][j+1][0], roads[i][j+1][1])
        dist, lx, ly = DistancePointLine(px, py, x1, y1, x2, y2)
        if dist < mindist:
            mindist = dist
            minx1, miny1 = (roads[i][j][0], roads[i][j][1])
            minx2, miny2 = (roads[i][j+1][0], roads[i][j+1][1])
            #minx1, miny1 = to_canvas_xy(roads[i][j][0], roads[i][j][1])
            #minx2, miny2 = to_canvas_xy(roads[i][j+1][0], roads[i][j+1][1])
            minlx, minly = lx, ly
            min_road_id = i
            min_segment_id = j

    lon, lat = to_lon_lat(px,py)
    llon, llat = to_lon_lat(minlx,minly)
    rdist = map_dist(lon, lat, llon, llat)
    print "(%f, %f) matching to (%f, %f), dist=%f, segment=(%d,%d), (%f,%f)-(%f,%f)" % (lon,lat,llon,llat, rdist, min_road_id, min_segment_id,minx1, miny1, minx2, miny2)
    return px, py, minlx, minly, min_road_id, min_segment_id, minx1, miny1, minx2, miny2

def is_line_segment_intersects_box(x1, y1, x2, y2, xTL, yTL, xBR, yBR):
    #Let the segment endpoints be p1=(x1 y1) and p2=(x2 y2). 
    #Let the rectangle's corners be (xTL yTL) and (xBR yBR).
    #All in canvas coord

    # test 4 corners of the rectangle to see whether they are all above or below the lin
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
    if y1 > yBR and y2 > yBR:
        return False # no intersection (line is below rectangle). 
    if y1 < yTL and y2 < yTL:
        return False # no intersection (line is above rectangle). 
    return True

def is_in_bbox(bbox, x, y):
    return bbox[0] <= x and bbox[2] > x and bbox[1] <= y and bbox[3] > y

def lineMagnitude (x1, y1, x2, y2):
    lineMagnitude = math.sqrt(math.pow((x2 - x1), 2)+ math.pow((y2 - y1), 2))
    return lineMagnitude
 
#Calc minimum distance from a point and a line segment (i.e. consecutive vertices in a polyline).
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

def line_segment_cross(x0, y0, x1, y1, x2, y2, x3, y3):
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
    if t<-0.001 or t>1.001 or u<-0.001 or u>1.001:
        return None, None   # intersection point is not on the segment
    return px, py


def old_line_segment_cross(x0, y0, x1, y1, x2, y2, x3, y3):
    # get (x0,y0)-(x1,y1) to (x2,y2)-(x3,y3) intersection point
    #(1-t0)*pt0+t0*pt1=(1-t1)*pt2+t1*pt3
    if (x0-x1)*(y2-y3)-(y0-y1)*(x2-x3) == 0:  # para
        return None, None
    t0=y2*(x3-x2)-x2*(y3-y2)-(y0*(x3-x2)-x0*(y3-y2))
    t0/=((y1-y0)*(x3-x2)-(x1-x0)*(y3-y2))
    t1=x0+t0*(x1-x0)-x2
    if math.fabs(t1) > 0.000000001:
        t1/=(x3-x2)

    # t0 and t1 on same line?
    if t0<0 or t0>1 or t1<0 or t1>1:
        return None, None
    return (1-t0)*x0+t0*x1, (1-t0)*y0+t0*y1

if __name__ == '__main__':
    master = Tk()
    #def task():
    #    print "hello"
    #    master.after(2000, task)
    #master.after(2000, task)

    map_canvas = MapCanvas(master)

    # draw map 
    #map_canvas.draw_map_shapes("beijingmap/polyline_0x1", "polyline")
    #map_canvas.draw_map_shapes("beijingmap/polyline_0x2")
    #map_canvas.draw_map_shapes("beijingmap/polyline_0x3")
    #map_canvas.draw_map_shapes("beijingmap/polyline_0x5")
    #map_canvas.draw_map_shapes("beijingmap/polyline_0x9")
    #map_canvas.draw_map_shapes("beijingmap/polyline_0x14")
    #map_canvas.draw_map_shapes("beijingmap/polygon_0x49", "polygon")

    filenames = map(lambda x: x[0:-4], glob.glob("beijingmap/polyline*.dbf"))
    map(lambda x: map_canvas.draw_map_shapes(x), filenames)
    #filenames = map(lambda x: x[0:-4], glob.glob("beijingmap/polygon*.dbf"))
    #map(lambda x: map_canvas.draw_shapes(x, "polygon"), filenames)

    map_canvas.split_roads_to_grid()

    # stat map shapes
    #map_canvas.stat_map_info()
    #map_canvas.draw_grid()
    
    # draw trajectory
    #map_canvas.draw_trajectory("13301104001.traj")#, start_time="20101101000000", end_time="20101102000000")
    #map_canvas.draw_trajectory("13301104001.20101101.traj")#, start_time="20101101000000", end_time="20101102000000")
    #map_canvas.draw_trajectory("13301104002.traj", "blue")
    #map_canvas.draw_trajectory("13301104003.traj", "green")

    # map matching
    #px, py = 116.206, 39.895
    #cpx, cpy = to_canvas_xy(px, py)
    #row, col = canvas_xy_to_grid_row_col(cpx, cpy)
    #print row, col
    #map_canvas.highlight_grid_cell(row, col)
    map_canvas.highlight_grid_cell(410, 315)
    #map_canvas.draw_map_matching_point("", 0, px, py)
    #map_canvas.draw_map_matching_trajectory("13301104001.20101101.traj")

    mainloop()
