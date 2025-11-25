from __future__ import annotations

__all__ = [
    "HUD2DScene",
    "UniversalNarrationManager",
    "Frame2DWrapper",
    "Frame2DAnimateWrapper",
    "TranscriptManager"
    # Add any other scene-related classes/functions you export
]

from typing import Literal, Type, Union, Any, Optional

from manim import Scene, logger, AnimationGroup, ThreeDScene, WHITE, UP, DOWN, Text, MathTex, Tex, BLACK, Mobject, \
    DEGREES, Transform


#####START everything related to HUD2DScene#####

class HUD2DScene(ThreeDScene):
    """A 2D scene with heads-up display (HUD) support using ThreeDScene's fixed-in-frame system.

    This scene extends :class:`~.ThreeDScene` but configures the camera for orthographic 2D viewing
    (looking straight down the Z-axis). It provides access to :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects`
    for creating HUD elements that remain fixed in the camera frame regardless of camera movements.

    The scene includes an integrated :class:`UniversalNarrationManager` that provides convenient
    methods for managing dual HUD text elements (upper narration and lower caption) using the
    primer pattern. This eliminates the need for manual primer creation and management.

    **Design Rationale**: This scene provides a performant 2D moving camera with HUD support by
    leveraging :class:`~.ThreeDScene`'s fixed-in-frame filtering system. The :class:`Frame2DWrapper`
    provides a MovingCameraScene-compatible API for 2D camera movements without requiring 3D
    functionality. This is the permanent solution for blanim/common, which exclusively uses 2D scenes.

    .. warning::
        **Camera Movement API**: This scene provides TWO camera movement APIs:

        **Recommended (blanim/common)**: :class:`Frame2DWrapper` API
            Use ``self.camera.frame.animate.shift()``, ``self.camera.frame.animate.scale()``, etc.
            This is the tested and recommended approach for 2D camera movements in blanim/common.

        **Alternative**: :class:`~.ThreeDScene` API
            Use ``self.move_camera(frame_center=...)``. This is the underlying 3D camera API
            but is NOT recommended for blanim/common since 3D functionality is never used.

        The :class:`Frame2DWrapper` mimics :class:`~.MovingCameraScene`'s frame API while
        maintaining access to :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` for HUD elements.

    .. warning::
        **Camera Orientation**: Do not modify the camera orientation after setup. This scene is
        designed exclusively for 2D use with a fixed top-down view. Changing ``phi``, ``theta``,
        or ``gamma`` values is untested and not supported.

    Examples
    --------

    **Using Frame2DWrapper API (Recommended)**:

    .. code-block:: python

        class FrameWrapperExample(HUD2DScene):
            def construct(self):
                # Create scene content
                square = Square(color=BLUE)
                self.add(square)

                # Use convenience methods for HUD text
                self.narrate(r"Main Title")  # Upper narration
                self.caption(r"Subtitle text")  # Lower caption

                # Camera movement using Frame2DWrapper - HUD stays fixed
                self.play(self.camera.frame.animate.shift(RIGHT * 2), run_time=2)

                # Can also use scale, move_to, etc.
                self.play(self.camera.frame.animate.scale(0.5))

                # Clear HUD elements
                self.clear_narrate()
                self.clear_caption()

    **Using ThreeDScene API (Alternative)**:

    .. code-block:: python

        class ThreeDAPIExample(HUD2DScene):
            def construct(self):
                square = Square(color=BLUE)
                self.add(square)

                self.narrate(r"Using 3D camera API")

                # Alternative: use ThreeDScene's move_camera
                self.move_camera(frame_center=RIGHT * 2, run_time=2)

    **Temporary Narration with Auto-Clear**:

    .. code-block:: python

        class TemporaryNarrationExample(HUD2DScene):
            def construct(self):
                square = Square()
                self.add(square)

                # Display narration for 2 seconds, then auto-clear
                self.narrate_and_clear(r"This appears briefly", display_time=2.0)

                # Display caption for 3 seconds, then auto-clear
                self.narrate_and_clear(r"Lower caption", display_time=3.0, upper=False)

    **Manual Primer Pattern (Advanced)**:

    .. code-block:: python

        class ManualPrimerExample(HUD2DScene):
            def construct(self):
                # Access the narration manager directly
                narration = self.narration.get_narration(r"Custom Title")
                self.play(Transform(self.narration.current_narration_text, narration))

                caption = self.narration.get_caption(r"Custom Subtitle")
                self.play(Transform(self.narration.current_caption_text, caption))

                # Camera movement
                self.play(self.camera.frame.animate.shift(LEFT * 2), run_time=2)

    **Custom Primer Configuration**:

    .. code-block:: python

        class CustomPrimerExample(HUD2DScene):
            def setup(self):
                super().setup()
                # Customize narration manager settings after initialization
                self.narration.max_narration_chars = 150  # Larger capacity
                self.narration.max_caption_chars = 200
                self.narration.set_narration_font_size(48)  # Larger font
                self.narration.set_caption_font_size(32)

            def construct(self):
                self.narrate(r"Large Title Text")
                self.caption(r"Large Caption Text")

    See Also
    --------
    :class:`~.ThreeDScene` : Parent class providing fixed-in-frame functionality
    :class:`Frame2DWrapper` : Wrapper providing MovingCameraScene-compatible frame API (recommended)
    :class:`UniversalNarrationManager` : Integrated HUD text manager with primer pattern
    :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` : Method for adding HUD elements
    :meth:`~.ThreeDScene.move_camera` : Alternative 3D camera API (not recommended for blanim/common)
    :class:`~.MovingCameraScene` : Manim's 2D camera scene (Frame2DWrapper mimics its API)

    Notes
    -----
    **Camera Configuration:**
        - Camera is set to orthographic 2D view (phi=0, theta=-90°) in :meth:`setup`
        - :class:`Frame2DWrapper` provides MovingCameraScene-compatible API for 2D movements
        - **Recommended API**: ``self.camera.frame.animate.shift()``, ``.scale()``, ``.move_to()``, etc.
        - **Alternative API**: ``self.move_camera(frame_center=...)`` (not recommended for blanim/common)

    **HUD System:**
        - Integrated :class:`UniversalNarrationManager` handles primer creation automatically
        - Uses :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` for HUD elements
        - **Spaces do NOT count** toward primer character capacity
        - **Default capacity**: 100 chars for narration, 100 chars for caption
        - **Only Transform works**: Do not use ReplacementTransform or other animations

    **Text Configuration:**
        - **Default text type**: Tex (supports Text and MathTex via ``narration_text_type``)
        - **Raw strings required**: Use ``r"..."`` for Tex/MathTex to avoid Python escape sequences
        - **Plain text**: Raw strings optional if no backslashes present

    **Implementation Details:**
        - **Renderer agnostic**: Cairo/OpenGL choice is irrelevant for 2D-only usage
        - **Permanent solution**: This is the stable implementation for blanim/common 2D scenes
        - **No 3D usage**: blanim/common never uses 3D features, only 2D camera movements

    Attributes
    ----------
    narration : UniversalNarrationManager
        Integrated narration manager for HUD text elements. Automatically initialized
        in :meth:`setup` with default settings. Provides access to primer mobjects
        and text generation methods.
    transcript : TranscriptManager
        Integrated transcript manager for writing scene descriptions to a text file.
        Automatically initialized in :meth:`setup`.
    narration_text_type : Literal["Tex", "MathTex", "Text"]
        Class attribute specifying the text type for narration and caption.
        Defaults to ``"Tex"``. Can be overridden in subclasses to use ``"MathTex"``
        or ``"Text"`` instead.
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
                    self.narrate(r"Scene is ready")

        See Also
        --------
        :meth:`construct` : Main method for defining scene content
        :class:`UniversalNarrationManager` : The narration manager created here
        :class:`Frame2DWrapper` : The frame wrapper created here
        :class:`TranscriptManager` : The transcript manager created here

        Notes
        -----
        Sets camera orientation to ``phi=0, theta=-90 * DEGREES`` for top-down 2D view.
        Creates :class:`Frame2DWrapper` to provide MovingCameraScene-compatible API for 2D camera movements.
        Creates the :class:`UniversalNarrationManager` instance with default settings.
        Creates the :class:`TranscriptManager` instance for transcript output.
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
        """Clean up scene resources and write transcript file.

        This method is called automatically after :meth:`construct` completes.
        It writes the accumulated transcript to a .txt file if any transcript
        lines were added during the scene.

        Examples
        --------
        .. code-block:: python

            class MyScene(HUD2DScene):
                def construct(self):
                    self.transcript.add_transcript("Scene content")
                    # tear_down() called automatically after construct()

        See Also
        --------
        :meth:`setup` : Initialization method called before construct
        :meth:`TranscriptManager._write_transcript` : Internal method that writes the file

        Notes
        -----
        - Called automatically by Manim's rendering pipeline
        - Do not call this method manually
        - Transcript is only written if lines were added via :meth:`TranscriptManager.add_transcript`
        """
        if self.transcript:
            # noinspection PyProtectedMember
            self.transcript._write_transcript()  # type: ignore[attr-defined]  # noqa: SLF001
        super().tear_down()

    def play(self, *args, **kwargs) -> None:
        """Play animations with Frame2DWrapper support.

        Overrides :meth:`~.Scene.play` to handle :class:`Frame2DAnimateWrapper`
        animations created by ``self.camera.frame.animate``. This allows using
        MovingCameraScene-style frame animations in the 2D HUD scene.

        Parameters
        ----------
        *args
            Animation objects to play. Can include :class:`Frame2DAnimateWrapper`
            instances from ``self.camera.frame.animate`` calls.
        **kwargs
            Additional arguments passed to :meth:`~.Scene.play`, such as
            ``run_time``, ``rate_func``, or ``lag_ratio``

        Examples
        --------
        .. code-block:: python

            class FrameAnimationExample(HUD2DScene):
                def construct(self):
                    square = Square()
                    self.add(square)

                    # Frame animation is automatically handled
                    self.play(
                        self.camera.frame.animate.shift(RIGHT * 2),
                        square.animate.scale(2),
                        run_time=2
                    )

        See Also
        --------
        :class:`Frame2DWrapper` : Wrapper providing frame.animate API
        :class:`Frame2DAnimateWrapper` : Animation builder for frame animations
        :meth:`~.Scene.play` : Parent class play method

        Notes
        -----
        - Automatically converts :class:`Frame2DAnimateWrapper` to :class:`~.AnimationGroup`
        - All other animations are passed through unchanged
        - This override is transparent to users
        """
        processed_args = []
        for arg in args:
            if isinstance(arg, Frame2DAnimateWrapper):
                built = arg.build()
                if built is not None:
                    processed_args.append(built)
            else:
                processed_args.append(arg)
        return super().play(*processed_args, **kwargs)

    def narrate(self, text: str, run_time: float = 0.5, **kwargs: Any) -> None:
        r"""Update upper narration text with animation.

        Uses the primer pattern to transform the upper narration text. The primer
        mobject is mutated to display the new text while remaining fixed in frame.

        .. warning::
            **Raw Strings Required for Tex/MathTex**

            When using ``narration_text_type = "Tex"`` or ``"MathTex"``, you MUST use
            raw strings (``r"..."``) if your text contains backslashes (LaTeX commands).

            **Python Escape Sequences vs LaTeX Commands:**

            Text strings undergo two layers of processing:

            1. **Python string parsing** (first): Interprets escape sequences like ``\n``, ``\t``, ``\\``
            2. **LaTeX compilation** (second): Processes LaTeX commands like ``\LaTeX``, ``\frac``

            Without raw strings, Python processes backslashes before LaTeX sees them:

            - ``self.narrate("\nabla")`` → Python interprets ``\n`` as newline, LaTeX receives newline + "abla" ✗
            - ``self.narrate(r"\nabla")`` → Python passes ``\nabla`` literally to LaTeX ✓

            **Python escape sequences that conflict with LaTeX commands:**
            ``\n``, ``\t``, ``\r``, ``\b``, ``\f``, ``\v``, ``\a``

            **LaTeX special characters (require backslash escape in LaTeX):**

            - ``\`` → ``\\`` (backslash itself - most critical)
            - ``$`` → ``\$`` (dollar sign - math mode delimiter)
            - ``%`` → ``\%`` (percent - comment character)
            - ``&`` → ``\&`` (ampersand - alignment character)
            - ``#`` → ``\#`` (hash - parameter marker)
            - ``_`` → ``\_`` (underscore - subscript in math mode)
            - ``^`` → ``\^`` (caret - superscript in math mode)
            - ``{`` → ``\{`` (left brace - grouping)
            - ``}`` → ``\}`` (right brace - grouping)
            - ``~`` → ``\~`` (tilde - non-breaking space)

            **Note**: These characters only need escaping in LaTeX when you want the literal
            character. For example, ``$x^2$`` uses ``^`` for superscript (no escape needed),
            but ``\^`` produces a literal caret character.

        .. note::
            **Plain Text Without Backslashes**

            Raw strings are only required when your text contains backslashes (LaTeX commands).
            For plain text without backslashes, raw strings are optional:

            - ``self.narrate("Hello World")`` ✓ (no backslashes, works fine)
            - ``self.narrate(r"Hello World")`` ✓ (also works, raw string is harmless)
            - ``self.narrate(r"\LaTeX")`` ✓ (backslashes present, raw string required)
            - ``self.narrate("\LaTeX")`` ✗ (Python interprets ``\L`` as escape sequence)

            **Rule of thumb**: If your string contains **any** backslash ``\``, use raw strings.
            If it contains **no** backslashes, raw strings are optional but recommended for consistency.

        Parameters
        ----------
        text : str
            Narration text to display at the top of the screen.
            See warnings and notes above for LaTeX requirements.
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

                    # With LaTeX commands (raw string required)
                    self.narrate(r"Step 1: Create square")
                    self.wait(1)

                    # Plain text (raw string optional but recommended)
                    self.narrate(r"Step 2: Transform")
                    self.play(square.animate.scale(2))

                    # Math notation
                    self.narrate(r"Area is $A = s^2$")

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
        - **Always use raw strings** (``r"..."``) when using Tex or MathTex with backslashes
        """
        narration = self.narration.get_narration(text)
        self.play(
            Transform(self.narration.current_narration_text, narration),
            run_time=run_time,
            **kwargs
        )

    def caption(self, text: str, run_time: float = 0.5, **kwargs: Any) -> None:
        r"""Update lower caption text with animation.

        Uses the primer pattern to transform the lower caption text. The primer
        mobject is mutated to display the new text while remaining fixed in frame.

        .. warning::
            **Raw Strings Required for Tex/MathTex**

            When using ``narration_text_type = "Tex"`` or ``"MathTex"``, you MUST use
            raw strings (``r"..."``) if your text contains backslashes (LaTeX commands).

            **Python Escape Sequences vs LaTeX Commands:**

            Text strings undergo two layers of processing:

            1. **Python string parsing** (first): Interprets escape sequences like ``\n``, ``\t``, ``\\``
            2. **LaTeX compilation** (second): Processes LaTeX commands like ``\LaTeX``, ``\frac``

            Without raw strings, Python processes backslashes before LaTeX sees them:

            - ``self.caption("\nabla")`` → Python interprets ``\n`` as newline, LaTeX receives newline + "abla" ✗
            - ``self.caption(r"\nabla")`` → Python passes ``\nabla`` literally to LaTeX ✓

            **Python escape sequences that conflict with LaTeX commands:**
            ``\n``, ``\t``, ``\r``, ``\b``, ``\f``, ``\v``, ``\a``

            **LaTeX special characters (require backslash escape in LaTeX):**

            - ``\`` → ``\\`` (backslash itself - most critical)
            - ``$`` → ``\$`` (dollar sign - math mode delimiter)
            - ``%`` → ``\%`` (percent - comment character)
            - ``&`` → ``\&`` (ampersand - alignment character)
            - ``#`` → ``\#`` (hash - parameter marker)
            - ``_`` → ``\_`` (underscore - subscript in math mode)
            - ``^`` → ``\^`` (caret - superscript in math mode)
            - ``{`` → ``\{`` (left brace - grouping)
            - ``}`` → ``\}`` (right brace - grouping)
            - ``~`` → ``\~`` (tilde - non-breaking space)

            **Note**: These characters only need escaping in LaTeX when you want the literal
            character. For example, ``$x^2$`` uses ``^`` for superscript (no escape needed),
            but ``\^`` produces a literal caret character.

        .. note::
            **Plain Text Without Backslashes**

            Raw strings are only required when your text contains backslashes (LaTeX commands).
            For plain text without backslashes, raw strings are optional:

            - ``self.caption("Hello World")`` ✓ (no backslashes, works fine)
            - ``self.caption(r"Hello World")`` ✓ (also works, raw string is harmless)
            - ``self.caption(r"\LaTeX")`` ✓ (backslashes present, raw string required)
            - ``self.caption("\LaTeX")`` ✗ (Python interprets ``\L`` as escape sequence)

            **Rule of thumb**: If your string contains **any** backslash ``\``, use raw strings.
            If it contains **no** backslashes, raw strings are optional but recommended for consistency.

        Parameters
        ----------
        text : str
            Caption text to display at the bottom of the screen.
            See warnings and notes above for LaTeX requirements.
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

                    # With LaTeX commands (raw string required)
                    self.caption(r"Detailed explanation here")
                    self.wait(1)

                    # Plain text (raw string optional but recommended)
                    self.caption(r"Simple description")
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
        - **Always use raw strings** (``r"..."``) when using Tex or MathTex with backslashes
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
                    # Show narration with raw string
                    self.narrate(r"Temporary message")
                    self.wait(2)

                    # Clear the narration (no raw string needed - no backslashes)
                    self.clear_narrate()
                    self.wait(1)

                    # Show new narration
                    self.narrate(r"New message")

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
        - No raw string needed for this method since it doesn't use LaTeX commands
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
                    # Show caption with raw string
                    self.caption(r"Detailed explanation")
                    self.wait(2)

                    # Clear the caption (no raw string needed - no backslashes)
                    self.clear_caption()
                    self.wait(1)

                    # Show new caption
                    self.caption(r"Updated explanation")

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
        - No raw string needed for this method since it doesn't use LaTeX commands
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

#TODO added z index to naration and caption, test these
#    appear to have worked, BUT may require a bg to ensure visibility when something renders below it in z space
class UniversalNarrationManager:
    """Internal HUD text manager using the primer pattern (not user-facing).

    This class is used internally by :class:`HUD2DScene` to manage narration
    and caption text. Users should interact with the scene-level convenience
    methods (:meth:`HUD2DScene.narrate`, :meth:`HUD2DScene.caption`) instead
    of accessing this manager directly.

    Parameters
    ----------
    scene : ThreeDScene
        Scene instance with add_fixed_in_frame_mobjects support
    text_type : Literal["Tex", "MathTex", "Text"], optional
        Text mobject type. Defaults to "Tex".

    Attributes
    ----------
    scene : ThreeDScene
        Reference to the scene instance
    current_narration_text : Mobject
        Primer mobject for upper narration (invisible, BLACK, font_size=1)
    current_caption_text : Mobject
        Primer mobject for lower caption (invisible, BLACK, font_size=1)
    narration_font_size : int
        Font size for narration text. Default: 32
    caption_font_size : int
        Font size for caption text. Default: 26
    narration_color : ManimColor
        Color for narration text. Default: WHITE
    caption_color : ManimColor
        Color for caption text. Default: WHITE
    narration_position : Vector3
        Position for narration. Default: UP
    caption_position : Vector3
        Position for caption. Default: DOWN
    max_narration_chars : int
        Maximum character capacity for narration (spaces excluded). Default: 100
    max_caption_chars : int
        Maximum character capacity for caption (spaces excluded). Default: 100
    text_class : Type[Union[Text, MathTex, Tex]]
        The class used for creating text mobjects

    Notes
    -----
    - Creates invisible primer mobjects for Transform animations
    - Primers are registered as fixed-in-frame automatically
    - Character capacity is fixed at initialization (spaces excluded)
    - Must use Transform, not ReplacementTransform
    """

    def __init__(
            self,
            scene: ThreeDScene,
            text_type: Literal["Tex", "MathTex", "Text"] = "Tex",
    ) -> None:
        self.scene = scene
        self.narration_font_size: int = 32 #TODO modified for an example video from 32, breaks at 40
        self.caption_font_size: int = 26 #TODO modified for an example video from 26, breaks at 32
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

        # SET Z-INDEX HERE - after registration but before storing references
        narration_primer.set_z_index(1000)
        caption_primer.set_z_index(1000)

        self.current_narration_text = narration_primer
        self.current_caption_text = caption_primer

    def get_narration(self, text: str) -> Mobject:
        """Create narration mobject with validation.

        Parameters
        ----------
        text : str
            Narration text content

        Returns
        -------
        Mobject
            Configured narration mobject positioned at primer location
        """

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
        """Create caption mobject with validation.

        Parameters
        ----------
        text : str
            Caption text content

        Returns
        -------
        Mobject
            Configured caption mobject positioned at primer location
        """

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
        """Validate LaTeX strings for common Python escape sequence issues.

        Logs a warning if the text contains Python escape sequences that would
        be interpreted before reaching LaTeX, indicating the user likely forgot
        to use a raw string.

        Parameters
        ----------
        text : str
            The LaTeX string to validate
        type_name : str
            Type identifier for warning message ("narration" or "caption")

        Notes
        -----
        This is a heuristic check, not foolproof. It detects common Python
        escape sequences (\\n, \\t, \\r, \\b, \\f, \\v, \\a) that conflict
        with LaTeX commands.
        """
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
        """Create invisible narration mobject for clearing.

        Returns
        -------
        Mobject
            Invisible narration mobject (BLACK, ".....")
        """
        empty = self.text_class(".....", color=BLACK, font_size=self.narration_font_size)
        empty.move_to(self.current_narration_text.get_center())
        return empty

    def get_empty_caption(self) -> Mobject:
        """Create invisible caption mobject for clearing.

        Returns
        -------
        Mobject
            Invisible caption mobject (BLACK, ".....")
        """
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

#TODO was able to break positioning of narration and caption during an example, attempt to break again(possibly from using movingcamera in 3dscene)
class Frame2DWrapper:
    """Internal wrapper that mimics MovingCamera.frame API for ThreeDCamera in 2D mode (not user-facing).

    This class is used internally by :class:`HUD2DScene` to provide a MovingCameraScene-compatible
    API for 2D camera movements. Users should interact with ``self.camera.frame.animate`` at the
    scene level for animated camera movements, rather than calling these methods directly.

    The methods in this class can be called directly to **snap** the camera to a position/scale
    immediately without animation, but this is rarely desired. For smooth animated transitions,
    use the :attr:`animate` property instead.

    Supports: move_to, shift, scale, set, get_center
    Does NOT support: save_state, restore (use manual positioning instead)

    Parameters
    ----------
    camera : ThreeDCamera
        The camera instance to wrap

    Attributes
    ----------
    camera : ThreeDCamera
        Reference to the ThreeDCamera instance being wrapped

    .. note::
        Unlike MovingCamera.frame, negative scale factors are not supported
        and will produce undefined behavior. Use positive scale factors only.
        Similarly, setting width or height to zero or negative values is not
        recommended.

    .. note::
        **Direct vs Animated Usage**

        Direct method calls snap immediately without animation:
        ``self.camera.frame.move_to(RIGHT * 2)`` - instant snap

        Using ``.animate`` creates smooth transitions:
        ``self.play(self.camera.frame.animate.move_to(RIGHT * 2))`` - animated movement

        Most users should prefer the animated approach for visual clarity.
    """

    def __init__(self, camera):
        """Initialize the Frame2DWrapper.

        Parameters
        ----------
        camera : ThreeDCamera
            The camera instance to wrap
        """
        self.camera = camera

    @property
    def animate(self):
        """Returns an animation builder that mimics frame.animate behavior.

        This is the **recommended** way to move the camera in HUD2DScene. It creates
        smooth animated transitions rather than instant snaps.

        Returns
        -------
        Frame2DAnimateWrapper
            Animation builder for frame transformations

        Examples
        --------
        .. code-block:: python

            # Recommended: Animated camera movement
            self.play(self.camera.frame.animate.shift(RIGHT * 2))
            self.play(self.camera.frame.animate.scale(0.5))

            # Can chain multiple transformations
            self.play(
                self.camera.frame.animate
                    .move_to(UP * 2)
                    .scale(2)
            )

        Notes
        -----
        Creates a fresh instance every time to ensure clean animation state.
        This is the primary interface users should use for camera movements.
        """
        return Frame2DAnimateWrapper(self)  # Create fresh instance every time

    def move_to(self, point):
        """Move frame center to point immediately (instant snap, no animation).

        **Note**: This method snaps the camera instantly without animation. For smooth
        animated transitions, use ``self.camera.frame.animate.move_to(point)`` instead.

        Parameters
        ----------
        point : Point3DLike
            Target position for frame center

        Returns
        -------
        Frame2DWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            # Direct call (instant snap - rarely desired)
            self.camera.frame.move_to(RIGHT * 2)

            # Recommended: Animated movement
            self.play(self.camera.frame.animate.move_to(RIGHT * 2))
        """
        # noinspection PyProtectedMember
        self.camera._frame_center.move_to(point) # type: ignore[attr-defined]  # noqa: SLF001
        return self

    def shift(self, vector):
        """Shift frame center by vector immediately (instant snap, no animation).

        **Note**: This method snaps the camera instantly without animation. For smooth
        animated transitions, use ``self.camera.frame.animate.shift(vector)`` instead.

        Parameters
        ----------
        vector : Vector3D
            Displacement vector

        Returns
        -------
        Frame2DWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            # Direct call (instant snap - rarely desired)
            self.camera.frame.shift(UP * 3)

            # Recommended: Animated movement
            self.play(self.camera.frame.animate.shift(UP * 3))
        """
        # noinspection PyProtectedMember
        self.camera._frame_center.shift(vector) # type: ignore[attr-defined]  # noqa: SLF001
        return self

    def scale(self, scale_factor: float):
        """Scale frame immediately (instant snap, no animation).

        **Note**: This method snaps the camera zoom instantly without animation. For smooth
        animated transitions, use ``self.camera.frame.animate.scale(scale_factor)`` instead.

        Parameters
        ----------
        scale_factor : float
            Scaling factor (must be positive). Values > 1 zoom out, values < 1 zoom in.

        Returns
        -------
        Frame2DWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            # Direct call (instant snap - rarely desired)
            self.camera.frame.scale(2)  # Instant zoom out

            # Recommended: Animated zoom
            self.play(self.camera.frame.animate.scale(2))  # Smooth zoom out

        Notes
        -----
        Negative scale factors produce undefined behavior and should not be used.
        Internally modifies the camera's zoom_tracker by dividing current zoom by scale_factor.
        """
        current_zoom = self.camera.zoom_tracker.get_value()
        self.camera.zoom_tracker.set_value(current_zoom / scale_factor)
        return self

    def set(self, width: float = None, height: float = None):
        """Set frame dimensions immediately (instant snap, no animation).

        **Note**: This method snaps the camera dimensions instantly without animation. For smooth
        animated transitions, use ``self.camera.frame.animate.set(width=...)`` instead.

        Parameters
        ----------
        width : float, optional
            Target frame width. Takes precedence if both specified.
        height : float, optional
            Target frame height. Used only if width not specified.

        Returns
        -------
        Frame2DWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            # Direct call (instant snap - rarely desired)
            self.camera.frame.set(width=10)  # Instant resize

            # Recommended: Animated resize
            self.play(self.camera.frame.animate.set(width=10))  # Smooth resize

        Notes
        -----
        If both width and height are specified, width takes precedence.
        Zero or negative values are not recommended and may cause undefined behavior.
        Internally calculates zoom factor based on config frame dimensions.
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
        """Get current frame center position.

        This method is useful for querying the current camera position, often used
        in combination with other positioning logic.

        Returns
        -------
        Point3D
            Current frame center position

        Examples
        --------
        .. code-block:: python

            # Get current position
            current_pos = self.camera.frame.get_center()

            # Use it to calculate relative movement
            target_pos = current_pos + RIGHT * 2
            self.play(self.camera.frame.animate.move_to(target_pos))
        """
        # noinspection PyProtectedMember
        return self.camera._frame_center.get_center() # type: ignore[attr-defined]  # noqa: SLF001

class Frame2DAnimateWrapper:
    """Animation builder for chaining camera movements (user-facing).

    This class provides the animation builder interface for `Frame2DWrapper.animate`,
    allowing users to chain multiple camera transformations into a single animation.
    It mirrors the behavior of :class:`~.MovingCameraScene`'s frame animation API.

    Users access this through ``self.camera.frame.animate`` in :class:`HUD2DScene`:

    .. code-block:: python

        # Single transformation
        self.play(self.camera.frame.animate.shift(RIGHT * 2))

        # Chained transformations
        self.play(
            self.camera.frame.animate
                .move_to(RIGHT * 2)
                .scale(0.5)
        )

    Parameters
    ----------
    frame_wrapper : Frame2DWrapper
        The Frame2DWrapper instance to animate

    Attributes
    ----------
    frame : Frame2DWrapper
        Reference to the Frame2DWrapper being animated
    target_center : Mobject
        Copy of the camera's frame center for tracking target position
    target_zoom : float
        Target zoom value for the animation

    Notes
    -----
    - Method chaining is supported: each method returns ``self``
    - All transformations are accumulated and applied together in :meth:`build`
    - The :meth:`build` method creates an :class:`~.AnimationGroup` with all transformations
    - This mirrors :class:`~.MovingCameraScene`'s ``camera.frame.animate`` behavior

    See Also
    --------
    :class:`Frame2DWrapper` : The wrapper being animated
    :class:`HUD2DScene` : Scene class that uses this animation builder
    :class:`~.MovingCameraScene` : Manim's 2D camera scene (API compatibility target)
    """

    def __init__(self, frame_wrapper: Frame2DWrapper):
        """Initialize the animation builder.

        Parameters
        ----------
        frame_wrapper : Frame2DWrapper
            The Frame2DWrapper instance to animate
        """
        self.frame = frame_wrapper
        # Store initial state
        # noinspection PyProtectedMember
        self.target_center = self.frame.camera._frame_center.copy() # type: ignore[attr-defined]  # noqa: SLF001
        self.target_zoom = self.frame.camera.zoom_tracker.get_value()

    def move_to(self, point):
        """Chain a move_to transformation.

        Moves the camera frame center to the specified point. This transformation
        will be animated when passed to :meth:`~.Scene.play`.

        Parameters
        ----------
        point : Point3DLike
            Target position for the camera frame center

        Returns
        -------
        Frame2DAnimateWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            class MoveToExample(HUD2DScene):
                def construct(self):
                    square = Square().shift(RIGHT * 3)
                    self.add(square)

                    # Animate camera to square
                    self.play(self.camera.frame.animate.move_to(square))
        """
        self.target_center.move_to(point)

        return self

    def shift(self, vector):
        """Chain a shift transformation.

        Shifts the camera frame center by the specified vector. This transformation
        will be animated when passed to :meth:`~.Scene.play`.

        Parameters
        ----------
        vector : Vector3D
            Displacement vector for the camera frame

        Returns
        -------
        Frame2DAnimateWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            class ShiftExample(HUD2DScene):
                def construct(self):
                    # Animate camera shift
                    self.play(self.camera.frame.animate.shift(RIGHT * 2 + UP))
        """
        self.target_center.shift(vector)

        return self

    def scale(self, scale_factor: float):
        """Chain a scale transformation.

        Scales the camera frame by the specified factor. Larger factors zoom out,
        smaller factors zoom in. This transformation will be animated when passed
        to :meth:`~.Scene.play`.

        Parameters
        ----------
        scale_factor : float
            Scaling factor (must be positive). Values > 1 zoom out, values < 1 zoom in.

        Returns
        -------
        Frame2DAnimateWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            class ScaleExample(HUD2DScene):
                def construct(self):
                    # Zoom in (scale < 1)
                    self.play(self.camera.frame.animate.scale(0.5))
                    self.wait()

                    # Zoom out (scale > 1)
                    self.play(self.camera.frame.animate.scale(2))

        Notes
        -----
        Negative scale factors are not supported and will produce undefined behavior.
        """
        self.target_zoom = self.target_zoom / scale_factor

        return self

    def set(self, width: float = None, height: float = None):
        """Chain a dimension-setting transformation.

        Sets the camera frame to specific width or height. This transformation
        will be animated when passed to :meth:`~.Scene.play`.

        Parameters
        ----------
        width : float, optional
            Target frame width. Takes precedence if both specified.
        height : float, optional
            Target frame height. Used only if width not specified.

        Returns
        -------
        Frame2DAnimateWrapper
            Self for method chaining

        Examples
        --------
        .. code-block:: python

            class SetExample(HUD2DScene):
                def construct(self):
                    square = Square(side_length=4)
                    self.add(square)

                    # Animate to fit square with margin
                    self.play(self.camera.frame.animate.set(width=6))

        Notes
        -----
        If both width and height are specified, width takes precedence.
        Zero or negative values are not recommended and may cause undefined behavior.
        """
        if width is not None:
            from manim import config
            self.target_zoom = config["frame_width"] / width

        elif height is not None:
            from manim import config
            self.target_zoom = config["frame_height"] / height

        return self

    # noinspection PyProtectedMember
    def build(self):
        """Build the animation from accumulated transformations.

        This method is called internally by :meth:`~.Scene.play` to create the
        actual animation. It combines all chained transformations into a single
        :class:`~.AnimationGroup`.

        Returns
        -------
        AnimationGroup
            Animation group containing frame center and zoom animations

        Notes
        -----
        - Always creates animations for both frame center and zoom, even if unchanged
        - Uses :class:`~.AnimationGroup` to synchronize transformations
        - Called automatically by Manim's animation system; users don't call this directly
        """
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
    """Internal manager for transcript output (not directly user-facing).

    This class is used internally by :class:`HUD2DScene` to manage transcript
    output. Users should interact with ``self.transcript.add_transcript()`` at
    the scene level to add transcript lines.

    The transcript provides verbose descriptions of scene events, separate from
    the visual narration/caption text shown on screen. Transcript lines are
    automatically written to a .txt file during scene teardown.

    Parameters
    ----------
    scene : Scene
        The scene instance that owns this transcript manager

    Attributes
    ----------
    scene : Scene
        Reference to the scene instance
    transcript_lines : list[str]
        Accumulated transcript lines to be written to file

    Examples
    --------
    .. code-block:: python

        class MyScene(HUD2DScene):
            def construct(self):
                # Visual narration (shown on screen)
                self.narrate(r"Step 1: Create square")

                # Transcript entry (written to .txt file)
                self.transcript.add_transcript(
                    "A blue square with side length 2 appears at the origin"
                )

                square = Square(color=BLUE, side_length=2)
                self.play(Create(square))

    See Also
    --------
    :class:`HUD2DScene` : Scene class with integrated transcript manager
    :meth:`HUD2DScene.tear_down` : Calls :meth:`_write_transcript` automatically

    Notes
    -----
    **Transcript vs Narration/Caption:**
        - **Narration/Caption**: Visual HUD text shown in the video
        - **Transcript**: Text file output for accessibility, subtitles, or documentation

    **File Output:**
        - Transcript is written to the same directory as the rendered video
        - Filename matches the video but with ``.txt`` extension instead of ``.mp4``
        - Empty transcripts are not written (no file created)
        - Manim also supports SRT subtitle file output (see Manim documentation)

    **Raw Strings:**
        - Transcript text does NOT require raw strings (it's not processed by LaTeX)
        - Plain text is written directly to the file
    """

    def __init__(self, scene: Scene) -> None:
        """Initialize the TranscriptManager.

        Parameters
        ----------
        scene : Scene
            The scene instance that owns this transcript manager
        """
        self.scene = scene
        self.transcript_lines: list[str] = []

    def add_transcript(self, content: str) -> None:
        """Add a line to the transcript file.

        This is the **user-facing method** for adding transcript entries. Each call
        adds the content as a new line in the transcript. The transcript is written
        to a .txt file automatically during scene teardown.

        Parameters
        ----------
        content : str
            Transcript line content. Plain text (no LaTeX processing).

        Examples
        --------
        .. code-block:: python

            class TranscriptExample(HUD2DScene):
                def construct(self):
                    # Visual narration
                    self.narrate(r"Creating shapes")

                    # Detailed transcript entry
                    self.transcript.add_transcript(
                        "Scene begins with title 'Creating shapes' displayed "
                        "at the top of the screen in white text"
                    )

                    square = Square(color=BLUE)
                    self.transcript.add_transcript(
                        "A blue square with side length 2 units appears at "
                        "the origin using the Create animation over 1 second"
                    )
                    self.play(Create(square))

        See Also
        --------
        :meth:`_write_transcript` : Internal method that writes the file
        :meth:`HUD2DScene.tear_down` : Automatically calls _write_transcript

        Notes
        -----
        - Each call adds a new line to the transcript
        - Lines are accumulated in memory and written during teardown
        - No raw strings needed (plain text, not LaTeX)
        - Useful for accessibility, documentation, or subtitle generation
        """
        self.transcript_lines.append(content)

    def _write_transcript(self) -> None:
        """Write accumulated transcript to file with appropriate logging (internal).

        This method is called automatically by :meth:`HUD2DScene.tear_down` after
        the scene completes. It writes all accumulated transcript lines to a .txt
        file in the same directory as the rendered video.

        Returns
        -------
        None
            No return value. Writes to file and logs success/failure.

        Notes
        -----
        **File Writing Behavior:**
            - Skips writing if no transcript lines were added
            - Creates .txt file with same name as video file
            - Joins all lines with newline characters
            - Uses UTF-8 encoding

        **Error Handling:**
            - Logs debug message if no transcript lines to write
            - Logs warning if renderer or file_writer attributes missing
            - Logs error if file writing fails
            - Does not raise exceptions (graceful degradation)

        **Automatic Invocation:**
            - Called by :meth:`HUD2DScene.tear_down` automatically
            - Users should never call this method directly
        """
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