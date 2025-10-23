# blanim/common_examples.py

from common import *

"""    
Camera Animation Patterns - Common Mistakes    
    
This file demonstrates correct and incorrect ways to animate the camera in HUD2DScene.    
The behavior matches Manim's MovingCameraScene exactly.    
    
GOLDEN RULE: Use method chaining on a SINGLE .animate call    
    ✓ CORRECT: self.play(camera.frame.animate.move_to(pos).shift(vec).scale(factor))    
    ✗ WRONG:   self.play(camera.frame.animate.move_to(pos), camera.frame.animate.shift(vec))    
    
See TestSeparateVsChained for detailed examples and explanations.    
"""

##########Transcript Usage##########

class TranscriptExample(HUD2DScene):
    # This is how to add a transcript (.txt) to the output folder next to your video (mp4) output of the same name
    def construct(self):
        # Create objects
        square = Square(color=BLUE)
        circle = Circle(color=RED, radius=1.5)

        # Introduction
        self.narrate("Geometric Transformations")
        self.transcript.add_transcript("Scene opens with title 'Geometric Transformations'")
        self.wait(1)

        # Create square
        self.caption("Creating a square")
        self.transcript.add_transcript("A blue square appears at the origin using Create animation")
        self.play(Create(square))
        self.wait(0.5)

        # Rotate square
        self.caption("Rotating 90 degrees")
        self.transcript.add_transcript("The square rotates 90 degrees clockwise over 1.5 seconds")
        self.play(Rotate(square, angle=PI / 2), run_time=1.5)
        self.wait(0.5)

        # Scale square
        self.caption("Scaling up")
        self.transcript.add_transcript("The square scales up by a factor of 1.5")
        self.play(square.animate.scale(1.5))
        self.wait(0.5)

        # Transform to circle
        self.caption("Morphing shape")
        self.transcript.add_transcript("The blue square transforms into a red circle using Transform animation")
        self.play(Transform(square, circle))
        self.wait(0.5)

        # Move circle
        self.caption("Moving right")
        self.transcript.add_transcript("The circle shifts 3 units to the right")
        self.play(square.animate.shift(RIGHT * 3))
        self.wait(0.5)

        # Fade out
        self.clear_caption()
        self.transcript.add_transcript("The circle fades out and the scene ends")
        self.play(FadeOut(square))
        self.clear_narrate()
        self.wait(1)

class NoTranscriptExample(HUD2DScene):
    """Example showing that scenes without transcript calls don't create files."""
    def construct(self):
        # Visual elements only, no transcript documentation
        self.narrate("No Transcript")
        square = Square()
        self.play(Create(square))
        # No .txt file will be created since add_transcript() was never called

##########
# PART 1: INDIVIDUAL OPERATIONS (NO CHAINING)
##########

class TestIndividualOperations(HUD2DScene):
    """Test each camera operation independently.

    All operations should work correctly when used alone.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: move_to alone
        self.narrate("camera.frame.animate.move_to(square)")
        self.caption("Camera smoothly moves to center on the blue square")
        self.play(self.camera.frame.animate.move_to(square), run_time=2.0)
        self.wait(1.0)

        # Test 2: shift alone
        self.narrate("camera.frame.animate.shift(RIGHT * 2)")
        self.caption("Camera shifts 2 units to the right")
        self.play(self.camera.frame.animate.shift(RIGHT * 2), run_time=2.0)
        self.wait(1.0)

        # Test 3: scale alone (zoom in)
        self.narrate("camera.frame.animate.scale(0.5)")
        self.caption("Camera zooms in (objects appear 2x larger)")
        self.play(self.camera.frame.animate.scale(0.5), run_time=2.0)
        self.wait(1.0)

        # Test 4: scale alone (zoom out)
        self.narrate("camera.frame.animate.scale(2.0)")
        self.caption("Camera zooms out (objects appear 2x smaller)")
        self.play(self.camera.frame.animate.scale(2.0), run_time=2.0)
        self.wait(1.0)

        # Test 5: set width alone
        self.narrate("camera.frame.animate.set(width=10)")
        self.caption("Camera sets frame width to 10 units")
        self.play(self.camera.frame.animate.set(width=10), run_time=2.0)
        self.wait(1.0)

        # Reset for next test
        self.narrate("Reset: move_to(ORIGIN).set(width=14)")
        self.caption("Camera returns to origin with default width")
        self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=14), run_time=2.0)
        self.wait(1.0)

##########
# PART 2: PANNING CHAINS (move_to + shift combinations)
##########

class TestPanningChains(HUD2DScene):
    """Test all combinations of panning operations chained together.

    Expected: All should work smoothly with target-based approach.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: move_to → shift
        self.narrate("camera.frame.animate.move_to(square).shift(UP * 1)")
        self.caption("Camera moves to square, then shifts up 1 unit (chained)")
        self.play(
            self.camera.frame.animate
            .move_to(square)
            .shift(UP * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: shift → move_to
        self.narrate("camera.frame.animate.shift(RIGHT * 2).move_to(circle)")
        self.caption("Camera shifts right 2 units, then moves to circle (final position: circle)")
        self.play(
            self.camera.frame.animate
            .shift(RIGHT * 2)
            .move_to(circle),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: move_to → shift → shift
        self.narrate("camera.frame.animate.move_to(ORIGIN).shift(RIGHT).shift(DOWN)")
        self.caption("Camera moves to origin, shifts right, then down (cumulative)")
        self.play(
            self.camera.frame.animate
            .move_to(ORIGIN)
            .shift(RIGHT * 1)
            .shift(DOWN * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: shift → shift → move_to
        self.narrate("camera.frame.animate.shift(LEFT).shift(UP).move_to(square)")
        self.caption("Camera shifts left, up, then moves to square (final position: square)")
        self.play(
            self.camera.frame.animate
            .shift(LEFT * 1)
            .shift(UP * 1)
            .move_to(square),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 5: move_to → move_to (overwrite)
        self.narrate("camera.frame.animate.move_to(circle).move_to(ORIGIN)")
        self.caption("Camera moves to circle, then to origin (second move_to overwrites first)")
        self.play(
            self.camera.frame.animate
            .move_to(circle)
            .move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

##########
# PART 3: ZOOM CHAINS (scale + set combinations)
##########

class TestZoomChains(HUD2DScene):
    """Test all combinations of zoom operations chained together.

    Expected: With target-based approach, these should work correctly.
    Last operation should determine final zoom level.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square)

        # Test 1: scale → scale (zoom in then out)
        self.narrate("camera.frame.animate.scale(0.5).scale(2.0)")
        self.caption("Camera zooms in 2x, then out 2x (net effect: back to original zoom)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: scale → set
        self.narrate("camera.frame.animate.scale(0.5).set(width=10)")
        self.caption("Camera zooms in 2x, then sets width to 10 (set overwrites scale)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .set(width=10),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: set → scale
        self.narrate("camera.frame.animate.set(width=8).scale(0.5)")
        self.caption("Camera sets width to 8, then zooms in 2x (cumulative: width=4)")
        self.play(
            self.camera.frame.animate
            .set(width=8)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: set → set (overwrite)
        self.narrate("camera.frame.animate.set(width=6).set(width=14)")
        self.caption("Camera sets width to 6, then to 14 (second set overwrites first)")
        self.play(
            self.camera.frame.animate
            .set(width=6)
            .set(width=14),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 5: Multiple scales
        self.narrate("camera.frame.animate.scale(0.5).scale(2.0).scale(0.5)")
        self.caption("Camera zooms in 2x, out 2x, in 2x (net effect: zoomed in 2x)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .scale(2.0)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

##########
# PART 4: MIXED CHAINS (panning + zoom in all orders)
##########

class TestMixedChains(HUD2DScene):
    """Test all combinations of panning and zoom operations chained together.

    Expected: With target-based approach, ALL combinations should work!
    This is the key improvement over the previous implementation.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: move_to → scale
        self.narrate("camera.frame.animate.move_to(square).scale(0.5)")
        self.caption("Camera moves to square AND zooms in 2x simultaneously")
        self.play(
            self.camera.frame.animate
            .move_to(square)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: scale → move_to
        self.narrate("camera.frame.animate.scale(2.0).move_to(circle)")
        self.caption("Camera zooms out 2x AND moves to circle simultaneously")
        self.play(
            self.camera.frame.animate
            .scale(2.0)
            .move_to(circle),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: shift → scale
        self.narrate("camera.frame.animate.shift(LEFT * 2).scale(0.5)")
        self.caption("Camera shifts left 2 units AND zooms in 2x simultaneously")
        self.play(
            self.camera.frame.animate
            .shift(LEFT * 2)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: scale → shift
        self.narrate("camera.frame.animate.scale(2.0).shift(RIGHT * 2)")
        self.caption("Camera zooms out 2x AND shifts right 2 units simultaneously")
        self.play(
            self.camera.frame.animate
            .scale(2.0)
            .shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 5: move_to → shift → scale
        self.narrate("camera.frame.animate.move_to(ORIGIN).shift(UP).scale(0.5)")
        self.caption("Camera moves to origin, shifts up, AND zooms in 2x (all combined)")
        self.play(
            self.camera.frame.animate
            .move_to(ORIGIN)
            .shift(UP * 1)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 6: scale → move_to → shift
        self.narrate("camera.frame.animate.scale(2.0).move_to(square).shift(DOWN)")
        self.caption("Camera zooms out 2x, moves to square, AND shifts down (all combined)")
        self.play(
            self.camera.frame.animate
            .scale(2.0)
            .move_to(square)
            .shift(DOWN * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 7: move_to → scale → shift
        self.narrate("camera.frame.animate.move_to(circle).scale(0.5).shift(RIGHT)")
        self.caption("Camera moves to circle, zooms in 2x, AND shifts right (all combined)")
        self.play(
            self.camera.frame.animate
            .move_to(circle)
            .scale(0.5)
            .shift(RIGHT * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 8: shift → scale → move_to
        self.narrate("camera.frame.animate.shift(LEFT).scale(2.0).move_to(ORIGIN)")
        self.caption("Camera shifts left, zooms out 2x, AND moves to origin (final: origin)")
        self.play(
            self.camera.frame.animate
            .shift(LEFT * 1)
            .scale(2.0)
            .move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 9: scale → shift → scale
        self.narrate("camera.frame.animate.scale(0.5).shift(UP).scale(2.0)")
        self.caption("Camera zooms in 2x, shifts up, AND zooms out 2x (net zoom: original)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .shift(UP * 1)
            .scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 10: move_to → set → shift
        self.narrate("camera.frame.animate.move_to(square).set(width=8).shift(DOWN)")
        self.caption("Camera moves to square, sets width to 8, AND shifts down (all combined)")
        self.play(
            self.camera.frame.animate
            .move_to(square)
            .set(width=8)
            .shift(DOWN * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 11: Complex chain with all operations
        self.narrate("camera.frame.animate.move_to(ORIGIN).shift(RIGHT).scale(0.5).shift(UP).scale(2.0)")
        self.caption("Complex: moves to origin, shifts right, zooms in, shifts up, zooms out")
        self.play(
            self.camera.frame.animate
            .move_to(ORIGIN)
            .shift(RIGHT * 1)
            .scale(0.5)
            .shift(UP * 1)
            .scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

##########
# PART 5: DIRECT (NON-ANIMATED) OPERATIONS
##########

class TestDirectOperations(HUD2DScene):
    """Test direct (non-animated) camera operations.

    These operations execute instantly without animation.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: Direct move_to
        self.narrate("camera.frame.move_to(square)")
        self.caption("Camera instantly jumps to square (no animation)")

        self.camera.frame.move_to(square)
        self.wait(1.0)

        # Test 2: Direct shift
        self.narrate("camera.frame.shift(RIGHT * 3)")
        self.caption("Camera instantly shifts right (no animation)")

        self.camera.frame.shift(RIGHT * 3)
        self.wait(1.0)

        # Test 3: Direct scale
        self.narrate("camera.frame.scale(0.5)")
        self.caption("Camera instantly zooms in (no animation)")

        self.camera.frame.scale(0.5)
        self.wait(1.0)

        # Test 4: Direct set
        self.narrate("camera.frame.set(width=14)")
        self.caption("Camera instantly sets width to 14 (no animation)")

        self.camera.frame.set(width=14)
        self.wait(1.0)

        # Test 5: Chained direct operations
        self.narrate("camera.frame.move_to(ORIGIN).shift(UP).scale(1.5)")
        self.caption("Camera instantly moves to origin, shifts up, and zooms out (all chained, no animation)")

        self.camera.frame.move_to(ORIGIN).shift(UP * 1).scale(1.5)
        self.wait(1.0)


##########
# PART 6: COMPARISON WITH SEPARATE ANIMATIONS
# This example demonstrates CORRECT vs INCORRECT camera animation patterns.
# Tests 2-4 show common mistakes that produce unexpected results.
##########

class TestSeparateVsChained(HUD2DScene):
    """Compare chained operations vs separate animations in same play().

    IMPORTANT: This example demonstrates both correct and incorrect usage patterns.

    **Correct Usage (Test 1):**
    - Chain multiple operations on a single .animate call
    - Example: `camera.frame.animate.move_to(pos).shift(vec).scale(factor)`

    **Incorrect Usage (Tests 2-4):**
    - Multiple separate .animate calls for the same mobject in one play()
    - Example: `play(obj.animate.move(), obj.animate.scale())`  # DON'T DO THIS

    **Why It Fails:**
    Manim's .animate system creates separate Animation objects for each .animate call.
    When multiple animations target the same mobject in a single play() call, only
    the LAST animation executes - all previous animations are discarded.

    This matches MovingCameraScene behavior and is documented in Manim's warning:
    "Passing multiple animations for the same Mobject in one call to Scene.play
    is discouraged and will most likely not work properly."

    See: manim/mobject/mobject.py:313-324 for the official warning.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # ========== TEST 1: CORRECT USAGE ==========
        self.narrate("camera.frame.animate.move_to(square).shift(RIGHT * 2)")
        self.caption("✓ CORRECT: Chained operations create single animation")

        self.play(
            self.camera.frame.animate.move_to(square).shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # ========== TEST 2: INCORRECT USAGE - Multiple Position Animations ==========
        self.narrate("camera.frame.animate.move_to(square), camera.frame.animate.shift(RIGHT * 2)")
        self.caption("✗ WRONG: Only shift executes, move_to is ignored (last animation wins)")

        # ANTI-PATTERN: Two separate .animate calls for same mobject
        # Expected: Camera moves to square THEN shifts right
        # Actual: Only the shift(RIGHT * 2) executes, move_to(square) is discarded
        self.play(
            self.camera.frame.animate.move_to(square),  # ← This is IGNORED
            self.camera.frame.animate.shift(RIGHT * 2),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # ========== TEST 3: INCORRECT USAGE - Position + Scale Animations ==========
        self.narrate("camera.frame.animate.move_to(circle).shift(UP), camera.frame.animate.scale(0.5)")
        self.caption("✗ WRONG: Only scale executes, chained position ops are ignored")

        # ANTI-PATTERN: Chained position ops + separate scale animation
        # Expected: Camera moves to circle+up AND zooms in
        # Actual: Only scale(0.5) executes, move_to().shift() is discarded
        # Note: Even though move_to/shift are chained, they're still part of the
        # FIRST .animate call, which gets overridden by the SECOND .animate call
        self.play(
            self.camera.frame.animate.move_to(circle).shift(UP * 1),  # ← IGNORED
            self.camera.frame.animate.scale(0.5),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        # NOTE: This reset also demonstrates the problem - move_to(ORIGIN) is ignored!
        # The camera stays at ORIGIN only because Test 3's position change was ignored,
        # so we're accidentally already at ORIGIN. This is NOT reliable behavior.
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),  # ← IGNORED
            self.camera.frame.animate.scale(2.0),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        # ========== TEST 4: INCORRECT USAGE - Three Separate Animations ==========
        self.narrate(
            "camera.frame.animate.move_to(circle), camera.frame.animate.shift(UP), camera.frame.animate.scale(0.5)")
        self.caption("✗ WRONG: Only scale executes, all position anims ignored")

        # ANTI-PATTERN: Three separate .animate calls
        # Expected: Camera moves to circle, shifts up, AND zooms in
        # Actual: Only scale(0.5) executes, both position animations are discarded
        self.play(
            self.camera.frame.animate.move_to(circle),  # ← IGNORED
            self.camera.frame.animate.shift(UP * 1),  # ← IGNORED
            self.camera.frame.animate.scale(0.5),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        self.narrate("Comparison complete!")
        self.caption("Remember: Chain operations on ONE .animate call, not multiple separate calls")
        self.wait(1.0)
# Compare to movingcamerascene
class MovingCameraComparison(MovingCameraScene):
    """Compare with standard MovingCameraScene behavior."""

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: Chained panning operations
        self.play(
            self.camera.frame.animate.move_to(square).shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: Same operations as separate animations
        self.play(
            self.camera.frame.animate.move_to(square),
            self.camera.frame.animate.shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: Chained panning + separate zoom
        self.play(
            self.camera.frame.animate.move_to(circle).shift(UP * 1),
            self.camera.frame.animate.scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            self.camera.frame.animate.scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: All separate animations
        self.play(
            self.camera.frame.animate.move_to(circle),
            self.camera.frame.animate.shift(UP * 1),
            self.camera.frame.animate.scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)


class TestHeightParameter(HUD2DScene):
    """Test height parameter in set() method."""

    def construct(self):
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])
        self.add(grid)

        # Test height alone
        self.narrate("camera.frame.animate.set(height=6)")
        self.play(self.camera.frame.animate.set(height=6), run_time=2.0)
        self.wait(1.0)

        # Test width and height (width takes precedence)
        self.narrate("camera.frame.animate.set(width=10, height=6)")
        self.caption("Width takes precedence when both specified")
        self.play(self.camera.frame.animate.set(width=10, height=6), run_time=2.0)
        self.wait(1.0)