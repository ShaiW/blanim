from manim import *

##all sort of stuff that manim should have but doesn't

class MovingCameraWithHUDScene(ThreeDScene):
    def __init__(self, **kwargs):
        super().__init__(
            camera_class=ThreeDCamera,
            default_angled_camera_orientation_kwargs={
                "phi": 0 * DEGREES,
                "theta": 0 * DEGREES,
            },
            **kwargs
        )
# TODO untested
    def auto_zoom(
            self,
            mobjects: list[Mobject],
            margin: float = 0,
            only_mobjects_in_frame: bool = False,
            animate: bool = True,
            **kwargs
    ):
        """Auto-zoom functionality for ThreeDScene when phi=0 and theta=0 (2D view)"""
        scene_critical_x_left = None
        scene_critical_x_right = None
        scene_critical_y_up = None
        scene_critical_y_down = None

        # Find bounding box - same logic as MovingCamera
        for m in mobjects:
            if only_mobjects_in_frame and not self._is_in_frame(m):
                continue

                # Initialize or update critical points
            if scene_critical_x_left is None:
                scene_critical_x_left = m.get_critical_point(LEFT)[0]
                scene_critical_x_right = m.get_critical_point(RIGHT)[0]
                scene_critical_y_up = m.get_critical_point(UP)[1]
                scene_critical_y_down = m.get_critical_point(DOWN)[1]
            else:
                if m.get_critical_point(LEFT)[0] < scene_critical_x_left:
                    scene_critical_x_left = m.get_critical_point(LEFT)[0]
                if m.get_critical_point(RIGHT)[0] > scene_critical_x_right:
                    scene_critical_x_right = m.get_critical_point(RIGHT)[0]
                if m.get_critical_point(UP)[1] > scene_critical_y_up:
                    scene_critical_y_up = m.get_critical_point(UP)[1]
                if m.get_critical_point(DOWN)[1] < scene_critical_y_down:
                    scene_critical_y_down = m.get_critical_point(DOWN)[1]

                    # Calculate center and dimensions
        center_x = (scene_critical_x_left + scene_critical_x_right) / 2
        center_y = (scene_critical_y_up + scene_critical_y_down) / 2
        new_width = abs(scene_critical_x_left - scene_critical_x_right)
        new_height = abs(scene_critical_y_up - scene_critical_y_down)

        # Calculate zoom factor based on current frame dimensions
        current_width = self.camera.frame_width
        current_height = self.camera.frame_height

        # Choose zoom based on which dimension needs more scaling
        if new_width / current_width > new_height / current_height:
            zoom_factor = current_width / (new_width + margin)
        else:
            zoom_factor = current_height / (new_height + margin)

            # Apply the transformation
        if animate:
            return self.move_camera(
                frame_center=[center_x, center_y, 0],
                zoom=zoom_factor,
                **kwargs
            )
        else:
            self.set_camera_orientation(
                frame_center=[center_x, center_y, 0],
                zoom=zoom_factor
            )
            return None

    def _is_in_frame(self, mobject):
        """Helper method to check if mobject is in frame"""
        # Simple implementation - you might want to make this more sophisticated
        center = mobject.get_center()
        frame_center = self.camera._frame_center.get_center()
        frame_width = self.camera.frame_width
        frame_height = self.camera.frame_height

        return (abs(center[0] - frame_center[0]) <= frame_width / 2 and
                abs(center[1] - frame_center[1]) <= frame_height / 2)



class MovingCameraFixedLayerScene(MovingCameraScene):
    """ An extension of MovingCameraScene that prevents camera
    shifts from moving mobjects with the fixedLayer attribute"""

    camera_height: float
    camera_shift: list[float]

    def __init__(self, **kwargs):
        super().__init__(camera_class = MovingCamera, **kwargs)
        self.camera_height = self.camera.frame_height
        self.camera_shift = self.camera.frame_center

    def play(self, *args, **kwargs):
        res = super().play(*args, **kwargs)
        #reposition fixed objects after animation
        for mob in filter(lambda x: (hasattr(x, 'fixedLayer') and x.fixedLayer), self.mobjects):
            dshift =  self.camera.frame_center - self.camera_shift
            mob.shift(dshift)
            dheight = self.camera.frame.height/self.camera_height
            mob.scale(dheight)
            mob.shift((mob.get_center()-self.camera.frame_center)*(dheight-1))
        self.camera_shift = self.camera.frame_center
        self.camera_height = self.camera.frame_height
        return res

    def get_moving_mobjects(self, *animations: Animation):
        #This causes fixed object to not be animated
        return list(filter(lambda x: not (hasattr(x, 'fixedLayer') and x.fixedLayer), super().get_moving_mobjects(*animations)))
    
    def fix(self, mob):
        mob.fixedLayer = True
        return mob
    
    def unfix(self, mob):
        mob.fixedLayer = False
        return mob
    
    def toggle_fix(self, mob):
        mob.fixedLayer = (not mob.fixedLayer) if hasattr(mob, "fixedLayer") else True
