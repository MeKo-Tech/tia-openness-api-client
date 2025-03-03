#!/usr/bin/env python3
"""
Example script to read all PLC blocks from a TIA Portal project.
This script works exclusively with already open TIA Portal instances.
It automatically handles Windows and WSL environments without any user configuration.
"""

import os
import sys
import argparse
import subprocess
import platform

# Check if running in WSL before importing TIA Portal
IS_WSL = False
try:
    if platform.system() == "Linux":
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                IS_WSL = True
except:
    pass

# Print warning if running in WSL
if IS_WSL:
    print("\n" + "=" * 80)
    print("WARNING: Running in WSL environment")
    print("Connecting to TIA Portal from WSL has limitations.")
    print(
        "If you encounter issues, consider running the script from Windows Python instead."
    )
    print("=" * 80 + "\n")

try:
    import tia_portal.config as tia_config
    from tia_portal import Client, Project
    from tia_portal.version import TiaVersion

    # Import TIA Portal libraries - will be available after importing tia_portal
    import Siemens.Engineering as tia  # type: ignore
except ImportError as e:
    print(f"Error importing TIA Portal libraries: {e}")
    if IS_WSL:
        print("\nWhen running in WSL, make sure:")
        print("1. TIA Portal is installed on Windows")
        print("2. The path to TIA Portal is accessible from WSL")
        print("3. You've installed the Python dependencies: pythonnet")
        print(
            "\nConsider running the script directly from Windows Python for better compatibility."
        )
    sys.exit(1)


def get_active_tia_portal_instances():
    """
    Get all active TIA Portal instances.

    Returns:
        list: List of TiaPortalProcess objects representing running TIA Portal instances
    """
    try:
        # Get all running TIA Portal processes
        tia_processes = tia.TiaPortal.GetProcesses()

        if not tia_processes or len(tia_processes) == 0:
            print("No running TIA Portal instances found.")
            print(
                "Please start TIA Portal and open a project before running this script."
            )
            return []

        return tia_processes
    except Exception as e:
        print(f"Error getting TIA Portal processes: {e}")
        if IS_WSL:
            print("\nIn WSL environments, connecting to running TIA Portal instances")
            print(
                "can be challenging due to Windows/Linux interoperability limitations."
            )
            print("Consider running this script directly from Windows Python.")
        return []


def main():
    """Main function to extract all blocks from a TIA Portal project using an open TIA Portal instance."""
    parser = argparse.ArgumentParser(
        description="Read PLC blocks from a project in an already open TIA Portal instance"
    )
    parser.add_argument(
        "--version",
        type=str,
        choices=["V15", "V15_1", "V16", "V17", "V18", "V19"],
        help="TIA Portal version (optional)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        tia_config.load()

        # Set version if specified
        if args.version:
            print(f"Setting TIA Portal version to {args.version}")
            tia_config.set_version(TiaVersion[args.version])
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    print(f"\nEnvironment information:")
    print(f"  - TIA Portal version: {tia_config.VERSION.name}")
    print(f"  - Running in WSL: {'Yes' if tia_config.IS_WSL else 'No'}")

    # Get active TIA Portal instances
    tia_processes = get_active_tia_portal_instances()
    if not tia_processes:
        sys.exit(1)

    # Create client and process blocks
    try:
        # Connect to existing TIA Portal instance
        print(f"\nFound {len(tia_processes)} running TIA Portal instances")

        # If multiple instances, let user choose one
        if len(tia_processes) > 1:
            print("\nSelect TIA Portal instance to connect to:")
            for i, process in enumerate(tia_processes):
                project_info = ""
                if process.ProjectPath:
                    project_info = (
                        f"(Project: {os.path.basename(str(process.ProjectPath))})"
                    )
                print(f"  {i+1}. Process ID: {process.Id} {project_info}")

            selection = int(
                input("\nEnter number (1-" + str(len(tia_processes)) + "): ")
            )
            if selection < 1 or selection > len(tia_processes):
                print("Invalid selection")
                sys.exit(1)

            selected_process = tia_processes[selection - 1]
        else:
            selected_process = tia_processes[0]

        print(f"\nConnecting to TIA Portal process (ID: {selected_process.Id})")

        # Create TIA Portal client by attaching to the existing process
        try:
            tia_portal = selected_process.Attach()
            print("Successfully attached to TIA Portal instance")
        except Exception as e:
            print(f"Error attaching to TIA Portal: {e}")
            if tia_config.IS_WSL:
                print("\nAttaching to TIA Portal from WSL has limitations.")
                print(
                    "This is likely due to interoperability issues between Windows and Linux."
                )
                print("Consider running this script directly from Windows Python.")
            sys.exit(1)

        # Create custom client and assign the session
        tia_client = Client()
        tia_client.session = tia_portal

        # Check if there's an open project
        if not selected_process.ProjectPath:
            print("No open project found in the TIA Portal instance.")
            print("Please open a project in TIA Portal and run this script again.")
            sys.exit(1)

        # Get information about the open project
        project_file_path = str(selected_process.ProjectPath)
        print(f"Found open project: {project_file_path}")

        # Get the currently open project
        current_project = tia_portal.Projects[0]

        # Extract project directory and name from the file path
        project_dir = os.path.dirname(os.path.dirname(project_file_path))
        project_name = os.path.basename(os.path.dirname(project_file_path))

        # Create the project object and assign the TIA project value
        project = Project(tia_client, project_dir, project_name)
        project.value = current_project
        tia_client.project = project

        print(f"Connected to project: {project_name}")

        # Get all PLCs
        plcs = tia_client.project.get_plcs()
        print(f"Found {len(plcs)} PLCs in the project")

        if len(plcs) == 0:
            print("No PLCs found in project")
            sys.exit(0)

        # Process each PLC
        for plc in plcs:
            print(f"\nProcessing PLC: {plc.name}")

            # Get software
            software = plc.get_software()

            # Get all blocks
            print("Retrieving all blocks (including those in subfolders)...")
            software_blocks = software.get_all_blocks(True)
            print(f"Found {len(software_blocks)} blocks")

            # Compile project to ensure blocks are accessible
            print("Compiling project...")
            tia_client.project.compile()
            print("Compilation complete")

            # Export each block
            print("\nExporting blocks:")
            export_path = None
            successful_exports = 0

            for i, block in enumerate(software_blocks, 1):
                block_name = getattr(block, "name", f"Block_{i}")
                print(
                    f"[{i}/{len(software_blocks)}] Exporting {block_name}...",
                    end="\r",
                )
                try:
                    export_path = block.export()
                    successful_exports += 1
                except Exception as e:
                    print(f"\nError exporting {block_name}: {e}")
                    continue

            if export_path:
                export_dir = os.path.dirname(export_path)
                print(
                    f"\n\nExported {successful_exports} of {len(software_blocks)} blocks"
                )
                print(f"Export directory: {export_dir}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.debug:
            import traceback

            traceback.print_exc()
    finally:
        print("\nLeaving TIA Portal instance running")


if __name__ == "__main__":
    main()
