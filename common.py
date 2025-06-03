from manim import *

##all sort of stuff that manim should have but doesn't
#TODO DO NOT USE - migrate narration to MovingCameraFixedLayerScene

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

        self.narration_text_mobject = MathTex(
            r"\text{created on init text and math: } \int_0^\infty e^{-x^2} dx",
            color=WHITE
        )

        # currently adding to scene upon creation
        self.narration_text_mobject.to_edge(UP)
        self.add_fixed_in_frame_mobjects(self.narration_text_mobject)
        print(len(self.foreground_mobjects))
        self.add_foreground_mobjects(self.narration_text_mobject)
        print(len(self.foreground_mobjects))

    def update_narration_text(self, new_text):
        # Fade out the old text
        print(len(self.foreground_mobjects))
        self.play(FadeOut(self.narration_text_mobject))
        print(len(self.foreground_mobjects))

        # Remove from fixed frame and foreground
        self.remove_fixed_in_frame_mobjects(self.narration_text_mobject)
        if self.narration_text_mobject in self.foreground_mobjects:
            self.foreground_mobjects.remove(self.narration_text_mobject)

            # Create new MathTex
        new_narration = MathTex(
            new_text,
            color=WHITE
        )
        new_narration.to_edge(UP)

        # Update reference and add to fixed objects
        self.narration_text_mobject = new_narration
        self.add_fixed_in_frame_mobjects(self.narration_text_mobject)
        self.add_foreground_mobjects(self.narration_text_mobject)

        # Fade in the new text
        self.play(FadeIn(self.narration_text_mobject))


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
