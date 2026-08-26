"""macOS Finder Quick Action / Service registration for SFC2."""
from __future__ import annotations

import os
import plistlib
import shutil
import sys
from pathlib import Path


def default_command_template() -> str:
    """Return command string with $f placeholder."""
    if getattr(sys, "frozen", False):
        executable = str(Path(sys.executable).resolve())
        return f'"{executable}" --convert "$f"'
    
    python_exe = str(Path(sys.executable).resolve())
    project_root = Path(__file__).resolve().parent.parent
    main_script = project_root / "main.py"
    if not main_script.is_file():
        main_script = Path(sys.argv[0]).resolve()
    return f'"{python_exe}" "{main_script}" --convert "$f"'


def register_context_menu(command_template: str | None = None) -> None:
    """Register 'SFC2で変換' as a macOS Finder Quick Action / Service."""
    if sys.platform != "darwin" and os.name != "posix":
        raise OSError("macOS context menu (Quick Actions) is only available on macOS.")

    workflow_dir = _workflow_path()
    contents_dir = workflow_dir / "Contents"
    contents_dir.mkdir(parents=True, exist_ok=True)

    cmd = command_template or default_command_template()
    
    # 1. Generate Info.plist for the workflow bundle
    info_plist_content = {
        "CFBundleName": "SFC2で変換",
        "CFBundleIdentifier": "com.kinakomochi.sfc2.convert-service",
        "CFBundleVersion": "1.0",
        "CFBundlePackageType": "BNDL",
        "CFBundleShortVersionString": "1.0",
        "NSServices": [
            {
                "NSMenuItem": {
                    "default": "SFC2で変換",
                },
                "NSMessage": "runWorkflowAsService",
                "NSPortName": "SFC2で変換",
                "NSSendFileTypes": [
                    "public.item",
                    "public.movie",
                    "public.audio",
                    "public.image",
                    "public.folder",
                ],
            }
        ],
    }

    with open(contents_dir / "Info.plist", "wb") as f:
        plistlib.dump(info_plist_content, f)

    # 2. Generate document.wflow XML containing a Run Shell Script action
    shell_script = f'''for f in "$@"; do
    {cmd}
done'''

    # XML escape helper
    escaped_script = (
        shell_script.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    wflow_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>523</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>AMAccepts</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Optional</key>
					<true/>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.path</string>
					</array>
				</dict>
				<key>AMActionVersion</key>
				<string>2.0.3</string>
				<key>AMParameterProperties</key>
				<dict>
					<key>COMMAND_STRING</key>
					<dict/>
					<key>inputMethod</key>
					<dict/>
				</dict>
				<key>AMProvides</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.path</string>
					</array>
				</dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>シェルスクリプトを実行</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>{escaped_script}</string>
					<key>inputMethod</key>
					<integer>1</integer>
					<key>shell</key>
					<string>/bin/zsh</string>
					<key>source</key>
					<string></string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.RunShellScript</string>
				<key>CFBundleVersion</key>
				<string>2.0.3</string>
				<key>CanShowSelectedItemsWhenRun</key>
				<false/>
				<key>CanShowWhenRun</key>
				<true/>
				<key>Category</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
					<string>Command</string>
					<string>Run</string>
					<string>Unix</string>
				</array>
				<key>OutputUUID</key>
				<string>00000000-0000-0000-0000-000000000001</string>
				<key>UUID</key>
				<string>00000000-0000-0000-0000-000000000002</string>
			</dict>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
"""
    with open(contents_dir / "document.wflow", "w", encoding="utf-8") as f:
        f.write(wflow_content)


def unregister_context_menu() -> None:
    """Remove the 'SFC2で変換' Quick Action workflow from ~/Library/Services."""
    workflow_dir = _workflow_path()
    if workflow_dir.exists():
        shutil.rmtree(workflow_dir, ignore_errors=True)
