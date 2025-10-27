from __future__ import annotations

from manim import *
from manim.utils.deprecation import deprecated


"""MARKED FOR DELETION"""

##########START Properly Documented Stuff##########

@deprecated(
    since="v1.0.0",  # Replace with your actual version
    replacement="HUD2DScene",
    message="This attribute-based implementation has performance limitations and cumulative scaling drift. "
            "Use HUD2DScene which provides narration, transcript management, and optimized fixed-layer handling."
)
class MovingCameraFixedLayerScene(MovingCameraScene):
    """A scene with a moving camera and support for fixed-layer elements (attribute-based).

    .. deprecated:: v1.0.0
        This class is deprecated. Use :class:`HUD2DScene` instead, which provides better
        performance, narration management, transcript creation, and avoids cumulative scaling drift.

    This scene extends :class:`~.MovingCameraScene` to provide HUD-like functionality where
    certain mobjects remain fixed in screen space regardless of camera movements (panning or
    zooming). This is the original implementation using attribute-based tracking.

    .. warning::
        This implementation is deprecated and should not be used in new projects. Use
        :class:`HUD2DScene` instead, which provides superior performance and additional
        features including narration management and transcript creation.

    The scene marks mobjects with a ``fixedLayer`` attribute and applies inverse transformations
    after each animation to counteract camera movements. Unlike :class:`~.ThreeDScene`'s
    ``add_fixed_in_frame_mobjects()``, this implementation is designed for 2D scenes.

    Why This Implementation is Deprecated
    --------------------------------------
    This implementation has several critical issues:

    **Performance Problems:**
        - Iterates through ALL scene mobjects on every ``play()`` call using ``filter()``
        - Uses ``hasattr()`` checks which add O(n) overhead on every animation
        - No early exit when camera hasn't moved or no fixed objects exist

    **Cumulative Scaling Drift:**
        - Applies cumulative scaling via ``scale()`` which compounds over multiple animations
        - Fixed objects gradually change size over many camera movements
        - No recalculation from frame properties like Manim's internal systems

    **Fragile Attribute-Based Tracking:**
        - Pollutes mobject namespace with ``fixedLayer`` attribute
        - Not type-safe (no IDE support or type checking)
        - Can be accidentally overwritten
        - Requires ``hasattr()`` checks everywhere

    Migration to HUD2DScene
    -----------------------
    :class:`HUD2DScene` provides:
        - Optimized fixed-layer handling without performance penalties
        - Built-in narration management via ``UniversalNarrationManager``
        - Automatic transcript creation via ``TranscriptManager``
        - Animation wrappers for enhanced control
        - No cumulative scaling drift

    Examples
    --------

    .. code-block:: python

        # OLD (deprecated):
        class FixedLayerExample(MovingCameraFixedLayerScene):
            def construct(self):
                title = Text("Fixed HUD Title").to_corner(UL)
                self.add(self.fix(title))

                square = Square()
                self.add(square)

                self.play(self.camera.frame.animate.scale(2))

        # NEW (recommended):
        class FixedLayerExample(HUD2DScene):
            def construct(self):
                title = Text("Fixed HUD Title").to_corner(UL)
                self.add_fixed_in_frame_mobjects(title)

                square = Square()
                self.add(square)

                self.play(self.camera.frame.animate.scale(2))

    .. code-block:: python

        # Blockchain example with deprecated class
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

    See Also
    --------
    :class:`HUD2DScene` : Recommended replacement with narration and transcript support
    :class:`~.MovingCameraScene` : Base class for moving camera functionality
    :class:`~.ThreeDScene` : 3D scene with ``add_fixed_in_frame_mobjects()`` method

    Notes
    -----
    - Fixed mobjects are tracked via ``fixedLayer`` attribute on each mobject
    - Scaling uses cumulative ``scale()`` which WILL cause drift over multiple animations
    - All mobjects are checked on every ``play()`` call regardless of camera movement
    - This class is kept only for backward compatibility; all new code should use :class:`HUD2DScene`

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

        .. deprecated:: v1.0.0
            Use :class:`HUD2DScene` instead.

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
            impact performance in scenes with many mobjects. Use :class:`HUD2DScene`
            instead, which provides better performance and additional features.

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
            Use :class:`HUD2DScene` instead, which provides optimized fixed-layer handling.

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

    @staticmethod
    def fix(mob):
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

    @staticmethod
    def unfix(mob):
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

    @staticmethod
    def toggle_fix(mob):
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

##########END Properly Documented Stuff##########

##########START Untested Stuff##########

##########END Untested Stuff##########
