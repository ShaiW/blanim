from common import *

class CameraTest(MovingCameraFixedLayerScene):
    def construct(self):
        label = Tex("This label is fixed!").to_edge(UP)
        label.fixedLayer = True
        self.play(
            Write(label),
            FadeIn(Square().shift(LEFT*2)),
            FadeIn(Square().shift(RIGHT*2)),
        )
        self.play(
            self.camera.frame.animate.shift(LEFT)
        )
        self.play(
            self.camera.frame.animate.shift(DOWN)
        )
        self.play(
            self.camera.frame.animate.scale(2)
        )
        self.play(
            self.camera.frame.animate.scale(1/3)
        )
        sq = Square().shift(DOWN*2)
        sq.fixedLayer = True
        self.play(
            FadeIn(sq)
        )
        self.play(
            self.camera.frame.animate.shift(DOWN*2 + LEFT*2)
        )
        self.wait()

class CameraTest2(MovingCameraFixedLayerScene):
    def construct(self):
        squares = [Square().scale(1/4) for _ in range(5)]
        self.add(*squares)
        for sq in squares:
            self.fix(sq)
            self.play(self.camera.frame.animate.shift(LEFT))
            print([sq.get_center() for sq in squares])
        self.wait()

class CameraTest3(MovingCameraFixedLayerScene):
    def construct(self):
        sq = Square().scale(1/4).shift(LEFT*7)
        self.add(sq, Square().scale(1/4).shift(DOWN+LEFT*7))
        for _ in range(15):
            self.play(self.camera.frame.animate.shift(LEFT), run_time = 0.5)
            self.toggle_fix(sq)
        self.wait()

class CameraTest4(MovingCameraFixedLayerScene):
    def construct(self):
        self.add(self.fix(Square()))
        for _ in range(10):
            self.play(self.camera.frame.animate.scale(1.5), run_time =0.3)
        for _ in range(20):
            self.play(self.camera.frame.animate.scale(0.66), run_time =0.3)
        self.wait()