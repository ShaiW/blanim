import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Set
import numpy as np
from manim import *  # currently using manim to determine what problems come from how I am using manim

from blanim import HUD2DScene


@dataclass
class BlockConfig:
    """Configuration for block creation."""
    size: float
    spacing: float
    stroke_width: int = 2
    fill_opacity: float = 0
    color: str = WHITE


class BlockFactory(ABC):
    """Abstract factory for creating blocks."""

    @abstractmethod
    def create_block(self, index: int, block_number: int, position: np.ndarray) -> Tuple[VGroup, Text]:
        """Create a block with its label at the specified position."""
        pass


class MainBlockFactory(BlockFactory):
    """Factory for creating main blocks with header and body."""

    def __init__(self, config: BlockConfig):
        self.config = config

    def create_block(self, index: int, block_number: int, position: np.ndarray) -> Tuple[VGroup, Text]:
        """Create a main block with header, body, and label."""
        # Create main container
        block = Square(
            side_length=self.config.size,
            color=self.config.color,
            fill_opacity=self.config.fill_opacity,
            stroke_width=3
        )
        block.move_to(position)

        # Create header and body
        header = self._create_header(block)
        body = self._create_body(block)

        block_group = VGroup(block, header, body)

        # Create label
        label_text = "Genesis" if block_number == 0 else f"Block {block_number}"
        label = Text(label_text, font_size=24)
        label.move_to(block_group.get_top() + UP * 0.3)

        return block_group, label

    def _create_header(self, block: Square) -> Rectangle:
        """Create header rectangle for a block."""
        header = Rectangle(
            width=3.5,
            height=0.8,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        header.move_to(block.get_center() + UP * 1.3)
        return header

    def _create_body(self, block: Square) -> Rectangle:
        """Create body rectangle for a block."""
        body = Rectangle(
            width=3.5,
            height=2.1,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        body.move_to(block.get_center() + DOWN * 0.6)
        return body


class MiniBlockFactory(BlockFactory):
    """Factory for creating mini blocks."""

    def __init__(self, config: BlockConfig, frame_center: np.ndarray):
        self.config = config
        self.frame_center = frame_center

    def create_block(self, index: int, block_number: int, position: np.ndarray) -> Tuple[Square, Text]:
        """Create a mini block with its label."""
        mini_block = Square(
            side_length=self.config.size,
            color=self.config.color,
            fill_opacity=self.config.fill_opacity,
            stroke_width=1
        )
        mini_block.move_to(position)

        # Create label
        label_text = "G" if block_number == 0 else str(block_number)
        mini_label = Text(label_text, font_size=6, color=WHITE)
        mini_label.move_to(mini_block.get_center())

        return mini_block, mini_label


class BlockManager:
    """Manages a collection of blocks and their visibility."""

    def __init__(self, factory: BlockFactory, max_blocks: int):
        self.factory = factory
        self.max_blocks = max_blocks
        self.blocks = []
        self.labels = []
        self.visible_indices: Set[int] = set()

    def initialize_blocks(self, count: int):
        """Initialize the specified number of blocks."""
        for i in range(count):
            # Create blocks at origin initially - they'll be positioned when needed
            block, label = self.factory.create_block(i, i, np.array([0, 0, 0]))
            self.blocks.append(block)
            self.labels.append(label)

    def get_block(self, index: int) -> Tuple[VGroup, Text]:
        """Get block and label at the specified index."""
        return self.blocks[index], self.labels[index]

    def find_available_index(self) -> int | None:
        """Find the next available block index."""
        for i in range(len(self.blocks)):
            if i not in self.visible_indices:
                return i
        return None

    def add_visible(self, index: int):
        """Mark block as visible."""
        self.visible_indices.add(index)

    def remove_visible(self, index: int):
        """Mark block as not visible."""
        self.visible_indices.discard(index)

    def clear_visible(self):
        """Clear all visible block tracking."""
        self.visible_indices.clear()

    def get_visible_indices(self) -> Set[int]:
        """Get set of visible block indices."""
        return self.visible_indices.copy()

class StreamingBlockFactory:
    """Factory for creating temporary streaming blocks."""

    def __init__(self, block_size: float):
        self.block_size = block_size

    def create_streaming_block(self, block_number: int, position: np.ndarray) -> Tuple[Rectangle, Text]:
        """Create a temporary streaming block."""
        stream_block = Rectangle(
            width=self.block_size * 0.8,
            height=self.block_size * 0.8,
            fill_opacity=0.3,
            stroke_opacity=0.7,
            color=BLUE
        )
        stream_block.move_to(position)

        stream_label = Text(f"Block {block_number}", font_size=18, color=WHITE)
        stream_label.move_to([position[0], position[1] + self.block_size / 2 + 0.3, 0])

        return stream_block, stream_label


class ScrollingBlocks(Scene):
    # Constants for better maintainability
    BLOCK_SIZE = 4
    MINI_BLOCK_SIZE = 0.3
    BLOCK_SPACING = 6
    MINI_BLOCK_SPACING = 0.4
    MAX_VISIBLE_BLOCKS = 3
    PRUNING_THRESHOLD = 16

    def __init__(self):
        super().__init__()

        # Initialize configurations
        self.main_block_config = BlockConfig(
            size=self.BLOCK_SIZE,
            spacing=self.BLOCK_SPACING,
            stroke_width=3
        )

        self.mini_block_config = BlockConfig(
            size=self.MINI_BLOCK_SIZE,
            spacing=self.MINI_BLOCK_SPACING,
            stroke_width=1
        )

        # Scene state
        self.next_block_number = 1
        self.total_blocks_created = 1
        self.mini_chain_frame = None

        # Will be initialized in setup
        self.main_block_manager = None
        self.mini_block_manager = None
        self.streaming_factory = None

    def construct(self):
        """Main scene construction method."""
        self._setup_scene_elements()
        self._create_initial_display()
        self._run_scrolling_animation()

    def _setup_scene_elements(self):
        """Create and position all scene elements."""
        narration = self._create_narration()
        self.mini_chain_frame = self._create_mini_chain_frame(narration)

        # Initialize factories and managers
        main_factory = MainBlockFactory(self.main_block_config)
        # Fix: Pass the frame center to MiniBlockFactory
        mini_factory = MiniBlockFactory(self.mini_block_config, self.mini_chain_frame.get_center())

        self.main_block_manager = BlockManager(main_factory, 4)
        self.mini_block_manager = BlockManager(mini_factory, 50)
        self.streaming_factory = StreamingBlockFactory(self.BLOCK_SIZE)

        # Create blocks
        self.main_block_manager.initialize_blocks(4)
        self.mini_block_manager.initialize_blocks(50)

        # Position blocks initially
        self._position_initial_blocks()

        # Display initial elements
        self.play(Write(narration))
        self.play(Create(self.mini_chain_frame))
        self.wait(1)

    def _position_initial_blocks(self):
        """Position blocks at their initial locations."""
        # Position main blocks
        for i in range(4):
            block, label = self.main_block_manager.get_block(i)
            position = self._get_block_position(i)
            block.move_to(position)
            label.move_to(block.get_top() + UP * 0.3)

            # Position mini blocks
        for i in range(50):
            mini_block, mini_label = self.mini_block_manager.get_block(i)
            position = self.mini_chain_frame.get_center() + RIGHT * i * self.MINI_BLOCK_SPACING
            mini_block.move_to(position)
            mini_label.move_to(mini_block.get_center())

    def _create_narration(self) -> Text:
        """Create the title narration text."""
        narration = Text("Kaspa Pruning (k=0)", font_size=36, color=WHITE)
        narration.to_edge(UP)
        return narration

    def _create_mini_chain_frame(self, narration: Text) -> Rectangle:
        """Create the mini-chain container frame."""
        frame = Rectangle(
            width=1.0,
            height=0.6,
            color=YELLOW,
            stroke_width=2,
            fill_opacity=0
        )
        frame.next_to(narration, DOWN, buff=0.3)
        return frame

    def _get_block_position(self, index: int) -> np.ndarray:
        """Calculate position for a block based on its index."""
        if index == 0:
            return np.array([-6, -0.75, 0])  # Left
        elif index == 1:
            return np.array([0, -0.75, 0])  # Center
        else:
            return np.array([6, -0.75, 0])  # Right

    def _create_initial_display(self):
        """Show the initial Genesis block and mini block."""
        main_block, main_label = self.main_block_manager.get_block(1)
        mini_block, mini_label = self.mini_block_manager.get_block(0)

        self.play(
            Create(main_block),
            Write(main_label),
            Create(mini_block),
            Write(mini_label)
        )

        self.main_block_manager.add_visible(1)
        self.mini_block_manager.add_visible(0)
        self.wait(1)

    def _run_scrolling_animation(self):
        """Execute the main scrolling animation loop."""
        # Normal scrolling for first few blocks
        for _ in range(5):
            self._scroll_left()
            self.wait(1)

            # Fast scroll to block 50
        self.wait(1)
        self._fast_scroll_to_block(50, scroll_duration=1.0)
        self.wait(2)

        # Continue normal scrolling from there
        for _ in range(5):
            self._scroll_left()
            self.wait(1)

        self.wait(2)

    def _fast_scroll_to_block(self, target_block_number: int, scroll_duration: float = 3.0):
        """Perform fast scroll with existing blocks moving and identical visual appearance."""
        # Phase 1: Speed up existing blocks while streaming identical filler blocks (70% of duration)
        self._accelerate_existing_and_stream_identical_blocks(target_block_number, scroll_duration * 0.7)

        # Phase 2: Position target blocks (30% of duration)
        self._position_target_blocks(target_block_number, scroll_duration * 0.3)

        self._update_tracking_for_target(target_block_number)

    def _accelerate_existing_and_stream_identical_blocks(self, target_block_number: int, duration: float):
        """Move existing blocks faster while streaming identical-looking filler blocks."""
        blocks_to_create = target_block_number - self.next_block_number - 3

        if blocks_to_create <= 0:
            return

            # Create batches of streaming blocks using MainBlockFactory for identical appearance
        batch_size = 4
        num_batches = max(1, blocks_to_create // batch_size)
        batch_duration = duration / num_batches

        for batch in range(num_batches):
            batch_animations = []
            batch_blocks = []
            batch_labels = []

            # Animate existing blocks moving faster to the left
            for block_idx in self.main_block_manager.get_visible_indices():
                block, label = self.main_block_manager.get_block(block_idx)
                batch_animations.extend([
                    block.animate.shift(LEFT * self.BLOCK_SPACING * 2),  # Move existing blocks faster
                    label.animate.shift(LEFT * self.BLOCK_SPACING * 2)
                ])

            for mini_idx in self.mini_block_manager.get_visible_indices():
                mini_block, mini_label = self.mini_block_manager.get_block(mini_idx)
                batch_animations.extend([
                    mini_block.animate.shift(LEFT * self.MINI_BLOCK_SPACING * 8),  # Move existing mini blocks faster
                    mini_label.animate.shift(LEFT * self.MINI_BLOCK_SPACING * 8)
                ])

                # Create identical-looking filler blocks using MainBlockFactory
            for i in range(batch_size):
                block_num = self.next_block_number + batch * batch_size + i
                if block_num >= target_block_number - 3:
                    break

                    # Use MainBlockFactory to create identical-looking blocks
                start_pos = np.array([12, -0.75, 0])  # Start off-screen right
                block, label = self.main_block_manager.factory.create_block(
                    0, block_num, start_pos
                )

                # Add to scene
                self.add(block, label)
                batch_blocks.append(block)
                batch_labels.append(label)

                # Create animation to move left across screen at same speed as existing blocks
                batch_animations.extend([
                    block.animate.shift(LEFT * 20),
                    label.animate.shift(LEFT * 20)
                ])

            if batch_animations:
                # Use rush_into rate function for acceleration effect
                self.play(*batch_animations, run_time=batch_duration, rate_func=rush_into)

                # Remove filler blocks after they pass
                for block, label in zip(batch_blocks, batch_labels):
                    self.remove(block, label)

    def _position_target_blocks(self, target_block_number: int, duration: float):
        """Position target blocks after existing blocks have moved off-screen."""
        # Clear existing blocks that have moved off-screen
        self._hide_current_blocks()

        # Calculate which blocks should be visible around target
        center_idx = 1  # Center position
        visible_range = range(
            max(0, target_block_number - center_idx),
            min(target_block_number + self.MAX_VISIBLE_BLOCKS - center_idx, target_block_number + 10)
        )

        # Position new target blocks
        new_block_animations = []

        for i, block_num in enumerate(visible_range):
            available_idx = self.main_block_manager.find_available_index()
            if available_idx is not None:
                # Calculate final position
                final_x = (i - center_idx) * self.BLOCK_SPACING

                # Start position (off-screen right)
                start_x = final_x + self.BLOCK_SPACING * 2

                # Get and position block
                block, label = self.main_block_manager.get_block(available_idx)
                block.move_to(np.array([start_x, -0.75, 0]))

                # Update label
                label_text = "Genesis" if block_num == 0 else f"Block {block_num}"
                label.become(Text(label_text, font_size=24))
                label.move_to(block.get_top() + UP * 0.3)

                # Add to scene
                self.add(block, label)
                self.main_block_manager.add_visible(available_idx)

                # Create deceleration animation using rush_from
                new_block_animations.extend([
                    block.animate.move_to(np.array([final_x, -0.75, 0])),
                    label.animate.move_to(np.array([final_x, -0.75 + self.BLOCK_SIZE / 2 + 0.3, 0]))
                ])

                # Reposition mini blocks
        self._reposition_mini_blocks_for_target(target_block_number)

        # Play settling animation with deceleration
        if new_block_animations:
            self.play(*new_block_animations, run_time=duration, rate_func=rush_from)

    def _hide_current_blocks(self):
        """Hide blocks from scene but keep them in memory."""
        # Remove from scene but don't clear from managers
        for block_idx in self.main_block_manager.get_visible_indices():
            block, label = self.main_block_manager.get_block(block_idx)
            self.remove(block, label)

        for mini_idx in self.mini_block_manager.get_visible_indices():
            mini_block, mini_label = self.mini_block_manager.get_block(mini_idx)
            self.remove(mini_block, mini_label)

            # Clear visibility tracking but blocks remain in memory
        self.main_block_manager.clear_visible()
        self.mini_block_manager.clear_visible()

    def _hide_current_blocks(self):
        """Hide blocks from scene but keep them in memory."""
        # Remove from scene but don't clear from managers
        for block_idx in self.main_block_manager.get_visible_indices():
            block, label = self.main_block_manager.get_block(block_idx)
            self.remove(block, label)

        for mini_idx in self.mini_block_manager.get_visible_indices():
            mini_block, mini_label = self.mini_block_manager.get_block(mini_idx)
            self.remove(mini_block, mini_label)

            # Clear visibility tracking but blocks remain in memory
        self.main_block_manager.clear_visible()
        self.mini_block_manager.clear_visible()

    def _reposition_mini_blocks_for_target(self, target_block_number: int):
        """Reposition mini blocks around the target block number."""
        # Calculate the range of blocks to show (±15 around target)
        start_block = max(0, target_block_number - 15)
        end_block = min(target_block_number + 15, 50)  # Max 50 mini blocks

        # Position mini blocks for the visible range
        for i, block_num in enumerate(range(start_block, end_block + 1)):
            if i < 50:  # We have 50 mini blocks available
                # Position mini block relative to frame center
                x_offset = (block_num - target_block_number) * self.MINI_BLOCK_SPACING
                x_pos = self.mini_chain_frame.get_center()[0] + x_offset

                mini_block, mini_label = self.mini_block_manager.get_block(i)
                mini_block.move_to(np.array([
                    x_pos,
                    self.mini_chain_frame.get_center()[1],
                    0
                ]))

                # Update label based on block number
                label_text = "G" if block_num == 0 else str(block_num)
                mini_label.become(Text(label_text, font_size=6, color=WHITE))
                mini_label.move_to(mini_block.get_center())

                # Add to scene and tracking
                self.add(mini_block, mini_label)
                self.mini_block_manager.add_visible(i)

    def _update_tracking_for_target(self, target_block_number: int):
        """Update tracking variables after fast scroll."""
        self.next_block_number = target_block_number + 1
        self.total_blocks_created = max(self.total_blocks_created, target_block_number + 1)

    def _scroll_left(self):
        """Perform left scrolling animation using block managers."""
        # Find available indices
        rightmost_block_idx = self.main_block_manager.find_available_index()
        rightmost_mini_idx = self.mini_block_manager.find_available_index()

        if rightmost_block_idx is None or rightmost_mini_idx is None:
            return

            # Position new elements
        self._position_new_block(rightmost_block_idx)
        self._position_new_mini_block(rightmost_mini_idx)

        # Create and play animations
        create_animations = self._create_block_animations(rightmost_block_idx, rightmost_mini_idx)
        fade_animations = self._create_fade_animations()

        all_animations = create_animations + fade_animations
        self.play(*all_animations, run_time=1)

        # Update tracking
        self._update_tracking(rightmost_block_idx, rightmost_mini_idx)

        # Shift remaining blocks
        self._shift_all_blocks_left()

    def _position_new_block(self, block_idx: int):
        """Position a new block next to the rightmost visible block."""
        visible_indices = self.main_block_manager.get_visible_indices()

        if not visible_indices:
            rightmost_pos = 0
        else:
            rightmost_pos = max([
                self.main_block_manager.get_block(i)[0].get_center()[0]
                for i in visible_indices
            ])

        final_position = np.array([rightmost_pos + self.BLOCK_SPACING, -0.75, 0])

        block, label = self.main_block_manager.get_block(block_idx)
        block.move_to(final_position)

        # Update label
        label.become(Text(f"Block {self.next_block_number}", font_size=24))
        label.move_to(block.get_top() + UP * 0.3)

    def _position_new_mini_block(self, mini_idx: int):
        """Position a new mini block next to the rightmost visible mini block."""
        visible_indices = self.mini_block_manager.get_visible_indices()

        if not visible_indices:
            rightmost_mini_pos = self.mini_chain_frame.get_center()[0]
        else:
            rightmost_mini_pos = max([
                self.mini_block_manager.get_block(i)[0].get_center()[0]
                for i in visible_indices
            ])

        final_position = np.array([
            rightmost_mini_pos + self.MINI_BLOCK_SPACING,
            self.mini_chain_frame.get_center()[1],
            0
        ])

        mini_block, mini_label = self.mini_block_manager.get_block(mini_idx)
        mini_block.move_to(final_position)

        # Update label
        mini_label.become(Text(f"{self.next_block_number}", font_size=6))
        mini_label.move_to(mini_block.get_center())

    def _create_block_animations(self, block_idx: int, mini_idx: int) -> list:
        """Create animations for new blocks appearing."""
        block, label = self.main_block_manager.get_block(block_idx)
        mini_block, mini_label = self.mini_block_manager.get_block(mini_idx)

        self.add(block, label)
        self.add(mini_block, mini_label)

        return [
            Create(block),
            Write(label),
            Create(mini_block),
            Write(mini_label)
        ]

    def _create_fade_animations(self) -> list:
        """Create fade animations for blocks that should disappear."""
        fade_animations = []
        visible_main = self.main_block_manager.get_visible_indices()
        visible_mini = self.mini_block_manager.get_visible_indices()

        # Fade main blocks if too many visible
        if len(visible_main) >= self.MAX_VISIBLE_BLOCKS:
            leftmost_idx = min(visible_main, key=lambda i:
            self.main_block_manager.get_block(i)[0].get_center()[0])

            block, label = self.main_block_manager.get_block(leftmost_idx)
            fade_animations.extend([FadeOut(block), FadeOut(label)])
            self.main_block_manager.remove_visible(leftmost_idx)

            # Fade mini blocks based on pruning rule
        if self.total_blocks_created >= self.PRUNING_THRESHOLD and visible_mini:
            leftmost_mini_idx = min(visible_mini, key=lambda i:
            self.mini_block_manager.get_block(i)[0].get_center()[0])

            mini_block, mini_label = self.mini_block_manager.get_block(leftmost_mini_idx)
            fade_animations.extend([FadeOut(mini_block), FadeOut(mini_label)])
            self.mini_block_manager.remove_visible(leftmost_mini_idx)

        return fade_animations

    def _update_tracking(self, block_idx: int, mini_idx: int):
        """Update tracking variables after adding new blocks."""
        self.main_block_manager.add_visible(block_idx)
        self.mini_block_manager.add_visible(mini_idx)
        self.next_block_number += 1
        self.total_blocks_created += 1

    def _shift_all_blocks_left(self):
        """Shift all visible blocks to the left."""
        shift_animations = []

        # Shift main blocks
        for i in self.main_block_manager.get_visible_indices():
            block, label = self.main_block_manager.get_block(i)
            shift_animations.extend([
                block.animate.shift(LEFT * self.BLOCK_SPACING),
                label.animate.shift(LEFT * self.BLOCK_SPACING)
            ])

            # Shift mini blocks
        for i in self.mini_block_manager.get_visible_indices():
            mini_block, mini_label = self.mini_block_manager.get_block(i)
            shift_animations.extend([
                mini_block.animate.shift(LEFT * self.MINI_BLOCK_SPACING),
                mini_label.animate.shift(LEFT * self.MINI_BLOCK_SPACING)
            ])

        self.play(*shift_animations, run_time=1)


class BitcoinVsKaspaLogarithmic(HUD2DScene):
    def construct(self):
        all_kaspa_blocks = VGroup()
        block_count = 0

        self.narrate(r"Bitcoin vs Kaspa: Block Production")
        self.add(all_kaspa_blocks)

        # Set initial zoom
        self.camera.zoom_tracker.set_value(6.0)

        frame_height = config["frame_height"]
        frame_width = config["frame_width"]
        margin = 1.0

        # Phase 1: 0-1 second (REDUCED: 10 blocks, ~15 seconds total)
        for i in range(10):
            time = (i + 1) * 0.1
            block_count += 1
            new_block = Square(side_length=1.0, stroke_width=0, fill_opacity=1, color="#70C7BA")
            all_kaspa_blocks.add(new_block)

            cols = min(block_count, 10)
            rows = math.ceil(block_count / cols)

            # ANIMATED repositioning with reduced run_time
            self.play(
                Create(new_block),
                all_kaspa_blocks.animate.arrange_in_grid(rows=rows, cols=cols, buff=0.1).move_to(ORIGIN),
                run_time=0.3  # REDUCED from 1
            )

            current_zoom = self.camera.zoom_tracker.get_value()
            visible_height = frame_height / current_zoom
            visible_width = frame_width / current_zoom

            if (all_kaspa_blocks.height > (visible_height - margin) or
                    all_kaspa_blocks.width > (visible_width - margin)):
                new_zoom = current_zoom * 0.85
                self.play(
                    self.camera.zoom_tracker.animate.set_value(new_zoom),
                    run_time=0.3  # REDUCED from 1
                )

            self.narrate(f"Time: {time:.1f}s | Kaspa: {block_count}")

            # Phase 2: 1-10 seconds (REDUCED: ~20 seconds total)
        for i in range(1, 10):
            time = i + 1
            block_count += 10
            new_blocks = VGroup(*[
                Square(side_length=1.0, stroke_width=0, fill_opacity=1, color="#70C7BA")
                for _ in range(10)
            ])
            all_kaspa_blocks.add(*new_blocks)

            cols = min(block_count, 20)
            rows = math.ceil(block_count / cols)

            # ANIMATED repositioning with reduced run_time
            self.play(
                Create(new_blocks),
                all_kaspa_blocks.animate.arrange_in_grid(rows=rows, cols=cols, buff=0.1).move_to(ORIGIN),
                run_time=0.5  # REDUCED from 2
            )

            current_zoom = self.camera.zoom_tracker.get_value()
            visible_height = frame_height / current_zoom
            visible_width = frame_width / current_zoom

            if (all_kaspa_blocks.height > (visible_height - margin) or
                    all_kaspa_blocks.width > (visible_width - margin)):
                new_zoom = current_zoom * 0.8
                self.play(
                    self.camera.zoom_tracker.animate.set_value(new_zoom),
                    run_time=0.5  # REDUCED from 2
                )

            self.narrate(f"Time: {time}s | Kaspa: {block_count}")

            # Phase 3: 10s-1min (REDUCED: ~15 seconds total)
        for i in range(1, 6):
            time = i * 10
            block_count += 100
            new_blocks = VGroup(*[
                Square(side_length=1.0, stroke_width=0, fill_opacity=1, color="#70C7BA")
                for _ in range(100)
            ])
            all_kaspa_blocks.add(*new_blocks)

            cols = int(math.sqrt(block_count) * 1.5)
            rows = math.ceil(block_count / cols)

            # ANIMATED repositioning with reduced run_time
            self.play(
                Create(new_blocks),
                all_kaspa_blocks.animate.arrange_in_grid(rows=rows, cols=cols, buff=0.1).move_to(ORIGIN),
                run_time=0.8  # REDUCED from 3
            )

            current_zoom = self.camera.zoom_tracker.get_value()
            visible_height = frame_height / current_zoom
            visible_width = frame_width / current_zoom

            if (all_kaspa_blocks.height > (visible_height - margin) or
                    all_kaspa_blocks.width > (visible_width - margin)):
                new_zoom = current_zoom * 0.75
                self.play(
                    self.camera.zoom_tracker.animate.set_value(new_zoom),
                    run_time=0.8  # REDUCED from 3
                )

            self.narrate(f"Time: {time}s | Kaspa: {block_count}")

            # Phase 4: 1min-10min (REDUCED: ~25 seconds total)
        for i in range(1, 10):
            minutes = i + 1
            block_count += 600
            new_blocks = VGroup(*[
                Square(side_length=1.0, stroke_width=0, fill_opacity=1, color="#70C7BA")
                for _ in range(600)
            ])
            all_kaspa_blocks.add(*new_blocks)

            cols = int(math.sqrt(block_count) * 1.2)
            rows = math.ceil(block_count / cols)

            # ANIMATED repositioning with reduced run_time
            self.play(
                Create(new_blocks),
                all_kaspa_blocks.animate.arrange_in_grid(rows=rows, cols=cols, buff=0.1).move_to(ORIGIN),
                run_time=1.0  # REDUCED from 4
            )

            current_zoom = self.camera.zoom_tracker.get_value()
            visible_height = frame_height / current_zoom
            visible_width = frame_width / current_zoom

            if (all_kaspa_blocks.height > (visible_height - margin) or
                    all_kaspa_blocks.width > (visible_width - margin)):
                new_zoom = current_zoom * 0.7
                self.play(
                    self.camera.zoom_tracker.animate.set_value(new_zoom),
                    run_time=1.0  # REDUCED from 4
                )

            self.narrate(f"Time: {minutes}min | Kaspa: {block_count}")

            # Phase 5: Bitcoin block (REDUCED: ~15 seconds total)
        self.narrate(r"10 Minutes: Bitcoin block created!")

        kaspa_top_left = all_kaspa_blocks.get_corner(UP + LEFT)

        bitcoin_block = Square(
            side_length=1.0,
            stroke_width=2,
            stroke_color=WHITE,
            fill_opacity=0.9,
            color="#F7931A"
        )
        bitcoin_block.move_to(kaspa_top_left + UP * 1.5)

        self.play(Create(bitcoin_block), run_time=2)  # REDUCED from 5

        # Zoom to Bitcoin block using set(height=...)
        bitcoin_height = bitcoin_block.height
        target_pos = bitcoin_block.get_center()
        self.play(
            self.camera.frame.animate.move_to(target_pos).set(height=bitcoin_height * 3),
            run_time=3  # REDUCED from 5
        )
        self.wait(1.5)  # REDUCED from 3

        # Final zoom out
        all_objects = VGroup(all_kaspa_blocks, bitcoin_block)
        total_height = all_objects.height

        self.play(
            self.camera.frame.animate.move_to(all_objects.get_center()).set(height=total_height * 1.2),
            run_time=2.5  # REDUCED from 4
        )
        self.caption(r"1 Bitcoin block vs 6000 Kaspa blocks")
        self.wait(2)  # REDUCED from 3