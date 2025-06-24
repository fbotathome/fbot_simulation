# fbot_simulation
This package provides a simulation environment for the FBOT project using ROS 2 and Gazebo.

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
ros2 launch fbot_simulation simulation.launch.py
```

This will start Gazebo with the configured world and models.

## Additional Launch Files
- `gpsr.launch.py`: Launches the GPSR scenario.
- `world.launch.py`: Launches the world only.

Example:
```sh
ros2 launch fbot_simulation gpsr.launch.py
```

## Directory Structure
- `launch/`: Launch files for simulation and scenarios
- `models/`: Gazebo models
- `urdf/`: Robot description files
- `config/`: Configuration files
- `worlds/`: Gazebo world files

## Testing
To run tests:
```sh
colcon test
```

---
For more details, check the source files and configuration in each directory.
