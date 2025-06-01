from manim import *

##all sort of stuff that manim should have but doesn't

class MovingCameraWithHUDScene(ThreeDScene):
    def __init__(self, **kwargs):
        super().__init__(
            camera_class=ThreeDCamera,
            default_angled_camera_orientation_kwargs={
                "phi": 60 * DEGREES,
                "theta": -45 * DEGREES,
            },
            **kwargs
        )


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
