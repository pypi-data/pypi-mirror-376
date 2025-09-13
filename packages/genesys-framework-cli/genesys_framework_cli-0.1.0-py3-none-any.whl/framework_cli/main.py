import os
import click
import subprocess
import sys
import re
import shutil
import sysconfig

@click.group()
def cli():
    """Genesys CLI for ROS 2 workspace management."""
    pass

def _get_sourcing_command(exit_on_error=True, clean_env=False):
    """
    Returns the platform-specific command to source the ROS 2 and local workspace environments.

    :param clean_env: If True, unsets common ROS environment variables for a clean build.
    """
    ros_distro = os.environ.get('ROS_DISTRO')
    if not ros_distro:
        if exit_on_error:
            click.secho("Error: ROS_DISTRO environment variable not set.", fg="red")
            click.secho("Cannot find ROS 2 installation to source.", fg="yellow")
            sys.exit(1)
        return None, None

    # Platform-specific setup
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        shell_exec = '/bin/bash'
        distro_setup_script = f"/opt/ros/{ros_distro}/setup.bash"
        ws_setup_script = "./install/setup.bash" # Relative to workspace root
        
        if not os.path.exists(distro_setup_script):
            if exit_on_error:
                click.secho(f"Error: ROS 2 setup script not found at {distro_setup_script}", fg="red")
                sys.exit(1)
            return None, None
            
        # Chain the sourcing commands
        command_parts = []
        if clean_env:
            # These are the most common variables that cause cross-workspace contamination.
            command_parts.extend(["unset AMENT_PREFIX_PATH", "unset COLCON_PREFIX_PATH"])

        command_parts.append(f"source {distro_setup_script}")
        if os.path.exists(ws_setup_script):
            command_parts.append(f"source {ws_setup_script}")
            
        source_prefix = " && ".join(command_parts) + " && "
        return source_prefix, shell_exec
    
    elif sys.platform == 'win32':
        click.secho("Warning: Auto-sourcing on Windows is not fully implemented. Please run this from a sourced ROS 2 terminal.", fg="yellow", err=True)
        return "", None # No prefix command, use default shell
    
    else:
        click.secho(f"Unsupported platform for auto-sourcing: {sys.platform}", fg="red")
        if exit_on_error:
            sys.exit(1)
        return None, None

@cli.command()
def doctor():
    """Checks the environment for potential issues and provides solutions."""
    click.secho("Running Genesys environment doctor...", fg="cyan", bold=True)
    all_ok = True

    # 1. Check if the user's script installation directory is on the PATH
    click.echo("\nChecking PATH configuration...")
    # Get the directory where pip installs scripts for the current python environment
    scripts_dir = sysconfig.get_path('scripts')

    # Check if this directory is in the system's PATH environment variable
    if scripts_dir not in os.environ.get('PATH', '').split(os.pathsep):
        all_ok = False
        click.secho("[X] PATH Issue Detected", fg="red")
        click.echo(f"  Your local scripts directory ('{scripts_dir}') is not on your system's PATH.")
        click.echo("  This can prevent you from running 'genesys' directly after installation.")

        # Provide platform-specific instructions
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            click.echo("\n  To fix this for your current session, run:")
            click.secho(f'  export PATH="{scripts_dir}:$PATH"', fg="yellow")
            click.echo("\n  To fix this permanently, copy and paste the following command:")
            # Detect shell to suggest the correct rc file (~/.bashrc, ~/.zshrc, etc.)
            shell = os.environ.get("SHELL", "")
            rc_file = ""
            if "zsh" in shell:
                rc_file = "~/.zshrc"
            elif "bash" in shell:
                rc_file = "~/.bashrc"
            else:
                # A safe fallback for other shells
                rc_file = "your shell's startup file (e.g., ~/.bashrc, ~/.zshrc)"

            click.secho(f"  echo 'export PATH=\"{scripts_dir}:$PATH\"' >> {rc_file}", fg="green")
            click.echo(f"  After running the command, please start a new terminal session for the change to take effect.")
        elif sys.platform == 'win32':
            click.echo("\n  To fix this, you need to add the following directory to your 'Path' environment variable:")
            click.secho(f"  {scripts_dir}", fg="yellow")
            click.echo("  You can do this through 'Edit the system environment variables' in the Control Panel.")
    else:
        click.secho("[✓] PATH configuration is correct.", fg="green")

    click.echo("\nChecking ROS 2 environment...")
    source_prefix, _ = _get_sourcing_command(exit_on_error=False)
    if source_prefix is None:
        all_ok = False
        click.secho("[X] ROS 2 Environment Issue Detected", fg="red")
        click.echo("  The ROS_DISTRO environment variable is not set or the setup script is missing.")
        click.echo("  Please ensure a ROS 2 distribution is installed and the ROS_DISTRO variable is set.")
    else:
        click.secho("[✓] ROS 2 environment sourcing is configured.", fg="green")

    click.echo("-" * 40)
    if all_ok:
        click.secho("✨ Your Genesys environment is ready to go!", fg="cyan", bold=True)
    else:
        click.secho("Please address the issues above to ensure Genesys works correctly.", fg="yellow")

@cli.command()
@click.argument('project_name')
def new(project_name):
    """Creates a new ROS 2 workspace with the Genesys framework structure."""
    
    workspace_root = project_name
    click.echo(f"Creating new Genesys project at: ./{workspace_root}")

    if os.path.exists(workspace_root):
        click.secho(f"Error: Directory '{workspace_root}' already exists.", fg="red")
        return

    # Define the structure from the "Workspace Structure" reference
    subdirs = [
        "src",
        "launch",
        "config",
        "sim/worlds",
        "sim/models",
        "tests",
        "scripts",
        "tools"
    ]

    try:
        os.makedirs(workspace_root)
        for subdir in subdirs:
            os.makedirs(os.path.join(workspace_root, subdir))
        click.secho(f"✓ Project '{project_name}' created successfully.", fg="green")
        click.echo("Next steps: 'cd {}' and start creating packages!".format(project_name))
    except Exception as e:
        click.secho(f"Failed to create project: {e}", fg="red")

@cli.command()
@click.option('--packages', '-p', multiple=True, help='Specific packages to build. Builds all if not specified.')
def build(packages):
    """Builds the entire workspace or specific packages."""
    # 1. Verify we are in a Genesys workspace root.
    if not os.path.isdir('src'):
        click.secho("Error: This command must be run from the root of a Genesys workspace.", fg="red")
        click.secho("(A 'src' directory was not found.)", fg="yellow")
        sys.exit(1)

    click.echo("Building the workspace...")

    source_prefix, shell_exec = _get_sourcing_command(clean_env=True)
    colcon_command = ['colcon', 'build', '--symlink-install']
    if packages:
        colcon_command.extend(['--packages-select'] + list(packages))

    command_to_run = source_prefix + ' '.join(colcon_command)

    click.echo(f"Running build command...")

    try:
        # Use Popen to stream output in real-time, which is better for build commands.
        process = subprocess.Popen(
            command_to_run,
            shell=True,
            executable=shell_exec,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.wait() # Wait for the build to finish
        
        if process.returncode == 0:
            click.secho("\n✓ Build completed successfully.", fg="green")
            click.echo("To use the new executables, you may need to source the workspace or start a new terminal.")
        else:
            raise subprocess.CalledProcessError(process.returncode, command_to_run)

    except subprocess.CalledProcessError as e:
        click.secho(f"\nBuild failed with exit code {e.returncode}.", fg="red")
        sys.exit(1)

def _add_python_entry_point(pkg_name, node_name):
    """Adds a new console_script entry to a package's setup.py file."""
    setup_file = os.path.join('src', pkg_name, 'setup.py')
    node_module_name = node_name.replace('.py', '')

    with open(setup_file, 'r') as f:
        content = f.read()

    # Use re.DOTALL to match newlines. Use named groups for clarity.
    match = re.search(
        r"(?P<pre>('|\")console_scripts('|\")\s*:\s*\[)(?P<scripts>[^\]]*)(?P<post>\])",
        content,
        re.DOTALL
    )

    if not match:
        click.secho(f"Error: Could not find 'console_scripts' in {setup_file}.", fg="red")
        return

    scripts_content = match.group('scripts')

    # Check if node is already registered
    if f"'{node_name} =" in scripts_content or f'"{node_name} =' in scripts_content:
        click.secho(f"Node '{node_name}' already exists in {setup_file}.", fg="yellow")
        return

    new_entry = f"'{node_name} = {pkg_name}.{node_module_name}:main'"

    # Find the last non-empty line in the scripts block
    lines = [line for line in scripts_content.split('\n') if line.strip()]

    if lines:
        # The list has existing entries.
        last_line = lines[-1]
        indentation = " " * (len(last_line) - len(last_line.lstrip()))
        text_to_insert = ""
        if not last_line.strip().endswith(','):
            text_to_insert += ","
        text_to_insert += f"\n{indentation}{new_entry}"
        updated_content = content.replace(last_line, last_line + text_to_insert)
    else:
        # The list is empty.
        pre_match_line_start = content.rfind('\n', 0, match.start('scripts')) + 1
        indentation = " " * (match.start('scripts') - pre_match_line_start) + "    "
        insertion = f"\n{indentation}{new_entry}\n"
        insertion_point = match.end('scripts')
        updated_content = content[:insertion_point] + insertion + content[insertion_point:]

    with open(setup_file, 'w') as f:
        f.write(updated_content)
    
    click.secho(f"✓ Registered '{node_name}' in {setup_file}", fg="green")

def _add_install_rule_for_launch_dir(pkg_name):
    """Adds the install rule for the launch directory to setup.py."""
    setup_file = os.path.join('src', pkg_name, 'setup.py')
    if not os.path.exists(setup_file):
        return  # Not a python package

    with open(setup_file, 'r') as f:
        content = f.read()

    # Check if the rule already exists to avoid duplicates
    if "glob(os.path.join('launch'" in content:
        return

    # Add necessary imports if they are missing
    imports_to_add = []
    if 'import os' not in content:
        imports_to_add.append('import os')
    if 'from glob import glob' not in content:
        imports_to_add.append('from glob import glob')
    
    if imports_to_add:
        content = "\n".join(imports_to_add) + "\n" + content

    # Find the line installing package.xml to insert our rule after it
    package_xml_line = "('share/' + package_name, ['package.xml'])"
    match = re.search(re.escape(package_xml_line), content)
    if not match:
        click.secho(f"Warning: Could not find package.xml install rule in {setup_file}. Cannot add launch install rule.", fg="yellow")
        return
    
    # Determine the indentation from the found line
    line_start = content.rfind('\n', 0, match.start()) + 1
    indentation = " " * (match.start() - line_start)

    # Note the comma at the beginning to correctly extend the list
    new_rule = f",\n{indentation}(os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.py')))"
    
    # Insert the new rule right after the package.xml line
    insertion_point = match.end()
    updated_content = content[:insertion_point] + new_rule + content[insertion_point:]

    with open(setup_file, 'w') as f:
        f.write(updated_content)
    
    click.secho(f"✓ Added launch directory install rule to {setup_file}", fg="green")

def _add_cpp_executable(pkg_name, node_name):
    """Adds a new executable and install rule to a package's CMakeLists.txt."""
    cmake_file = os.path.join('src', pkg_name, 'CMakeLists.txt')
    node_src_file = f"src/{node_name}.cpp"

    with open(cmake_file, 'r') as f:
        content = f.read()

    if f'add_executable({node_name}' in content:
        click.secho(f"Node '{node_name}' already appears to be registered in {cmake_file}.", fg="yellow")
        return

    # Find the ament_package() call to insert before it
    ament_package_call = re.search(r"ament_package\(\)", content)
    if not ament_package_call:
        click.secho(f"Error: Could not find ament_package() call in {cmake_file}.", fg="red")
        return

    insert_pos = ament_package_call.start()
    new_cmake_commands = f"""
add_executable({node_name} {node_src_file})
ament_target_dependencies({node_name} rclcpp)

install(TARGETS
  {node_name}
  DESTINATION lib/${{PROJECT_NAME}}
)

"""
    updated_content = content[:insert_pos] + new_cmake_commands + content[insert_pos:]

    with open(cmake_file, 'w') as f:
        f.write(updated_content)
    
    click.secho(f"✓ Registered '{node_name}' in {cmake_file}", fg="green")

def _add_install_rule_for_launch_dir_cpp(pkg_name):
    """Adds the install rule for the launch directory to CMakeLists.txt."""
    cmake_file = os.path.join('src', pkg_name, 'CMakeLists.txt')
    if not os.path.exists(cmake_file):
        return # Not a C++ package

    with open(cmake_file, 'r') as f:
        content = f.read()

    # Check if the rule already exists
    if 'install(DIRECTORY launch' in content:
        return

    # Find the ament_package() call to insert before it
    ament_package_call = re.search(r"ament_package\(\)", content)
    if not ament_package_call:
        click.secho(f"Warning: Could not find ament_package() call in {cmake_file}. Cannot add launch install rule.", fg="yellow")
        return

    insert_pos = ament_package_call.start()
    new_cmake_commands = f"""install(
  DIRECTORY launch
  DESTINATION share/${{PROJECT_NAME}}
)

"""
    updated_content = content[:insert_pos] + new_cmake_commands + content[insert_pos:]

    with open(cmake_file, 'w') as f:
        f.write(updated_content)
    
    click.secho(f"✓ Added launch directory install rule to {cmake_file}", fg="green")

def _add_launch_file_boilerplate(pkg_name, node_name):
    """Auto-generates a boilerplate launch file for a new node."""
    launch_dir = os.path.join('src', pkg_name, 'launch')
    os.makedirs(launch_dir, exist_ok=True)
    launch_file = os.path.join(launch_dir, f"{pkg_name}_launch.py")
    
    # Only create a launch file if it doesn't already exist to avoid overwriting a custom one
    if not os.path.exists(launch_file):
        boilerplate = f"""from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='{pkg_name}',
            executable='{node_name}',
            name='{node_name}',
            output='screen',
            emulate_tty=True
        ),
    ])
"""
        with open(launch_file, 'w') as f:
            f.write(boilerplate)
        click.secho(f"✓ Auto-generated launch file: {launch_file}", fg="green")

def _add_node_to_launch(pkg_name, node_name):
    """Adds a new Node entry into the package's launch file if it exists."""
    launch_file = os.path.join('src', pkg_name, 'launch', f"{pkg_name}_launch.py")
    if not os.path.exists(launch_file):
        return  # no launch file yet (handled in _add_launch_file_boilerplate)

    with open(launch_file, 'r') as f:
        content = f.read()

    # Build the new Node block (with trailing comma!)
    new_node_block = f"""        Node(
            package='{pkg_name}',
            executable='{node_name}',
            name='{node_name}',
            output='screen',
            emulate_tty=True
        ),"""

    if new_node_block in content:
        click.secho(f"Launch file already contains '{node_name}'.", fg="yellow")
        return

    # Regex: insert before the closing ] of LaunchDescription([...])
    updated_content = re.sub(
        r"(\s*)\]\)\s*$",
        f"{new_node_block}\n    ])",
        content,
        flags=re.MULTILINE
    )

    with open(launch_file, 'w') as f:
        f.write(updated_content)

    click.secho(f"✓ Added '{node_name}' to launch file: {launch_file}", fg="green")

def _add_default_launch_file(pkg_name):
    """Auto-generates a default.launch.py that includes the main package launch file."""
    launch_dir = os.path.join('src', pkg_name, 'launch')
    os.makedirs(launch_dir, exist_ok=True)
    default_launch_file = os.path.join(launch_dir, "default.launch.py")
    pkg_specific_launch_file = f"{pkg_name}_launch.py"

    # Don't overwrite if it exists to preserve user customizations
    if os.path.exists(default_launch_file):
        return

    boilerplate = f"""import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    \"\"\"
    This is the default launch file for the '{pkg_name}' package.
    It is launched when running 'framework launch --all'.
    By default, it includes the package-specific launch file.
    \"\"\"
    pkg_specific_launch_file_path = os.path.join(
        get_package_share_directory('{pkg_name}'),
        'launch',
        '{pkg_specific_launch_file}'
    )

    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(pkg_specific_launch_file_path))
    ])
"""
    with open(default_launch_file, 'w') as f:
        f.write(boilerplate)
    click.secho(f"✓ Auto-generated default launch file: {default_launch_file}", fg="green")

@cli.command(name='make:node')
@click.argument('node_name')
@click.option('--pkg', 'pkg_name', required=True, help='The name of the package to add the node to.')
def make_node(node_name, pkg_name):
    """Creates a new node file and registers it in an existing package."""
    pkg_path = os.path.join('src', pkg_name)
    if not os.path.isdir(pkg_path):
        click.secho(f"Error: Package '{pkg_name}' not found at {pkg_path}", fg="red")
        sys.exit(1)

    # Convert node_name (e.g. my_awesome_node) to ClassName (e.g. MyAwesomeNode)
    class_name = "".join(word.capitalize() for word in node_name.split('_'))

    # Determine package type and create node
    if os.path.exists(os.path.join(pkg_path, 'setup.py')):
        # Python package
        node_dir = os.path.join(pkg_path, pkg_name)
        os.makedirs(node_dir, exist_ok=True)
        node_file = os.path.join(node_dir, f"{node_name}.py")
        
        boilerplate = f"""from framework_core.decorators import node, timer, publisher
from framework_core.helpers import spin_node
from std_msgs.msg import String

@node("{node_name}")
class {class_name}:
    \"\"\"
    A simple talker node that publishes a message every second.
    This node is auto-generated by the Genesys framework.
    \"\"\"
    def __init__(self):
        # The logger is automatically injected by the @node decorator.
        self.counter = 0
       

    @timer(period_sec=1.0)
    @publisher(topic="chatter", msg_type=String)
    def publish_message(self):
        \"\"\"
        This method is executed every second by the timer.
        The String object it returns is automatically published to the 'chatter' topic.
        \"\"\"
        msg = String()
        msg.data = f"Hello from Genesys! Message #{{self.counter}}"
        
        self.logger.info(f'Publishing: "{{msg.data}}"')
        self.counter += 1
        
        return msg

def main(args=None):
    \"\"\"The main entry point for the node, using the spin_node helper.\"\"\"
    spin_node({class_name}, args)

if __name__ == '__main__':
    main()
"""
        with open(node_file, 'w') as f:
            f.write(boilerplate)
        click.secho(f"✓ Created Python node file: {node_file}", fg="green")
        _add_python_entry_point(pkg_name, node_name)
        _add_launch_file_boilerplate(pkg_name, node_name)
        _add_node_to_launch(pkg_name, node_name)
        _add_default_launch_file(pkg_name)
        _add_install_rule_for_launch_dir(pkg_name)
    elif os.path.exists(os.path.join(pkg_path, 'CMakeLists.txt')):
        # C++ package
        node_dir = os.path.join(pkg_path, 'src')
        os.makedirs(node_dir, exist_ok=True)
        node_file = os.path.join(node_dir, f"{node_name}.cpp")
        boilerplate = f"""#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include <chrono>
#include <functional>
#include <string>

// This is a standard C++ node. Once Genesys C++ macros are implemented,
// this boilerplate will be updated to use them for a cleaner developer experience.

using namespace std::chrono_literals;

class {class_name} : public rclcpp::Node
{{
public:
    {class_name}()
    : Node("{node_name}"), count_(0)
    {{
        publisher_ = this->create_publisher<std_msgs::msg::String>("chatter", 10);
        timer_ = this->create_timer(
            1s, std::bind(&{class_name}::timer_callback, this));
        RCLCPP_INFO(this->get_logger(), "{class_name} has been constructed.");
    }}

private:
    void timer_callback()
    {{
        auto message = std_msgs::msg::String();
        message.data = "Hello from Genesys C++! #" + std::to_string(count_++);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        publisher_->publish(message);
    }}
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
    size_t count_;
}};

int main(int argc, char * argv[])
{{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<{class_name}>());
    rclcpp::shutdown();
    return 0;
}}
"""
        with open(node_file, 'w') as f:
            f.write(boilerplate)
        click.secho(f"✓ Created C++ node file: {node_file}", fg="green")
        _add_cpp_executable(pkg_name, node_name)
        _add_launch_file_boilerplate(pkg_name, node_name)
        _add_node_to_launch(pkg_name, node_name)
        _add_install_rule_for_launch_dir_cpp(pkg_name)
        _add_default_launch_file(pkg_name)
    else:
        click.secho(f"Error: Could not determine package type for '{pkg_name}'. No setup.py or CMakeLists.txt found.", fg="red")
        sys.exit(1)

    click.echo("\nRun 'genesys build' to make the new node available.")

@cli.command(name='make:pkg')
@click.argument('package_name')
@click.option('--with-node', is_flag=True, help='Create an initial node for the package.')
@click.option('--dependencies', '-d', multiple=True, help='ROS 2 package dependencies.')
@click.pass_context
def make_pkg(ctx, package_name, with_node, dependencies):
    """Creates a new ROS 2 package inside the src/ directory."""

    # Verify workspace root
    if not os.path.isdir('src'):
        click.secho("Error: This command must be run from the root of a Genesys workspace.", fg="red")
        click.secho("(A 'src' directory was not found.)", fg="yellow")
        sys.exit(1)

    click.echo(f"Creating new ROS 2 package: {package_name}")

    # Interactive prompt for language choice
    lang_choice = click.prompt(
        'Choose a language for the package',
        type=click.Choice(['Python', 'C++'], case_sensitive=False),
        default='Python',
        show_default=True
    )
    build_type = 'ament_python' if lang_choice.lower() == 'python' else 'ament_cmake'

    command = [
        'ros2', 'pkg', 'create',
        '--build-type', build_type,
        '--destination-directory', 'src',
        package_name
    ]
    
    if dependencies:
        command.extend(['--dependencies'] + list(dependencies))

    source_prefix, shell_exec = _get_sourcing_command(clean_env=True)
    command_to_run = source_prefix + ' '.join(command)

    try:
        subprocess.run(
            command_to_run,
            check=True,
            capture_output=True,
            text=True,
            shell=True,
            executable=shell_exec
        )
        click.secho(f"✓ Package '{package_name}' created successfully in 'src/'.", fg="green")
    except subprocess.CalledProcessError as e:
        click.secho(f"Error creating package '{package_name}':", fg="red")
        click.echo(e.stderr or e.stdout)
        sys.exit(1)

    if with_node:
        ctx.invoke(make_node, node_name=f"{package_name}_node", pkg_name=package_name)

@cli.command()
@click.argument('launch_target', required=False)
@click.option('--all', 'launch_all', is_flag=True, help='Launch the default.launch.py from all packages.')
@click.pass_context
def launch(ctx, launch_target, launch_all):
    """
    Launches ROS 2 nodes.

    Can be used in several ways:\n
    - genesys launch --all (launches default.launch.py from all packages)\n
    - genesys launch <pkg_name>:<launch_file.py>\n
    - genesys launch <pkg_name> (launches <pkg_name>_launch.py by default)
    """
    if launch_all and launch_target:
        click.secho("Error: Cannot use --all with a specific launch target.", fg="red")
        sys.exit(1)
    
    if not launch_all and not launch_target:
        click.secho("Error: Must provide a launch target or use the --all flag.", fg="red")
        click.echo(ctx.get_help())
        sys.exit(1)

    # Verify we are in a workspace that has been built.
    if not os.path.isdir('install'):
        click.secho("Error: 'install' directory not found. Have you built the workspace yet?", fg="red")
        click.secho("Try running 'genesys build' first.", fg="yellow")
        sys.exit(1)

    source_prefix, shell_exec = _get_sourcing_command(clean_env=True)

    if launch_all:
        click.echo("Searching for 'default.launch.py' in all packages...")
        
        src_dir = 'src'
        if not os.path.isdir(src_dir):
            click.secho("Error: 'src' directory not found. This command must be run from the workspace root.", fg="red")
            sys.exit(1)

        packages = [d for d in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, d))]
        
        default_launches = []
        for pkg in packages:
            default_launch_file_src = os.path.join(src_dir, pkg, 'launch', 'default.launch.py')
            if os.path.exists(default_launch_file_src):
                default_launches.append((pkg, 'default.launch.py'))
        
        if not default_launches:
            click.secho("No 'default.launch.py' files found in any package.", fg="yellow")
            return

        click.echo("Found default launch files in:")
        for pkg, _ in default_launches:
            click.echo(f"  - {pkg}")

        # Generate a master launch file
        import tempfile
        
        launch_includes = []
        for pkg, launch_file in default_launches:
            launch_includes.append(
                f"        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('{pkg}'), 'launch', '{launch_file}'))),"
            )
        
        launch_content_parts = [
            "import os",
            "from ament_index_python.packages import get_package_share_directory",
            "from launch import LaunchDescription",
            "from launch.actions import IncludeLaunchDescription",
            "from launch.launch_description_sources import PythonLaunchDescriptionSource",
            "",
            "def generate_launch_description():",
            "    return LaunchDescription([",
            *launch_includes,
            "    ])"
        ]
        launch_content = "\n".join(launch_content_parts)

        temp_launch_file = None
        process = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_all_launch.py') as f:
                temp_launch_file = f.name
                f.write(launch_content)
            
            command_to_run = source_prefix + f"ros2 launch {temp_launch_file}"
            click.echo(f"\nExecuting master launch file: {os.path.basename(temp_launch_file)}")
            process = subprocess.Popen(command_to_run, shell=True, executable=shell_exec)
            process.wait()
        except KeyboardInterrupt:
            click.echo("\nLaunch interrupted by user.")
            if process and process.poll() is None:
                process.terminate()
        except Exception as e:
            click.secho(f"An error occurred during launch: {e}", fg="red")
        finally:
            if temp_launch_file and os.path.exists(temp_launch_file):
                os.remove(temp_launch_file)

    else: # launch_target is provided
        if ':' in launch_target:
            pkg_name, launch_file = launch_target.split(':', 1)
        else:
            pkg_name = launch_target
            launch_file = f"{pkg_name}_launch.py"
            click.echo(f"No launch file specified, defaulting to '{launch_file}'")

        launch_command = f"ros2 launch {pkg_name} {launch_file}"
        command_to_run = source_prefix + launch_command

        click.echo(f"Executing: {launch_command}")

        try:
            process = subprocess.Popen(command_to_run, shell=True, executable=shell_exec)
            process.wait()
        except KeyboardInterrupt:
            click.echo("\nLaunch interrupted by user.")
            if process and process.poll() is None:
                process.terminate()
        except Exception as e:
            click.secho(f"An error occurred during launch: {e}", fg="red")

@cli.command()
@click.argument('node_name')
def run(node_name):
    """Runs a ROS 2 node by its executable name, automatically finding the package."""
    # 1. Verify we are in a workspace that has been built.
    if not os.path.isdir('install'):
        click.secho("Error: 'install' directory not found. Have you built the workspace yet?", fg="red")
        click.secho("Try running 'genesys build' first.", fg="yellow")
        sys.exit(1)

    click.echo(f"Attempting to run node: {node_name}")

    # 2. Get the sourcing command, which now includes the local install space.
    source_prefix, shell_exec = _get_sourcing_command(clean_env=True)
    
    # 3. Find the package for the given node by listing all executables.
    list_exec_command = source_prefix + "ros2 pkg executables"
    try:
        result = subprocess.run(
            list_exec_command,
            check=True, capture_output=True, text=True, shell=True, executable=shell_exec
        )
    except subprocess.CalledProcessError as e:
        click.secho("Error: Failed to list ROS 2 executables.", fg="red")
        click.echo(e.stderr or e.stdout)
        sys.exit(1)

    # 4. Parse the output to find the package name.
    package_name = None
    available_nodes = []
    for line in result.stdout.strip().split('\n'):
        parts = line.split()
        if len(parts) < 2:
            continue
        pkg = parts[0]
        nodes = parts[1:]
        available_nodes.extend(nodes)
        if node_name in nodes:
            package_name = pkg
            break

    
    if not package_name:
        click.secho(f"Error: Node '{node_name}' not found in any package.", fg="red")
        click.echo("Please ensure you have built your workspace and the node name is correct.")
        if available_nodes:
            click.echo("\nAvailable nodes are:")
            for node in sorted(available_nodes):
                click.echo(f"  - {node}")
        sys.exit(1)

    click.echo(f"Found node '{node_name}' in package '{package_name}'. Starting node...")

    # 5. Construct and run the final command.
    run_command = f"ros2 run {package_name} {node_name}"
    command_to_run = source_prefix + run_command

    try:
        # Use Popen to stream output and allow user to Ctrl+C the node.
        process = subprocess.Popen(command_to_run, shell=True, executable=shell_exec)
        process.wait()
    except KeyboardInterrupt:
        click.echo("\nNode execution interrupted by user.")
        process.terminate()

@cli.command()
@click.argument('world_file')
def sim(world_file):
    """Launches a simulation with a specified world file and robot model."""
    # 1. Verify workspace state
    if not os.path.isdir('install'):
        click.secho("Error: 'install' directory not found. Have you built the workspace yet?", fg="red")
        click.secho("Try running 'genesys build' first.", fg="yellow")
        sys.exit(1)

    sim_worlds_dir = 'sim/worlds'
    if not os.path.isdir(sim_worlds_dir):
        click.secho(f"Error: Simulation worlds directory not found at './{sim_worlds_dir}'", fg="red")
        click.secho("Ensure your project was created with 'genesys new'.", fg="yellow")
        sys.exit(1)

    world_path = os.path.join(sim_worlds_dir, world_file)
    if not os.path.exists(world_path):
        click.secho(f"Error: World file not found: {world_path}", fg="red")
        sys.exit(1)

    # 2. Find robot model in sim/models
    sim_models_dir = 'sim/models'
    robot_model_path = None
    if os.path.isdir(sim_models_dir):
        for file in os.listdir(sim_models_dir):
            if file.endswith(('.urdf', '.sdf')):
                robot_model_path = os.path.join(sim_models_dir, file)
                click.echo(f"Found robot model: {robot_model_path}")
                break

    if not robot_model_path:
        click.secho("Warning: No robot model (.urdf or .sdf) found in 'sim/models/'.", fg="yellow")
        click.secho("Gazebo will be launched without a robot.", fg="yellow")

    # 3. Generate temporary launch file
    import tempfile
    workspace_root_abs = os.getcwd()
    world_path_abs = os.path.join(workspace_root_abs, world_path)

    robot_model_path_abs = None
    if robot_model_path:
        robot_model_path_abs = os.path.join(workspace_root_abs, robot_model_path)

    launch_content_parts = [
        "import os",
        "from ament_index_python.packages import get_package_share_directory",
        "from launch import LaunchDescription",
        "from launch.actions import IncludeLaunchDescription",
        "from launch.launch_description_sources import PythonLaunchDescriptionSource",
        "from launch_ros.actions import Node",
        "",
        "def generate_launch_description():",
        "    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')",
        f"    world_path = '{world_path_abs}'",
        "    gzserver_cmd = IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')), launch_arguments={'world': world_path, 'verbose': 'true'}.items())",
        "    gzclient_cmd = IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')))",
        "    ld = LaunchDescription([gzserver_cmd, gzclient_cmd])",
    ]

    if robot_model_path_abs:
        robot_name = os.path.splitext(os.path.basename(robot_model_path_abs))[0]
        launch_content_parts.extend([
            f"    with open('{robot_model_path_abs}', 'r') as infp:",
            "        robot_desc = infp.read()",
            "    robot_state_publisher_node = Node(package='robot_state_publisher', executable='robot_state_publisher', output='screen', parameters=[{'robot_description': robot_desc, 'use_sim_time': True}])",
            f"    spawn_entity_node = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', '{robot_name}', '-topic', 'robot_description'], output='screen')",
            "    ld.add_action(robot_state_publisher_node)",
            "    ld.add_action(spawn_entity_node)",
        ])

    launch_content_parts.append("    return ld")
    launch_content = "\n".join(launch_content_parts)

    temp_launch_file = None
    process = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_sim_launch.py') as f:
            temp_launch_file = f.name
            f.write(launch_content)
        source_prefix, shell_exec = _get_sourcing_command(clean_env=True)
        command_to_run = source_prefix + f"ros2 launch {temp_launch_file}"
        click.echo(f"Executing: ros2 launch {os.path.basename(temp_launch_file)}")
        process = subprocess.Popen(command_to_run, shell=True, executable=shell_exec)
        click.secho("\n✓ Simulation is starting...", fg="cyan")
        if robot_model_path:
            click.echo("  Run your robot's control and logic nodes in a separate, sourced terminal (e.g., 'genesys launch <pkg_name>').")
        process.wait()
    except KeyboardInterrupt:
        click.echo("\nSimulation interrupted by user.")
        if process and process.poll() is None:
            process.terminate()
    except Exception as e:
        click.secho(f"An error occurred during simulation launch: {e}", fg="red")
    finally:
        if temp_launch_file and os.path.exists(temp_launch_file):
            os.remove(temp_launch_file)

if __name__ == '__main__':
    cli()
