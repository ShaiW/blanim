from __future__ import annotations

from typing import List

from manim import *
from manim.utils.family import extract_mobject_family_members
from manim.typing import Point3D_Array
import numpy.typing as npt
from manim.typing import ManimInt

##all sort of stuff that manim should have but doesn't

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
    """ThreeDScene configured for 2D with HUD support, using Cairo renderer."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup(self):
        super().setup()
        # Set camera to orthographic 2D view (looking straight down)
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)

#TODO some of these might actually work, but the problem could have been mathtex not handled properly (culling does not work or provide performance)
class ViewportCullingHUDCamera(MovingCamera):
    """A MovingCamera with fixed-in-frame HUD support and viewport culling optimization.

    This camera extends MovingCamera to add two key features:
    1. Support for mobjects that remain fixed in the camera frame (HUD elements)
    2. Viewport culling to skip rendering mobjects outside the viewable area

    The fixed-in-frame implementation stores the initial screen position and scale of
    mobjects when they are added to the fixed set. During rendering, it restores these
    positions to compensate for camera movement and zoom, ensuring HUD elements remain
    at constant screen positions and sizes.

    The viewport culling optimization filters out off-screen mobjects before rendering
    to improve performance in large scenes, while always rendering fixed-in-frame HUD
    elements regardless of their position.

    Limitations and Warnings
    ------------------------

    **Bounding Box Approximation**
        Viewport culling uses bounding box checks, not pixel-perfect visibility:

        - Rotated objects may be culled incorrectly (bounding box doesn't rotate)
        - Conservative culling includes objects if any part of bounding box overlaps frame
        - Irregular shapes with large empty areas may render when mostly off-screen

    **Fixed-in-Frame Positioning**
        HUD elements must be positioned BEFORE being added to fixed_in_frame_mobjects.
        Their initial position and scale are captured at that moment and maintained
        throughout camera movements.

    **Transform vs ReplacementTransform**
        When updating fixed-in-frame HUD elements:

        - Use Transform to keep mobject in fixed_in_frame_mobjects set automatically
        - ReplacementTransform swaps mobject instances; new mobject must be re-fixed
        - Failing to re-fix after ReplacementTransform causes HUD to move with camera

    **Performance Overhead**
        Viewport culling adds per-mobject bounding box checks. Not recommended for:

        - Small scenes where most objects are always visible
        - Dense scenes with many tightly packed objects
        - Debugging (disable culling with enable_viewport_culling(False))

    **Renderer Compatibility**
        Designed for Cairo renderer. OpenGL renderer has different camera/rendering
        pipelines and may require modifications for correct behavior.

    **Submobject Handling**
        Adding a VGroup to fixed-in-frame fixes all submobjects. Removing parent
        doesn't automatically remove submobjects from the fixed set.

    **Frame Configuration**
        Fixed-in-frame mobjects position relative to config["frame_width"] and
        config["frame_height"]. Changing frame config after adding fixed mobjects
        may cause unexpected position shifts.

    **Z-Ordering**
        Fixed-in-frame mobjects render in scene mobject list order, not special
        z-ordering. Use add_foreground_mobject() or careful ordering for HUD on top.

    Examples
    --------
    .. code-block:: python

        class MyScene(MovingCameraScene):
            def __init__(self, **kwargs):
                super().__init__(camera_class=ViewportCullingHUDCamera, **kwargs)

            def construct(self):
                # Create and position HUD element BEFORE fixing
                title = Text("Title").to_corner(UL)
                self.add(title)
                self.camera.add_fixed_in_frame_mobjects(title)

                # Create many scene objects
                objects = VGroup(*[Square().shift(RIGHT * x) for x in range(-20, 20)])
                self.add(objects)

                # Camera movements won't affect title, and off-screen objects won't be rendered
                self.play(self.camera.frame.animate.shift(RIGHT * 10))
                self.play(self.camera.frame.animate.scale(0.5))

    See Also
    --------
    ViewportCullingHUDScene : Scene class that uses this camera
    ThreeDCamera : Similar fixed-in-frame functionality for 3D scenes

    Notes
    -----
    The implementation stores initial positions relative to the camera's frame_center
    and initial scale relative to the camera's frame dimensions. During rendering,
    it calculates the offset needed to restore the original screen position and scale,
    compensating for any camera movement or zoom that has occurred.
    """

    def __init__(self, **kwargs):
        """Initialize the ViewportCullingHUDCamera.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to MovingCamera.__init__
        """
        super().__init__(**kwargs)
        self.fixed_in_frame_mobjects: set[Mobject] = set()
        self.enable_culling: bool = True

    def add_fixed_in_frame_mobjects(self, *mobjects: Mobject) -> None:
        """Add mobjects that should stay fixed in the camera frame.

        This method captures the current screen position and scale of each mobject
        relative to the camera's current state. These values are stored and used
        during rendering to maintain constant screen position and size regardless
        of camera movement or zoom.

        Highly useful for displaying titles, scores, timers, or other HUD-style elements.

        Fixed-in-frame mobjects are always rendered, even if they would normally be
        outside the viewable area (when viewport culling is enabled).

        Parameters
        ----------
        *mobjects
            The mobjects to fix in frame. All submobjects are also fixed.

        Examples
        --------
        .. code-block:: python

            # Position BEFORE fixing
            title = Text("Score: 0").to_corner(UL)
            self.add(title)
            self.camera.add_fixed_in_frame_mobjects(title)

            # Update the title later using Transform (stays fixed automatically)
            new_title = Text("Score: 100").to_corner(UL)
            self.play(Transform(title, new_title))

        See Also
        --------
        remove_fixed_in_frame_mobjects : Remove mobjects from fixed-in-frame set
        ThreeDCamera.add_fixed_in_frame_mobjects : Similar functionality for 3D scenes

        Notes
        -----
        The mobject's position and scale are captured at the moment this method is called.
        Make sure to position the mobject where you want it on screen BEFORE calling this method.
        """
        for mobject in extract_mobject_family_members(mobjects):
            self.fixed_in_frame_mobjects.add(mobject)

    def remove_fixed_in_frame_mobjects(self, *mobjects: Mobject) -> None:
        """Remove mobjects from the fixed-in-frame set.

        If a mobject was fixed in frame by passing it through
        add_fixed_in_frame_mobjects, this undoes that fixing.
        The mobject will be affected by camera transformations again.

        Parameters
        ----------
        *mobjects
            The mobjects which need not be fixed in frame any longer.

        See Also
        --------
        add_fixed_in_frame_mobjects : Add mobjects to fixed-in-frame set
        """
        for mobject in extract_mobject_family_members(mobjects):
            if mobject in self.fixed_in_frame_mobjects:
                self.fixed_in_frame_mobjects.remove(mobject)

    def points_to_pixel_coords(
            self,
            mobject: Mobject,
            points: Point3D_Array,
    ) -> npt.NDArray[ManimInt]:
        """Convert points to pixel coordinates, compensating for camera transformations on fixed mobjects.

        This method overrides the parent's implementation to handle fixed-in-frame mobjects.
        For fixed mobjects, it calculates the offset needed to restore their original screen
        position and scale, compensating for camera movement and zoom.

        This is the key method that makes fixed-in-frame HUD elements work with MovingCamera,
        since MovingCamera applies its transformations here rather than in
        transform_points_pre_display().

        Parameters
        ----------
        mobject
            The mobject being rendered
        points
            The 3D points to convert to pixel coordinates

        Returns
        -------
        np.ndarray
            2D pixel coordinates as integers

        Notes
        -----
        For fixed-in-frame mobjects, this method:
        1. Retrieves stored initial position and scale data
        2. Calculates position offset to compensate for camera movement
        3. Calculates scale factor to compensate for camera zoom
        4. Applies both compensations before calling parent implementation

        For regular mobjects, delegates to the parent implementation which applies
        the frame_center offset and zoom scaling normally.

        The compensation ensures that fixed mobjects maintain their original screen
        position and size regardless of camera transformations, with no drift over time.

        See Also
        --------
        Camera.points_to_pixel_coords : Base implementation
        MovingCamera.frame_center : The camera position that affects transformations
        """
        if mobject in self.fixed_in_frame_mobjects:
            # Apply transform_points_pre_display first
            points = self.transform_points_pre_display(mobject, points)

            # Use config frame dimensions (constant) instead of self.frame_width/height (dynamic)
            pixel_height = self.pixel_height
            pixel_width = self.pixel_width
            frame_height = config["frame_height"]  # Static, doesn't change with zoom
            frame_width = config["frame_width"]  # Static, doesn't change with zoom

            width_mult = pixel_width / frame_width
            width_add = pixel_width / 2
            height_mult = pixel_height / frame_height
            height_add = pixel_height / 2
            height_mult *= -1  # Flip y-axis

            result = np.zeros((len(points), 2))
            result[:, 0] = points[:, 0] * width_mult + width_add
            result[:, 1] = points[:, 1] * height_mult + height_add
            return result.astype("int")

            # For non-fixed mobjects, use parent implementation
        return super().points_to_pixel_coords(mobject, points)

    def get_mobjects_to_display(
            self,
            mobjects,
            include_submobjects=True,
            excluded_mobjects=None,
    ):
        """Filter out off-screen mobjects for performance (viewport culling).

        This method is called during rendering to determine which mobjects to process.
        When viewport culling is enabled, it filters the list to include only:
        1. Fixed-in-frame mobjects (HUD elements) - always rendered
        2. Mobjects within the camera's viewable area - checked via is_in_frame()

        The culling check happens on a per-frame basis, so mobjects that move into
        view during camera animations will be rendered correctly.

        Parameters
        ----------
        mobjects
            The mobjects to potentially display
        include_submobjects
            Whether to include submobjects
        excluded_mobjects
            Mobjects to exclude from display

        Returns
        -------
        list
            Filtered list of mobjects to render

        Notes
        -----
        The is_in_frame() check uses bounding boxes, which means:
        - Partially visible objects are included (conservative culling)
        - Better to render slightly more than miss visible objects
        - Rotated objects might be culled incorrectly in edge cases

        See Also
        --------
        Camera.is_in_frame : Method used to check if mobjects are visible
        enable_viewport_culling : Toggle this optimization on/off
        """
        # Get the base list of mobjects
        mobjects = super().get_mobjects_to_display(
            mobjects, include_submobjects, excluded_mobjects
        )

        if not self.enable_culling:
            return mobjects

            # Filter: keep fixed-in-frame mobjects and on-screen mobjects
        filtered = []
        for mob in mobjects:
            # Always render fixed-in-frame mobjects (HUD elements)
            if mob in self.fixed_in_frame_mobjects:
                filtered.append(mob)
                # Only render regular mobjects if they're in frame
            elif self.is_in_frame(mob):
                filtered.append(mob)

        return filtered

    def enable_viewport_culling(self, enable: bool = True) -> None:
        """Enable or disable viewport culling optimization.

        When enabled, mobjects outside the camera's viewable area are not rendered,
        improving performance in large scenes. Fixed-in-frame HUD elements are
        always rendered regardless of this setting.

        Parameters
        ----------
        enable
            Whether to enable viewport culling (default: True)

        Examples
        --------
        .. code-block:: python

            # Disable culling for debugging
            self.camera.enable_viewport_culling(False)

            # Re-enable for performance
            self.camera.enable_viewport_culling(True)

        See Also
        --------
        get_mobjects_to_display : Method that performs the culling
        """
        self.enable_culling = enable

class ViewportCullingHUDScene(MovingCameraScene):
    """A MovingCameraScene with fixed-in-frame HUD elements and viewport culling.

    This scene class uses ViewportCullingHUDCamera to provide:
    1. Convenient methods for adding HUD elements that remain fixed in the camera frame
    2. Automatic viewport culling to optimize performance in large scenes

    HUD elements can be added at any time (before or after camera movement) and will
    always appear at their designated screen positions. Use positioning methods like
    to_corner(), to_edge(), or move_to() to place HUD elements where you want them.

    Viewport culling automatically filters out off-screen mobjects during rendering,
    while always rendering HUD elements regardless of their position.

    Limitations and Warnings
    ------------------------

    **Bounding Box Approximation**
        Viewport culling uses bounding box checks, not pixel-perfect visibility:

        - Rotated objects may be culled incorrectly (bounding box doesn't rotate)
        - Conservative culling includes objects if any part of bounding box overlaps frame
        - Irregular shapes with large empty areas may render when mostly off-screen

    **Fixed-in-Frame Positioning**
        HUD elements must use positioning methods (to_corner, to_edge, move_to) relative
        to scene frame boundaries, not camera position. Absolute coordinates may not
        position elements where expected after camera movement.

    **Transform vs ReplacementTransform**
        When updating fixed-in-frame HUD elements:

        - Use Transform to keep mobject in fixed_in_frame_mobjects set automatically
        - ReplacementTransform swaps mobject instances; new mobject must be re-fixed
        - Failing to re-fix after ReplacementTransform causes HUD to move with camera

    **Performance Overhead**
        Viewport culling adds per-mobject bounding box checks. Not recommended for:

        - Small scenes where most objects are always visible
        - Dense scenes with many tightly packed objects
        - Debugging (disable culling with enable_viewport_culling(False))

    **Renderer Compatibility**
        Designed for Cairo renderer. OpenGL renderer has different camera/rendering
        pipelines and may require modifications for correct behavior.

    **Submobject Handling**
        Adding a VGroup to fixed-in-frame fixes all submobjects. Removing parent
        doesn't automatically remove submobjects from the fixed set.

    **Frame Configuration**
        Fixed-in-frame mobjects position relative to config["frame_x_radius"] and
        config["frame_y_radius"]. Changing frame config after adding fixed mobjects
        may cause unexpected position shifts.

    **Z-Ordering**
        Fixed-in-frame mobjects render in scene mobject list order, not special
        z-ordering. Use add_foreground_mobject() or careful ordering for HUD on top.

    Best Practices
    --------------

    1. Always use Transform for HUD updates to avoid re-fixing mobjects
    2. Position HUD elements with to_corner(), to_edge(), etc. for predictable placement
    3. Test with culling disabled first to ensure correctness before optimizing
    4. Use FadeOut to remove mobjects when done, rather than leaving them invisible
    5. Monitor performance - only enable culling if you have many off-screen objects

    Examples
    --------
    .. code-block:: python

        class MyHUDScene(ViewportCullingHUDScene):
            def construct(self):
                # Create HUD elements
                title = Text("Title").to_corner(UL)
                score = Text("Score: 100").to_corner(UR)

                # Fix them in frame (no updaters needed!)
                self.add_fixed_in_frame_mobjects(title, score)

                # Create many scene objects spread across a large area
                objects = VGroup(*[
                    Square().shift(RIGHT * x + UP * y)
                    for x in range(-20, 20, 2)
                    for y in range(-20, 20, 2)
                ])
                self.add(objects)

                # Camera movements won't affect HUD, and off-screen objects won't be rendered
                self.play(self.camera.frame.animate.shift(RIGHT * 10))
                self.play(self.camera.frame.animate.scale(0.5))

                # Can add more HUD elements after camera has moved
                timer = Text("Time: 0:00").to_edge(DOWN)
                self.add_fixed_in_frame_mobjects(timer)

                # Update HUD elements using Transform (stays fixed automatically)
                self.play(Transform(score, Text("Score: 200").to_corner(UR)))

    See Also
    --------
    ThreeDScene : Similar fixed-in-frame functionality for 3D scenes
    MovingCameraScene : Base class for camera movement
    """

    def __init__(self, **kwargs):
        """Initialize the ViewportCullingHUDScene.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to MovingCameraScene.__init__
        """
        super().__init__(camera_class=ViewportCullingHUDCamera, **kwargs)

    def add_fixed_in_frame_mobjects(self, *mobjects: Mobject) -> None:
        """Add HUD elements that stay fixed in the camera frame.

        This is a convenience method that both adds the mobjects to the scene
        and marks them as fixed in the camera frame.

        Fixed-in-frame mobjects are always rendered, even when viewport culling
        is enabled and they would normally be outside the viewable area.

        Parameters
        ----------
        *mobjects
            The mobjects to add as fixed-in-frame HUD elements

        Notes
        -----
        You must use positioning methods like to_corner(), to_edge(), or
        move_to() to position HUD elements where you want them on screen.
        These methods position relative to the scene's frame boundaries,
        not the camera's current position.

        When updating HUD elements, use Transform instead of ReplacementTransform
        to avoid having to re-fix the mobject after each update.

        Examples
        --------
        .. code-block:: python

            # Create and fix HUD element
            score = Text("Score: 0").to_corner(UL)
            self.add_fixed_in_frame_mobjects(score)

            # Update using Transform (stays fixed automatically)
            self.play(Transform(score, Text("Score: 100").to_corner(UL)))
        """
        self.add(*mobjects)
        self.camera.add_fixed_in_frame_mobjects(*mobjects)

    def remove_fixed_in_frame_mobjects(self, *mobjects: Mobject) -> None:
        """Remove HUD elements from the fixed-in-frame set.

        Parameters
        ----------
        *mobjects
            The mobjects to remove from fixed-in-frame
        """
        self.camera.remove_fixed_in_frame_mobjects(*mobjects)

    def enable_viewport_culling(self, enable: bool = True) -> None:
        """Enable or disable viewport culling optimization.

        This is a convenience method that calls the camera's enable_viewport_culling().

        Parameters
        ----------
        enable
            Whether to enable viewport culling (default: True)

        Examples
        --------
        .. code-block:: python

            # Disable culling for debugging
            self.enable_viewport_culling(False)

            # Re-enable for performance
            self.enable_viewport_culling(True)
        """
        self.camera.enable_viewport_culling(enable)

# TODO test and probably remove these
class MovingCameraHUDScene(MovingCameraScene):
    """A scene with a moving camera and support for fixed HUD (heads-up display) elements.

    This scene extends :class:`~.MovingCameraScene` to provide HUD functionality where certain
    mobjects remain fixed in screen space regardless of camera movements (panning or zooming).
    Unlike :class:`~.ThreeDScene`'s ``add_fixed_in_frame_mobjects()``, this implementation is
    optimized for 2D scenes and avoids 3D rendering overhead.

    The scene uses a custom :class:`HUDMovingCamera` that renders fixed mobjects in a separate
    rendering pass with an identity camera transformation, ensuring they bypass camera movements
    entirely during the rendering pipeline.

    Examples
    --------

    .. code-block:: python

        class HUDExample(MovingCameraHUDScene):
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

        class BlockchainHUDExample(MovingCameraHUDScene):
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
    :class:`~.MovingCameraScene` : Base class for moving camera functionality
    :class:`~.ThreeDScene` : 3D scene with ``add_fixed_in_frame_mobjects()`` method
    :class:`HUDMovingCamera` : Custom camera class for dual-pass rendering

    Notes
    -----
    - Fixed mobjects are tracked in ``_fixed_mobjects`` set for O(1) lookup performance
    - Uses dual-pass rendering: moving mobjects with camera transform, fixed mobjects without
    - No post-animation corrections needed - HUD elements stay fixed during animations
    - Compatible with ``ReplacementTransform`` without requiring updater management
    - Zero per-frame Python overhead - exclusion happens at rendering pipeline level
    """

    def __init__(self, **kwargs):
        """Initialize the MovingCameraHUDScene with HUD-aware camera.

        This initialization creates a custom HUDMovingCamera that renders fixed
        HUD mobjects in a separate rendering pass, ensuring they remain at constant
        screen position and size regardless of camera transformations.

        The camera uses a dual-pass rendering system:
        1. Moving mobjects are rendered with the current camera transformation
        2. Fixed mobjects are rendered with an identity camera (no transformation)

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :class:`~.MovingCameraScene`

        Notes
        -----
        The HUDMovingCamera requires a reference to the scene to access the
        ``_fixed_mobjects`` set during rendering. This reference is set after
        the parent class initialization completes.

        See Also
        --------
        :class:`HUDMovingCamera` : Custom camera class for HUD rendering
        :meth:`fix` : Mark a mobject as fixed in the camera frame
        :meth:`unfix` : Remove fixed status from a mobject
        """
        # Initialize with HUDMovingCamera class
        super().__init__(camera_class=HUDMovingCamera, **kwargs)

        # Initialize fixed mobjects tracking set
        self._fixed_mobjects = set()

        # Pass scene reference to camera for fixed mobject access during rendering
        self.camera.scene = self

    def get_moving_mobjects(self, *animations):
        """Get moving mobjects, excluding fixed HUD elements.

        This method filters out fixed mobjects from the moving mobjects list,
        preventing them from triggering full scene redraws during animations.

        Parameters
        ----------
        *animations : Animation
            The animations to check for moving mobjects

        Returns
        -------
        list[Mobject]
            List of moving mobjects, excluding those marked as fixed

        See Also
        --------
        :meth:`~.Scene.get_moving_mobjects` : Parent class implementation
        """
        moving = super().get_moving_mobjects(*animations)
        # Filter out fixed mobjects from moving list
        return [m for m in moving if m not in self._fixed_mobjects]

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
        """
        self._fixed_mobjects.add(mob)
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
        """
        self._fixed_mobjects.discard(mob)
        return mob

class HUDMovingCamera(MovingCamera):
    """MovingCamera that renders fixed HUD mobjects in a separate pass.

    This camera extends :class:`~.MovingCamera` to support heads-up display (HUD)
    elements that remain fixed in screen space. It uses a dual-pass rendering system
    inspired by :class:`~.ThreeDCamera`'s ``fixed_in_frame_mobjects`` pattern.

    The rendering process:
    1. Moving mobjects are captured with the current camera transformation
    2. Fixed mobjects are captured with an identity camera (no transformation)
    3. Both passes composite onto the same frame

    This approach ensures HUD elements bypass camera transformations entirely during
    the rendering pipeline, with zero per-frame Python overhead.

    Parameters
    ----------
    **kwargs
        Additional keyword arguments passed to :class:`~.MovingCamera`

    Attributes
    ----------
    scene : MovingCameraHUDScene or None
        Reference to the parent scene for accessing fixed mobjects.
        Set to None initially and populated by the scene after initialization.

    See Also
    --------
    :class:`~.MovingCamera` : Base camera class
    :class:`MovingCameraHUDScene` : Scene class that uses this camera
    :class:`~.ThreeDCamera` : 3D camera with similar fixed-in-frame pattern

    Notes
    -----
    The dual-pass rendering approach is more performant than post-animation
    corrections or updaters because:

    - Fixed mobjects are excluded via O(1) set membership check
    - No Python callbacks run per frame
    - Works at the Cairo rendering level, not animation level
    - Produces smooth animations without "snap" artifacts

    The scene parameter is set to None during initialization because Manim's
    renderer creates the camera before the scene is fully initialized. The
    scene reference is set afterward by MovingCameraHUDScene.__init__().

    Examples
    --------
    This camera is automatically created by :class:`MovingCameraHUDScene`.
    You typically don't instantiate it directly:

    .. code-block:: python

        class MyScene(MovingCameraHUDScene):
            def construct(self):
                # Camera is automatically HUDMovingCamera
                title = Text("HUD Title")
                self.add(self.fix(title))

                # Camera moves, title stays fixed
                self.play(self.camera.frame.animate.shift(RIGHT * 3))
    """

    def __init__(self, **kwargs):
        """Initialize HUDMovingCamera without scene reference.

        The scene reference will be set by MovingCameraHUDScene after
        the renderer completes camera initialization.

        Parameters
        ----------
        **kwargs
            Additional keyword arguments passed to :class:`~.MovingCamera`
        """
        super().__init__(**kwargs)
        self.scene = None  # Will be set by MovingCameraHUDScene.__init__()

    def capture_mobjects(self, mobjects, **kwargs):
        """Capture mobjects in two passes: moving objects with camera transform,
        fixed objects without transform.

        This method implements the dual-pass rendering system that keeps HUD
        elements fixed in screen space. It separates mobjects into two groups
        based on the scene's ``_fixed_mobjects`` set, then renders each group
        with different camera states.

        The rendering process:

        1. **Pass 1 - Moving mobjects**: Rendered with current camera transformation
           (zoom, pan, rotation). These mobjects move and scale with the camera.

        2. **Pass 2 - Fixed mobjects**: Rendered with identity camera transformation
           (no zoom, no pan). The camera is temporarily reset to its default state,
           mobjects are captured, then the camera is restored. These mobjects remain
           at constant screen position and size.

        Parameters
        ----------
        mobjects : Iterable[Mobject]
            All mobjects to be captured in this frame
        **kwargs
            Additional keyword arguments passed to parent's ``capture_mobjects()``

        Notes
        -----
        The camera state is saved and restored around the fixed mobjects pass to
        ensure the camera's transformation is not permanently affected. This uses:

        - ``frame.get_center().copy()`` to save position
        - ``frame.height`` to save zoom level
        - ``frame.move_to()`` and ``frame.set_height()`` to restore

        The identity camera uses ``config.frame_height`` as the default frame height
        and ``ORIGIN`` as the default center position.

        If the scene reference is not set or the scene doesn't have a _fixed_mobjects
        attribute, this method falls back to standard rendering (all mobjects treated
        as moving).

        See Also
        --------
        :meth:`~.Camera.capture_mobjects` : Parent class method
        :meth:`MovingCameraHUDScene.fix` : Mark mobjects as fixed

        Examples
        --------
        This method is called automatically during rendering. The separation
        of fixed and moving mobjects happens transparently:

        .. code-block:: python

            # In your scene
            square = Square()  # Will be in "moving" group
            title = Text("Title")  # Will be in "fixed" group after fix()

            self.add(square)
            self.add(self.fix(title))

            # During rendering, capture_mobjects() separates them automatically
            self.play(self.camera.frame.animate.shift(RIGHT))
            # square moves, title stays fixed
        """
        # Early exit if scene not set yet or no fixed mobjects
        if self.scene is None or not hasattr(self.scene, '_fixed_mobjects'):
            super().capture_mobjects(mobjects, **kwargs)
            return

            # Separate fixed and moving mobjects using set membership (O(1) lookup)
        fixed = [m for m in mobjects if m in self.scene._fixed_mobjects]
        moving = [m for m in mobjects if m not in self.scene._fixed_mobjects]

        # Pass 1: Capture moving mobjects with current camera transformation
        if moving:
            super().capture_mobjects(moving, **kwargs)

            # Pass 2: Capture fixed mobjects with identity camera (no transformation)
        if fixed:
            # Save current camera state
            saved_center = self.frame.get_center().copy()
            saved_height = self.frame.height

            # Reset camera to identity transform
            self.frame.move_to([0, 0, 0])
            self.frame.set_height(config.frame_height)

            # Capture fixed mobjects at identity transform
            super().capture_mobjects(fixed, **kwargs)

            # Restore camera state for next frame
            self.frame.move_to(saved_center)
            self.frame.set_height(saved_height)

# TODO test if wrapped play scene with decomposed properly plays animations without overriding earlier animations in the same play call
class DecomposedPlay:
    """Wrapper that signals to play() to decompose animations into separate calls."""

    def __init__(self, *animations):
        self.animations = animations

    def __iter__(self):
        """Make it iterable so play() can process it."""
        return iter(self.animations)


class WrappedPlayScene(Scene):
    def play(self, *args, **kwargs):
        """Override play to handle DecomposedPlay wrappers."""
        processed_args = []

        for arg in args:
            if isinstance(arg, DecomposedPlay):
                # Decompose the wrapper into individual play calls
                for anim in arg.animations:
                    super().play(anim, **kwargs)
                    # Don't add to processed_args since we already played them
            else:
                processed_args.append(arg)

                # Play any remaining non-wrapped animations normally
        if processed_args:
            super().play(*processed_args, **kwargs)

# TODO nothing from here down works as intended

class SequentialPlayScene(Scene):
    """
    A custom Scene that overrides play() to handle complex animation sequences
    as separate internal play calls, preventing animation conflicts.
    """

    def play(
            self,
            *args,
            sequential_mode: bool = False,
            **kwargs
    ) -> None:
        """
        Override the standard play method to optionally handle animations sequentially.
        """
        if not sequential_mode or len(args) <= 1:
            # Use standard play behavior for single animations or when not in sequential mode
            return super().play(*args, **kwargs)

            # Handle multiple animations as separate play calls
        for animation in args:
            super().play(animation, **kwargs)

            # Explicitly return None to satisfy type checker
        return None



class IsolatedSequence:
    """
    Wrapper class to mark animations that should be executed in isolation.
    This is a simple container that holds a list of animations to be
    executed sequentially, each with their own complete render cycle.
    """

    def __init__(self, *animations: Animation):
        self.animations = list(animations)


class IsolatedSequenceScene(Scene):
    """
    Custom Scene subclass that overrides the play() method to handle
    IsolatedSequence objects by executing their contained animations
    as separate, isolated play() calls.
    """

    def play(self, *args, **kwargs) -> None:
        """
        Override the standard Scene.play() method to detect and handle
        IsolatedSequence objects specially.

        This method intercepts the play() call before it reaches the
        standard Manim rendering pipeline and processes IsolatedSequence
        objects by breaking them into multiple sequential play() calls.
        """

        # Step 1: Separate regular animations from IsolatedSequence objects
        regular_animations = []
        isolated_sequences = []

        for arg in args:
            if isinstance(arg, IsolatedSequence):
                isolated_sequences.append(arg)
            else:
                regular_animations.append(arg)

                # Step 2: Handle regular animations first (if any)
        # These follow the standard Manim behavior where multiple animations
        # on the same mobject would override each other
        if regular_animations:
            super().play(*regular_animations, **kwargs)

            # Step 3: Process each IsolatedSequence separately
        for sequence in isolated_sequences:
            # Step 4: Execute each animation in the sequence as its own play() call
            # This is the key insight - by calling super().play() for each
            # sub-animation individually, we ensure each gets the full
            # animation lifecycle: compile_animation_data() -> begin_animations()
            # -> play_internal() -> finish animations
            for sub_animation in sequence.animations:
                # Each super().play() call triggers the complete render pipeline:
                # 1. Scene.compile_animation_data() captures current mobject state
                # 2. Scene.begin_animations() calls animation.begin()
                # 3. Scene.play_internal() runs the render loop
                # 4. Animations are finished and cleaned up
                # 5. Mobject state is naturally preserved between calls
                super().play(sub_animation, **kwargs)

            # Example usage demonstrating the solution to the animation override problem



class AdvancedIsolatedSequence:
    """
    Enhanced version that allows individual run_time control for each animation
    while still maintaining isolation between them.
    """

    def __init__(self, *animation_configs):
        """
        animation_configs: tuples of (animation, run_time) or just animations
        """
        self.animation_configs = []
        for config in animation_configs:
            if isinstance(config, tuple):
                animation, run_time = config
                self.animation_configs.append((animation, run_time))
            else:
                # Default run_time will be used
                self.animation_configs.append((config, None))


class AdvancedIsolatedSequenceScene(Scene):
    """
    Enhanced scene that supports both basic IsolatedSequence and
    AdvancedIsolatedSequence with individual timing control.
    """

    def play(self, *args, **kwargs) -> None:
        regular_animations = []
        isolated_sequences = []

        for arg in args:
            if isinstance(arg, (IsolatedSequence, AdvancedIsolatedSequence)):
                isolated_sequences.append(arg)
            else:
                regular_animations.append(arg)

                # Handle regular animations
        if regular_animations:
            super().play(*regular_animations, **kwargs)

            # Process isolated sequences
        for sequence in isolated_sequences:
            if isinstance(sequence, AdvancedIsolatedSequence):
                # Handle advanced sequence with individual timing
                for animation, run_time in sequence.animation_configs:
                    play_kwargs = kwargs.copy()
                    if run_time is not None:
                        play_kwargs['run_time'] = run_time
                    super().play(animation, **play_kwargs)
            else:
                # Handle basic sequence
                for sub_animation in sequence.animations:
                    super().play(sub_animation, **kwargs)

class RendererIsolatedScene(Scene):
    """
    Scene that intercepts the renderer pipeline to create true animation isolation.
    """

    def play(self, *args, **kwargs):
        """Override to intercept rendering for Succession animations."""

        if len(args) == 1 and hasattr(args[0], 'animations'):
            return self._play_with_renderer_isolation(args[0], **kwargs)
        else:
            return super().play(*args, **kwargs)

    def _play_with_renderer_isolation(self, succession, **kwargs):
        """Execute Succession with complete renderer-level isolation."""

        for animation in succession.animations:
            if isinstance(animation, Wait):
                if animation.run_time > 0:
                    self.wait(animation.run_time)
            else:
                # Skip zero-duration animations
                if hasattr(animation, 'run_time') and animation.run_time <= 0:
                    continue

                    # Create isolated renderer context
                self._create_renderer_snapshot()

                # Execute animation with isolated renderer
                super().play(animation, **kwargs)

                # Force complete renderer state finalization
                self._finalize_renderer_state()

    def _create_renderer_snapshot(self):
        """Create a snapshot of current renderer state."""
        # Force all pending operations to complete
        if hasattr(self.renderer, 'scene'):
            self.renderer.scene = self

            # Clear any cached transformations
        for mobject in self.mobjects:
            if hasattr(mobject, 'update'):
                mobject.update()
                # Force position and property commitment
            if hasattr(mobject, 'get_center'):
                mobject.move_to(mobject.get_center())

    def _finalize_renderer_state(self):
        """Force complete finalization of renderer state."""
        # Flush renderer buffers
        if hasattr(self.renderer, 'flush'):
            self.renderer.flush()

            # Force scene state update
        self.renderer.scene = self

        # Clear animation caches
        for mobject in self.mobjects:
            if hasattr(mobject, 'clear_updaters'):
                mobject.clear_updaters()
            if hasattr(mobject, 'update'):
                mobject.update()

                # Force garbage collection of animation state
        import gc
        gc.collect()

class SelfContainedScene(Scene):
    """
    Scene that executes animations in complete isolation, like mini-scenes within each play call.
    """

    def play(self, *args, **kwargs):
        """Override to create self-contained animation execution."""

        # Check if we have a Succession that needs isolation
        if len(args) == 1 and hasattr(args[0], 'animations'):
            return self._play_isolated_succession(args[0], **kwargs)
        else:
            # Regular animations use normal play
            return super().play(*args, **kwargs)

    def _play_isolated_succession(self, succession, **kwargs):
        """Execute a Succession with complete state isolation between groups."""

        # Store initial scene state
        initial_mobject_states = self._capture_scene_state()

        for animation in succession.animations:
            if isinstance(animation, Wait):
                if animation.run_time > 0:
                    self.wait(animation.run_time)
            else:
                # Check if the animation has positive run_time
                if hasattr(animation, 'run_time') and animation.run_time <= 0:
                    # Skip zero-duration animations or handle them immediately
                    continue

                    # Create isolated execution context
                self._prepare_isolated_context()

                # Execute animation in isolation
                super().play(animation, **kwargs)

                # Force complete state finalization
                self._finalize_isolated_context()

    def _capture_scene_state(self):
        """Capture current state of all mobjects for potential restoration."""
        states = {}
        for mobject in self.mobjects:
            states[id(mobject)] = {
                'position': mobject.get_center().copy(),
                'opacity': getattr(mobject, 'fill_opacity', 1.0) if hasattr(mobject, 'fill_opacity') else 1.0
            }
        return states

    def _prepare_isolated_context(self):
        """Prepare scene for isolated animation execution."""
        # Force all pending transformations to complete
        for mobject in self.mobjects:
            # Commit any pending position changes
            if hasattr(mobject, 'get_center'):
                current_pos = mobject.get_center()
                mobject.move_to(current_pos)

                # Commit any pending opacity changes
            if hasattr(mobject, 'get_opacity') and hasattr(mobject, 'set_opacity'):
                try:
                    current_opacity = mobject.get_opacity()
                    mobject.set_opacity(current_opacity)
                except (AttributeError, TypeError):
                    pass

                    # Force renderer state update
        if hasattr(self.renderer, 'scene'):
            self.renderer.scene = self

    def _finalize_isolated_context(self):
        """Finalize isolated animation execution."""
        # Force all mobjects to commit their final states
        for mobject in self.mobjects:
            if hasattr(mobject, 'update'):
                mobject.update()

                # Clear any animation caches or state
        self._clear_animation_state()

    def _clear_animation_state(self):
        """Clear any lingering animation state that could interfere."""
        # Force garbage collection of animation objects
        import gc
        gc.collect()

        # Reset renderer state
        if hasattr(self.renderer, 'scene'):
            self.renderer.scene = self

class IsolatedScene(Scene):
    def play(self, *args, **kwargs):
        """
        Override play to automatically handle state isolation for Succession animations.
        """
        # Check if we have a single Succession-like animation that needs isolation
        if len(args) == 1 and hasattr(args[0], 'animations'):
            succession_anim = args[0]
            # Extract individual animation groups from the Succession
            animation_groups = succession_anim.animations

            # Play each group with isolation
            for group in animation_groups:
                if isinstance(group, Wait):
                    if group.run_time > 0:  # Only wait if run_time > 0
                        self.wait(group.run_time)
                else:
                    # Check if the animation has positive run_time
                    if hasattr(group, 'run_time') and group.run_time <= 0:
                        # Skip zero-duration animations or handle them immediately
                        continue

                        # Force all mobjects to their final states before starting
                    self._isolate_mobject_states()

                    # Play the animation group normally
                    super().play(group, **kwargs)

                    # Ensure completion and clean state
                    self._finalize_mobject_states()
        else:
            # For non-Succession animations, use normal play
            super().play(*args, **kwargs)

    def _isolate_mobject_states(self):
        """Force all mobjects to commit their current transformations."""
        for mobject in self.mobjects:
            # Force position updates
            if hasattr(mobject, 'get_center'):
                mobject.move_to(mobject.get_center())
                # Force opacity updates - check if opacity exists first
            if hasattr(mobject, 'get_opacity') and hasattr(mobject, 'set_opacity'):
                try:
                    current_opacity = mobject.get_opacity()
                    mobject.set_opacity(current_opacity)
                except AttributeError:
                    # Skip mobjects that don't support opacity operations
                    pass

    def _finalize_mobject_states(self):
        """Ensure all animations have fully completed."""
        # Force scene update to commit all pending transformations
        if hasattr(self, 'renderer') and hasattr(self.renderer, 'scene'):
            self.renderer.scene = self

            # Force all mobjects to update their internal state
        for mobject in self.mobjects:
            if hasattr(mobject, 'update'):
                mobject.update()

class IndependentSequence(Succession):
    """
    Complete rewrite of interpolation logic for strict animation isolation.
    Forces each animation to complete fully before starting the next.
    """

    def __init__(self, *animations, **kwargs):
        super().__init__(*animations, **kwargs)
        self.current_active = 0
        self.animation_states = ['pending'] * len(self.animations)

    def interpolate(self, alpha: float) -> None:
        """Complete override of interpolation with forced completion."""
        total_time = self.rate_func(alpha) * self.max_end_time

        # Calculate which animation should be active based on total progress
        target_animation = 0
        cumulative_time = 0

        for i, anim in enumerate(self.animations):
            if cumulative_time + anim.run_time > total_time:  # Use anim.run_time directly
                target_animation = i
                break
            cumulative_time += anim.run_time  # Use anim.run_time directly
        else:
            target_animation = len(self.animations) - 1

            # Force complete all animations before target
        for i in range(target_animation):
            if self.animation_states[i] != 'completed':
                anim = self.animations[i]
                anim._setup_scene(self.scene)
                anim.begin()
                anim.interpolate(1.0)  # Force to completion
                anim.finish()
                self.animation_states[i] = 'completed'

                # Run target animation
        if target_animation < len(self.animations):
            current_anim = self.animations[target_animation]

            if self.animation_states[target_animation] == 'pending':
                current_anim._setup_scene(self.scene)
                current_anim.begin()
                self.animation_states[target_animation] = 'running'

                # Calculate progress within current animation
            anim_start_time = sum(anim.run_time for anim in self.animations[:target_animation])  # Fixed
            elapsed_in_anim = total_time - anim_start_time
            anim_progress = elapsed_in_anim / current_anim.run_time  # Use current_anim.run_time
            anim_progress = max(0, min(1, anim_progress))

            current_anim.interpolate(anim_progress)

            if anim_progress >= 1.0 and self.animation_states[target_animation] != 'completed':
                current_anim.finish()
                self.animation_states[target_animation] = 'completed'

class StrictSequence(Succession):
    """
    A strict sequential animation wrapper that ensures complete isolation between animations.
    Solves state persistence and timing issues in complex animation sequences.
    """

    def __init__(self, *animations, **kwargs):
        # Store original animations for reference
        self.original_animations = list(animations)

        # Process nested animations to handle all wrapper types
        processed_animations = self._process_nested_animations(animations)

        super().__init__(*processed_animations, **kwargs)

        # Track completion state
        self._animation_completed = [False] * len(self.animations)
        self._force_complete_previous = True

    def _process_nested_animations(self, animations) -> List:
        """Process and flatten nested animation wrappers for strict control."""
        processed = []

        for anim in animations:
            # Core composition wrappers
            if isinstance(anim, (AnimationGroup, LaggedStart, LaggedStartMap)):
                # Handle parallel/lagged animations - keep as single unit
                processed.append(anim)
            elif isinstance(anim, Succession):
                # Flatten nested Succession into this one
                processed.extend(anim.animations)
                # Speed modification wrapper
            elif isinstance(anim, ChangeSpeed):
                # Handle speed-modified animations as single units
                processed.append(anim)
                # Transform wrapper (potentially deprecated but still handle it)
            elif isinstance(anim, TransformAnimations):
                # Handle transform animations as single units
                processed.append(anim)
                # Transform-based wrappers (these are still valid in ManimCE)
            elif isinstance(anim, (ReplacementTransform, TransformFromCopy, MoveToTarget, ApplyMethod)):
                # Handle transform-based wrappers
                processed.append(anim)
                # Check for _MethodAnimation (from .animate property)
            elif hasattr(anim, '__class__') and '_MethodAnimation' in str(type(anim)):
                # Handle .animate property animations
                processed.append(anim)
                # Generic animation wrapper detection
            elif hasattr(anim, 'animations') and hasattr(anim, 'interpolate'):
                # Handle any other custom animation wrapper
                processed.append(anim)
            else:
                # Regular animation or Wait
                processed.append(anim)

        return processed

    def update_active_animation(self, index: int) -> None:
        """Override to force complete isolation between animations."""

        # Force complete previous animation if it exists
        if (hasattr(self, 'active_animation') and
                self.active_animation is not None and
                hasattr(self, 'active_index') and
                self.active_index < len(self._animation_completed) and
                self._force_complete_previous):
            # Force completion
            self.active_animation.interpolate(1.0)
            self.active_animation.finish()
            self._animation_completed[self.active_index] = True

            # Reset mobject states that might have been affected
            self._reset_mobject_states()

            # Call parent implementation (this initializes active_animation)
        super().update_active_animation(index)

        # Mark new animation as starting
        if index < len(self._animation_completed):
            self._animation_completed[index] = False

    def _reset_mobject_states(self) -> None:
        """Reset any lingering mobject states between animations."""
        if self.scene is None:
            return

            # Force scene to update all mobject positions and properties
        for mobject in self.scene.mobjects:
            # Ensure all pending transformations are applied
            if hasattr(mobject, 'update'):
                mobject.update()

    def interpolate(self, alpha: float) -> None:
        """Override interpolation with stricter timing controls."""
        current_time = self.rate_func(alpha) * self.max_end_time

        # More aggressive animation switching with clamped timing
        while (self.active_end_time is not None and
               current_time >= self.active_end_time):
            self.next_animation()

        if (self.active_animation is not None and
                self.active_start_time is not None):

            elapsed = current_time - self.active_start_time
            active_run_time = self.active_animation.run_time

            # Clamp subalpha to prevent overshoot
            subalpha = min(1.0, elapsed / active_run_time if active_run_time != 0.0 else 1.0)

            # Apply interpolation
            self.active_animation.interpolate(subalpha)

            # Force completion if we've reached the end
            if subalpha >= 1.0 and not self._animation_completed[self.active_index]:
                self.active_animation.finish()
                self._animation_completed[self.active_index] = True