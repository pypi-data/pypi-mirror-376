import numpy as np


def biased_round(value):
    """
    Rounds a value to the nearest integer, with a bias to displace off the cusp
    and prevent common oscillation errors
    """
    bias = 1e-10 if value > 0 else -1e-10
    return round(value + bias)


def interpolate_to_length(input_array, n):
    """
    Interpolates an input numpy array to a new array of length n.

    Parameters:
    - input_array: numpy array of arbitrary length.
    - n: the length of the new interpolated array.

    Returns:
    - A new numpy array of length n with values interpolated from the input array.
    """
    # Initialize the new array with zeros
    new_array = np.zeros(n)

    # Indices in the new array where the original values will be placed
    original_indices = np.linspace(0, n - 1, num=len(input_array), dtype=int)

    # Place the original values at the computed indices
    new_array[original_indices] = input_array

    # Interpolate the values for the indices in between
    for i in range(1, len(original_indices)):
        start_idx, end_idx = original_indices[i - 1], original_indices[i]
        new_array[start_idx : end_idx + 1] = np.linspace(
            input_array[i - 1], input_array[i], end_idx - start_idx + 1
        )

    return new_array


def tween(a, b, t):
    """
    Tweens between two values a and b by a factor t.

    Parameters:
    - a: the starting value.
    - b: the ending value.
    - t: the factor to tween between a and b.
    """
    return a + (b - a) * t


class Pose:
    # we need a class to represent a 2d pose and all of its dynamics
    # this class will be used to represent
    #  life of the active render and manipulation of the pose in seconds
    # vector values all of the range -1 to 1
    #  pos (x,y), ang and size
    # vector values of the range of 0 to 1\
    #  alpha the blend alpha of the related object
    # delta values of increase in vector values over time on a second unit
    #  d_pos in a vector of direction and value per sec
    #  d_rotation as a value per sec
    #  d_size as a value per sec
    #  d_alpha as a value per sec
    # limit values of vector values and what happens when they ge there
    #  position, rotation and size, alpha
    # modifiers to the delta values over time
    #  m_pos accel dec linear and angular
    #  m_rotation rate of change of d_rotation
    #  m_size rate of change of d_size
    #  m_alpha rate of change of d_alpha

    # we will start with an init class that just create the vector values
    # all other deltas and modifiers will be added later, this will allow incremental implementation

    def __init__(self, x, y, ang, size, life, alpha=1.0):
        """
        Initialize a new pose object.

        Parameters:
        - x: the x position of the pose.
        - y: the y position of the pose.
        - ang: the angle of the pose.
        - size: the size of the pose.
        - life: the lifetime of the pose.
        - alpha: the alpha value of the pose.
        """
        self.x = x
        self.y = y
        self.ang = ang
        self.size = size
        self.life = life
        self.alpha = alpha

        self.d_pos = (0, 0)
        self.d_rotation = 0
        self.d_size = 0
        self.d_alpha = 0

        # this will be a list of functions that will be called to modify the delta or vector values
        # they will be of the form f( pose, dt ) -> None
        # every registered modifier will run
        # they can unregister themselves and register others
        # we can build a lib of interesting modifiers
        self.modifier_callbacks = []

    def set_vectors(self, x, y, ang, size, life, alpha=1.0):
        """
        Set the vector values of the pose.

        Parameters:
        - x: the x position of the pose.
        - y: the y position of the pose.
        - ang: the angle of the pose.
        - size: the size of the pose.
        - life: the lifetime of the pose.
        - alpha: the alpha value of the pose.
        """
        # x and y are ranged values from -1 to 1 where
        # 0,0 is the center of the matrix
        # -1, 1 are the bounds
        self.x = x
        self.y = y
        # and is a ranged value from -1 to 1 where
        # 0 to 1 is 360 degrees anticlockwise
        # 0 to -1 is 360 degrees clockwise
        # 0 points to the right
        self.ang = ang
        # size is a ranged value where 1 = 100% and 0 = 0%
        self.size = size
        # life is the time in seconds the pose will be active
        # object poses should only updated and rendered if there is life
        self.life = life
        # alpha is the blend value of the object from 0 to 1 where
        # 0 is fully transparent
        # 1 is fully opaque
        self.alpha = alpha

    def set_deltas(self, d_pos, d_rotation, d_size):
        """
        Set the delta values of the pose per second

        Parameters:
        - d_pos: the delta position of the pose.
        - d_rotation: the delta rotation of the pose.
        - d_size: the delta size of the pose.
        """
        # d_pos is a tuple of ( linear, angule ) where
        # linear is the distance in x,y units per second
        # angular is the angle in the -1 to 1 ( -360 to 360 ) range per second
        self.d_pos = d_pos
        # d_rotation is change of ang per second with the same unit implications
        self.d_rotation = d_rotation
        self.d_size = d_size

    def apply_d_pos(self, dt):
        """
        Apply the delta position to the pose.

        Parameters:
        - dt: the time in seconds since the last update.
        """
        lin, ang = self.d_pos
        ang_radians = ang * -2 * np.pi
        direction = np.array([np.cos(ang_radians), np.sin(ang_radians)])
        movement_vector = direction * lin * dt
        self.x += movement_vector[0]
        self.y += movement_vector[1]

    def update(self, dt):
        """
        Update the pose with the given time delta.

        Parameters:
        - dt: the time in seconds since the last update.
        """
        self.life -= dt
        if self.life <= 0.0:
            return False

        self.ang = (((self.ang + 1) + self.d_rotation * dt) % 2) - 1
        self.apply_d_pos(dt)

        # note that alpha and size are capped at application in the render
        # stage to allow them to go out of range and be used as thresholds
        # for behaviour
        self.alpha += self.d_alpha * dt
        self.size += self.d_size * dt

        for modifier in self.modifier_callbacks:
            modifier(self, dt)

        return True
