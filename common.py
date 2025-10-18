from __future__ import annotations

from manim import *

##all sort of stuff that manim should have but doesn't

##########START Properly Documented Stuff##########

class MovingCameraFixedLayerScene(MovingCameraScene):
    """A scene with a moving camera and support for fixed-layer elements (attribute-based).

    This scene extends :class:`~.MovingCameraScene` to provide HUD-like functionality where
    certain mobjects remain fixed in screen space regardless of camera movements (panning or
    zooming). This is the original implementation using attribute-based tracking.

    .. warning::
        This implementation has been superseded by :class:`MovingCameraHUDScene`, which uses
        set-based tracking for better performance. The optimized version has not yet been
        fully tested in production. This class is kept for backward compatibility and
        comparison purposes.

    The scene marks mobjects with a ``fixedLayer`` attribute and applies inverse transformations
    after each animation to counteract camera movements. Unlike :class:`~.ThreeDScene`'s
    ``add_fixed_in_frame_mobjects()``, this implementation is designed for 2D scenes.

    Performance Considerations
    --------------------------
    This implementation has several performance limitations:

    - Iterates through all scene mobjects on every ``play()`` call using ``filter()``
    - Uses ``hasattr()`` checks which add overhead
    - Applies cumulative scaling via ``scale()`` which can compound over multiple animations
    - No early exit when no fixed mobjects exist or camera hasn't moved

    For better performance, consider using :class:`MovingCameraHUDScene` instead.

    Examples
    --------

    .. code-block:: python

        class FixedLayerExample(MovingCameraFixedLayerScene):
            def construct(self):
                # Create HUD title that stays fixed
                title = Text("Fixed HUD Title").to_corner(UL)
                self.add(self.fix(title))

                # Create regular content that moves with camera
                square = Square()
                self.add(square)

                # Camera zooms, but title stays fixed
                self.play(self.camera.frame.animate.scale(2))
                self.play(self.camera.frame.animate.shift(RIGHT * 3))

    .. code-block:: python

        class BlockchainFixedLayerExample(MovingCameraFixedLayerScene):
            def construct(self):
                # Fixed state indicator
                state_text = Text("State: 0").to_edge(DOWN)
                self.add(self.fix(state_text))

                # Moving blockchain blocks
                blocks = VGroup(*[Square().shift(RIGHT * i * 2) for i in range(5)])
                self.add(blocks)

                # Zoom out to show all blocks, state text stays readable
                self.play(self.camera.frame.animate.scale(3))

                # Toggle fixed status
                self.toggle_fix(state_text)  # Now moves with camera
                self.play(self.camera.frame.animate.shift(LEFT * 2))

    See Also
    --------
    :class:`~.MovingCameraHUDScene` : Optimized version using set-based tracking
    :class:`~.MovingCameraScene` : Base class for moving camera functionality
    :class:`~.ThreeDScene` : 3D scene with ``add_fixed_in_frame_mobjects()`` method

    Notes
    -----
    - Fixed mobjects are tracked via ``fixedLayer`` attribute on each mobject
    - Scaling uses cumulative ``scale()`` which may cause drift over multiple animations
    - All mobjects are checked on every ``play()`` call regardless of camera movement
    - The optimized :class:`MovingCameraHUDScene` addresses these performance issues

    Attributes
    ----------
    camera_height : float
        Cached camera frame height from previous animation
    camera_shift : list[float]
        Cached camera frame center position from previous animation
    """

    camera_height: float
    camera_shift: list[float]

    def __init__(self, **kwargs):
        """Initialize the MovingCameraFixedLayerScene.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :class:`~.MovingCameraScene`
        """
        super().__init__(camera_class=MovingCamera, **kwargs)
        self.camera_height = self.camera.frame_height
        self.camera_shift = self.camera.frame_center

    def play(self, *args, **kwargs):
        """Play animations and apply fixed-layer corrections.

        After playing animations via the parent class, this method automatically
        repositions and rescales fixed mobjects to counteract camera transformations,
        keeping them at constant screen position and size.

        .. warning::
            This method iterates through all scene mobjects on every call, which may
            impact performance in scenes with many mobjects. Consider using
            :class:`MovingCameraHUDScene` for better performance.

        Parameters
        ----------
        *args
            Positional arguments passed to :meth:`~.Scene.play`
        **kwargs
            Keyword arguments passed to :meth:`~.Scene.play`

        Returns
        -------
        None

        Notes
        -----
        The method applies corrections in three steps:

        1. Shift mobjects to counteract camera position change
        2. Scale mobjects to counteract camera zoom change (cumulative)
        3. Adjust position based on distance from camera center

        The cumulative scaling may cause drift over many animations.
        """
        res = super().play(*args, **kwargs)

        # Reposition fixed objects after animation
        for mob in filter(lambda x: (hasattr(x, 'fixedLayer') and x.fixedLayer), self.mobjects):
            dshift = self.camera.frame_center - self.camera_shift
            mob.shift(dshift)
            dheight = self.camera.frame.height / self.camera_height
            mob.scale(dheight)
            mob.shift((mob.get_center() - self.camera.frame_center) * (dheight - 1))

        self.camera_shift = self.camera.frame_center
        self.camera_height = self.camera.frame_height
        return res

    def get_moving_mobjects(self, *animations):
        """Get moving mobjects, excluding fixed-layer elements.

        This method filters out fixed mobjects from the moving mobjects list,
        preventing them from triggering full scene redraws during animations.

        .. warning::
            Uses ``hasattr()`` checks on all moving mobjects, which adds overhead.
            The optimized :class:`MovingCameraHUDScene` uses set membership for O(1) lookup.

        Parameters
        ----------
        *animations : Animation
            The animations to check for moving mobjects

        Returns
        -------
        list[Mobject]
            List of moving mobjects, excluding those marked with ``fixedLayer=True``

        See Also
        --------
        :meth:`~.Scene.get_moving_mobjects` : Parent class implementation
        """
        # This causes fixed objects to not be animated
        return list(filter(lambda x: not (hasattr(x, 'fixedLayer') and x.fixedLayer),
                           super().get_moving_mobjects(*animations)))

    def fix(self, mob):
        """Mark a mobject as fixed in the camera frame (HUD element).

        Fixed mobjects maintain constant screen position and size regardless of
        camera movements. This is useful for UI elements, titles, state indicators,
        and other heads-up display components.

        Parameters
        ----------
        mob : Mobject
            The mobject to mark as fixed

        Returns
        -------
        Mobject
            The same mobject (for method chaining)

        Examples
        --------
        .. code-block:: python

            # Mark and add in one line
            self.add(self.fix(Text("HUD Title")))

            # Or separately
            title = Text("HUD Title")
            self.fix(title)
            self.add(title)

        See Also
        --------
        :meth:`unfix` : Remove fixed status from a mobject
        :meth:`toggle_fix` : Toggle fixed status

        Notes
        -----
        Sets the ``fixedLayer`` attribute to ``True`` on the mobject.
        """
        mob.fixedLayer = True
        return mob

    def unfix(self, mob):
        """Remove fixed status from a mobject.

        After calling this method, the mobject will move and scale normally
        with camera transformations.

        Parameters
        ----------
        mob : Mobject
            The mobject to unmark as fixed

        Returns
        -------
        Mobject
            The same mobject (for method chaining)

        See Also
        --------
        :meth:`fix` : Mark a mobject as fixed in frame
        :meth:`toggle_fix` : Toggle fixed status

        Notes
        -----
        Sets the ``fixedLayer`` attribute to ``False`` on the mobject.
        """
        mob.fixedLayer = False
        return mob

    def toggle_fix(self, mob):
        """Toggle the fixed status of a mobject.

        If the mobject is currently fixed, it becomes unfixed, and vice versa.
        If the mobject has no ``fixedLayer`` attribute, it is set to fixed.

        Parameters
        ----------
        mob : Mobject
            The mobject whose fixed status should be toggled

        Returns
        -------
        Mobject
            The same mobject (for method chaining)

        Examples
        --------
        .. code-block:: python

            title = Text("Toggle Me")
            self.add(self.fix(title))

            # Camera moves, title stays fixed
            self.play(self.camera.frame.animate.shift(RIGHT * 2))

            # Toggle to unfixed
            self.toggle_fix(title)

            # Camera moves, title moves with it
            self.play(self.camera.frame.animate.shift(LEFT * 2))

        See Also
        --------
        :meth:`fix` : Mark a mobject as fixed in frame
        :meth:`unfix` : Remove fixed status from a mobject

        Notes
        -----
        Uses ``hasattr()`` to check for existing ``fixedLayer`` attribute.
        """
        mob.fixedLayer = (not mob.fixedLayer) if hasattr(mob, "fixedLayer") else True
        return mob

class HUD2DScene(ThreeDScene):
    """A 2D scene with heads-up display (HUD) support using ThreeDScene's fixed-in-frame system.

    This scene extends :class:`~.ThreeDScene` but configures the camera for orthographic 2D viewing
    (looking straight down the Z-axis). It provides access to :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects`
    for creating HUD elements that remain fixed in the camera frame regardless of camera movements.

    **Design Rationale**: This is a workaround for Manim's lack of a performant 2D moving camera
    scene with HUD support. Previous attempts to optimize :class:`MovingCameraFixedLayerScene`
    encountered issues, leading to this approach of leveraging :class:`~.ThreeDScene`'s performant
    fixed-in-frame filtering system. A proper 2D HUD scene implementation is planned for future development.

    .. warning::
        **Camera Movement API**: This scene uses :meth:`~.ThreeDScene.move_camera` for camera
        movements, NOT :class:`~.MovingCameraScene`'s frame manipulation methods. You cannot use
        ``self.camera.frame.animate.shift()`` or similar 2D camera APIs. Use ``move_camera(frame_center=...)``
        instead.

    .. warning::
        **Camera Orientation**: Do not modify the camera orientation after setup. This scene is
        designed exclusively for 2D use with a fixed top-down view. Changing ``phi``, ``theta``,
        or ``gamma`` values is untested and not supported.

    .. warning::
        **Primer Pattern Requirements**: When using text in the HUD, you MUST:

        1. Create an invisible primer with sufficient character capacity (excluding spaces)
        2. Add primer to fixed-in-frame BEFORE any transforms
        3. Use ONLY :class:`~.Transform` (not ReplacementTransform)
        4. Always transform the SAME primer mobject
        5. Never exceed primer character capacity (overflow chars detach from HUD)
        6. Pick ONE text type (Text, MathTex, or Tex) and stick with it - do NOT mix

    **Character Counting Rules**:

    - **Spaces do NOT count** toward character capacity in any text type
    - Only visible non-space characters count (letters, numbers, symbols)
    - LaTeX commands (``\\``, ``{}``, ``^``, etc.) do NOT count as characters
    - Example: ``"HELLO WORLD"`` = 10 characters (space excluded)
    - Example: ``r"\\text{HELLO WORLD}"`` = 10 characters (space excluded)

    **Primer Overflow Behavior**:

    When text exceeds primer character capacity, overflow characters will:

    - Appear in the scene but NOT stay fixed in the HUD
    - Remain attached to the moving scene content
    - Move with camera transformations instead of staying fixed
    - **Non-deterministic**: Which specific characters detach is unpredictable
    - Avoid overflow by ensuring primer capacity exceeds longest text

    Examples
    --------

    .. code-block:: python

        class BasicHUD(HUD2DScene):
            def construct(self):
                # Primer: 10 char capacity (spaces excluded)
                hud = Text("0123456789", color=BLACK).to_corner(UL)
                self.add_fixed_in_frame_mobjects(hud)

                # Transform to visible (10 chars: HELLOWORLD)
                self.play(Transform(hud, Text("HELLO WORLD", color=WHITE).to_corner(UL)))

                # Camera moves, HUD stays fixed
                self.move_camera(frame_center=RIGHT * 2, run_time=2)

    .. code-block:: python

        class OverflowExample(HUD2DScene):
            def construct(self):
                hud = Text("0123456789", color=BLACK).to_corner(UL)  # 10 char capacity
                self.add_fixed_in_frame_mobjects(hud)

                # 13 chars (HELLOWORLDABC) - some chars detach (non-deterministic)
                self.play(Transform(hud, Text("HELLO WORLD ABC", color=WHITE).to_corner(UL)))
                self.move_camera(frame_center=RIGHT * 3)  # Detached chars move with camera

    .. code-block:: python

        class MathTexHUDExample(HUD2DScene):
            def construct(self):
                square = Square(color=GREEN)
                self.add(square)

                # MathTex primer (10 character capacity, spaces excluded)
                hud_text = MathTex(r"\\text{0123456789}", color=BLACK).to_corner(UL)
                self.add_fixed_in_frame_mobjects(hud_text)

                # Transform to math expression (4 chars: x, 2, y, 2)
                math_expr = MathTex(r"\\text{x}^{2}+\\text{y}^{2}", color=WHITE).to_corner(UL)
                self.play(Transform(hud_text, math_expr))

                # Camera movement
                self.move_camera(frame_center=LEFT * 2, run_time=2)

    .. code-block:: python

        class TexHUDExample(HUD2DScene):
            def construct(self):
                square = Square(color=RED)
                self.add(square)

                # Tex primer (10 character capacity, spaces excluded)
                hud_text = Tex(r"\\text{0123456789}", color=BLACK).to_corner(UL)
                self.add_fixed_in_frame_mobjects(hud_text)

                # Transform to LaTeX (5 chars: L, a, T, e, X)
                latex_text = Tex(r"\\LaTeX", color=WHITE).to_corner(UL)
                self.play(Transform(hud_text, latex_text))

                # Camera movement
                self.move_camera(frame_center=ORIGIN, run_time=2)

    See Also
    --------
    :class:`~.ThreeDScene` : Parent class providing fixed-in-frame functionality
    :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` : Method for adding HUD elements
    :meth:`~.ThreeDScene.move_camera` : Camera movement method (NOT MovingCameraScene API)
    :class:`MovingCameraFixedLayerScene` : Alternative 2D HUD implementation (less performant)
    :class:`NarrationTextFactory` : Factory for creating HUD text with primer pattern
    :class:`NarrationManager` : Scene-aware wrapper for managing HUD text lifecycle

    Notes
    -----
    - Camera is set to orthographic 2D view (phi=0, theta=-90°) in :meth:`setup`
    - Uses :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` for HUD elements
    - **Spaces do NOT count** toward primer character capacity
    - **Primer must have enough non-space characters** for longest text you'll display
    - **Overflow behavior is non-deterministic**: unpredictable which chars detach
    - **Only Transform works**: Do not use ReplacementTransform or other animations
    - **Do NOT mix text types**: Pick Text, MathTex, OR Tex and stick with it
    - **Mixing types not recommended**: Causes failures and performance degradation
    - **Camera API**: Use ``move_camera(frame_center=...)``, not ``camera.frame.animate``
    - **Tested text types**: Text, MathTex, Tex (each tested individually, not mixed)
    - **Renderer agnostic**: Cairo/OpenGL choice is irrelevant for 2D-only usage
    - This is a temporary workaround; proper 2D HUD scene is planned

    Attributes
    ----------
    None (inherits from ThreeDScene)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        """Initialize the HUD2DScene.  

        Parameters  
        ----------  
        **kwargs  
            Keyword arguments passed to :class:`~.ThreeDScene`  
        """

    def setup(self):
        """Set up the scene with 2D orthographic camera orientation.

        This method is called automatically before :meth:`construct`. It configures
        the camera to look straight down the Z-axis, providing a 2D view while
        maintaining access to 3D scene features like fixed-in-frame mobjects.

        .. warning::
            Do not override this method or modify camera orientation after setup.
            This scene is designed exclusively for 2D use.

        Notes
        -----
        Sets camera orientation to ``phi=0, theta=-90 * DEGREES`` for top-down 2D view.
        """
        super().setup()
        # Set camera to orthographic 2D view (looking straight down)
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)

##########END Properly Documented Stuff##########