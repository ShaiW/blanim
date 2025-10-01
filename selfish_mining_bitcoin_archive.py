# Archive of replaced code for reference
#old     def resolve_selfish_chain_wins(self):
        # """Handle resolution when selfish chain is revealed and wins"""
        #
        # # Get the winning selfish block (most recent)
        # winning_block = self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else None
        # if not winning_block:
        #     return
        #
        #     # First: Move selfish chain to honest chain position, honest chain moves up
        # selfish_shift = UP * 1.2  # Move selfish chain up to honest position (y=0)
        # honest_shift = UP * 1.2  # Move honest chain up by same amount
        #
        # selfish_mobjects = []
        # for block in self.selfish_chain.blocks:
        #     selfish_mobjects.extend(block.get_mobjects())
        # selfish_mobjects.extend(self.selfish_chain.lines)
        #
        # honest_mobjects = []
        # for block in self.honest_chain.blocks:
        #     honest_mobjects.extend(block.get_mobjects())
        # honest_mobjects.extend(self.honest_chain.lines)
        #
        # # Animate the chain position swap
        # self.scene.play(AnimationGroup(
        #     *[mob.animate.shift(selfish_shift) for mob in selfish_mobjects],
        #     *[mob.animate.shift(honest_shift) for mob in honest_mobjects]
        # ))
        #
        # # Second: Calculate shift to move winning block to genesis position
        # current_winning_pos = winning_block.get_center()
        # genesis_pos = np.array(self.genesis_position)
        # shift_to_genesis = genesis_pos - current_winning_pos
        #
        # # Collect all mobjects for final positioning
        # all_mobjects = selfish_mobjects + honest_mobjects
        # all_mobjects.extend(self.genesis.get_mobjects())
        #
        # # Move all blocks so winning block reaches genesis position
        # self.scene.play(AnimationGroup(
        #     *[mob.animate.shift(shift_to_genesis) for mob in all_mobjects]
        # ))
        #
        # # Third: Fade out all blocks except the winning block
        # fade_out_mobjects = []
        # for block in self.selfish_chain.blocks[:-1]:  # All but last selfish
        #     fade_out_mobjects.extend(block.get_mobjects())
        # for block in self.honest_chain.blocks:  # All honest blocks
        #     fade_out_mobjects.extend(block.get_mobjects())
        # fade_out_mobjects.extend(self.selfish_chain.lines)
        # fade_out_mobjects.extend(self.honest_chain.lines)
        # fade_out_mobjects.extend(self.genesis.get_mobjects())
        # fade_out_mobjects.append(winning_block.label)  # Keep square, fade label
        #
        # self.scene.play(AnimationGroup(
        #     *[self.animation_factory.fade_out_and_remove(mob) for mob in fade_out_mobjects]
        # ))
        #
        # # Fourth: Reset genesis position and fade in (like zero_to_zero)
        # for mob in self.genesis.get_mobjects():
        #     mob.move_to(self.genesis_position)
        #
        # self.scene.play(AnimationGroup(
        #     *[self.animation_factory.fade_in_and_create(mob) for mob in self.genesis.get_mobjects()],
        #     self.animation_factory.fade_out_and_remove(winning_block.square)
        # ))

# def resolve_honest_chain_wins(self):
#     """Handle resolution when honest chain is ahead - all blocks move, fade out except winner"""
#
#     # Get the winning honest block (most recent)
#     winning_block = self.honest_chain.blocks[-1] if self.honest_chain.blocks else None
#     if not winning_block:
#         return
#
#         # Calculate exact shift needed to move winning block to genesis position
#     current_winning_pos = winning_block.get_center()
#     genesis_pos = np.array(self.genesis_position)
#     shift_vector = genesis_pos - current_winning_pos
#
#     # Collect all mobjects that need to move
#     all_mobjects = []
#     for block in self.honest_chain.blocks:
#         all_mobjects.extend(block.get_mobjects())
#     for block in self.selfish_chain.blocks:
#         all_mobjects.extend(block.get_mobjects())
#     all_mobjects.extend(self.honest_chain.lines)
#     all_mobjects.extend(self.selfish_chain.lines)
#     all_mobjects.extend(self.genesis.get_mobjects())
#
#     # First: Move all blocks so winning block reaches genesis position
#     self.scene.play(AnimationGroup(
#         *[mob.animate.shift(shift_vector) for mob in all_mobjects]
#     ))
#
#     # Second: Fade out all blocks except the winning block
#     fade_out_mobjects = []
#     for block in self.honest_chain.blocks[:-1]:  # All but last (winning) block
#         fade_out_mobjects.extend(block.get_mobjects())
#     for block in self.selfish_chain.blocks:  # All selfish blocks
#         fade_out_mobjects.extend(block.get_mobjects())
#     fade_out_mobjects.extend(self.honest_chain.lines)
#     fade_out_mobjects.extend(self.selfish_chain.lines)
#     fade_out_mobjects.extend(self.genesis.get_mobjects())
#     fade_out_mobjects.append(winning_block.label)  # Keep square, fade label
#
#     self.scene.play(AnimationGroup(
#         *[self.animation_factory.fade_out_and_remove(mob) for mob in fade_out_mobjects]
#     ))
#
#     # Third: Fade out winning block square and fade in genesis
#     for mob in self.genesis.get_mobjects():
#         mob.move_to(self.genesis_position)
#
#     self.scene.play(AnimationGroup(
#         *[self.animation_factory.fade_in_and_create(mob) for mob in self.genesis.get_mobjects()],
#         self.animation_factory.fade_out_and_remove(winning_block.square)
#     ))

#    def _setup_blocks(self):
#        # First selfish block parents to genesis
#        self.selfish_chain.add_block("s1", -2, parent_block=self.genesis)
#
#        # Subsequent selfish blocks parent to previous block
#        for i in range(2, 5):
#            parent = self.selfish_chain.blocks[-1]
#            self.selfish_chain.add_block(f"s{i}", -2 + (i - 1) * 2, parent_block=parent)
#
#        # Same pattern for honest chain
#        self.honest_chain.add_block("h1", -2, parent_block=self.genesis)
#        for i in range(2, 5):
#            parent = self.honest_chain.blocks[-1]
#            self.honest_chain.add_block(f"h{i}", -2 + (i - 1) * 2, parent_block=parent)
#
#    def _setup_lines(self):
#        # Create lines for selfish chain
#        self.selfish_chain.create_line_to_genesis(self.genesis, 0)
#        for i in range(1, 4):
#            self.selfish_chain.create_line_to_previous(i)
#
#            # Create lines for honest chain
#        self.honest_chain.create_line_to_genesis(self.genesis, 0)
#        for i in range(1, 4):
#            self.honest_chain.create_line_to_previous(i)

    # def intro_anim(self):
    #     self.current_state = "intro"
    #
    #     intro_animation = Succession(
    #         AnimationGroup(
    #             self.animation_factory.fade_in_and_create(self.state_manager.get_state("selfish_mining")),
    #             *[self.animation_factory.fade_in(mob) for mob in self.genesis.get_mobjects()],
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[0].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[0]),
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[1].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[1]),
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[2].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[2]),
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[3].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[3]),
    #             *[self.animation_factory.fade_in(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.honest_chain.lines[0])
    #         ),
    #         Wait(self.wait_time),
    #         AnimationGroup(
    #             self.animation_factory.fade_out_and_remove(self.state_manager.get_state("selfish_mining")),
    #             *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[0].get_mobjects()],
    #             self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[0]),
    #             *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[1].get_mobjects()],
    #             self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[1]),
    #             *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[2].get_mobjects()],
    #             self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[2]),
    #             *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[3].get_mobjects()],
    #             self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[3]),
    #             *[self.animation_factory.fade_out(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
    #             self.animation_factory.fade_out_and_remove(self.honest_chain.lines[0])
    #         ),
    #         AnimationGroup(
    #             self.animation_factory.fade_in_and_create(self.state_manager.get_state("state0"))
    #         )
    #     )
    #     return intro_animation
    #
    # def state_zero(self):
    #     self.current_state = "zero"
    #
    #     # All selfish miner transitions
    #
    # def zero_to_one(self):
    #     self.current_state = "one"
    #     return Succession(
    #         AnimationGroup(
    #             self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state0"))
    #         ),
    #         Wait(self.wait_time),
    #         AnimationGroup(
    #             self.animation_factory.fade_in_and_create(self.state_manager.get_state("state1")),
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[0].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[0])
    #         )
    #     )
    #
    # def one_to_two(self):
    #     self.current_state = "two"
    #     return Succession(
    #         AnimationGroup(
    #             self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state1"))
    #         ),
    #         Wait(self.wait_time),
    #         AnimationGroup(
    #             self.animation_factory.fade_in_and_create(self.state_manager.get_state("state2")),
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[1].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[1])
    #         )
    #     )
    #
    # def two_to_three(self):
    #     self.current_state = "three"
    #     return Succession(
    #         AnimationGroup(
    #             self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state2"))
    #         ),
    #         Wait(self.wait_time),
    #         AnimationGroup(
    #             self.animation_factory.fade_in_and_create(self.state_manager.get_state("state3")),
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[2].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[2])
    #         )
    #     )
    #
    # def three_to_four(self):
    #     self.current_state = "four"
    #     return Succession(
    #         AnimationGroup(
    #             self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state3"))
    #         ),
    #         Wait(self.wait_time),
    #         AnimationGroup(
    #             self.animation_factory.fade_in_and_create(self.state_manager.get_state("state4")),
    #             *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[3].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.selfish_chain.lines[3])
    #         )
    #     )
    #
    # def one_to_zero_prime(self):
    #     self.current_state = "zero_prime"
    #     return Succession(
    #         AnimationGroup(
    #             self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state1"))
    #         ),
    #         Wait(self.wait_time),
    #         AnimationGroup(
    #             self.animation_factory.fade_in_and_create(self.state_manager.get_state("state0prime")),
    #             *[self.animation_factory.fade_in(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
    #             self.animation_factory.fade_in_and_create(self.honest_chain.lines[0])
    #         )
    #     )
    #
    # def zero_to_zero(self):
    #     """Complete implementation of the complex zero_to_zero transition"""
    #     self.current_state = "zero"
    #
    #     self.scene.play(AnimationGroup(
    #         self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state0"))
    #     ))
    #
    #     self.scene.play(Wait(self.wait_time))
    #
    #     self.scene.play(AnimationGroup(
    #         *[self.animation_factory.fade_in(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
    #         self.animation_factory.fade_in_and_create(self.honest_chain.lines[0])
    #     ))
    #
    #     self.scene.play(Wait(self.wait_time))
    #
    #     # Move genesis and honest block
    #     self.scene.play(AnimationGroup(
    #         *[mob.animate.move_to((-6, 0, 0)) for mob in self.genesis.get_mobjects()],
    #         *[mob.animate.move_to((-4, 0, 0)) for mob in self.honest_chain.blocks[0].get_mobjects()],
    #         self.honest_chain.lines[0].animate.shift(LEFT * 2)
    #     ))
    #
    #     self.scene.play(Wait(self.wait_time))
    #
    #     # CORRECTED: Fade out line, genesis AND honest block label, keep only honest block square
    #     self.scene.play(AnimationGroup(
    #         *[self.animation_factory.fade_out(mob) for mob in self.genesis.get_mobjects()],
    #         self.animation_factory.fade_out(self.honest_chain.blocks[0].label),  # Fade out label
    #         self.animation_factory.fade_out_and_remove(self.honest_chain.lines[0])
    #         # Note: only honest block square stays visible here
    #     ))
    #
    #     self.scene.play(Wait(self.wait_time))
    #
    #     # Reset genesis position while it's invisible
    #     for mob in self.genesis.get_mobjects():
    #         mob.move_to(self.genesis_position)
    #
    #         # CORRECTED: Fade in genesis while fading out honest block square
    #     self.scene.play(AnimationGroup(
    #         *[self.animation_factory.fade_in(mob) for mob in self.genesis.get_mobjects()],
    #         self.animation_factory.fade_out(self.honest_chain.blocks[0].square)  # Only fade out square
    #     ))
    #
    #     self.scene.bring_to_front(*self.genesis.get_mobjects())
    #
    #     return

# class SelfishMiningExampleOld(Scene):
#     def construct(self):
#         # Create the SelfishMining instance
#         sm = SelfishMiningSquares(self)
#
#         self.wait(2)
#         # Start with the intro animation
#         self.play(sm.intro_anim())
#
#         # The intro_anim already ends with state0 showing and genesis visible
#         self.wait(1)
#
#         # Transition from state 0 to state 1 (selfish miner finds a block)
#         self.play(sm.zero_to_one())
#         self.wait(1)
#
#         # Transition from state 1 to state 2 (selfish miner finds another block)
#         self.play(sm.one_to_two())
#         self.wait(1)
#
#         # Transition from state 2 to state 3 (selfish miner finds another block)
#         self.play(sm.two_to_three())
#         self.wait(1)
#
#         # Transition from state 3 to state 4 (selfish miner finds another block)
#         self.play(sm.three_to_four())
#         self.wait(1)
#
#         # Now show what happens when honest miner finds a block in state 1
#         # First, let's go back to state 1 by fading out the higher state blocks
#         self.play(Succession(
#             AnimationGroup(
#                 sm.animation_factory.fade_out_and_remove(sm.state_manager.get_state("state4")),
#                 *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[1].get_mobjects()],
#                 sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[1]),
#                 *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[2].get_mobjects()],
#                 sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[2]),
#                 *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[3].get_mobjects()],
#                 sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[3]),
#             ),
#             Wait(1),
#             AnimationGroup(
#                 sm.animation_factory.fade_in_and_create(sm.state_manager.get_state("state1")),
#             )
#         ))
#         self.wait(1)
#
#         # Show transition from state 1 to state 0' (honest miner finds a block)
#         self.play(sm.one_to_zero_prime())
#         self.wait(1)
#
#         # Finally, demonstrate the zero_to_zero transition
#         # First fade out state 0' elements and show state 0
#         self.play(Succession(
#             AnimationGroup(
#                 sm.animation_factory.fade_out_and_remove(sm.state_manager.get_state("state0prime")),
#                 *[sm.animation_factory.fade_out(mob) for mob in sm.honest_chain.blocks[0].get_mobjects()],
#                 sm.animation_factory.fade_out_and_remove(sm.honest_chain.lines[0]),
#                 *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[0].get_mobjects()],
#                 sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[0]),
#             ),
#             Wait(1),
#             AnimationGroup(
#                 sm.animation_factory.fade_in_and_create(sm.state_manager.get_state("state0"))
#             )
#         ))
#         self.wait(2)
#
#         # Show the zero_to_zero transition (honest miner finds a block in state 0)
#         sm.zero_to_zero()
#
#         self.wait(2)