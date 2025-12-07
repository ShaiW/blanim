from __future__ import annotations

__all__ = ["ParentLine"]

from manim import Line, WHITE, CapStyleType, UpdateFromFunc, ParsableManimColor


#TODO ensure lines have their own properties preserved so animations can be created by accessing lines properties
class ParentLine(Line):
    """Uses no updater, update from func during movement anims on either parent or child block.square"""
    def __init__(self, this_block, parent_block, line_color: ParsableManimColor = WHITE, is_selected_parent_line = False):#TODO is sp.line is defined in visual block, NOT line
        """A line connecting parent and child blocks with automatic position updates.

        This line uses the UpdateFromFunc pattern to maintain its position during block
        movement animations. It does not use continuous updaters; instead, update animations
        are created on-demand via `create_update_animation()` and managed by the DAG's
        deduplication system.

        **Z-Index Layering System**

        Lines use z-index range 0-10 to ensure they render behind blocks (11-20):

        - Regular lines: z_index = 1 (bottom layer)
        - Selected parent lines: z_index = 5 (middle of line range, above regular lines)
        - Blocks (backgrounds): z_index = 11
        - Blocks (squares): z_index = 12
        - Blocks (labels): z_index = 13

        This hierarchy ensures:

        1. All lines render behind all blocks
        2. Selected parent lines render above regular lines
        3. Room for future intermediate layers (e.g., z_index=2 for special line types)

        **Architecture Integration**

        - Owned by child block (created during child initialization)
        - Should be registered with both parent and child blocks' `connected_lines` lists
        - Position updates triggered by DAG's `deduplicate_line_animations()` helper
        - Compatible with HUD2DScene's z-index rendering system

        Parameters
        ----------
        this_block : Mobject
            The child block's square (NOT the block itself). Used as line start point.
        parent_block : Mobject
            The parent block's square (NOT the block itself). Used as line end point.
        line_color : ManimColor, optional
            Line color. Defaults to WHITE.
        is_selected_parent_line : bool, optional
            Whether this is a selected parent line (renders above regular lines).
            Defaults to False.

        Attributes
        ----------
        this_block : Mobject
            Reference to child block's square for position updates
        parent_block : Mobject
            Reference to parent block's square for position updates
        is_selected_parent_line : bool
            Whether this line is marked as selected

        Examples
        --------
        .. code-block:: python

            # Create regular parent line
            line = ParentLine(child.square, parent.square)

            # Create selected parent line (renders above other lines)
            selected_line = ParentLine(
                child.square,
                parent.square,
                line_color=YELLOW,
                is_selected_parent_line=True
            )

            # Use in animation (handled by DAG)
            animations = dag.deduplicate_line_animations(
                block1.animate_move_to(new_pos1),
                block2.animate_move_to(new_pos2),
            )
            scene.play(*animations)

        Notes
        -----
        - **REQUIREMENT**: Must pass block.square, NOT the block itself
        - Does not use `shade_in_3d=True` (incompatible with animation system)
        - Uses z-index for rendering order, not z-coordinate positioning
        - Line updates must be deduplicated when multiple connected blocks move
        - Compatible with ThreeDScene's default z-index rendering system

        See Also
        --------
        HUD2DScene : Scene class with z-index support
        BlockWithBg : Reference implementation for block structure
        ConnectingLine : Reference implementation for line architecture
        """
        super().__init__(
            start=this_block.get_left(),
            end=parent_block.get_right(),
            buff=0.1,
            color=line_color,
            stroke_width=4,
            cap_style = CapStyleType.ROUND,
        )

        self.this_block = this_block
        self.parent_block = parent_block

        self.is_selected = is_selected_parent_line
        self.set_z_index(5 if is_selected_parent_line else 1)

    def _update_position_and_size(self, mobject):
        new_start = self.this_block.get_left()
        new_end = self.parent_block.get_right()

        self.set_points_by_ends(new_start, new_end, buff=self.buff)

    def create_update_animation(self):
        return UpdateFromFunc(
            self,
            update_function=self._update_position_and_size,
            suspend_mobject_updating=False
        )