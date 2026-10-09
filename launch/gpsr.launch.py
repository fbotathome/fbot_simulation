import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node, SetParameter
from launch_ros.descriptions import ParameterValue


def _share_parent(pkg):
    try:
        return str(Path(get_package_share_directory(pkg)).parent.resolve())
    except PackageNotFoundError:
        return None


def generate_launch_description():
    sim_share = get_package_share_directory('fbot_simulation')

    args = [
        DeclareLaunchArgument('world', default_value='arena_env.world',
                              description='World file inside fbot_simulation/worlds'),
        DeclareLaunchArgument('use_navigation', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_moveit', default_value='true'),
        DeclareLaunchArgument('use_agent', default_value='true'),
        DeclareLaunchArgument('spawn_x', default_value='0.0'),
        DeclareLaunchArgument('spawn_y', default_value='1.0'),
        DeclareLaunchArgument('spawn_yaw', default_value='0.0'),
    ]

    resource_paths = [os.path.join(sim_share, 'models')]
    for pkg in ('boris_description', 'shark_description', 'sensors_description',
                'boris_head_description', 'interbotix_xsarm_descriptions'):
        p = _share_parent(pkg)
        if p:
            resource_paths.append(p)
    env = [
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.pathsep.join(resource_paths)),
        AppendEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', os.pathsep.join(resource_paths)),
    ]

    use_sim_time = SetParameter(name='use_sim_time', value=True)

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-r -v4 ', os.path.join(sim_share, 'worlds', ''), LaunchConfiguration('world')],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ',
            os.path.join(get_package_share_directory('boris_description'), 'urdf', 'boris_description.xacro'),
            ' use_sim:=true arm_z_position:=0.23',
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen',
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{'source_list': ['/gz/joint_states'], 'rate': 50}],
        output='log',
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='create_robot',
        arguments=[
            '-name', 'boris',
            '-topic', 'robot_description',
            '-x', LaunchConfiguration('spawn_x'),
            '-y', LaunchConfiguration('spawn_y'),
            '-z', '0.05',
            '-Y', LaunchConfiguration('spawn_yaw'),
        ],
        output='screen',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )
    base_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['hoverboard_base_controller', '--controller-manager', '/controller_manager'],
    )
    arm_controllers_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['interbotix_arm_controller', 'interbotix_gripper_controller',
                   '--controller-manager', '/controller_manager'],
    )
    start_controllers_after_jsb = RegisterEventHandler(
        OnProcessExit(target_action=joint_state_broadcaster_spawner,
                      on_exit=[base_controller_spawner, arm_controllers_spawner]))

    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/scan_ground@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/scan_back@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/wx200/astra2_top_camera/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/wx200/astra2_top_camera/rgb/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/wx200/astra2_wrist_camera/rgb/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/scan_ground', '/scan2'),
            ('/scan_back', '/scan3'),
        ],
        output='screen',
    )
    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=[
            '/wx200/astra2_top_camera/rgb/image_raw',
            '/wx200/astra2_top_camera/depth/image_raw',
            '/wx200/astra2_wrist_camera/rgb/image_raw',
        ],
        output='screen',
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('fbot_navigation'), 'launch', 'navigation_sim.launch.py')),
        launch_arguments={'use_rviz': LaunchConfiguration('use_rviz')}.items(),
        condition=IfCondition(LaunchConfiguration('use_navigation')),
    )

    actions = args + env + [
        use_sim_time,
        gz_sim,
        robot_state_publisher,
        joint_state_publisher,
        spawn_robot,
        joint_state_broadcaster_spawner,
        start_controllers_after_jsb,
        gz_bridge,
        image_bridge,
        navigation,
    ]

    try:
        moveit_share = get_package_share_directory('boris_moveit_config')
        move_group = os.path.join(moveit_share, 'launch', 'move_group.launch.py')
        if os.path.exists(move_group):
            actions.append(IncludeLaunchDescription(
                PythonLaunchDescriptionSource(move_group),
                condition=IfCondition(LaunchConfiguration('use_moveit'))))
    except PackageNotFoundError:
        pass

    try:
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('fbot_agent'), 'launch', 'fbot_agent.launch.py')),
            condition=IfCondition(LaunchConfiguration('use_agent'))))
    except PackageNotFoundError:
        pass

    return LaunchDescription(actions)
