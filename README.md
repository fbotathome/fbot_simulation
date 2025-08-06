<img width="5315" height="719" alt="fbot_simulation" src="https://github.com/user-attachments/assets/a7a50137-774d-4370-987d-8d12e89bb63a" />

This package provides a simulation environment using ROS 2 and Gazebo.

## Prerequisites
- ROS 2 Humble
- Gazebo simulator

## Installation
1. Clone this repository into your ROS 2 workspace (`src` folder).
2. Install dependencies:
   ```sh
   rosdep install --from-paths src --ignore-src -r -y
   ```
3. Build the workspace:
   ```sh
   colcon build
   ```
4. Source the workspace:
   ```sh
   source install/setup.zsh
   # or
   source install/setup.bash
   ```

## Running the Simulation
To launch the simulation environment, use:
```sh
ros2 launch fbot_simulation gpsr.launch.py
```

This should start Gazebo with the configured world and models.

## Directory Structure
- `launch/`: Launch files for simulation and scenarios
- `models/`: Gazebo models
- `urdf/`: Robot description files
- `config/`: Configuration files
- `worlds/`: Gazebo world files

---
For more details, check the source files and configuration in each directory.
