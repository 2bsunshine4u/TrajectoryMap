from Tkinter import *
import math
#import psycopg2
import shapefile
import glob
import time
import thread
import sys
import uuid
import re
from TrajectoryMap import *
import psycopg2

from TrajectoryUtils import map_dist, rand_color, line_segment_cross, DistancePointLine, is_line_segment_intersects_box, hsv2rgb
JPEG_ROOT = "/usr/lib"
#from PIL import Image, ImageTk

import random

class MapCanvas(Frame):

    CHECK_BUTTON_STATES = ["hidden", "normal"]

    def __init__(self, traj_map, parent=None, resolution=0.01):
        '''
        INPUT:
            traj_map: trajectory map
            resolution: map resolution, in pixcel/m
        '''
        self.traj_map = traj_map
        self.RESOLUTION = resolution
        self.CANVAS_WIDTH = resolution * map_dist(traj_map.min_longitude, traj_map.min_latitude, \
                traj_map.max_longitude, traj_map.min_latitude)
        self.CANVAS_HEIGHT = resolution * map_dist(traj_map.min_longitude, traj_map.min_latitude, \
                traj_map.min_longitude, traj_map.max_latitude)
        
        self.scale = 1.0       # zoomin/zoomout scale
        
        self.CANVAS_MIN_X, self.CANVAS_MIN_Y = self.to_canvas_xy_t(traj_map.min_longitude, traj_map.max_latitude)
        self.CANVAS_MAX_X, self.CANVAS_MAX_Y = self.to_canvas_xy_t(traj_map.max_longitude, traj_map.min_latitude)
        
        
        
        self.GRID_INTERVAL_KM = 0.5 # grid size in km
        self.GRID_INTERVAL = self.GRID_INTERVAL_KM * 1000 * self.RESOLUTION
 
        self.TOTAL_GRID_ROWS = int((self.CANVAS_MAX_Y - self.CANVAS_MIN_Y) / self.GRID_INTERVAL + 1)
        self.TOTAL_GRID_COLS = int((self.CANVAS_MAX_X - self.CANVAS_MIN_X) / self.GRID_INTERVAL + 1)

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

        ###
        ###Draw_traj
        #self.point = Entry(self, text="POINT", background = 'yellow')
        #self.point.pack(side=LEFT, padx=5, pady=5)
        #self.dist = Entry(self, text="DIST", background = 'yellow')
        #self.dist.pack(side=LEFT, padx=5, pady=5)
        #bt_roadid = Button(self, text="Draw traj", command=self.onDrawTrajPressed)
        #bt_roadid.pack(side=LEFT, padx=5, pady=5)
        #####
        bt_redraw = Button(self, text="Redraw", command=self.onRedrawPressed)
        bt_redraw.pack(fill=BOTH, padx=5, pady=5)
        
        ###Draw_traj
        default_value_sttime = StringVar()
        default_value_sttime.set('2010-11-03 06:03:17')
        self.sttime = Entry(self, textvariable = default_value_sttime, background = 'yellow')
        self.sttime.pack(side=LEFT, padx=5, pady=5)
        default_value_endtime = StringVar()
        default_value_endtime.set('2010-11-03 06:32:28')
        self.endtime = Entry(self, textvariable = default_value_endtime, background = 'yellow')
        self.endtime.pack(side=LEFT, padx=5, pady=5)
        Search_range = Button(self, text="Search Range", command=self.onSearchRangePressed)
        Search_range.pack(side=LEFT, padx=5, pady=5)
        
        '''
        self.point = Entry(self, text="POINT", background = 'yellow')
        self.point.grid(row=4,column=0)
        self.dist = Entry(self, text="DIST", background = 'yellow')
        self.dist.grid(row=4,column=1)
        bt_roadid = Button(self, text="Draw traj", command=self.onDrawTrajPressed)
        bt_roadid.grid(row=4,column=2)
        '''
        
        ###bt_zoomout = Button(self, text="Zoom Out", command=self.onZoomoutPressed)
        ###bt_zoomout.pack(side=RIGHT, padx=5, pady=5)
        ###bt_zoomin = Button(self, text="Zoom In", command=self.onZoominPressed)
        ###bt_zoomin.pack(side=RIGHT, padx=5, pady=5)
        
        self.road_id_text = Entry(self, background = 'yellow')
        self.road_id_text.pack(side=LEFT, padx=5, pady=5)

        ###Search_traj
        bt_roadid = Button(self, text="Search traj", command=self.onSearchTrajPressed)
        bt_roadid.pack(side=LEFT, padx=5, pady=5)
        
        #bt_savePic = Button(self, text="Save Pic", command=self.onSavePicture)
        #bt_savePic.pack(side=LEFT, padx=5, pady=5)
        
        ###Draw_traj
        self.default_value1 = StringVar()
        self.default_value1.set('116.34,39.83')
        self.point = Entry(self, textvariable = self.default_value1, background = 'yellow')
        self.point.pack(side=LEFT, padx=5, pady=5)
        
        default_value2 = StringVar()
        default_value2.set('50')
        self.dist = Entry(self, textvariable = default_value2, background = 'yellow')
        self.dist.pack(side=LEFT, padx=5, pady=5)
        bt_roadid = Button(self, text="Draw traj", command=self.onDrawTrajPressed)
        bt_roadid.pack(side=LEFT, padx=5, pady=5)
        


        self.var_pos = StringVar()
        footer = Label(self, textvariable=self.var_pos)
        footer.pack(fill=BOTH)
        
        
        self.traj_var_cb = {}   # traj_name -> var for checkbutton state of trajectory
        self.traj_mm_var_cb = {}  # traj_name -> var for checkbutton state of trajectory map matching
        self.max_time = 0
        self.min_time = sys.maxint

        self.coress_dict = {}
        self.traj_shapes = {}

    def to_lon_lat(self, x, y):
        #cx = self.canvas.canvasx(self.canvas.winfo_width()/2)
        #cy = self.canvas.canvasy(self.canvas.winfo_height()/2)
        #x += cx
        #y += cy
        
        lon = x * (self.traj_map.max_longitude - self.traj_map.min_longitude) / \
                (self.CANVAS_WIDTH * self.scale) + self.traj_map.min_longitude
        lat = (self.CANVAS_HEIGHT * self.scale - y) * (self.traj_map.max_latitude - self.traj_map.min_latitude) / \
                (self.CANVAS_HEIGHT * self.scale) + self.traj_map.min_latitude
        return lon, lat
        
    def to_canvas_xy_t(self, lon, lat):
        x = (lon - self.traj_map.min_longitude) * self.CANVAS_WIDTH / \
                (self.traj_map.max_longitude - self.traj_map.min_longitude)
        y = self.CANVAS_HEIGHT - (lat - self.traj_map.min_latitude) * self.CANVAS_HEIGHT / \
                (self.traj_map.max_latitude - self.traj_map.min_latitude)
        return x, y
        
    def to_canvas_xy(self, lon, lat):
        #cx = self.canvas.canvasx(self.canvas.winfo_width()/2)
        #cy = self.canvas.canvasy(self.canvas.winfo_height()/2)
        
        
        x = (lon - self.traj_map.min_longitude) * (self.CANVAS_WIDTH) / \
                (self.traj_map.max_longitude - self.traj_map.min_longitude)
        y = self.CANVAS_HEIGHT - (lat - self.traj_map.min_latitude) * (self.CANVAS_HEIGHT) / \
                (self.traj_map.max_latitude - self.traj_map.min_latitude)
                
        #print x, y, self.scale ###yangxy
        #x -= cx
        #y -= cy
        return x, y

    # draw city map
    def draw_map(self):
        for i in range(0, len(self.traj_map.roads)):
            p = map(lambda x: self.to_canvas_xy(x[0], x[1]), self.traj_map.roads[i]) ###yangxy
            if len(p) >= 2:
                #self.canvas.create_line(p, fill="red", tag="map")
                #self.canvas.create_line(p, fill=rand_color(), tag="map",width=1)
                self.canvas.create_line(p, fill="grey", tag="map",width=1)
                #self.canvas.create_line(p, fill="white", tag="map",width=1)
                #self.canvas.create_text(p[0][0],p[0][1],text="(r=%d)" %(i))
                #map(lambda x: self.canvas.create_text(x[0],x[1],text="(r=%d)" %(i)),p)
                #self.canvas.create_text(p[2][0],p[2][1],text="(r=%d)" %(i))
                #print "line: %s" % p
                #map(lambda x: self.canvas.create_oval(x[0]-0.01, x[1]-0.01, x[0]+0.01, x[1]+0.01,tag="map", fill="yellow"), p)
                #pass

            #self.canvas.create_text(p[0][0],p[0][1],text=unicode(self.traj_map.road_names[i],"gbk"), tag="road-name")
        
        for i in range(0, len(self.traj_map.roads2)):
            p = map(lambda x: self.to_canvas_xy(x[0], x[1]), self.traj_map.roads2[i]) ###yangxy
            if len(p) >= 2:
                self.canvas.create_line(p, fill="red", tag="map",width=2)
              
        self.canvas.itemconfig("map", state=MapCanvas.CHECK_BUTTON_STATES[self.var_cb_map.get()])
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))

    def clean_road(self):
        self.clean_road = {}
        self.roads = []
        num = 0
        roads_temp = self.traj_map.roads
        for i in range(0,len(roads_temp))[::-1]:
            if len(roads_temp[i]) >=2 :
                road_i = map(lambda x: (x[0],x[1]), roads_temp[i])
                for j in range(1,len(road_i))[::-1]:
                    road_j = (road_i[j-1][0],road_i[j-1][1],road_i[j][0],road_i[j][1])
                    if road_j in self.clean_road:
                        num += 1
                        #print "same road! num:%d id:(%d,%d)" % (num,i,j)
                        del self.traj_map.roads[i][j]
                        self.clean_road[road_j] += [(i,j)]
                    else:
                        self.clean_road[road_j] = [(i,j)]

        for i in range(0,len(self.traj_map.roads))[::-1]:
            if len(self.traj_map.roads[i]) <= 2:
                del self.traj_map.roads[i]

        for road_j in self.clean_road:
            self.roads += [[(road_j[0],road_j[1]),(road_j[2],road_j[3])]]

        #print "roads:%s" % self.roads
        f = open('roads','w')
        for road in self.traj_map.roads:
            f.write('%s\n' % road)
        #f.write('%s' % (self.roads))
        f.close()
        #print "roads_num:%d" % len(self.roads)
       
    def draw_all_trajectories(self):
        for filename in self.traj_map.trajectory_points.keys():
            print "logging ~~~~~~~~~~~filename:%s~~~~~~~~~~~~~~~~~~~~~~" % filename
            self.draw_trajectory(filename, rand_color())

    def draw_trajectory(self, filename, traj_color="red", start_time=None, end_time=None):
        if filename in self.traj_shapes:
            traj_color, points = self.traj_shapes[filename]
        else:
            # not loaded before, load it!
            traj_file = open(filename, "r")
            lines = map(lambda x: x.split(), traj_file.readlines())
            points = map(lambda x: [time.mktime(time.strptime(x[0], "%Y%m%d%H%M%S")), float(x[1]), float(x[2])], lines)
            self.traj_shapes[filename] = (traj_color, points)

        timestamps = map(lambda x: x[0], points)
        self.min_time = min(min(timestamps), self.min_time)
        self.max_time = max(max(timestamps), self.max_time)
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

        # filter points according to start_time and end_time
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

        p = map(lambda x: self.to_canvas_xy(x[1], x[2]), points)
        print "Corresponding Points Number:", len(p)
        if len(p) > 0:
            self.canvas.create_line(p, fill=traj_color, tag=("traj", "traj-" + filename), \
                state=MapCanvas.CHECK_BUTTON_STATES[self.traj_var_cb[filename].get()])
            map(lambda x: self.canvas.create_oval(x[0]-0.01, x[1]-0.01, x[0]+0.01, x[1]+0.01, fill=traj_color, outline="black",width=2), p)
        # draw bounding box
        #for p in points:
        #    if p.row > -1 and p.col > -1:
        #        xTL, yTL = self.grid_row_col_to_canvas_xy(p.row, p.col)
        #        xBR, yBR = self.grid_row_col_to_canvas_xy(p.row + 1, p.col + 1)
        #        self.canvas.create_rectangle(xTL,yTL,xBR,yBR, fill="red")

        # reset zoom scale
        self.scale = 3.0

    def draw_all_map_matching_trajectories(self):
        for f in self.traj_shapes.keys():
            self.draw_map_matching_trajectory(f)

    def onCanvasMotion(self, event):
        #print 'onCanvasMotion'
        lon, lat = self.to_lon_lat(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        x0 = self.canvas.canvasx(0)
        y0 = self.canvas.canvasy(0)
        self.var_pos.set("(%4.4f, %4.4f), scale=%.2f" % (lon, lat, self.scale))
        #self.var_pos.set("(%4.4f, %4.4f),(%4.4f, %4.4f), scale=%.2f" % (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),x0, y0, self.scale))

    def onCanvasDragBegin(self, event):
        # change cursor to hand
        print 'onCanvasDragBegin'
        lon, lat = self.to_lon_lat(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        x0 = self.canvas.canvasx(0)
        y0 = self.canvas.canvasy(0)
        self.start_lon = lon
        self.start_x = self.canvas.canvasx(event.x)
        self.start_lat = lat
        self.start_y = self.canvas.canvasy(event.y)
        print lon,lat

    def onCanvasDragEnd(self, event):
        # change cursor back to arrow
        print 'onCanvasDragEnd'
        lon, lat = self.to_lon_lat(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        x0 = self.canvas.canvasx(0)
        y0 = self.canvas.canvasy(0)
        self.end_lon = lon
        self.end_x = self.canvas.canvasx(event.x)
        self.end_lat = lat
        self.end_y = self.canvas.canvasy(event.y)
        time1=0
        time2=3
        ##draw query range
        p=[[self.start_x,self.start_y],[self.end_x,self.start_y],[self.end_x,self.end_y],\
            [self.start_x,self.end_y],[self.start_x,self.start_y]]
        print p
        self.canvas.create_line(p, fill="green", tag="map",width=3)
        ##
        ##range = [[self.start_lon,self.start_lat,time1],[self.end_lon,self.end_lat,time2]]
        ##self.range_query(range)
        ##
        self.default_value1.set("%s,%s"%(lon,lat))
        #print lon,lat
        
    def onSearchRangePressed(self):
        sttime_str = self.sttime.get()
        endtime_str = self.endtime.get()
        range = [[self.start_lon,self.start_lat,sttime_str],[self.end_lon,self.end_lat,endtime_str]]
        self.range_query(range)
        

    def onCanvasDrag(self, event):
        #print 'onCanvasDrag'
        pass

    def onCanvasSelectBegin(self, event):
        # change cursor back to arrow
        print 'onCanvasSelectBegin'
        self.canvas['cursor'] = 'tcross'
        self.select_rect_left = left  = self.canvas.canvasx(event.x)
        self.select_rect_top = top = self.canvas.canvasy(event.y)
        self.canvas.coords(self.select_rect_id, left, top, left, top)
        self.canvas.itemconfigure(self.select_rect_id, state="normal")

    def onCanvasSelectEnd(self, event):
        # change cursor back to arrow
        print 'onCanvasSelectEnd'
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
        print 'onCanvasSelectDrag'
        self.select_rect_right = right  = self.canvas.canvasx(event.x)
        self.select_rect_bottom = bottom = self.canvas.canvasy(event.y)
        self.canvas.coords(self.select_rect_id, self.select_rect_left, self.select_rect_top, right, bottom)

    def onCanvasMouseWheel(self, event):
        print 'onCanvasMouseWheel'
        if (event.delta < 0): self.canvas.yview("scroll", 1, "units")
        elif (event.delta > 0): self.canvas.yview("scroll", -1, "units")

    def onDrawRoadidPressed(self):
        temp_road_id = self.road_id_text.get()
        if(temp_road_id != ''):
            self.drawRoadid(temp_road_id)
            

            
    #Zoom In
    def onCanvasLeftDoubleClick(self, event):
        self.zoomIn(event.x, event.y)

    #Zoom Out
    def onCanvasRightDoubleClick(self, event):
        print "!!!!!!!!!!11"
        self.zoomOut(event.x, event.y)

    def onZoominPressed(self):
        pass
        ####self.zoomIn(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2)

    def onZoomoutPressed(self):
        pass
        ####self.zoomOut(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2)

    def zoomIn(self, x, y, scale=1.2):
        #self.CANVAS_WIDTH *= scale
        #self.CANVAS_HEIGHT *= scale
        self.scale *= scale
        cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
        self.canvas.scale(ALL, cx, cy, scale, scale)
        ###self.canvas.config(scrollregion=self.canvas.bbox(ALL))

    def zoomOut(self, x, y, scale=1.2):
        #self.CANVAS_WIDTH /= scale
        #self.CANVAS_HEIGHT /= scale
        if(self.scale < 1):
            pass
        else:
            self.scale /= scale
            cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
            self.canvas.scale(ALL, cx, cy, 1.0/scale, 1.0/scale)
            ###self.canvas.config(scrollregion=self.canvas.bbox(ALL))
            #self.CANVAS_WIDTH = self.CANVAS_WIDTH 

    def onRedrawPressed(self):
        #self.canvas.delete("map")
        #self.canvas.delete("road")
        self.canvas.delete("traj")
        #for i in self.map_shapes.keys():
        #self.draw_map()
        for i in self.traj_map.trajectory_points.keys():
            self.draw_trajectory(i, start_time=self.scale_start.get(), end_time=self.scale_end.get())

    def onStartTimeScaleChanged(self, event):
        self.var_start_time.set(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.scale_start.get())))

    def onEndTimeScaleChanged(self, event):
        self.var_end_time.set(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.scale_end.get())))

    def onLayerRedraw(self, tag, var):
        self.canvas.itemconfig(tag, state=MapCanvas.CHECK_BUTTON_STATES[var.get()])

    def onDrawTrajPressed(self):
        temp_point_str = self.point.get()
        temp_dist_str = self.dist.get()
        
        if(temp_point_str != '' and temp_dist_str != ''):
            self.drawTraj(temp_point_str, temp_dist_str)
            
    def onSavePicture(self):
        ''' '''
        self.canvas.pack()
        self.canvas.update()
        self.canvas.postscript(file="saved.ps",colormode="color")

    def onSearchTrajPressed(self):
        temp_traj_id = self.road_id_text.get()
        if(temp_traj_id != ''):
            self.drawTrajid(temp_traj_id)
        
            
    def highlight_grid_cell(self, row, col):
        segments = self.traj_map.grid_road_index[row][col]
        print segments
        print len(segments)
        points = self.traj_map.roads
        print map(lambda x: points[x[0]][x[1]], segments)
        # highlight grid cell border
        xTL, yTL = self.grid_row_col_to_canvas_xy(row, col)
        xBR, yBR = self.grid_row_col_to_canvas_xy(row + 1, col + 1)
        self.canvas.create_rectangle(xTL,yTL,xBR,yBR, width=3)
        self.canvas.create_text(xTL, yTL, text="%d, %d" % (row ,col), anchor=NW, tag="grid")
        # highlight trajectories in grid cell
        for road_id, seg_id in segments:
            x1, y1 = self.to_canvas_xy(points[road_id][seg_id][0], points[road_id][seg_id][1])
            x2, y2 = self.to_canvas_xy(points[road_id][seg_id+1][0], points[road_id][seg_id+1][1])
            self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text="(%d,%d)" % (road_id, seg_id))
            self.canvas.create_line(x1, y1, x2, y2, fill="red", tag="map")

    def highlight_intersections(self):
        # highlight intersection in grid cell
        for i in range(0, len(self.traj_map.intersections)):
            cix, ciy = self.to_canvas_xy(self.traj_map.intersections[i][0], self.traj_map.intersections[i][1])
            self.canvas.create_oval(cix-0.01, ciy-0.01, cix+0.01, ciy+0.01, fill="yellow")
            iname = str(self.traj_map.intersections[i][2])
            self.canvas.create_text(cix, ciy+0.02, text="(%d,%s)" % (i, iname), fill="red")

    def highlight_road_set(self, road_set):
        for i in road_set:
            p = map(lambda x: self.to_canvas_xy(x[0], x[1]), self.traj_map.roads[i])
            self.canvas.create_line(p, fill="red", width=5)
            self.canvas.create_text(p[0][0], p[0][1], text="%d" % i)

    def canvas_xy_to_grid_row_col(self, x, y):
        # x, y in canvas coord
        return int((y - self.CANVAS_MIN_Y) / self.traj_map.GRID_INTERVAL), \
                int((x - self.CANVAS_MIN_X) / self.traj_map.GRID_INTERVAL)

    def grid_row_col_to_canvas_xy(self, row, col):
        # return Top Left corner coord
        return self.CANVAS_MIN_X + col * self.traj_map.GRID_INTERVAL, \
                self.CANVAS_MIN_Y + row * self.traj_map.GRID_INTERVAL

#============================================================================
    def simple_map_matching(self, search_range, plon, plat):
        px, py = self.to_canvas_xy(plon, plat)
        #search_range: [(road_id, seg_id),...]
        # get all min_type
        maxdist = 0.5
        matching_set = []
        #print "search_range:%s" % search_range
        
        for i, j in search_range:
            flag = False
            x1, y1 = self.to_canvas_xy(self.traj_map.roads[i][j][0], self.traj_map.roads[i][j][1])
            x2, y2 = self.to_canvas_xy(self.traj_map.roads[i][j+1][0], self.traj_map.roads[i][j+1][1])
            dist, lx, ly = DistancePointLine(px, py, x1, y1, x2, y2) 
            #print "segment:%s-%s dist:%s" % (i,j,dist)
            if dist < maxdist:
                for idx in range(0, len(matching_set)):  #insert segs whose dist less than 50m into list in order of dist
                    if(dist < matching_set[idx][0]):
                        matching_set.insert(idx, (dist, i, j))
                        flag = True
                        break
                if flag == False:
                    matching_set.append((dist, i, j))

        print len(matching_set)

        return matching_set
    
        #print "(%f, %f) matching to (%f, %f), dist=%f, segment=(%d,%d), (%f,%f)-(%f,%f)"\
        #    % (lon,lat,llon,llat, rdist, min_road_id, min_segment_id,minx1, miny1, minx2, miny2)
    
        #draw_line(minx1, miny1, minx2, miny2,fill="yellow") 
        return px, py, minlx, minly, min_road_id, min_segment_id, minx1, miny1, minx2, miny2, rdist

    def split_roads_to_grid(self):
        #self.traj_map.roads = [y.shape.self.traj_map.roads for x in self.map_shapes.values() for y in x[1]]
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
        for i in range(0, len(self.traj_map.roads)):
            for j in range(0, len(self.traj_map.roads[i])-1):
                #print "i,j",i,j
                x1, y1 = self.to_canvas_xy(self.traj_map.roads[i][j][0], self.traj_map.roads[i][j][1])
                x2, y2 = self.to_canvas_xy(self.traj_map.roads[i][j+1][0], self.traj_map.roads[i][j+1][1])
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


    def draw_point(self, x, y):
        x,y = self.to_canvas_xy(x, y)
        self.canvas.create_oval(x,y,x,y,fill="red", tag="map-matching")

    def draw_line(self, x1, y1, x2, y2):
        #print "draw_line:",x1,y1,'- ', x2,y2
        self.MapMatchingFile.write("%f %f-%f %f\n" % (x1, y1, x2, y2))

    def draw_shortest_path(self, prev_road_id, prev_segment_id, min_road_id, min_segment_id):
        print "Search for shortest_path to road-segment: ", min_road_id, '-', min_segment_id
        tar = (min_road_id, min_segment_id)

        while prev_road_id != tar[0] or prev_segment_id != tar[1]:
            sql = "SELECT prev_roadid, prev_segmentid from shortest_path where src_roadid = %d and src_segmentid = %d and dst_roadid = %d and dst_segmentid = %d" % (prev_road_id, prev_segment_id, tar[0], tar[1])
            self.cursor_to.execute(sql)
            result = self.cursor_to.fetchall()

            if len(result) == 0:
                print "Failed!"
                return -1

            print "Succeeded!"
            self.draw_line(self.traj_map.roads[tar[0]][tar[1]][0], self.traj_map.roads[tar[0]][tar[1]][1], self.traj_map.roads[tar[0]][tar[1]+1][0], self.traj_map.roads[tar[0]][tar[1]+1][1])

            tar = result[0] 
            print "Filled road-segment: ",tar[0], "-", tar[1]
        return 0

    def draw_map_matching_point(self, obj_id, timestamp, px, py, prev_road_id, prev_segment_id):
        #yxy#roads = [y.shape.points for x in self.map_shapes.values() for y in x[1]]
        # get searching range
        cpx, cpy = self.to_canvas_xy(px, py)
        row, col = self.canvas_xy_to_grid_row_col(cpx, cpy)
        row_l = max(0, row - 1)
        row_h = min(self.TOTAL_GRID_ROWS, row + 1)
        col_l = max(0, col - 1)
        col_h = min(self.TOTAL_GRID_COLS, col + 1)       
 
        print "Draw MapMatching path at time:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        search_range = []
        #print 'row_l,row_h,col_l,col_h',row_l,row_h,col_l,col_h
        for i in range(row_l, row_h + 1):
            for j in range(col_l, col_h + 1):
                search_range += self.grid_road_index[i][j]
        matching_set = self.simple_map_matching(search_range, px, py) 
        #print timestamp, px, py, minlx, minly, min_road_id, min_segment_id, dist

        flag = False #indicate the result of matching

        for dist, road_id, seg_id in matching_set:
            if road_id == prev_road_id: #Draw directly if in the same road 
                for j in range(min(seg_id, prev_segment_id), max(seg_id, prev_segment_id) + 1):
                    print road_id, "-", j
                    self.draw_line(self.traj_map.roads[road_id][j][0], self.traj_map.roads[road_id][j][1], self.traj_map.roads[road_id][j+1][0], self.traj_map.roads[road_id][j+1][1])
                    flag = True
                break
            else: #search for shortest path in database if not in the same road
                if self.draw_shortest_path(prev_road_id, prev_segment_id, road_id, seg_id) == 0:
                    flag = True
                    break

        if flag == False and len(matching_set) > 0: #draw simple matching result if there is no shortest path
            road_id = matching_set[0][1]
            seg_id = matching_set[0][2]
            print "No shortest path exists! Simple matching: ", road_id, '-', seg_id
            self.draw_line(self.traj_map.roads[road_id][seg_id][0], self.traj_map.roads[road_id][seg_id][1], self.traj_map.roads[road_id][seg_id+1][0], self.traj_map.roads[road_id][seg_id+1][1])
        
        #self.draw_point(px, py)
        #self.draw_point(minlx, minly)
        #self.draw_line(px, py, minlx, minly, fill="yellow", dash=(3,3), width=1)
        #self.draw_line(minx1, miny1, minx2, miny2)

	if len(matching_set) == 0:
            return -1, -1
        return road_id, seg_id

    def draw_map_matching_trajectory(self, filename):
        print "loading shortest path ~~~~~~~~~~~dbname:%s~~~~~~~~~~~~~~~~~~~~~~" % filename
        #outfile = open(filename, 'w')
        print "Connecting.."
        self.conn_to = psycopg2.connect(host='localhost',port='5432',database="shortest_path",
                                   user='postgres',password='123456')
        print "Connected.\n"
        self.cursor_to = self.conn_to.cursor()

        print "Map Matching ~~~~~~~~~~~filename:%s~~~~~~~~~~~~~~~~~~~~~~" % filename
        traj_color, points = self.traj_shapes[filename]
        self.split_roads_to_grid()
        prev_road_id, prev_segment_id = points[0][1:3]
      
        self.MapMatchingFile = open(filename + '_matching', 'w')

        for p in points:
            i, j = self.draw_map_matching_point(filename, p[0], p[1], p[2], prev_road_id, prev_segment_id)
            if not (i,j) == (-1,-1):
                prev_road_id = i
                prev_segment_id = j
   	    else:
                print "Matching Failed! The GPS point has been discarded!"	

        self.MapMatchingFile.close()

        self.conn_to.commit()
        self.conn_to.close()

    def display_map_matching_trajectory(self, filename, fill="red", width=3.0, dash=""):
        traj_file = open(filename + "_matching", "r")
        while 1:
            lines = traj_file.readlines(1000)
            if not lines:
                break
            for line in lines:
                line = line.strip()
                words = line.split('-')
                point1 = words[0].split(' ')
                point2 = words[1].split(' ')
                x1,y1 = self.to_canvas_xy(float(point1[0]), float(point1[1]))
                x2,y2 = self.to_canvas_xy(float(point2[0]), float(point2[1]))
                self.canvas.create_line(x1, y1, x2, y2, fill=fill, width=width, dash=dash, tag="map-matching")
                print "draw_trajectory_segment: ", point1[0], point1[1], 'to', point2[0], point2[1] 
        traj_file.close()

    def write_roadid(self):
        ''' '''
        output_file = open('road_network2', 'w')
        for i in range(len(self.traj_map.roads)):
            for j in range(len(self.traj_map.roads[i])-1):
                output_file.write('%s-%s\t%s %s\n' %(i,j,self.traj_map.roads[i][j],self.traj_map.roads[i][j+1]))
        output_file.close()
        
    def get_time_from(self, filename):
        f = open(filename,"r")
        #partten = re.compile(r'Total runtime: \d+.\d+ ms')
        #(116.405340122 40.0498876108 1288567347.17,116.407181771 40.0522671435 1288567402.72)
        partten = re.compile(r'\(\d+.\d+ \d+.\d+ \d+.\d+,\d+.\d+ \d+.\d+ \d+.\d+\)')
        while 1:
            lines = f.readlines(1000)
            if not lines :
                break
            else:
                for line in lines:
                    match = re.findall(partten,line)
                    if match:
                        i = 0
                        for linestring in  match:
                            #i += 1
                            #if i > 10:
                            #    break
                            linestring =  linestring[1:-1]
                            points = linestring.split(',')
                            point_start = points[0].split(' ')
                            point_end = points[1].split(' ')
                            point_start = point_start[0:2]
                            point_end = point_end[0:2]
                            #print points
                            p = map(lambda x: self.to_canvas_xy(float(x[0]), float(x[1])), [point_start,point_end])
                            #print p
                            self.canvas.create_line(p, fill='green', tag="map",width=1)
                            map(lambda x: self.canvas.create_oval(x[0]-0.01, x[1]-0.01, x[0]+0.01, x[1]+0.01,tag="map", fill="yellow"), p)
        f.close()
        
    def draw_query(self, filename):
        f = open(filename,"r")
        lines = f.readlines()
        for i in range(len(lines)):
        #for line in lines:
            line = lines[i]
            line = line.strip()
            words = line.split(',')
            point_start = words[0:2]
            point_end = words[2:4]
            [point_start,point_end] = map(lambda x: self.to_canvas_xy(float(x[0]), float(x[1])), [point_start,point_end])
            self.canvas.create_rectangle(point_start[0],point_start[1],point_end[0],point_end[1])
            self.canvas.create_text(point_start[0],point_start[1],text="%d" % i)
            
        f.close()
if __name__ == '__main__':
    # full map
    beijingmap = TrajectoryMap(115.2, 117.5, 39.40, 41.10, grid_interval=500)
    # city center
    #map = Map(116.1, 116.7, 39.65, 40.1)

    # load map 
    #filenames = []
    #filenames += ["beijingmap/polyline_0x1"]
    #filenames += ["beijingmap/polyline_0x2"]
    #filenames += ["beijingmap/polyline_0x3"]
    #filenames += ["beijingmap/polyline_0x5"]
    #filenames += ["beijingmap/polyline_0x9"]
    #filenames += ["beijingmap/polyline_0x14"]

    filenames = map(lambda x: x[0:-4], glob.glob("beijingmap/polyline*.dbf"))
    #filenames = map(lambda x: x[0:-4], glob.glob("beijingmap/polygon*.dbf"))
    #filenames = map(lambda x: x[0:-4], glob.glob("beijingmap/point*.dbf"))
    beijingmap.load_roads(filenames)

    # stat map roads
    beijingmap.stat_map_info()

    # load trajectory
    beijingmap.load_trajectory("13301104001.20101101.traj")
    #beijingmap.load_trajectory("13301104002.traj")
    #beijingmap.load_trajectory("13301104003.traj")
    beijingmap.stat_trajectories()

    # make road index
    beijingmap.index_roads_on_grid()
    #beijingmap.dump_grid_road_index()

    # generate road graph
    #beijingmap.gen_intersections_in_grid_cell(60, 49)
    #beijingmap.gen_intersections_in_grid_cell(60, 50)
    #beijingmap.gen_intersections_in_grid_cell(60, 51)
    #beijingmap.gen_intersections_in_grid_cell(60, 52)
    #beijingmap.gen_intersections_in_grid_cell(60, 53)
    #beijingmap.gen_road_graph()
    #beijingmap.gen_intersections_in_grid_cell(410, 315)
    
    #calculate the shortestpath
    #beijingmap.ShortestPath()

    # map matching
    #beijingmap.simple_map_matching_trajectory("13301104001.20101101.traj")
    #beijingmap.simple_map_matching_trajectory("13301104002.traj")

    master = Tk()
    map_canvas = MapCanvas(beijingmap, master)
    map_canvas.draw_map()
    #map_canvas.draw_grid()
    map_canvas.draw_all_trajectories()
    #map_canvas.draw_trajectory("13301104001.20101101.traj")#, start_time="20101101000000", end_time="20101102000000")
    #map_canvas.draw_trajectory("13301104002.traj", "blue")
    #map_canvas.draw_trajectory("13301104003.traj", "green")
    # map matching
    #px, py = 116.206, 39.895
    #cpx, cpy = map_canvas.to_canvas_xy(px, py)
    #row, col = map_canvas.canvas_xy_to_grid_row_col(cpx, cpy)
    #print row, col
    #map_canvas.highlight_grid_cell(row, col)
    #map_canvas.highlight_grid_cell(410, 315)
    #map_canvas.highlight_grid_cell(60, 49)
    #map_canvas.highlight_grid_cell(120, 150)
    #map_canvas.highlight_grid_cell(60, 51)
    #map_canvas.highlight_grid_cell(60, 52)
    #map_canvas.highlight_grid_cell(60, 53)
    #map_canvas.highlight_intersections()

    #load the shortest_path and mapmatch
    #map_canvas.draw_map_matching_point("", 0, px, py)
    map_canvas.draw_all_map_matching_trajectories()
    #map_canvas.draw_map_matching_trajectory("13301104001.20101101.traj")
 
    map_canvas.display_map_matching_trajectory("13301104001.20101101.traj")

    #roads = [7878, 7879]
    #map_canvas.highlight_road_set(roads)

    mainloop()
