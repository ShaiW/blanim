from __future__ import annotations

from typing import Optional, Any, Literal, Type

from manim import *

##all sort of stuff that manim should have but doesn't

##########START Properly Documented Stuff##########

# Reccomend moving everything to HUD2DScene
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

#####START everything related to HUD2DScene#####
#TODO properly document all this AND create examples in common_examples.py for everything added
#TODO test everything in examples AND then correct the documentation here
class HUD2DScene(ThreeDScene):
    """A 2D scene with heads-up display (HUD) support using ThreeDScene's fixed-in-frame system.

    This scene extends :class:`~.ThreeDScene` but configures the camera for orthographic 2D viewing
    (looking straight down the Z-axis). It provides access to :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects`
    for creating HUD elements that remain fixed in the camera frame regardless of camera movements.

    The scene includes an integrated :class:`UniversalNarrationManager` that provides convenient
    methods for managing dual HUD text elements (upper narration and lower caption) using the
    primer pattern. This eliminates the need for manual primer creation and management.

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

    Examples
    --------

    **Using Convenience Methods (Recommended)**:

    .. code-block:: python

        class ConvenienceHUDExample(HUD2DScene):
            def construct(self):
                # Create scene content
                square = Square(color=BLUE)
                self.add(square)

                # Use convenience methods for HUD text
                self.narrate("Main Title")  # Upper narration
                self.caption("Subtitle text")  # Lower caption

                # Camera movement - HUD stays fixed
                self.move_camera(frame_center=RIGHT * 2, run_time=2)

                # Clear HUD elements
                self.clear_narrate()
                self.clear_caption()

    **Temporary Narration with Auto-Clear**:

    .. code-block:: python

        class TemporaryNarrationExample(HUD2DScene):
            def construct(self):
                square = Square()
                self.add(square)

                # Display narration for 2 seconds, then auto-clear
                self.narrate_and_clear("This appears briefly", display_time=2.0)

                # Display caption for 3 seconds, then auto-clear
                self.narrate_and_clear("Lower caption", display_time=3.0, upper=False)

    **Manual Primer Pattern (Advanced)**:

    .. code-block:: python

        class ManualPrimerExample(HUD2DScene):
            def construct(self):
                # Access the narration manager directly
                narration = self.narration.get_narration("Custom Title")
                self.play(Transform(self.narration.current_narration_text, narration))

                caption = self.narration.get_caption("Custom Subtitle")
                self.play(Transform(self.narration.current_caption_text, caption))

                # Camera movement
                self.move_camera(frame_center=LEFT * 2, run_time=2)

    **Custom Primer Configuration**:

    .. code-block:: python

        class CustomPrimerExample(HUD2DScene):
            def setup(self):
                super().setup()
                # Override default narration manager with custom settings
                self.narration = UniversalNarrationManager(
                    self,
                    max_narration_chars=150,  # Larger capacity
                    max_caption_chars=200,
                    narration_font_size=48,   # Larger font
                    caption_font_size=32
                )

            def construct(self):
                self.narrate("Large Title Text")
                self.caption("Large Caption Text")

    See Also
    --------
    :class:`~.ThreeDScene` : Parent class providing fixed-in-frame functionality
    :class:`UniversalNarrationManager` : Integrated HUD text manager with primer pattern
    :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` : Method for adding HUD elements
    :meth:`~.ThreeDScene.move_camera` : Camera movement method (NOT MovingCameraScene API)
    :class:`MovingCameraFixedLayerScene` : Alternative 2D HUD implementation (less performant)

    Notes
    -----
    - Camera is set to orthographic 2D view (phi=0, theta=-90°) in :meth:`setup`
    - Integrated :class:`UniversalNarrationManager` handles primer creation automatically
    - Uses :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` for HUD elements
    - **Spaces do NOT count** toward primer character capacity
    - **Default capacity**: 100 chars for narration, 100 chars for caption
    - **Only Transform works**: Do not use ReplacementTransform or other animations
    - **Do NOT mix text types**: Currently supports Text only (MathTex/Tex support planned)
    - **Camera API**: Use ``move_camera(frame_center=...)``, not ``camera.frame.animate``
    - **Renderer agnostic**: Cairo/OpenGL choice is irrelevant for 2D-only usage
    - This is a temporary workaround; proper 2D HUD scene is planned

    Attributes
    ----------
    narration : UniversalNarrationManager
        Integrated narration manager for HUD text elements. Automatically initialized
        in :meth:`setup` with default settings. Provides access to primer mobjects
        and text generation methods.
    """
    narration_text_type: Literal["Tex", "MathTex", "Text"] = "Tex"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the HUD2DScene.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :class:`~.ThreeDScene`

        Notes
        -----
        The narration manager is initialized to None here and will be created
        in :meth:`setup` to ensure the rendering infrastructure is ready.
        """
        super().__init__(**kwargs)

        self.narration: Optional[UniversalNarrationManager] = None # manim warns against overriding init
        self.transcript: Optional[TranscriptManager] = None # manim warns against overriding init

    def setup(self) -> None:
        """Set up the scene with 2D orthographic camera orientation.

        This method is called automatically before :meth:`construct`. It configures
        the camera to look straight down the Z-axis, providing a 2D view while
        maintaining access to 3D scene features like fixed-in-frame mobjects.

        .. warning::
            Do not override this method or modify camera orientation after setup.
            This scene is designed exclusively for 2D use.

        Examples
        --------
        .. code-block:: python

            class MyScene(HUD2DScene):
                def construct(self):
                    # setup() has already been called automatically
                    self.narrate("Scene is ready")

        See Also
        --------
        :meth:`construct` : Main method for defining scene content
        :class:`UniversalNarrationManager` : The narration manager created here

        Notes
        -----
        Sets camera orientation to ``phi=0, theta=-90 * DEGREES`` for top-down 2D view.
        Creates the :class:`UniversalNarrationManager` instance with default settings.
        """
        super().setup()
        # Set camera to orthographic 2D view (looking straight down)
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)

        # Create 2D frame wrapper for MovingCameraScene API compatibility
        self.camera.frame = Frame2DWrapper(self.camera)

        # Initialize universal narration manager with dual text support
        self.narration = UniversalNarrationManager(
            self,
            text_type=self.narration_text_type
        )

        self.transcript = TranscriptManager(self)

    def tear_down(self) -> None:
        """Write transcript before tearing down."""
        if self.transcript:
            # noinspection PyProtectedMember
            self.transcript._write_transcript()  # type: ignore[attr-defined]  # noqa: SLF001
        super().tear_down()

    def play(self, *args, **kwargs) -> None:
        """Override play to handle Frame2DAnimateWrapper."""
        processed_args = []
        for arg in args:
            if isinstance(arg, Frame2DAnimateWrapper):
                built = arg.build()
                if built is not None:
                    processed_args.append(built)
            else:
                processed_args.append(arg)
        return super().play(*processed_args, **kwargs)

    def narrate(self,
                text: str,  # Removed Annotated
                run_time: float = 0.5,
                **kwargs: Any
                ) -> None:
        """Update upper narration text with animation.

        Uses the primer pattern to transform the upper narration text. The primer
        mobject is mutated to display the new text while remaining fixed in frame.

        .. warning::
            **Raw Strings Required for Tex/MathTex**

            When using ``narration_text_type = "Tex"`` or ``"MathTex"``, you MUST use
            raw strings (``r"..."``) to prevent Python from interpreting backslashes.

            **Special Characters Requiring Escape in LaTeX:**

            - ``\\`` → ``\\\\`` (backslash)
            - ``$`` → ``\\$`` (dollar sign)
            - ``%`` → ``\\%`` (percent)
            - ``&`` → ``\\&`` (ampersand)
            - ``#`` → ``\\#`` (hash)
            - ``_`` → ``\\_`` (underscore)
            - ``^`` → ``\\^`` (caret)
            - ``{`` → ``\\{`` (left brace)
            - ``}`` → ``\\}`` (right brace)
            - ``~`` → ``\\~`` (tilde)

        Parameters
        ----------
        text : str
            Narration text to display at the top of the screen.
            See warning above for LaTeX requirements.
        run_time : float
            Duration of the transform animation in seconds
        **kwargs
            Additional arguments passed to :meth:`~.Scene.play`, such as
            ``rate_func`` or ``lag_ratio``

        Examples
        --------
        .. code-block:: python

            class NarrateExample(HUD2DScene):
                def construct(self):
                    square = Square()
                    self.add(square)

                    # Basic usage
                    self.narrate(r"Step 1: Create square")
                    self.wait(1)

                    # With custom animation timing
                    self.narrate(r"Step 2: Transform", run_time=1.0)
                    self.play(square.animate.scale(2))

        See Also
        --------
        :meth:`caption` : Update lower caption text
        :meth:`clear_narrate` : Clear upper narration
        :meth:`narrate_and_clear` : Display and auto-clear narration
        :class:`UniversalNarrationManager` : The underlying manager

        Notes
        -----
        - Uses :class:`~.Transform` animation on the primer mobject
        - Text remains fixed in frame during camera movements
        - Character count (excluding spaces) must not exceed ``max_narration_chars``
        - The primer mobject is mutated, not replaced
        - **Default text type**: Tex (text mode with ``$...$`` for math expressions)
        - **Always use raw strings** (``r"..."``) when using Tex or MathTex
        """
        narration = self.narration.get_narration(text)
        self.play(
            Transform(self.narration.current_narration_text, narration),
            run_time=run_time,
            **kwargs
        )

    def caption(self,
                text: str,  # Removed Annotated
                run_time: float = 0.5,
                **kwargs: Any
                ) -> None:
        """Update lower caption text with animation.

        Uses the primer pattern to transform the lower caption text. The primer
        mobject is mutated to display the new text while remaining fixed in frame.

        .. warning::
            **Raw Strings Required for Tex/MathTex**

            When using ``narration_text_type = "Tex"`` or ``"MathTex"``, you MUST use
            raw strings (``r"..."``) to prevent Python from interpreting backslashes.

            **Special Characters Requiring Escape in LaTeX:**

            - ``\\`` → ``\\\\`` (backslash)
            - ``$`` → ``\\$`` (dollar sign)
            - ``%`` → ``\\%`` (percent)
            - ``&`` → ``\\&`` (ampersand)
            - ``#`` → ``\\#`` (hash)
            - ``_`` → ``\\_`` (underscore)
            - ``^`` → ``\\^`` (caret)
            - ``{`` → ``\\{`` (left brace)
            - ``}`` → ``\\}`` (right brace)
            - ``~`` → ``\\~`` (tilde)

        Parameters
        ----------
        text : str
            Caption text to display at the bottom of the screen.
            See warning above for LaTeX requirements.
        run_time : float
            Duration of the transform animation in seconds
        **kwargs
            Additional arguments passed to :meth:`~.Scene.play`, such as
            ``rate_func`` or ``lag_ratio``

        Examples
        --------
        .. code-block:: python

            class CaptionExample(HUD2DScene):
                def construct(self):
                    circle = Circle()
                    self.add(circle)

                    # Basic usage with Tex (default)
                    self.caption(r"Detailed explanation here")
                    self.wait(1)

                    # With math notation
                    self.caption(r"The radius is $r = 5$")
                    self.wait(1)

                    # With custom rate function
                    from manim import smooth
                    self.caption(r"Smooth transition", run_time=1.0, rate_func=smooth)

        See Also
        --------
        :meth:`narrate` : Update upper narration text
        :meth:`clear_caption` : Clear lower caption
        :meth:`narrate_and_clear` : Display and auto-clear caption
        :class:`UniversalNarrationManager` : The underlying manager

        Notes
        -----
        - Uses :class:`~.Transform` animation on the primer mobject
        - Text remains fixed in frame during camera movements
        - Character count (excluding spaces) must not exceed ``max_caption_chars``
        - The primer mobject is mutated, not replaced
        - **Default text type**: Tex (text mode with ``$...$`` for math expressions)
        - **Always use raw strings** (``r"..."``) when using Tex or MathTex
        """
        caption = self.narration.get_caption(text)
        self.play(
            Transform(self.narration.current_caption_text, caption),
            run_time=run_time,
            **kwargs
        )

    def clear_narrate(self, run_time: float = 0.5, **kwargs: Any) -> None:
        """Clear upper narration text with animation.

        Transforms the narration to invisible text (BLACK color) to effectively
        clear it from view while maintaining the primer mobject.

        Parameters
        ----------
        run_time : float
            Duration of the clear animation in seconds
        **kwargs
            Additional arguments passed to :meth:`~.Scene.play`

        Examples
        --------
        .. code-block:: python

            class ClearNarrateExample(HUD2DScene):
                def construct(self):
                    self.narrate("Temporary message")
                    self.wait(2)

                    # Clear the narration
                    self.clear_narrate()
                    self.wait(1)

                    # Show new narration
                    self.narrate("New message")

        See Also
        --------
        :meth:`narrate` : Display upper narration
        :meth:`clear_caption` : Clear lower caption
        :meth:`narrate_and_clear` : Display and auto-clear in one call

        Notes
        -----
        - Transforms to invisible text (BLACK color with "....." content)
        - The primer mobject remains in the scene but is not visible
        - Uses the same :class:`~.Transform` pattern as :meth:`narrate`
        """
        empty = self.narration.get_empty_narration()
        self.play(
            Transform(self.narration.current_narration_text, empty),
            run_time=run_time,
            **kwargs
        )

    def clear_caption(self, run_time: float = 0.5, **kwargs: Any) -> None:
        """Clear lower caption text with animation.

        Transforms the caption to invisible text (BLACK color) to effectively
        clear it from view while maintaining the primer mobject.

        Parameters
        ----------
        run_time : float
            Duration of the clear animation in seconds
        **kwargs
            Additional arguments passed to :meth:`~.Scene.play`

        Examples
        --------
        .. code-block:: python

            class ClearCaptionExample(HUD2DScene):
                def construct(self):
                    self.caption("Detailed explanation")
                    self.wait(2)

                    # Clear the caption
                    self.clear_caption()
                    self.wait(1)

                    # Show new caption
                    self.caption("Updated explanation")

        See Also
        --------
        :meth:`caption` : Display lower caption
        :meth:`clear_narrate` : Clear upper narration
        :meth:`narrate_and_clear` : Display and auto-clear in one call

        Notes
        -----
        - Transforms to invisible text (BLACK color with "....." content)
        - The primer mobject remains in the scene but is not visible
        - Uses the same :class:`~.Transform` pattern as :meth:`caption`
        """
        empty = self.narration.get_empty_caption()
        self.play(
            Transform(self.narration.current_caption_text, empty),
            run_time=run_time,
            **kwargs
        )

    def narrate_and_clear(
        self,
        text: str,
        display_time: float = 2.0,
        fade_time: float = 0.5,
        upper: bool = True,
        **kwargs: Any
    ) -> None:
        """Display narration temporarily, then auto-clear.

        Convenience method that displays text, waits for a specified duration,
        then automatically clears it. Useful for temporary messages or tooltips.

        Parameters
        ----------
        text : str
            Text to display temporarily
        display_time : float
            How long to display the text before clearing (in seconds)
        fade_time : float
            Duration of both the fade-in and fade-out animations (in seconds)
        upper : bool
            If True, use upper narration; if False, use lower caption
        **kwargs
            Additional arguments passed to :meth:`~.Scene.play` for both
            the display and clear animations

        Examples
        --------
        .. code-block:: python

            class TemporaryTextExample(HUD2DScene):
                def construct(self):
                    square = Square()
                    self.add(square)

                    # Show temporary narration at top
                    self.narrate_and_clear("Watch this!", display_time=1.5)

                    # Animate while narration is visible
                    self.play(square.animate.rotate(PI))

                    # Show temporary caption at bottom
                    self.narrate_and_clear(
                        "Rotation complete",
                        display_time=2.0,
                        upper=False
                    )

        .. code-block:: python

            class CustomTimingExample(HUD2DScene):
                def construct(self):
                    # Quick flash message
                    self.narrate_and_clear(
                        "Quick message",
                        display_time=0.5,
                        fade_time=0.2
                    )

                    # Slow, dramatic reveal
                    self.narrate_and_clear(
                        "Important announcement",
                        display_time=3.0,
                        fade_time=1.5
                    )

        See Also
        --------
        :meth:`narrate` : Display upper narration (persistent)
        :meth:`caption` : Display lower caption (persistent)
        :meth:`clear_narrate` : Clear upper narration manually
        :meth:`clear_caption` : Clear lower caption manually

        Notes
        -----
        - Internally calls :meth:`narrate` or :meth:`caption`, then :meth:`~.Scene.wait`,
          then :meth:`clear_narrate` or :meth:`clear_caption`
        - Total time is ``fade_time + display_time + fade_time``
        - Uses the same primer pattern as other narration methods
        - Useful for tooltips, temporary instructions, or status messages
        """
        if upper:
            self.narrate(text, run_time=fade_time, **kwargs)
            self.wait(display_time)
            self.clear_narrate(run_time=fade_time, **kwargs)
        else:
            self.caption(text, run_time=fade_time, **kwargs)
            self.wait(display_time)
            self.clear_caption(run_time=fade_time, **kwargs)

class UniversalNarrationManager:
    """Universal HUD text manager for ThreeDScene with dual-text primer pattern.

    Manages HUD text elements using the primer pattern. Creates invisible primer
    text mobjects once during initialization for both upper narration and lower
    caption, then provides methods to generate visible text for Transform animations.
    Primers are automatically registered as fixed-in-frame with the scene.

    Parameters
    ----------
    scene : ThreeDScene
        Scene instance with add_fixed_in_frame_mobjects support
    text_type : Literal["Text", "MathTex", "Tex"], optional
        The type of text mobject to use for narration and caption.
        Defaults to "Text".
        Mixing Text, MathTex, or Tex within the same manager is not supported
        and will break the primer pattern.

    Attributes
    ----------
    scene : ThreeDScene
        Reference to the scene instance
    current_narration_text : Mobject
        Primer mobject for upper narration text
    current_caption_text : Mobject
        Primer mobject for lower caption text
    narration_font_size : int
        Font size for upper narration text
    caption_font_size : int
        Font size for lower caption text
    narration_color : ManimColor
        Color for upper narration text
    caption_color : ManimColor
        Color for lower caption text
    text_class : Type[Union[Text, MathTex, Tex]]
        The class used for creating text mobjects (Text, MathTex, or Tex)

    Notes
    -----
    - The primer pattern requires that all subsequent Transforms reuse the same primer mobjects
    - Character capacity is fixed at initialization (spaces excluded)
    - Must use Transform, NOT ReplacementTransform
    - Exceeding capacity causes characters to detach from HUD
    - The text type (Text, MathTex, or Tex) is set at initialization and cannot be mixed.
      Mixing text types will break the primer pattern.
    """

    def __init__(
            self,
            scene: ThreeDScene,
            text_type: Literal["Tex", "MathTex", "Text"] = "Tex",
    ) -> None:
        self.scene = scene
        self.narration_font_size: int = 32
        self.caption_font_size: int = 26
        self.narration_color = WHITE
        self.caption_color = WHITE
        self.narration_position = UP
        self.caption_position = DOWN
        self.max_narration_chars: int = 100
        self.max_caption_chars: int = 100

        if text_type == "Text":
            self.text_class: Type[Union[Text, MathTex, Tex]] = Text
        elif text_type == "MathTex":
            self.text_class = MathTex
        elif text_type == "Tex":
            self.text_class = Tex
        else:
            # Default to Text for invalid text_type
            logger.warning(
                f"Invalid text_type '{text_type}'. Defaulting to 'Tex'. "
                f"Valid options are: 'Tex', 'MathTex', 'Text'"
            )
            self.text_class = Tex

        # Create invisible primer mobjects for narration and caption
        # Use "0" * max_chars to ensure consistent width for primer
        narration_primer_string = "0" * self.max_narration_chars
        caption_primer_string = "0" * self.max_caption_chars

        narration_primer = self.text_class(
            narration_primer_string, color=BLACK, font_size=1
        )
        narration_primer.to_edge(self.narration_position)

        caption_primer = self.text_class(
            caption_primer_string, color=BLACK, font_size=1
        )
        caption_primer.to_edge(self.caption_position)

        # Register primers as fixed-in-frame
        self.scene.add_fixed_in_frame_mobjects(narration_primer, caption_primer)

        self.current_narration_text = narration_primer
        self.current_caption_text = caption_primer

    def get_narration(self, text: str) -> Mobject:
        """Creates a narration Mobject with validation."""
        if self.text_class in (MathTex, Tex):
            self._validate_latex_string(text, "narration")

        narration = self.text_class(
            text,
            font_size=self.narration_font_size,
            color=self.narration_color,
        )
        narration.move_to(self.current_narration_text.get_center())
        return narration

    def get_caption(self, text: str) -> Mobject:
        """Creates a caption Mobject with validation."""
        if self.text_class in (MathTex, Tex):
            self._validate_latex_string(text, "caption")

        caption = self.text_class(
            text,
            font_size=self.caption_font_size,
            color=self.caption_color,
        )
        caption.move_to(self.current_caption_text.get_center())
        return caption

    @staticmethod
    def _validate_latex_string(text: str, type_name: str) -> None:
        """Internal method to validate LaTeX strings for common issues."""
        # Check for unescaped backslashes that might be Python escape sequences
        # This is a heuristic, not foolproof, but catches common mistakes.
        if '\\' in text:
            # Common Python escape sequences that would break LaTeX commands
            python_escapes = ['\\n', '\\t', '\\r', '\\b', '\\f', '\\v', '\\a']
            if any(seq in text for seq in python_escapes):
                logger.warning(
                    f"[{type_name}] String '{text[:50]}...' contains Python escape sequences. "
                    f"Did you forget to use a raw string (r'...')? "
                    f"This can lead to LaTeX compilation errors or incorrect rendering."
                )

    def get_empty_narration(self) -> Mobject:
        empty = self.text_class(".....", color=BLACK, font_size=self.narration_font_size)
        empty.move_to(self.current_narration_text.get_center())
        return empty

    def get_empty_caption(self) -> Mobject:
        empty = self.text_class(".....", color=BLACK, font_size=self.caption_font_size)
        empty.move_to(self.current_caption_text.get_center())
        return empty

    def set_narration_font_size(self, font_size: int):
        """Change font size for future narrations.

        Parameters
        ----------
        font_size : int
            New font size for narrations
        """
        self.narration_font_size = font_size

    def set_caption_font_size(self, font_size: int):
        """Change font size for future captions.

        Parameters
        ----------
        font_size : int
            New font size for captions
        """
        self.caption_font_size = font_size

    def set_narration_color(self, narration_color):
        """Change color for future narrations.

        Parameters
        ----------
        narration_color : ManimColor
            New color for narrations
        """
        self.narration_color = narration_color

    def set_caption_color(self, caption_color):
        """Change color for future captions.

        Parameters
        ----------
        caption_color : ManimColor
            New color for captions
        """
        self.caption_color = caption_color

class Frame2DWrapper:
    """Wrapper that mimics MovingCamera.frame API for ThreeDCamera in 2D mode.

    Supports: move_to, shift, scale, set, get_center
    Does NOT support: save_state, restore (use manual positioning instead)

    .. note::
        Unlike MovingCamera.frame, negative scale factors are not supported
        and will produce undefined behavior. Use positive scale factors only.
        Similarly, setting width or height to zero or negative values is not
        recommended.
    """

    def __init__(self, camera):
        self.camera = camera

    @property
    def animate(self):
        """Returns an animation builder that mimics frame.animate behavior."""
        return Frame2DAnimateWrapper(self)  # Create fresh instance every time

    def move_to(self, point):
        """Move frame center to point (mimics ScreenRectangle.move_to)."""
        # noinspection PyProtectedMember
        self.camera._frame_center.move_to(point) # type: ignore[attr-defined]  # noqa: SLF001
        return self

    def shift(self, vector):
        """Shift frame center by vector (mimics ScreenRectangle.shift)."""
        # noinspection PyProtectedMember
        self.camera._frame_center.shift(vector) # type: ignore[attr-defined]  # noqa: SLF001
        return self

    def scale(self, scale_factor: float):
        """Scale frame (mimics ScreenRectangle.scale via zoom)."""
        current_zoom = self.camera.zoom_tracker.get_value()
        self.camera.zoom_tracker.set_value(current_zoom / scale_factor)
        return self

    def set(self, width: float = None, height: float = None):
        """Set frame dimensions (mimics ScreenRectangle.set via zoom).

        If both width and height are specified, width takes precedence.
        """
        if width is not None:
            from manim import config
            zoom_factor = config["frame_width"] / width
            self.camera.zoom_tracker.set_value(zoom_factor)
        elif height is not None:
            from manim import config
            zoom_factor = config["frame_height"] / height
            self.camera.zoom_tracker.set_value(zoom_factor)
        return self

    def get_center(self):
        """Get frame center (mimics ScreenRectangle.get_center)."""
        # noinspection PyProtectedMember
        return self.camera._frame_center.get_center() # type: ignore[attr-defined]  # noqa: SLF001

class Frame2DAnimateWrapper:
    """Animation builder that mimics Manim's _AnimationBuilder pattern."""

    def __init__(self, frame_wrapper: Frame2DWrapper):
        self.frame = frame_wrapper
        # Store initial state
        # noinspection PyProtectedMember
        self.target_center = self.frame.camera._frame_center.copy() # type: ignore[attr-defined]  # noqa: SLF001
        self.target_zoom = self.frame.camera.zoom_tracker.get_value()
#        self.operations = []

    def move_to(self, point):
        """Apply move_to to target center."""
        self.target_center.move_to(point)
#        self.operations.append(('move_to', point))
        return self

    def shift(self, vector):
        """Apply shift to target center."""
        self.target_center.shift(vector)
#        self.operations.append(('shift', vector))
        return self

    def scale(self, scale_factor: float):
        """Apply scale to target zoom."""
        self.target_zoom = self.target_zoom / scale_factor
#        self.operations.append(('scale', scale_factor))
        return self

    def set(self, width: float = None, height: float = None):
        """Apply set to target zoom.

        If both width and height are specified, width takes precedence.
        """
        if width is not None:
            from manim import config
            self.target_zoom = config["frame_width"] / width
#            self.operations.append(('set', {'width': width}))
        elif height is not None:
            from manim import config
            self.target_zoom = config["frame_height"] / height
#            self.operations.append(('set', {'height': height}))
        return self

    # noinspection PyProtectedMember
    def build(self):
        animations = [
            # Always create animation for frame center (even if unchanged)
            self.frame.camera._frame_center.animate.move_to( # type: ignore[attr-defined]  # noqa: SLF001
                self.target_center.get_center()
            ),
            # Always create animation for zoom (even if unchanged)
            self.frame.camera.zoom_tracker.animate.set_value(self.target_zoom),
        ]

        return AnimationGroup(*animations)

class TranscriptManager:
    """Manages transcript output independently from visual display.

    This class handles verbose descriptions of scene events, separate from
    the narration/caption text shown on screen. Transcript lines are automatically
    written to a .txt file during scene teardown.
    """

    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.transcript_lines: list[str] = []

    def add_transcript(self, content: str) -> None:
        """Add a line to the transcript file.

        Each call adds the content as a new line in the transcript.
        """
        self.transcript_lines.append(content)

    def _write_transcript(self) -> None:
        """Write accumulated transcript to file with appropriate logging."""
        if not self.transcript_lines:
            logger.debug("No transcript lines to write, skipping transcript file creation.")
            return

        if not hasattr(self.scene.renderer, 'file_writer'):
            logger.warning("Cannot write transcript: renderer has no file_writer attribute.")
            return

        file_writer = self.scene.renderer.file_writer
        if not hasattr(file_writer, 'movie_file_path'):
            logger.warning("Cannot write transcript: file_writer has no movie_file_path attribute.")
            return

        transcript_path = None
        try:
            transcript_path = file_writer.movie_file_path.with_suffix('.txt')
            transcript_path.write_text('\n'.join(self.transcript_lines), encoding='utf-8')
            logger.info(
                "\nTranscript file has been written as %(path)s\n",
                {"path": f"'{transcript_path}'"}  # ← Added single quotes here
            )
        except Exception as e:
            path_str = str(transcript_path) if transcript_path else "unknown path"
            logger.error(
                "\nFailed to write transcript to %(path)s: %(error)s\n",
                {"path": f"'{path_str}'", "error": str(e)}  # ← Added single quotes here too
            )

##########END Properly Documented Stuff##########


"""  
BASELINE ALIGNMENT PLAN FOR TEXT/MATHTEX/TEX MOBJECTS  
  
Goal: Ensure consistent baseline alignment across text changes by aligning to a reference vowel character.  
  
Approach:  #could simplify to not use a reference mobject and just pick an arbitrary point like align up shift DOWN instead.
1. Create an invisible reference mobject (e.g., Text("a", color=BLACK) or MathTex(r"\text{a}", color=BLACK))  
   positioned at a fixed location to serve as the "baseline ruler"  
  
2. Before each text change:  
   - Find the first vowel (a, e, i, o, u) in the new text mobject's submobjects
   - Get its baseline using get_critical_point(DOWN)[1]   
   - Calculate y-offset needed to align that vowel's baseline to the reference  
   - Apply shift(UP * offset) to the entire text mobject  
  
3. Implementation considerations:  
   - For MathTex/Tex: Use tex_string attribute to identify characters  
   - For Text: Use positional tracking through submobjects list  
   - Use family_members_with_points() to flatten hierarchy and find leaf submobjects  
     
4. Key methods to use:  
   - get_critical_point(DOWN) - gets bottom edge (baseline for non-descenders)  
   - shift() - applies vertical offset  
   - align_to(reference, DOWN) - alternative alignment method  
   - next_to(reference, RIGHT, buff=0, aligned_edge=DOWN) - another option  
  
5. This works universally because Text, MathTex, and Tex all:  
   - Inherit from SVGMobject  
   - Have hierarchical submobject structures  
   - Support the same Mobject positioning methods  
     
Result: All text without descenders (p, g, y, q, j) appears on the same imaginary line,  
preventing vertical drift across text changes, similar to how text aligns in a book.  
  
See DecimalNumber class (manim/mobject/text/numbers.py:168-197) for similar baseline  
alignment implementation with aligned_edge=DOWN.  
"""



##########START Untested Stuff##########

##########END Untested Stuff##########
