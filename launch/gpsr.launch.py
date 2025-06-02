import os
import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, SetEnvironmentVariable
from launch.event_handlers import OnProcessExit
import launch.launch_description_sources
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import EnvironmentVariable
from ament_index_python.packages import get_package_share_directory
from pathlib import Path
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch_ros.descriptions import ParameterValue, ParameterFile

from ament_index_python.packages import get_package_share_directory
from interbotix_xs_modules.xs_common import (
    get_interbotix_xsarm_models,
)
from interbotix_xs_modules.xs_launch import (
    construct_interbotix_xsarm_semantic_robot_description_command,
    declare_interbotix_xsarm_robot_description_launch_arguments,
    determine_use_sim_time_param,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition, LaunchConfigurationEquals
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
    TextSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import yaml
from interbotix_xs_modules.xs_common import (
    get_interbotix_xsarm_models,
)


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def generate_launch_description():
    # Set ignition resource path
    '''ign_gz_resource_path_env_var = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=[
            EnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', default_value=''),
            '/home/fbot/.gazebo/models/',
            str(Path(get_package_share_directory('boris_description')).parent.resolve()),
            str(Path(get_package_share_directory('hector_models')).parent.resolve()),
            str(os.path.join(get_package_share_directory('fbot_simulation'), 'models')),
            str(Path(get_package_share_directory('interbotix_xsarm_descriptions')).parent.resolve())
        ]
    )'''
    ign_package = get_package_share_directory('ros_gz_sim')
    ign_sim = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(ign_package, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': "-r -v4 " + str(os.path.join(get_package_share_directory('fbot_simulation'), 'worlds', 'arena_env.world')),
            'on_exit_shutdown': 'true'
        }.items()
    )
    robot_description = ParameterValue(
        Command(['xacro ', str(os.path.join(get_package_share_directory('boris_description'), 'urdf', 'boris_full.xacro'))]), value_type=str
    )
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare('boris_moveit_config'),
            'config',
            'ros2_controllers.yaml',
        ]
    )
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        #namespace='/wx200'
    )
    joint_trajectory_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'interbotix_arm_controller',
            'interbotix_gripper_controller',
            '--param-file',
            robot_controllers,
            ],
        #namespace='/wx200'
    )
    ign_create_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='create_robot',
        arguments=[
            '-param', 'robot_description',
            '-y', '1.0',
            '-z', '0.1'
        ],
        parameters=[{
            'robot_description': robot_description,
        }],
    )
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            #'use_sim_time': True,
        }],
        #namespace='/wx200',
        output={'both': 'screen'},
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        #namespace='/wx200',
        parameters=[{
            #'use_sim_time': True,
        }],
        output={'both': 'log'},
    )
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ign_bridge',
        arguments=[
            #"/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock"
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            "/hoverboard_base_controller/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            "/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan",
            "/back/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan",
            "/ground/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan",
            "/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V",
            "/wx200/astra2_top_camera/depth/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
            "/wx200/astra2_top_camera/rgb/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
            "/wx200/astra2_wrist_camera/rgb/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
        ],
        output="screen"
    )
    image_gz_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=[
            '/wx200/astra2_top_camera/rgb/image_raw',
            '/wx200/astra2_top_camera/depth/image_raw',
            '/wx200/astra2_wrist_camera/rgb/image_raw',
        ],
        output='screen',
    )
    '''navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')),
        launch_arguments={
            'use_sim_time': 'true',
            'autostart': 'True',
            'map': os.path.join(get_package_share_directory('fbot_navigation'), 'maps', 'arena_env.yaml'),
            'params_file': os.path.join(get_package_share_directory('fbot_navigation'), 'param', 'tb3_nav2_params_sim.yaml'),
            'slam': 'False',
        }.items()
    )'''
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('fbot_navigation'), 'launch', 'navigation.launch.py')),
        launch_arguments={
        }.items()
    )
    scan_relay = Node(
        package='topic_tools',
        executable='relay',
        name='relay_scan',
        arguments=[
            '/lms1xx/scan', '/scan'
        ]
    )
    moveit = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            launch_file_path=os.path.join(get_package_share_directory('boris_moveit_config'), 'launch', 'demo.launch.py')
        )
    )
    agent = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            launch_file_path=os.path.join(get_package_share_directory('fbot_agent'), 'launch', 'fbot_agent.launch.py')
        )
    )
    return LaunchDescription([
        #ign_gz_resource_path_env_var,
        ign_sim,
        ign_create_robot,
        robot_state_publisher_node,
        joint_state_publisher_node,
        joint_state_broadcaster_spawner,
        joint_trajectory_controller_spawner, 
        gz_bridge,
        image_gz_bridge,
        navigation,
        scan_relay,
        #static_transform,
        #move_group_node,
        #rviz,
        moveit,
        agent,
    ])