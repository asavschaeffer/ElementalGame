from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    NodePath, GeomNode, Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter,
    GeomTriangles, Point3, Vec3, Vec4, CollideMask, BitMask32, CollisionNode,
    CollisionSphere, AmbientLight, DirectionalLight, Texture, TextNode, TextureStage,
    LVector3f, TransformState, LPoint3f
)
import numpy as np
from opensimplex import OpenSimplex
import random
import math
from collections import deque
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class ProceduralWorld(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        logger.info("Initializing ProceduralWorld")
        
        self.MAP_SIZE = 1024
        self.HEIGHT_SCALE = 150
        self.WATER_LEVEL = 20
        self.GRID_SIZE = 128
        logger.debug(f"World parameters set: MAP_SIZE={self.MAP_SIZE}, HEIGHT_SCALE={self.HEIGHT_SCALE}, "
                    f"WATER_LEVEL={self.WATER_LEVEL}, GRID_SIZE={self.GRID_SIZE}")
        
        self.height_noise = OpenSimplex(seed=random.randint(0, 1000000))
        self.detail_noise = OpenSimplex(seed=random.randint(0, 1000000))
        self.moisture_noise = OpenSimplex(seed=random.randint(0, 1000000))
        self.forest_noise = OpenSimplex(seed=random.randint(0, 1000000))
        logger.debug("Noise generators initialized with random seeds")
        
        self.disableMouse()
        self.camera.setPos(self.MAP_SIZE/2, -self.MAP_SIZE/2, 200)
        self.camera.lookAt(self.MAP_SIZE/2, self.MAP_SIZE/2, 0)
        logger.info("Camera initialized at position (%d, %d, %d)", 
                   self.MAP_SIZE/2, -self.MAP_SIZE/2, 200)
        
        self.setup_lighting()
        self.heightmap = self.generate_heightmap()
        self.terrain = self.create_terrain()
        self.water = self.create_water()
        self.forest_areas = self.identify_forest_areas()
        self.place_trees()
        self.place_rocks()
        self.spawn_points = self.find_spawn_points()
        self.mark_spawn_points()
        self.setup_controls()
        logger.info("World generation completed")

    def setup_lighting(self):
        logger.info("Setting up lighting")
        ambient_light = AmbientLight("ambient_light")
        ambient_light.setColor(Vec4(0.4, 0.4, 0.4, 1))
        ambient_node = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_node)
        logger.debug("Ambient light set with color (0.4, 0.4, 0.4, 1)")
        
        directional_light = DirectionalLight("directional_light")
        directional_light.setColor(Vec4(0.8, 0.8, 0.7, 1))
        directional_light.setDirection(Vec3(-0.5, -0.5, -0.8))
        directional_node = self.render.attachNewNode(directional_light)
        self.render.setLight(directional_node)
        logger.debug("Directional light set with color (0.8, 0.8, 0.7, 1) and direction (-0.5, -0.5, -0.8)")

    def generate_heightmap(self):
        logger.info("Generating heightmap")
        heightmap = np.zeros((self.GRID_SIZE, self.GRID_SIZE))
        octaves, persistence, lacunarity, scale = 6, 0.5, 2.0, 0.007
        
        mountain_range1_center = (0.05, 0.5)
        mountain_range1_width = 0.2
        mountain_range1_height = 1.0
        
        mountain_range2_center = (0.7, 0.3)
        mountain_range2_width = 0.3
        mountain_range2_height = 0.8
        
        river_start = (mountain_range2_center[0], mountain_range2_center[1])
        river_end = (0.5, 1.0)
        
        logger.debug("Starting terrain generation loop")
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                nx, ny = x / self.GRID_SIZE, y / self.GRID_SIZE
                height = 0
                amplitude, frequency = 1.0, 1.0
                for i in range(octaves):
                    sample_x = nx * frequency * self.GRID_SIZE * scale
                    sample_y = ny * frequency * self.GRID_SIZE * scale
                    height += self.height_noise.noise2(sample_x, sample_y) * amplitude
                    amplitude *= persistence
                    frequency *= lacunarity
                
                height = (height + 1) / 2
                
                dist1 = math.sqrt((nx - mountain_range1_center[0])**2 + (ny - mountain_range1_center[1])**2)
                mountain1 = max(0, 1 - dist1 / mountain_range1_width) ** 2 * mountain_range1_height
                
                dist2 = math.sqrt((nx - mountain_range2_center[0])**2 + (ny - mountain_range2_center[1])**2)
                mountain2 = max(0, 1 - dist2 / mountain_range2_width) ** 2 * mountain_range2_height
                
                combined_height = height * 0.4 + max(mountain1, mountain2)
                
                if nx > 0.7:
                    beach_factor = (nx - 0.7) / 0.3
                    combined_height *= max(0, 1 - beach_factor * 1.5)
                    if 0.7 < nx < 0.85:
                        coastal_noise = self.height_noise.noise2(nx * 30, ny * 30) * 0.1
                        combined_height += coastal_noise * (1 - beach_factor)
                
                if 0.3 < nx < 0.7 and 0.3 < ny < 0.7:
                    hills_noise = self.detail_noise.noise2(nx * 15, ny * 15) * 0.15
                    combined_height += hills_noise
                
                heightmap[y, x] = combined_height * self.HEIGHT_SCALE
        
        logger.debug("Carving river")
        self.carve_river(heightmap, 
                        (int(river_start[0] * self.GRID_SIZE), int(river_start[1] * self.GRID_SIZE)),
                        (int(river_end[0] * self.GRID_SIZE), int(river_end[1] * self.GRID_SIZE)))
        
        logger.info("Heightmap generation completed")
        return heightmap

    def carve_river(self, heightmap, start, end):
        logger.info("Carving river from %s to %s", start, end)
        
        open_set = [(0, start)]
        closed_set = set()
        came_from = {}
        g_score = {start: 0}
        f_score = {start: math.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)}
        
        while open_set:
            _, current = min(open_set, key=lambda x: x[0])
            open_set = [item for item in open_set if item[1] != current]
            
            if current == end:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                
                river_width = 3
                logger.debug("Carving river path with width %d", river_width)
                for pos in path:
                    x, y = pos
                    heightmap[y, x] = max(self.WATER_LEVEL - 2, heightmap[y, x] * 0.6)
                    for dx in range(-river_width, river_width + 1):
                        for dy in range(-river_width, river_width + 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.GRID_SIZE and 0 <= ny < self.GRID_SIZE:
                                dist = math.sqrt(dx**2 + dy**2)
                                if dist <= river_width:
                                    influence = 1 - (dist / river_width)
                                    new_height = heightmap[ny, nx] * (1 - influence * 0.5)
                                    if dist < river_width * 0.7:
                                        new_height = min(new_height, self.WATER_LEVEL - 1)
                                    heightmap[ny, nx] = new_height
                logger.info("River carving completed")
                return
            
            closed_set.add(current)
            for nx, ny in [(current[0] + dx, current[1] + dy) 
                          for dx, dy in [(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]
                          if 0 <= current[0] + dx < self.GRID_SIZE and 0 <= current[1] + dy < self.GRID_SIZE]:
                if (nx, ny) in closed_set:
                    continue
                
                height_current = heightmap[current[1], current[0]]
                height_neighbor = heightmap[ny, nx]
                height_factor = max(0, min(5, (height_current - height_neighbor) + 2))
                tentative_g = g_score.get(current, float('inf')) + 1 + (5 / (height_factor + 1))
                
                if any(n == (nx, ny) for _, n in open_set) and tentative_g >= g_score.get((nx, ny), float('inf')):
                    continue
                
                came_from[(nx, ny)] = current
                g_score[(nx, ny)] = tentative_g
                f_score[(nx, ny)] = tentative_g + math.sqrt((nx - end[0])**2 + (ny - end[1])**2)
                if not any(n == (nx, ny) for _, n in open_set):
                    open_set.append((f_score[(nx, ny)], (nx, ny)))

    def create_terrain(self):
        logger.info("Creating terrain mesh")
        format = GeomVertexFormat.getV3n3c4t2()
        vertex_data = GeomVertexData("terrain", format, Geom.UHStatic)
        
        vertex = GeomVertexWriter(vertex_data, "vertex")
        normal = GeomVertexWriter(vertex_data, "normal")
        color = GeomVertexWriter(vertex_data, "color")
        texcoord = GeomVertexWriter(vertex_data, "texcoord")
        
        scale_x = self.MAP_SIZE / (self.GRID_SIZE - 1)
        scale_y = self.MAP_SIZE / (self.GRID_SIZE - 1)
        
        logger.debug("Adding terrain vertices")
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                height = self.heightmap[y, x]
                vertex.addData3f(x * scale_x, y * scale_y, height)
                nx, ny, nz = self.calculate_normal(x, y)
                normal.addData3f(nx, ny, nz)
                r, g, b = self.get_terrain_color(x, y, height)
                color.addData4f(r, g, b, 1.0)
                texcoord.addData2f(x / (self.GRID_SIZE - 1), y / (self.GRID_SIZE - 1))
        
        logger.debug("Creating terrain triangles")
        tris = GeomTriangles(Geom.UHStatic)
        for y in range(self.GRID_SIZE - 1):
            for x in range(self.GRID_SIZE - 1):
                v0 = y * self.GRID_SIZE + x
                v1 = v0 + 1
                v2 = (y + 1) * self.GRID_SIZE + x
                v3 = v2 + 1
                tris.addVertices(v0, v1, v2)
                tris.addVertices(v2, v1, v3)
        
        geom = Geom(vertex_data)
        geom.addPrimitive(tris)
        node = GeomNode("terrain")
        node.addGeom(geom)
        terrain = self.render.attachNewNode(node)
        logger.info("Terrain mesh creation completed")
        return terrain

    def calculate_normal(self, x, y):
        scale_x = self.MAP_SIZE / (self.GRID_SIZE - 1)
        scale_y = self.MAP_SIZE / (self.GRID_SIZE - 1)
        h = self.heightmap[y, x]
        
        h_dx = (self.heightmap[y, x+1] if x < self.GRID_SIZE-1 else h) - (self.heightmap[y, x-1] if x > 0 else h)
        dx = (2 * scale_x if 0 < x < self.GRID_SIZE-1 else scale_x)
        
        h_dy = (self.heightmap[y+1, x] if y < self.GRID_SIZE-1 else h) - (self.heightmap[y-1, x] if y > 0 else h)
        dy = (2 * scale_y if 0 < y < self.GRID_SIZE-1 else scale_y)
        
        nx, ny, nz = -h_dx / dx, -h_dy / dy, 1.0
        length = math.sqrt(nx*nx + ny*ny + nz*nz)
        if length > 0:
            nx, ny, nz = nx/length, ny/length, nz/length
        return nx, ny, nz

    def get_terrain_color(self, x, y, height):
        nx, ny = x / self.GRID_SIZE, y / self.GRID_SIZE
        moisture = (self.moisture_noise.noise2(nx * 5, ny * 5) + 1) / 2
        
        colors = {
            'water_deep': (0.0, 0.1, 0.4),
            'water_shallow': (0.0, 0.4, 0.7),
            'sand': (0.8, 0.7, 0.5),
            'grass_dry': (0.5, 0.7, 0.3),
            'grass_lush': (0.3, 0.8, 0.2),
            'rock': (0.5, 0.5, 0.5),
            'snow': (0.9, 0.9, 0.95)
        }
        
        if height < self.WATER_LEVEL - 5:
            return colors['water_deep']
        elif height < self.WATER_LEVEL:
            t = (height - (self.WATER_LEVEL - 5)) / 5
            return self.lerp_color(colors['water_deep'], colors['water_shallow'], t)
        elif height < self.WATER_LEVEL + 2:
            return colors['sand']
        elif height < self.HEIGHT_SCALE * 0.4:
            return self.lerp_color(colors['grass_dry'], colors['grass_lush'], moisture)
        elif height < self.HEIGHT_SCALE * 0.7:
            t = (height - self.HEIGHT_SCALE * 0.4) / (self.HEIGHT_SCALE * 0.3)
            return self.lerp_color(colors['grass_lush'], colors['rock'], t)
        elif height < self.HEIGHT_SCALE * 0.9:
            return colors['rock']
        else:
            t = (height - self.HEIGHT_SCALE * 0.9) / (self.HEIGHT_SCALE * 0.1)
            return self.lerp_color(colors['rock'], colors['snow'], t)

    def lerp_color(self, color1, color2, t):
        t = max(0.0, min(1.0, t))
        return tuple(c1 * (1 - t) + c2 * t for c1, c2 in zip(color1, color2))

    def create_water(self):
        logger.info("Creating water plane")
        format = GeomVertexFormat.getV3n3c4t2()
        vertex_data = GeomVertexData("water", format, Geom.UHStatic)
        
        vertex = GeomVertexWriter(vertex_data, "vertex")
        normal = GeomVertexWriter(vertex_data, "normal")
        color = GeomVertexWriter(vertex_data, "color")
        texcoord = GeomVertexWriter(vertex_data, "texcoord")
        
        corners = [(0, 0), (self.MAP_SIZE, 0), (0, self.MAP_SIZE), (self.MAP_SIZE, self.MAP_SIZE)]
        for x, y in corners:
            vertex.addData3f(x, y, self.WATER_LEVEL)
            normal.addData3f(0, 0, 1)
            color.addData4f(0.2, 0.5, 0.8, 0.7)
            texcoord.addData2f(x / self.MAP_SIZE, y / self.MAP_SIZE)
        
        tris = GeomTriangles(Geom.UHStatic)
        tris.addVertices(0, 1, 2)
        tris.addVertices(2, 1, 3)
        
        geom = Geom(vertex_data)
        geom.addPrimitive(tris)
        node = GeomNode("water")
        node.addGeom(geom)
        water = self.render.attachNewNode(node)
        water.setTransparency(True)
        logger.info("Water plane created")
        return water

    def identify_forest_areas(self):
        logger.info("Identifying forest areas")
        forest_areas = []
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                height = self.heightmap[y, x]
                if self.WATER_LEVEL + 5 < height < self.HEIGHT_SCALE * 0.5:
                    nx, ny = x / self.GRID_SIZE, y / self.GRID_SIZE
                    forest_density = (self.forest_noise.noise2(nx * 10, ny * 10) + 1) / 2
                    if forest_density > 0.6:
                        forest_areas.append((x, y, forest_density))
        logger.info("Found %d potential forest areas", len(forest_areas))
        return forest_areas

    def place_trees(self):
        logger.info("Placing trees")
        max_trees = 200
        selected_areas = (random.sample(self.forest_areas, max_trees) 
                         if len(self.forest_areas) > max_trees else self.forest_areas)
        
        scale_x = self.MAP_SIZE / (self.GRID_SIZE - 1)
        scale_y = self.MAP_SIZE / (self.GRID_SIZE - 1)
        
        for x, y, density in selected_areas:
            height = self.heightmap[y, x]
            world_x, world_y = x * scale_x, y * scale_y
            
            tree = self.render.attachNewNode("tree")
            tree_height = 5 + density * 5
            trunk_height = tree_height * 0.6
            
            trunk = self.create_cylinder(tree_height * 0.06, trunk_height, (0.5, 0.3, 0.2, 1.0))
            trunk.reparentTo(tree)
            trunk.setPos(0, 0, trunk_height / 2)
            
            foliage = self.create_cone(tree_height * 0.3, tree_height - trunk_height, (0.2, 0.8, 0.2, 1.0))
            foliage.reparentTo(tree)
            foliage.setPos(0, 0, trunk_height)
            
            tree.setPos(world_x, world_y, height)
            tree.setH(random.uniform(0, 360))
            tree.setScale(0.8 + density * 0.4)
        
        logger.info("Placed %d trees", len(selected_areas))

    def create_cylinder(self, radius, height, color):
        sides = 8
        format = GeomVertexFormat.getV3n3c4()
        vertex_data = GeomVertexData("cylinder", format, Geom.UHStatic)
        
        vertex = GeomVertexWriter(vertex_data, "vertex")
        normal = GeomVertexWriter(vertex_data, "normal")
        color_writer = GeomVertexWriter(vertex_data, "color")
        
        vertex.addData3f(0, 0, height / 2)
        vertex.addData3f(0, 0, -height / 2)
        normal.addData3f(0, 0, 1)
        normal.addData3f(0, 0, -1)
        color_writer.addData4f(*color)
        color_writer.addData4f(*color)
        
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x, y = radius * math.cos(angle), radius * math.sin(angle)
            vertex.addData3f(x, y, height / 2)
            normal.addData3f(0, 0, 1)
            color_writer.addData4f(*color)
            vertex.addData3f(x, y, -height / 2)
            normal.addData3f(0, 0, -1)
            color_writer.addData4f(*color)
            vertex.addData3f(x, y, height / 2)
            normal.addData3f(x, y, 0)
            color_writer.addData4f(*color)
            vertex.addData3f(x, y, -height / 2)
            normal.addData3f(x, y, 0)
            color_writer.addData4f(*color)
        
        tris = GeomTriangles(Geom.UHStatic)
        for i in range(sides):
            v1, v2 = 2 + i * 4, 2 + ((i + 1) % sides) * 4
            tris.addVertices(0, v1, v2)
            v1, v2 = 3 + i * 4, 3 + ((i + 1) % sides) * 4
            tris.addVertices(1, v2, v1)
            v1, v2, v3, v4 = 4 + i * 4, 5 + i * 4, 4 + ((i + 1) % sides) * 4, 5 + ((i + 1) % sides) * 4
            tris.addVertices(v1, v2, v3)
            tris.addVertices(v3, v2, v4)
        
        geom = Geom(vertex_data)
        geom.addPrimitive(tris)
        node = GeomNode("cylinder")
        node.addGeom(geom)
        return NodePath(node)

    def create_cone(self, radius, height, color):
        sides = 8
        format = GeomVertexFormat.getV3n3c4()
        vertex_data = GeomVertexData("cone", format, Geom.UHStatic)
        
        vertex = GeomVertexWriter(vertex_data, "vertex")
        normal = GeomVertexWriter(vertex_data, "normal")
        color_writer = GeomVertexWriter(vertex_data, "color")
        
        vertex.addData3f(0, 0, height)
        vertex.addData3f(0, 0, 0)
        normal.addData3f(0, 0, 1)
        normal.addData3f(0, 0, -1)
        color_writer.addData4f(*color)
        color_writer.addData4f(*color)
        
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x, y = radius * math.cos(angle), radius * math.sin(angle)
            vertex.addData3f(x, y, 0)
            normal.addData3f(0, 0, -1)
            color_writer.addData4f(*color)
            vertex.addData3f(x, y, 0)
            side_normal = Vec3(x, y, height/2)
            side_normal.normalize()
            normal.addData3f(side_normal)
            color_writer.addData4f(*color)
        
        tris = GeomTriangles(Geom.UHStatic)
        for i in range(sides):
            v1, v2 = 2 + i * 2, 2 + ((i + 1) % sides) * 2
            tris.addVertices(1, v2, v1)
            v1, v2 = 3 + i * 2, 3 + ((i + 1) % sides) * 2
            tris.addVertices(0, v1, v2)
        
        geom = Geom(vertex_data)
        geom.addPrimitive(tris)
        node = GeomNode("cone")
        node.addGeom(geom)
        return NodePath(node)

    def place_rocks(self):
        logger.info("Placing rocks")
        num_rocks = 100
        scale_x = self.MAP_SIZE / (self.GRID_SIZE - 1)
        scale_y = self.MAP_SIZE / (self.GRID_SIZE - 1)
        
        placed = 0
        for _ in range(num_rocks):
            x, y = random.randint(0, self.GRID_SIZE - 1), random.randint(0, self.GRID_SIZE - 1)
            height = self.heightmap[y, x]
            if height < self.WATER_LEVEL:
                logger.debug("Skipping rock placement at (%d, %d) - underwater", x, y)
                continue
            
            world_x, world_y = x * scale_x, y * scale_y
            rock = self.create_rock()
            rock.setPos(world_x, world_y, height)
            rock.setH(random.uniform(0, 360))
            rock_scale = random.uniform(0.5, 3.0)
            rock.setScale(rock_scale)
            placed += 1
        
        logger.info("Placed %d rocks", placed)

    def create_rock(self):
        logger.debug("Creating rock mesh")
        sphere_rad = 1.0
        t = (1.0 + math.sqrt(5.0)) / 2.0
        vertices = [
            (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
            (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
            (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)
        ]
        vertices = [(x * sphere_rad / math.sqrt(x*x + y*y + z*z), 
                    y * sphere_rad / math.sqrt(x*x + y*y + z*z), 
                    z * sphere_rad / math.sqrt(x*x + y*y + z*z)) 
                   for x, y, z in vertices]
        
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
        ]
        
        rock_noise = OpenSimplex(seed=random.randint(0, 1000000))
        noisy_vertices = []
        for x, y, z in vertices:
            noise_val = rock_noise.noise3(x * 2, y * 2, z * 2) * 0.3
            new_radius = sphere_rad * (1.0 + noise_val)
            noisy_vertices.append((
                x * new_radius / sphere_rad,
                y * new_radius / sphere_rad,
                z * new_radius / sphere_rad
            ))
        
        format = GeomVertexFormat.getV3n3c4()
        vertex_data = GeomVertexData("rock", format, Geom.UHStatic)
        vertex = GeomVertexWriter(vertex_data, "vertex")
        normal = GeomVertexWriter(vertex_data, "normal")
        color_writer = GeomVertexWriter(vertex_data, "color")
        
        rock_colors = [(0.5, 0.5, 0.5, 1.0), (0.4, 0.4, 0.4, 1.0), (0.6, 0.6, 0.6, 1.0), (0.45, 0.45, 0.48, 1.0)]
        for v in noisy_vertices:
            vertex.addData3f(*v)
            norm = Vec3(*v)
            norm.normalize()
            normal.addData3f(norm)
            color_writer.addData4f(*random.choice(rock_colors))
        
        tris = GeomTriangles(Geom.UHStatic)
        for face in faces:
            tris.addVertices(*face)
        
        geom = Geom(vertex_data)
        geom.addPrimitive(tris)
        node = GeomNode("rock")
        node.addGeom(geom)
        logger.debug("Rock mesh created")
        return self.render.attachNewNode(node)

    def find_spawn_points(self):
        logger.info("Finding spawn points")
        walkable_points = []
        scale_x = self.MAP_SIZE / (self.GRID_SIZE - 1)
        scale_y = self.MAP_SIZE / (self.GRID_SIZE - 1)
        
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                height = self.heightmap[y, x]
                if height <= self.WATER_LEVEL or height > self.HEIGHT_SCALE * 0.7:
                    continue
                nx, ny, nz = self.calculate_normal(x, y)
                slope = math.acos(nz) * 180 / math.pi
                if slope > 30:
                    continue
                world_x, world_y = x * scale_x, y * scale_y
                walkable_points.append((world_x, world_y, height))
        
        if len(walkable_points) < 2:
            logger.warning("Not enough walkable points found, using default spawn points")
            return [
                (self.MAP_SIZE * 0.25, self.MAP_SIZE * 0.25, self.WATER_LEVEL + 10),
                (self.MAP_SIZE * 0.75, self.MAP_SIZE * 0.75, self.WATER_LEVEL + 10)
            ]
        
        sample_points = random.sample(walkable_points, min(1000, len(walkable_points)))
        max_distance = 0
        spawn_points = None
        
        for i, p1 in enumerate(sample_points):
            for p2 in sample_points[i+1:]:
                dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                if dist > max_distance:
                    max_distance = dist
                    spawn_points = [p1, p2]
        
        logger.info("Found %d spawn points with maximum distance %f", len(spawn_points), max_distance)
        return spawn_points

    def mark_spawn_points(self):
        logger.info("Marking spawn points")
        for i, point in enumerate(self.spawn_points):
            color = (1.0, 0.0, 0.0, 1.0) if i == 0 else (0.0, 0.0, 1.0, 1.0)
            marker = self.create_cylinder(2, 15, color)
            marker.reparentTo(self.render)
            marker.setPos(point[0], point[1], point[2])
            
            sphere = self.loader.loadModel("models/misc/sphere")
            if not sphere:
                logger.error("Failed to load sphere model for spawn point %d", i)
                continue
            sphere.reparentTo(marker)
            sphere.setPos(0, 0, 15)
            sphere.setScale(3)
            sphere.setColor(*color)
            
            text_node = TextNode(f'spawn_text_{i}')
            text_node.setText(f"Spawn {i+1}")
            text_node.setTextColor(1, 1, 1, 1)
            text_node.setAlign(TextNode.ACenter)
            text_node_path = self.render.attachNewNode(text_node)
            text_node_path.setPos(point[0], point[1], point[2] + 20)
            text_node_path.setScale(5)
            text_node_path.setBillboardPointEye()
            logger.debug("Spawn point %d marked at position %s", i, point)

    def setup_controls(self):
        logger.info("Setting up controls")
        self.keyMap = {
            "forward": False, "backward": False, "left": False, "right": False,
            "up": False, "down": False, "cam-left": False, "cam-right": False
        }
        
        key_mappings = {
            "escape": sys.exit,
            "w": ("forward", True), "w-up": ("forward", False),
            "s": ("backward", True), "s-up": ("backward", False),
            "a": ("left", True), "a-up": ("left", False),
            "d": ("right", True), "d-up": ("right", False),
            "space": ("up", True), "space-up": ("up", False),
            "shift": ("down", True), "shift-up": ("down", False),
            "arrow_left": ("cam-left", True), "arrow_left-up": ("cam-left", False),
            "arrow_right": ("cam-right", True), "arrow_right-up": ("cam-right", False)
        }
        
        for key, action in key_mappings.items():
            if callable(action):
                self.accept(key, action)
            else:
                self.accept(key, self.updateKeyMap, [action[0], action[1]])
        
        self.taskMgr.add(self.move, "moveTask")
        logger.debug("Control mappings established")

    def updateKeyMap(self, key, value):
        self.keyMap[key] = value
        logger.debug("Key %s updated to %s", key, value)

    def move(self, task):
        dt = globalClock.getDt()
        speed = 100.0
        pos = self.camera.getPos()
        h = self.camera.getH()
        
        movements = {
            "forward": self.camera.getMat().getRow3(1) * speed * dt,
            "backward": -self.camera.getMat().getRow3(1) * speed * dt,
            "left": -self.camera.getMat().getRow3(0) * speed * dt,
            "right": self.camera.getMat().getRow3(0) * speed * dt,
            "up": LVector3f(0, 0, speed * dt),
            "down": LVector3f(0, 0, -speed * dt)
        }
        
        for key, vec in movements.items():
            if self.keyMap[key]:
                pos += vec
        
        if self.keyMap["cam-left"]:
            h += 50 * dt
        if self.keyMap["cam-right"]:
            h -= 50 * dt
        
        self.camera.setPos(pos)
        self.camera.setH(h)
        return task.cont

if __name__ == "__main__":
    logger.info("Starting application")
    try:
        app = ProceduralWorld()
        app.run()
    except Exception as e:
        logger.error("Application failed: %s", str(e), exc_info=True)
        sys.exit(1)