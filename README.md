# blanim
A wrapper for manim for blockchain and blockDAG related animations

# About
BLanim (short for BLockDAG animations) is an extension of the [Manim (community)](https://github.com/ManimCommunity/manim) Python package, a community-maintained version of the library used by 3Blue1Brown to animate mathematical concepts. BLanim extends Manim with utilities specifically designed for creating visual illustrations of blockchain and blockDAG related concepts. I develop Manim to produce animations for my YouTube channel, [the Deepdive](https://www.youtube.com/@desheDives).

BLanim is currently in a pre-pre-pre-alpha stage and is only publicly available for collaboration purposes. It is not well packaged yet, lacks documentation, and needs a lot of refactoring and missing features. If you'd like to contribute, please don't hesitate to contact me.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ShaiW/blanim)

Note: from here to end is AI generated and can likely be improved

# BLanim: BlockDAG Animation Library  
  
BLanim is a comprehensive Python library extending [Manim (community)](https://github.com/ManimCommunity/manim) with specialized tools for creating blockchain and blockDAG animations. Built for educational content creation, it provides complete visualization systems for both linear chains (Bitcoin) and directed acyclic graphs (Kaspa).
  
## Features  
  
### Complete Blockchain Visualization  
- **Bitcoin Support**: Linear blockchain visualization with single-parent chains
- **Kaspa Support**: Full DAG visualization with GHOSTDAG consensus algorithm   
- **Multiple Parent Lines**: Visual support for blocks referencing multiple parents
  
### Sophisticated Architecture  
- **Manager Delegation Pattern**: Specialized managers for distinct concerns
- **Three-Layer Separation**: Logical blocks (structure), visual blocks (rendering), DAG layer (orchestration)
- **Unified Configuration**: Type-safe config system with blockchain-specific parameters
  
### Advanced Animation Features  
- **Workflow Control**: Step-by-step, immediate, or batch animation patterns
- **Network Simulation**: Realistic block generation with propagation delays
- **GHOSTDAG Visualization**: Complete consensus algorithm animation with blue/red classification
  
## Scene Infrastructure  
  
### 🎬 HUD2DScene Framework  
- **Dual Text Channels**: Upper narration and lower caption with primer pattern optimization
- **Fixed-in-Frame HUD**: Elements stay visible during camera movements
- **Camera Controls**: MovingCameraScene-compatible API with Frame2DWrapper
  
### 📝 Text Management  
- **UniversalNarrationManager**: Handles text creation with LaTeX validation
- **Transcript Support**: Automatic .txt file generation for accessibility
- **Raw String Handling**: Built-in validation for LaTeX commands

### 🎥 Camera Animation  
- **Frame2DWrapper**: 2D camera movements with 3D scene benefits
- **Animation Chaining**: Method chaining for smooth transitions

## Quick Start  
  
### Installation  
```bash  
pip install blanim  
```  
  
### Basic Usage  
  
```python  
from blanim import *  
  
class MyBlockchainScene(HUD2DScene):  
    def construct(self):  
        # Create Kaspa DAG  
        dag = KaspaDAG(scene=self)  
          
        # Add blocks with automatic animation  
        genesis = dag.add_block()  
        block1 = dag.add_block(parents=[genesis])  
        block2 = dag.add_block(parents=[genesis])  
          
        # Create merge block  
        merge = dag.add_block(parents=[block1, block2])  
          
        # Animate GHOSTDAG process  
        dag.animate_ghostdag_process(merge)  
```  
  
### Network Simulation  
  
Simulate realistic network conditions:  
  
```python  
blocks = dag.simulate_blocks(  
    duration_seconds=20,  # 20 seconds of simulation  
    blocks_per_second=1,  # 1 BPS network rate  
    network_delay_ms=350  # 350ms propagation delay  
)  
dag.create_blocks_from_simulator_list(blocks)  
```  
  
## Architecture  
  
### Core Components  
  
```  
blanim/  
├── core/                    # Base infrastructure  
│   ├── base_config.py       # Configuration interface  
│   ├── base_visual_block.py # Visual rendering base  
│   ├── parent_line.py       # Connection lines  
│   └── hud_2d_scene.py      # Scene with narration support  
└── blockDAGs/               # Blockchain implementations  
    ├── bitcoin/             # Linear chains  
    │   ├── config.py  
    │   ├── logical_block.py  
    │   ├── visual_block.py  
    │   └── chain.py  
    └── kaspa/               # DAG structures  
        ├── config.py  
        ├── logical_block.py  
        ├── visual_block.py  
        ├── dag.py  
        └── ghostdag.py  
```  
  
### Manager Pattern  
  
KaspaDAG uses specialized managers for clean separation of concerns:  
  
- **BlockManager**: Block creation and workflow control  
- **Movement**: Block positioning and camera tracking  
- **Retrieval**: Block lookup with fuzzy matching  
- **RelationshipHighlighter**: Past/future/anticone visualization  
- **GhostDAGHighlighter**: Consensus algorithm animation  
- **BlockSimulator**: Network parameter simulation  
  
## Configuration  
  
### Type-Safe Configuration  
  
Each blockchain type has its own configuration class:  
  
```python  
# Kaspa configuration  [header-1](#header-1)
kaspa_config = KaspaConfig(  
    k=18,                              # GHOSTDAG parameter  
    block_color=WHITE,  
    ghostdag_blue_color=BLUE,  
    ghostdag_red_color=RED,  
    create_run_time=2.0  
)  
  
# Bitcoin configuration    [header-2](#header-2)
bitcoin_config = BitcoinConfig(  
    block_color=ORANGE,  
    create_run_time=1.5  
)  
```  
  
## Testing  
  
Comprehensive test suite with visual validation:  
  
```bash  
# Run Kaspa tests  [header-3](#header-3)
python -m tests.kaspa_tests  
  
# Run Bitcoin tests    [header-4](#header-4)
python -m tests.bitcoin_tests  
```  
  
## Examples  
  
- **Basic DAG Creation**: Simple parent-child relationships  
- **Network Simulation**: Realistic block generation under varying conditions  
- **GHOSTDAG Process**: Step-by-step consensus algorithm visualization  
- **Relationship Highlighting**: Past cone, future cone, and anticone visualization  
  
## Contributing  
  
BLanim follows a modular architecture pattern. When contributing:  
  
1. **Maintain Separation**: Keep logical, visual, and orchestration layers separate  
2. **Use Manager Pattern**: New functionality should follow the delegation pattern  
3. **Add Tests**: Include visual test scenes for new features  
4. **Document**: Update docstrings and architecture documentation  