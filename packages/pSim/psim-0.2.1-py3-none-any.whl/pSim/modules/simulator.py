import numpy as np
from pSim.pybox2d.library.Box2D import b2ContactListener
from pSim.pybox2d.library.Box2D.b2 import world


class ContactListener(b2ContactListener):
    def __init__(self):
        super().__init__()
        self.collision_robot_ball = False
        self.collision_robot_wall = False

    def BeginContact(self, contact):
        bodyA = contact.fixtureA.body
        bodyB = contact.fixtureB.body
        if (
            bodyA.userData["type"] == "robot"
            and bodyB.userData["type"] == "ball"
            or bodyA.userData["type"] == "ball"
            and bodyB.userData["type"] == "robot"
        ):
            self.collision_robot_ball = True

        if (
            bodyA.userData["type"] == "robot"
            and bodyB.userData["type"] == "wall"
            or bodyA.userData["type"] == "wall"
            and bodyB.userData["type"] == "robot"
        ):
            self.collision_robot_wall = True


class Simulator:
    def __init__(self, field_size=(1.70, 1.30), r=0.025, b=0.075, max_wheel=30):
        self.field_size = field_size
        self.world = world(gravity=(0, 0), doSleep=True)

        self.walls_body = None

        self.robots_agent = None
        self.robots_adversary = None
        self.ball_body = None

        self.robot_size = 0.08
        self.ball_radius = 0.02125

        self.vx, self.vy = 0, 0
        self.r, self.b = r, b
        self.max_wheel = max_wheel
        self.max_v, self.max_w = max_wheel * r, 2 * max_wheel * r / b

        # Contact listener
        self.contact_listener = ContactListener()
        self.world.contactListener = self.contact_listener

    def create_walls(self):
        wall_thickness = 0.05
        half_width = self.field_size[0] / 2
        half_height = self.field_size[1] / 2

        walls = [
            (
                (0, half_height + wall_thickness / 2),
                (half_width, wall_thickness / 2),
            ),  # Top
            (
                (0, -half_height - wall_thickness / 2),
                (half_width, wall_thickness / 2),
            ),  # Buttom
            (
                (-half_width - wall_thickness / 2, 0),
                (wall_thickness / 2, half_height),
            ),  # Left
            (
                (half_width + wall_thickness / 2, 0),
                (wall_thickness / 2, half_height),
            ),  # Right
        ]

        outside_corners = [
            (
                (-half_width + 0.05, 0.40 / 2 + 0.45 / 2),
                (0.05, 0.45 / 2),
            ),  # Top Left Corner
            (
                (-half_width + 0.05, -0.40 / 2 - 0.45 / 2),
                (0.05, 0.45 / 2),
            ),  # Buttom Left Corner
            (
                (half_width - 0.05, 0.40 / 2 + 0.45 / 2),
                (0.05, 0.45 / 2),
            ),  # Top Right Corner
            (
                (half_width - 0.05, -0.40 / 2 - 0.45 / 2),
                (0.05, 0.45 / 2),
            ),  # Buttom Right Corner
        ]

        inside_corners = [
            (
                (-half_width + 0.10, half_height - 0.07),
                (-half_width + 0.10, half_height),
                (-half_width + 0.17, half_height),
            ),  # Top Left Corner
            (
                (half_width - 0.10, -half_height + 0.07),
                (half_width - 0.10, -half_height),
                (half_width - 0.17, -half_height),
            ),  # Buttom Right Corner
            (
                (half_width - 0.10, half_height - 0.07),
                (half_width - 0.10, half_height),
                (half_width - 0.17, half_height),
            ),  # Top Right Corner
            (
                (-half_width + 0.10, -half_height + 0.07),
                (-half_width + 0.10, -half_height),
                (-half_width + 0.17, -half_height),
            ),  # Buttom Left Corner
        ]

        for pos, size in walls + outside_corners:
            wall_body = self.world.CreateStaticBody(position=pos)
            wall_body.CreatePolygonFixture(box=size, density=0.0, friction=0.8)
            wall_body.userData = {"type": "wall"}

        for points in inside_corners:
            wall_body = self.world.CreateStaticBody(position=(0, 0))
            wall_body.CreatePolygonFixture(vertices=points, density=0.0, friction=0.8)
            wall_body.userData = {"type": "wall"}

        self.walls_body = wall_body

    def create_robot(self, x, y, angle):
        body = self.world.CreateDynamicBody(position=(x, y), angle=angle)
        body.CreatePolygonFixture(
            box=(self.robot_size / 2, self.robot_size / 2),
            density=416.6667,
            friction=0.8,
        )
        body.userData = {"type": "robot"}
        return body

    def create_ball(self, x, y):
        body = self.world.CreateDynamicBody(position=(x, y), bullet=True)
        body.CreateCircleFixture(
            radius=self.ball_radius, density=1139.55, friction=0.3, restitution=0.25
        )
        body.linearVelocity = (
            np.random.uniform(-self.vx, 0),
            np.random.uniform(-self.vy, self.vy),
        )
        # body.linearVelocity = (
        #     np.random.uniform(-self.vx, self.vx),
        #     np.random.uniform(-self.vy, self.vy),
        # )
        body.userData = {"type": "ball"}
        return body

    def apply_force(self):
        if self.ball_body is not None:
            velocity = self.ball_body.linearVelocity
            friction_coefficient = 0.5
            force = -friction_coefficient * velocity
            self.ball_body.ApplyForce(force, self.ball_body.position, wake=True)

        # Normalize robot angles to [-π, π] range
        for robot in self.robots_agent:
            robot.angle = np.arctan2(np.sin(robot.angle), np.cos(robot.angle))
        for robot in self.robots_adversary:
            robot.angle = np.arctan2(np.sin(robot.angle), np.cos(robot.angle))

    def reset_simulator(self, robots_agent_pose, ball_pos, robots_adversary_pose=None):
        # Destroy objects
        if self.ball_body is not None:
            self.world.DestroyBody(self.ball_body)

        if self.robots_agent is not None:
            for body in self.robots_agent:
                self.world.DestroyBody(body)
            self.robots_agent = None

        if self.robots_adversary is not None:
            for body in self.robots_adversary:
                self.world.DestroyBody(body)
            self.robots_adversary = None

        # Create objects
        if self.walls_body is None:
            self.create_walls()
        self.ball_body = self.create_ball(*ball_pos)
        self.robots_agent = [self.create_robot(*pos) for pos in robots_agent_pose]

        if robots_adversary_pose is not None:
            self.robots_adversary = [self.create_robot(*pos) for pos in robots_adversary_pose]

    def agent_step(self, idx, action):
        norm = np.sum(np.abs(action))
        if norm > 1:
            action = action / norm
        v, w = action * np.array([self.max_v, self.max_w])
        angle = self.robots_agent[idx].angle
        self.robots_agent[idx].linearVelocity = (v * np.cos(angle), v * np.sin(angle))
        self.robots_agent[idx].angularVelocity = w

    def adversary_step(self, idx, action):
        norm = np.sum(np.abs(action))
        if norm > 1:
            action = action / norm
        v, w = action * np.array([self.max_v, self.max_w])
        angle = self.robots_adversary[idx].angle
        self.robots_adversary[idx].linearVelocity = (v * np.cos(angle), v * np.sin(angle))
        self.robots_adversary[idx].angularVelocity = w

    def get_distance(self, idx, object):
        return np.linalg.norm(self.robots_agent[idx].position - object.position)

    def get_diff_angle(self, idx, object):
        idx_object_angle = np.arctan2(
            object.position.y - self.robots_agent[idx].position.y,
            object.position.x - self.robots_agent[idx].position.x,
        )
        diff_angle = idx_object_angle - self.robots_agent[idx].angle
        return np.cos(diff_angle), np.sin(diff_angle)

    def agent_observation(self, idx):
        distance_ball = self.get_distance(idx, self.ball_body)
        distances_agent = [
            self.get_distance(idx, robot)
            for robot in self.robots_agent
            if robot != self.robots_agent[idx]
        ]
        distances_adversary = [self.get_distance(idx, robot) for robot in self.robots_adversary]

        angle_ball = self.get_diff_angle(idx, self.ball_body)
        angle_agent = [
            self.get_diff_angle(idx, robot)
            for robot in self.robots_agent
            if robot != self.robots_agent[idx]
        ]
        angle_adversary = [self.get_diff_angle(idx, robot) for robot in self.robots_adversary]

        cos_angle_agent = [angle[0] for angle in angle_agent]
        sin_angle_agent = [angle[1] for angle in angle_agent]
        cos_angle_adversary = [angle[0] for angle in angle_adversary]
        sin_angle_adversary = [angle[1] for angle in angle_adversary]

        observation = np.array(
            [
                # self observation
                self.robots_agent[idx].position.x,
                self.robots_agent[idx].position.y,
                np.cos(self.robots_agent[idx].angle),
                np.sin(self.robots_agent[idx].angle),
                self.robots_agent[idx].linearVelocity.x,
                self.robots_agent[idx].linearVelocity.y,
                self.robots_agent[idx].angularVelocity,
                # ball observation
                self.ball_body.position.x,
                self.ball_body.position.y,
                self.ball_body.linearVelocity.x,
                self.ball_body.linearVelocity.y,
                # distances
                distance_ball,
                *distances_agent,
                *distances_adversary,
                # # angles
                *angle_ball,
                *cos_angle_agent,
                *sin_angle_agent,
                *cos_angle_adversary,
                *sin_angle_adversary,
            ],
            dtype=np.float32,
        )

        return observation
