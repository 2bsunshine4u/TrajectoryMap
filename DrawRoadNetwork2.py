import glob
from Tkinter import *
from TrajectoryMap import *
from TrajectoryUtils import map_dist, rand_color, line_segment_cross
from TrajectoryMapCanvas import MapCanvas
from ConnPostgreSQL import *

#from SimpleMapMatching import *

import logging
import logging.config
    
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("example")

def get_timestamp(str):
    return time.mktime(time.strptime(str, "%Y%m%d%H%M%S"))

if __name__ == '__main__':
    # full map
    beijingmap = TrajectoryMap(115.2, 117.5, 39.40, 41.10, grid_interval=500)
    # city center

    # load map 
    filenames = []
    filenames += map(lambda x: x[0:-4], glob.glob("beijing_osm/beijing_highway.shp"))
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*1.dbf"))#highway
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*2.dbf"))
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*3.dbf"))
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*5.dbf"))#road
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*x6.dbf"))#lroad 65282
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*8.dbf"))#cross_road
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*9.dbf"))#cross_road
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*a.dbf"))#point
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*c.dbf"))#point
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*16.dbf"))#point
    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polyline_*14.dbf"))#cross_road

    #filenames += map(lambda x: x[0:-4], glob.glob("beijingmap/polygon_*.dbf"))
    #filenames += map(lambda x: x[0:-4], glob.glob("BJSHP/*polyline.dbf"))
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/cloverleafl_*.dbf"))
##    filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/mstreet_*.dbf"))
##    filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/street_*.dbf"))
##    filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/sstreet_*.dbf"))
##    filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/ostreet_*.dbf"))
##    filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/bystreet_*.dbf"))
##    filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/mroad_*.dbf"))
##    filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/highway_*.dbf"))
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/*_point.dbf"))
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/*_tic.dbf"))
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/blocka_d_polygon.dbf")) #ok
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/foresta_d_polygon.dbf")) #ok
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/rivera_d_polygon.dbf")) #ok
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/streetbuf_arc.dbf")) #not ok
    #filenames += map(lambda x: x[0:-4], glob.glob("../bj-shapefiles-2006/streetbuf_polygon.dbf")) #ok


    #beijingmap.load_roads(filenames)
    ##beijingmap.load_road_network('road_network.osm_300')
    beijingmap.load_road_network('merge_roads.osm.5_new')
    ####beijingmap.load_road_network('merge_roads.osm.5_test')
    #beijingmap.load_road_network('draw_map_little_than100')
    #beijingmap.load_road_seg('13301156450.mapmatch.100_0_100')
    #beijingmap.load_road_seg('draw_map_rm100')
    #beijingmap.load_road_network2('merge_roads.5')
    logger.debug("filenames:%s",filenames)

    # stat map roads
    logger.info("map_info_start::")
    beijingmap.stat_map_info()
    logger.info("map_info_end::")

    # load trajectory

    # make road index

    # generate road graph

    # map matching

    master = Tk()
    map_canvas = MapCanvas(beijingmap, master)
    #map_canvas.clean_road()
    #map_canvas.draw_map()
    #map_canvas.draw_road_network("road_network.new.osm")
    #map_canvas.draw_road_network_new("road_network_add_point_5.new")
    #map_canvas.draw_road_network_new("road_network.new.osm")
    #map_canvas.draw_road_network_new("split.300.2")
    #map_canvas.read_road_network("split.300.2")
    #map_canvas.draw_map()
    #map_canvas.find_crossing()
    #map_canvas.draw_crossing()
    #for i in range(50):
    #     map_canvas.draw_random_trajectory()

    #    '''filename=road_network_add_point.new'''
    map_canvas.draw_map()
    #map_canvas.write_roadid()
    #map_canvas.find_crossing()
    #map_canvas.draw_crossing()
    
    #for i in range(50):
    #    map_canvas.draw_random_trajectory()
    #map_canvas.insert_postgres()
    
    #map_canvas.draw_trajectory("./data/13301104003.traj", "green")
    #map_canvas.draw_trajectory("./data/Traj_log", "green")
    #map_canvas.draw_trajectory("13301104001.20101101.traj", "red")
    #map_canvas.draw_trajectory("13301104002.20101101.traj", "yellow")
    #####map_canvas.draw_random_traj_file('random_traj.0611.10_out')
    #map_canvas.draw_trajectory_without_time("gps", "green")
    #map_canvas.draw_trajectory_without_time("data/460020367335134.traj_log.2", "green")
    #map_canvas.draw_trajectory_without_time("data/Traj_log.2", "red")
    #map_canvas.draw_trajectory_without_time("2cp.txt", "green")
    ###map_canvas.draw_mapmatch_without_time("13301156449.mapmatch.100","green")
    ###map_canvas.draw_mapmatch_without_time("13301156449.mapmatch.200","green")
    ###map_canvas.draw_mapmatch_without_time("13301156449.mapmatch.300","green")
    ###map_canvas.draw_mapmatch_without_time("13301156449.mapmatch.400","green")
    ###map_canvas.draw_mapmatch_without_time("13301156449.mapmatch.500","green")
    #*#map_canvas.draw_mapmatch_without_time("13301104001.l","green")
    '''
    map_canvas.draw_mapmatch_without_time("diff_road/13301156450.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156451.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156452.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156453.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156454.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156455.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156457.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156458.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156459.mapmatch.100_0","green")
    
    map_canvas.draw_mapmatch_without_time("diff_road/13301156460.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156461.mapmatch.100_0","green")
    map_canvas.draw_mapmatch_without_time("diff_road/13301156462.mapmatch.100_0","green")
    '''
    ##map_canvas.draw_mapmatch_without_time("diff_road/13301156463.mapmatch.100_0","green")
    '''
    con = ConnPostgreSQL(host='192.168.1.236')
    sql = """
select t.traj_id
from traj_without_rid_line_%s t
where ST_DWithin(
        ST_Transform(GeomFromText('%s',4326),26986),
        ST_Transform(t.traj_point,26986),
        %s 
);
"""% ('10000','POINT(116.3427505 39.85953522)',100)
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
        
        traj_point = con.extract_traj(result)
        map_canvas.draw_traj(traj_point,traj_color="black")
        
        '''
    #map_canvas.draw_mapmatch_without_time("diff_road/13301156465.mapmatch.100_0","green")
    #map_canvas.draw_mapmatch_without_time("13301156449.mapmatch.600","green")
    #map_canvas.draw_mapmatch_without_time("13301104001.mapmatch.cp","green")
    #map_canvas.draw_mapmatch_without_time("13301104003.mapmatch.cp","green")
    #map_canvas.draw_mapmatch_without_time("13301104007.mapmatch.cp","green")
    #map_canvas.draw_mapmatch_without_time("13301104009.mapmatch.cp","green")
    
    #map_canvas.draw_mapmatch_without_time("13301104001.mapmatch.300","green")
    #map_canvas.draw_mapmatch_without_time("13301104001.mapmatch.400","green")
    #map_canvas.draw_mapmatch_without_time("13301104001.mapmatch.500","green")
    #map_canvas.draw_mapmatch_without_time("13301104001.mapmatch.600","green")
    #map_canvas.draw_mapmatch_without_time("13301104001.mapmatch.700","green")
    
    #map_canvas.draw_mapmatch_without_time("13301104003.mapmatch.300","green")
    #map_canvas.draw_mapmatch_without_time("13301104003.mapmatch.400","green")
    #map_canvas.draw_mapmatch_without_time("13301104003.mapmatch.500","green")
    #map_canvas.draw_mapmatch_without_time("13301104003.mapmatch.600","green")
    #map_canvas.draw_mapmatch_without_time("13301104003.mapmatch.700","green")
    #map_canvas.draw_mapmatch_without_time("miss_points_50000_100","green")
    #map_canvas.draw_trajectory("13331159428.txt", "yellow")
    ##map_canvas.draw_road_speed("l_road_id_speed_new")
    #map_canvas.draw_road_speed("road_speed")
    #map_canvas.write_roadid()
    #map_canvas.get_time_from('query_1.txt')
    #map_canvas.draw_query('test_points')
    #map_canvas.draw_query('test_points_2')
    #map_canvas.draw_query('test_points_speed_10')

    ##mapmatching
    #map_canvas.split_roads_to_grid()
    #map_canvas.draw_grid()
    #map_canvas.draw_trajectory("./data/13301104001.20101101_traj","green")    
    #map_canvas.draw_map_matching_trajectory("./data/13301104001.20101101_traj")
    #map_canvas.get_map_matching_trajectory("l_20101102.all.sort")
    #map_canvas.draw_map_without_time("l_20101101_13301104001.all.sort","green")
    #map_canvas.get_map_matching_trajectory("l_20101101_13301104001.all.sort")

    mainloop()
