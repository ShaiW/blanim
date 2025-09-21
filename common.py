from typing import List

from manim import *

##all sort of stuff that manim should have but doesn't

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