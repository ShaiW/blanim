# Archive of replaced code for reference

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