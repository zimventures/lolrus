"""
Main lolrus application using DearPyGui.
"""

import os
import sys
from collections.abc import Callable
from datetime import datetime

import dearpygui.dearpygui as dpg
import humanize

# Windows-only drag and drop support
if sys.platform == "win32":
    try:
        import DearPyGui_DragAndDrop as dpg_dnd
        HAS_DND = True
    except ImportError:
        HAS_DND = False
else:
    HAS_DND = False

from lolrus import __version__
from lolrus.connections import COMMON_ENDPOINTS, Connection, ConnectionManager
from lolrus.s3_client import AsyncOperation, OperationStatus, S3Client, S3Object


class LolrusApp:
    """Main application class for lolrus S3 browser."""

    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800

    def __init__(self):
        """Initialize the application."""
        self.connection_manager = ConnectionManager()
        self.s3_client: S3Client | None = None
        self.current_connection: Connection | None = None
        self.current_bucket: str | None = None
        self.current_prefix: str = ""
        self.current_objects: list[S3Object] = []
        self.current_prefixes: list[str] = []
        self.selected_keys: set[str] = set()

        # Active async operations
        self.active_operations: list[AsyncOperation] = []

        # Sort state
        self.sort_column: str | None = None  # Column tag (e.g., "col_name", "col_size")
        self.sort_ascending: bool = True

        # UI element tags
        self.TAG_MAIN_WINDOW = "main_window"
        self.TAG_CONNECTION_COMBO = "connection_combo"
        self.TAG_BUCKET_COMBO = "bucket_combo"
        self.TAG_PATH_INPUT = "path_input"
        self.TAG_OBJECT_TABLE = "object_table"
        self.TAG_STATUS_TEXT = "status_text"
        self.TAG_PROGRESS_BAR = "progress_bar"
        self.TAG_PROGRESS_TEXT = "progress_text"

        # Column tags for sort indicator updates
        self.TAG_COL_NAME = "col_name"
        self.TAG_COL_SIZE = "col_size"
        self.TAG_COL_MODIFIED = "col_modified"
        self.TAG_COL_STORAGE = "col_storage"

        # Log console state
        self.log_buffer: list[str] = []
        self.console_visible: bool = False
        self.console_height: int = 150
        self.is_dragging_console: bool = False
        self.drag_start_y: float = 0
        self.drag_start_height: int = 0
        self.TAG_LOG_CONSOLE = "log_console"
        self.TAG_CONSOLE_CONTAINER = "console_container"
        self.TAG_CONSOLE_HANDLE = "console_resize_handle"

        # Preview state
        self.preview_visible: bool = False
        self.preview_object: S3Object | None = None
        self.preview_type: str | None = None  # "text", "image", "archive"
        self.TAG_PREVIEW_PANEL = "preview_panel"
        self.TAG_PREVIEW_HEADER = "preview_header"
        self.TAG_PREVIEW_CONTENT = "preview_content"

    def run(self):
        """Run the application."""
        dpg.create_context()

        # Initialize drag and drop support (Windows only)
        if HAS_DND:
            dpg_dnd.initialize()

        self._setup_theme()
        self._create_ui()
        self._setup_console_resize_handlers()

        dpg.create_viewport(
            title=f"lolrus v{__version__} - I has a bucket!",
            width=self.WINDOW_WIDTH,
            height=self.WINDOW_HEIGHT,
        )

        # Set viewport icon if available
        self._set_viewport_icon()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.TAG_MAIN_WINDOW, True)

        # Set up file drop callback (Windows only)
        if HAS_DND:
            dpg_dnd.set_drop(self._on_files_dropped)

        # Main loop
        while dpg.is_dearpygui_running():
            self._update_progress()
            self._update_console_drag()
            dpg.render_dearpygui_frame()

        # Cleanup
        if self.s3_client:
            self.s3_client.close()
        dpg.destroy_context()

    def _set_viewport_icon(self):
        """Set the viewport icon if icon files are available."""
        from pathlib import Path

        # Try multiple locations for icon files
        possible_paths = [
            Path(__file__).parent.parent.parent / "assets",  # Development: repo/assets
            Path(sys.executable).parent / "assets",  # PyInstaller: dist/assets
            Path.cwd() / "assets",  # Current directory
        ]

        icon_path = None

        for assets_dir in possible_paths:
            # On Windows, use .ico file; on other platforms use .png
            if sys.platform == "win32":
                ico_path = assets_dir / "lolrus.ico"
                if ico_path.exists():
                    icon_path = str(ico_path)
                    break
            else:
                png_path = assets_dir / "icon_256.png"
                if png_path.exists():
                    icon_path = str(png_path)
                    break

        # Set icons if found
        if icon_path:
            try:
                dpg.set_viewport_small_icon(icon_path)
                dpg.set_viewport_large_icon(icon_path)
            except Exception:
                pass  # Icon setting is optional

    def _setup_theme(self):
        """Set up the application theme."""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 4)

            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 100, 150))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 120, 170))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (60, 90, 140))

        dpg.bind_theme(global_theme)

        # Danger button theme (for delete operations)
        with dpg.theme(tag="danger_theme"), dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (150, 50, 50))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (180, 70, 70))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (130, 40, 40))

        # Success theme
        with dpg.theme(tag="success_theme"), dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 120, 50))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 150, 70))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (40, 100, 40))

        # Resize handle theme - subtle bar that highlights on hover
        with dpg.theme(tag="resize_handle_theme"), dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (80, 80, 80))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (120, 120, 120))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 100))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0)

    def _create_ui(self):
        """Create the main UI."""
        # Create texture registry for image previews
        dpg.add_texture_registry(tag="texture_registry")

        with dpg.window(tag=self.TAG_MAIN_WINDOW):
            # Menu bar
            with dpg.menu_bar(), dpg.menu(label="Help"):
                dpg.add_menu_item(label="About", callback=self._show_about_dialog)

            # Top toolbar
            with dpg.group(horizontal=True):
                dpg.add_text("Connection:")
                dpg.add_combo(
                    tag=self.TAG_CONNECTION_COMBO,
                    items=self._get_connection_names(),
                    width=200,
                    callback=self._on_connection_selected,
                )
                dpg.add_button(label="New", callback=self._show_new_connection_dialog)
                dpg.add_button(label="Edit", callback=self._show_edit_connection_dialog)
                dpg.add_button(label="Delete", callback=self._delete_connection)

                dpg.add_spacer(width=20)

                dpg.add_text("Bucket:")
                dpg.add_combo(
                    tag=self.TAG_BUCKET_COMBO,
                    items=[],
                    width=200,
                    callback=self._on_bucket_selected,
                    enabled=False,
                )

                dpg.add_spacer(width=20)
                dpg.add_button(label="Logs", callback=self._toggle_console, tag="logs_btn")

            dpg.add_spacer(height=5)

            # Path bar
            with dpg.group(horizontal=True):
                dpg.add_text("Path:")
                dpg.add_input_text(
                    tag=self.TAG_PATH_INPUT,
                    width=-200,
                    callback=self._on_path_changed,
                    on_enter=True,
                    enabled=False,
                )
                dpg.add_button(label="Go Up", callback=self._go_up, enabled=False, tag="go_up_btn")
                dpg.add_button(label="Refresh", callback=self._refresh, enabled=False, tag="refresh_btn")

            dpg.add_spacer(height=5)

            # Action buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Upload", callback=self._upload_files, enabled=False, tag="upload_btn")
                dpg.add_button(label="Download", callback=self._download_selected, enabled=False, tag="download_btn")
                dpg.add_button(label="Delete Selected", callback=self._delete_selected, enabled=False, tag="delete_btn")
                dpg.bind_item_theme("delete_btn", "danger_theme")

                dpg.add_spacer(width=20)

                dpg.add_button(label="🔥 Empty Bucket", callback=self._empty_bucket, enabled=False, tag="nuke_btn")
                dpg.bind_item_theme("nuke_btn", "danger_theme")

                dpg.add_spacer(width=20)
                dpg.add_text("", tag="selection_count")

            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Main content area: table + preview panel side-by-side
            with dpg.group(horizontal=True, tag="main_content_group"):
                # Table container (width adjusts when preview is shown)
                with (
                    dpg.child_window(tag="table_container", width=-1, height=-80, border=False),
                    dpg.table(
                        tag=self.TAG_OBJECT_TABLE,
                        header_row=True,
                        resizable=True,
                        policy=dpg.mvTable_SizingStretchProp,
                        borders_innerH=True,
                        borders_outerH=True,
                        borders_innerV=True,
                        borders_outerV=True,
                        scrollY=True,
                        height=-1,
                        sortable=True,
                        callback=self._on_table_sort,
                    ),
                ):
                    dpg.add_table_column(label="", width_fixed=True, init_width_or_weight=30, no_sort=True)  # Checkbox
                    dpg.add_table_column(label="Name", init_width_or_weight=3, tag=self.TAG_COL_NAME)
                    dpg.add_table_column(label="Size", init_width_or_weight=1, tag=self.TAG_COL_SIZE)
                    dpg.add_table_column(label="Last Modified", init_width_or_weight=1.5, tag=self.TAG_COL_MODIFIED)
                    dpg.add_table_column(label="Storage Class", init_width_or_weight=1, tag=self.TAG_COL_STORAGE)

                # Preview panel (initially hidden)
                with dpg.child_window(tag=self.TAG_PREVIEW_PANEL, width=400, height=-80, show=False, border=True):
                    # Header with filename and close button (table for alignment)
                    with dpg.table(header_row=False, borders_innerH=False, borders_outerH=False,
                                   borders_innerV=False, borders_outerV=False):
                        dpg.add_table_column(init_width_or_weight=1.0)  # Text column (stretches)
                        dpg.add_table_column(width_fixed=True, init_width_or_weight=30)  # Button column
                        with dpg.table_row():
                            dpg.add_text("", tag=self.TAG_PREVIEW_HEADER)
                            dpg.add_button(label="X", callback=self._close_preview, width=25)
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    # Content area (populated dynamically based on preview type)
                    with dpg.group(tag=self.TAG_PREVIEW_CONTENT):
                        dpg.add_text("Click an object to preview", color=(150, 150, 150))

            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Log console resize handle (drag bar)
            with dpg.group(tag=self.TAG_CONSOLE_HANDLE, show=False):
                dpg.add_button(
                    label="",
                    width=-1,
                    height=6,
                    tag="console_drag_btn",
                )
                dpg.bind_item_theme("console_drag_btn", "resize_handle_theme")

            # Log console (collapsible)
            with dpg.child_window(tag=self.TAG_CONSOLE_CONTAINER, height=self.console_height, show=False, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Copy", callback=self._copy_logs)
                    dpg.add_button(label="Clear", callback=self._clear_logs)
                dpg.add_input_text(
                    tag=self.TAG_LOG_CONSOLE,
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=-1,
                    tab_input=False,
                )

            # Status bar
            with dpg.group(horizontal=True):
                dpg.add_text("Ready", tag=self.TAG_STATUS_TEXT)
                dpg.add_spacer(width=20)
                dpg.add_progress_bar(tag=self.TAG_PROGRESS_BAR, default_value=0, width=300, show=False)
                dpg.add_text("", tag=self.TAG_PROGRESS_TEXT)

    def _get_connection_names(self) -> list[str]:
        """Get list of saved connection names."""
        return [c.name for c in self.connection_manager.list_connections()]

    def _update_connection_combo(self):
        """Update the connection combo box."""
        dpg.configure_item(self.TAG_CONNECTION_COMBO, items=self._get_connection_names())

    def _set_status(self, text: str):
        """Set the status bar text and log it."""
        dpg.set_value(self.TAG_STATUS_TEXT, text)
        self._add_log(text)

    def _add_log(self, message: str, level: str = "INFO"):
        """Add a log entry to the console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}"
        self.log_buffer.append(log_line)

        # Limit buffer to 1000 lines
        if len(self.log_buffer) > 1000:
            self.log_buffer = self.log_buffer[-1000:]

        # Update display
        dpg.set_value(self.TAG_LOG_CONSOLE, "\n".join(self.log_buffer))

    def _toggle_console(self):
        """Toggle log console visibility."""
        self.console_visible = not self.console_visible
        dpg.configure_item(self.TAG_CONSOLE_CONTAINER, show=self.console_visible)
        dpg.configure_item(self.TAG_CONSOLE_HANDLE, show=self.console_visible)
        # Update button label
        label = "Hide Logs" if self.console_visible else "Logs"
        dpg.configure_item("logs_btn", label=label)
        # Adjust table height
        self._update_table_height()

    def _update_table_height(self):
        """Update table/preview height based on console visibility and size."""
        # Base space reserved for status bar and spacing
        base_reserved = 80
        if self.console_visible:
            # Reserve additional space for console + drag handle (6px bar + spacing)
            handle_height = 12
            total_reserved = base_reserved + self.console_height + handle_height
        else:
            total_reserved = base_reserved

        # Update both table container and preview panel heights
        dpg.configure_item("table_container", height=-total_reserved)
        dpg.configure_item(self.TAG_PREVIEW_PANEL, height=-total_reserved)

    def _copy_logs(self):
        """Copy all logs to clipboard using tkinter."""
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append("\n".join(self.log_buffer))
        root.update()
        root.destroy()
        self._set_status("Logs copied to clipboard")

    def _clear_logs(self):
        """Clear all logs."""
        self.log_buffer.clear()
        dpg.set_value(self.TAG_LOG_CONSOLE, "")
        self._set_status("Logs cleared")

    def _setup_console_resize_handlers(self):
        """Set up mouse handlers for console resizing."""
        with dpg.item_handler_registry(tag="console_drag_handler"):
            dpg.add_item_clicked_handler(callback=self._on_console_drag_start)
        dpg.bind_item_handler_registry("console_drag_btn", "console_drag_handler")

    def _on_console_drag_start(self, sender, app_data):
        """Handle start of console resize drag."""
        self.is_dragging_console = True
        self.drag_start_y = dpg.get_mouse_pos(local=False)[1]
        self.drag_start_height = self.console_height

    def _update_console_drag(self):
        """Update console height during drag (called every frame)."""
        if not self.is_dragging_console:
            return

        # Check if mouse button is still held
        if not dpg.is_mouse_button_down(dpg.mvMouseButton_Left):
            self.is_dragging_console = False
            return

        # Calculate new height based on mouse movement
        current_y = dpg.get_mouse_pos(local=False)[1]
        delta_y = self.drag_start_y - current_y  # Negative = dragging up = increase height

        new_height = max(50, min(500, self.drag_start_height + delta_y))
        self.console_height = new_height
        dpg.configure_item(self.TAG_CONSOLE_CONTAINER, height=new_height)
        # Also adjust table height to accommodate the new console size
        self._update_table_height()

    def _update_progress(self):
        """Update progress bars for active operations."""
        if not self.active_operations:
            return

        # Update progress for active operations
        active = [op for op in self.active_operations if op.status == OperationStatus.RUNNING]
        if active:
            op = active[0]
            dpg.configure_item(self.TAG_PROGRESS_BAR, show=True)
            dpg.set_value(self.TAG_PROGRESS_BAR, op.progress)
            dpg.set_value(self.TAG_PROGRESS_TEXT, f"{op.description}: {op.completed_items}/{op.total_items}")
        else:
            dpg.configure_item(self.TAG_PROGRESS_BAR, show=False)
            dpg.set_value(self.TAG_PROGRESS_TEXT, "")

        # Clean up completed operations
        self.active_operations = [op for op in self.active_operations if op.status in (OperationStatus.PENDING, OperationStatus.RUNNING)]

    def _on_connection_selected(self, sender, app_data):
        """Handle connection selection."""
        connection_name = app_data
        if not connection_name:
            return

        conn = self.connection_manager.get_connection(connection_name, load_credentials=True)
        if conn is None:
            self._set_status(f"Connection '{connection_name}' not found")
            return

        self._set_status(f"Connecting to {conn.endpoint_url}...")

        # Close existing client
        if self.s3_client:
            self.s3_client.close()

        try:
            self.s3_client = S3Client(
                endpoint_url=conn.endpoint_url,
                access_key=conn.access_key,
                secret_key=conn.secret_key,
                region=conn.region,
                log_callback=self._add_log,
            )

            if not self.s3_client.test_connection():
                self._set_status("Connection failed - check credentials")
                self.s3_client = None
                return

            self.current_connection = conn
            self._set_status(f"Connected to {conn.name}")

            # Load buckets
            buckets = self.s3_client.list_buckets()
            bucket_names = [b.name for b in buckets]
            dpg.configure_item(self.TAG_BUCKET_COMBO, items=bucket_names, enabled=True)

            # Enable path input
            dpg.configure_item(self.TAG_PATH_INPUT, enabled=True)
            dpg.configure_item("refresh_btn", enabled=True)

        except Exception as e:
            self._set_status(f"Connection error: {e}")
            self.s3_client = None

    def _on_bucket_selected(self, sender, app_data):
        """Handle bucket selection."""
        bucket_name = app_data
        if not bucket_name or not self.s3_client:
            return

        self.current_bucket = bucket_name
        self.current_prefix = ""
        dpg.set_value(self.TAG_PATH_INPUT, "")
        self._refresh_object_list()

        # Enable action buttons
        dpg.configure_item("go_up_btn", enabled=True)
        dpg.configure_item("upload_btn", enabled=True)
        dpg.configure_item("nuke_btn", enabled=True)

    def _on_path_changed(self, sender, app_data):
        """Handle path input change."""
        self.current_prefix = app_data
        self._refresh_object_list()

    def _go_up(self):
        """Navigate up one directory level."""
        if not self.current_prefix:
            return

        # Remove trailing slash, then go up one level
        prefix = self.current_prefix.rstrip("/")
        if "/" in prefix:
            self.current_prefix = prefix.rsplit("/", 1)[0] + "/"
        else:
            self.current_prefix = ""

        dpg.set_value(self.TAG_PATH_INPUT, self.current_prefix)
        self._refresh_object_list()

    def _refresh(self):
        """Refresh the current view."""
        self._refresh_object_list()

    def _refresh_object_list(self):
        """Refresh the object list for current bucket/prefix."""
        if not self.s3_client or not self.current_bucket:
            return

        self._set_status(f"Loading {self.current_bucket}/{self.current_prefix}...")
        self.selected_keys.clear()

        try:
            objects, prefixes = self.s3_client.list_objects(
                self.current_bucket,
                self.current_prefix,
            )
            self.current_objects = objects
            self.current_prefixes = prefixes

            # Apply current sort settings
            self._apply_current_sort()

            self._populate_table()
            self._set_status(f"Loaded {len(prefixes)} folders, {len(objects)} objects")
            self._update_selection_count()

        except Exception as e:
            self._set_status(f"Error loading objects: {e}")

    def _populate_table(self):
        """Populate the object table with current data."""
        # Update column labels with sort indicators
        self._update_column_labels()

        # Clear existing rows
        for child in dpg.get_item_children(self.TAG_OBJECT_TABLE, 1):
            dpg.delete_item(child)

        # Add folder rows
        for prefix in self.current_prefixes:
            folder_name = prefix.rstrip("/").split("/")[-1] + "/"
            with dpg.table_row(parent=self.TAG_OBJECT_TABLE):
                dpg.add_checkbox(callback=self._on_item_checked, user_data=prefix)
                dpg.add_selectable(label=f"📁 {folder_name}", span_columns=True, callback=self._on_folder_clicked, user_data=prefix)

        # Add object rows
        for obj in self.current_objects:
            with dpg.table_row(parent=self.TAG_OBJECT_TABLE):
                dpg.add_checkbox(callback=self._on_item_checked, user_data=obj.key)

                # Create selectable with unique tag for popup attachment
                selectable_tag = self._make_selectable_tag(obj.key)
                dpg.add_selectable(
                    label=f"📄 {obj.name}",
                    callback=self._on_object_clicked,
                    user_data=obj,
                    tag=selectable_tag,
                )

                # Context menu popup (right-click)
                with dpg.popup(selectable_tag, mousebutton=dpg.mvMouseButton_Right):
                    dpg.add_menu_item(label="Preview", callback=self._context_preview, user_data=obj)
                    dpg.add_menu_item(label="Download", callback=self._context_download, user_data=obj)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Copy URL", callback=self._context_copy_url, user_data=obj)
                    dpg.add_menu_item(label="Copy Key", callback=self._context_copy_key, user_data=obj)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Rename...", callback=self._context_rename, user_data=obj)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Delete", callback=self._context_delete, user_data=obj)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Properties...", callback=self._context_properties, user_data=obj)

                dpg.add_text(humanize.naturalsize(obj.size, binary=True))
                dpg.add_text(obj.last_modified.strftime("%Y-%m-%d %H:%M:%S"))
                dpg.add_text(obj.storage_class)

    def _on_item_checked(self, sender, app_data, key: str):
        """Handle item checkbox toggle."""
        if app_data:
            self.selected_keys.add(key)
        else:
            self.selected_keys.discard(key)

        self._update_selection_count()

    def _update_selection_count(self):
        """Update the selection count display."""
        count = len(self.selected_keys)
        if count > 0:
            dpg.set_value("selection_count", f"{count} item(s) selected")
            dpg.configure_item("download_btn", enabled=True)
            dpg.configure_item("delete_btn", enabled=True)
        else:
            dpg.set_value("selection_count", "")
            dpg.configure_item("download_btn", enabled=False)
            dpg.configure_item("delete_btn", enabled=False)

    def _on_folder_clicked(self, sender, app_data, prefix: str):
        """Handle folder click - navigate into it."""
        self.current_prefix = prefix
        dpg.set_value(self.TAG_PATH_INPUT, prefix)
        self._refresh_object_list()

    def _on_object_clicked(self, sender, app_data, obj: S3Object):
        """Handle object click - show preview if supported."""
        preview_type = self._get_preview_type(obj)

        if preview_type is None:
            self._set_status(f"No preview available for {obj.name}")
            return

        self._show_preview(obj, preview_type)

    def _on_table_sort(self, sender, sort_specs):
        """Handle table column header click for sorting."""
        if sort_specs is None:
            return

        # sort_specs format: [[column_id, direction], ...]
        # column_id is the DearPyGui internal numeric ID
        # direction: 1 = ascending, -1 = descending
        column_id = sort_specs[0][0]
        direction = sort_specs[0][1]

        # Convert numeric ID to string tag
        column_tag = dpg.get_item_alias(column_id)

        self.sort_column = column_tag
        self.sort_ascending = direction > 0

        self._apply_current_sort()
        self._populate_table()

    def _apply_current_sort(self):
        """Apply current sort settings to objects and prefixes."""
        if self.sort_column is None:
            return

        reverse = not self.sort_ascending

        if self.sort_column == self.TAG_COL_NAME:
            self.current_prefixes.sort(key=lambda p: p.lower(), reverse=reverse)
            self.current_objects.sort(key=lambda o: o.name.lower(), reverse=reverse)
        elif self.sort_column == self.TAG_COL_SIZE:
            self.current_objects.sort(key=lambda o: o.size, reverse=reverse)
        elif self.sort_column == self.TAG_COL_MODIFIED:
            self.current_objects.sort(key=lambda o: o.last_modified, reverse=reverse)
        elif self.sort_column == self.TAG_COL_STORAGE:
            self.current_objects.sort(key=lambda o: o.storage_class, reverse=reverse)

    def _update_column_labels(self):
        """Update column labels with sort indicators."""
        # Base labels for each column
        columns = [
            (self.TAG_COL_NAME, "Name"),
            (self.TAG_COL_SIZE, "Size"),
            (self.TAG_COL_MODIFIED, "Last Modified"),
            (self.TAG_COL_STORAGE, "Storage Class"),
        ]

        for tag, base_label in columns:
            if self.sort_column == tag:
                indicator = " ▲" if self.sort_ascending else " ▼"
                dpg.configure_item(tag, label=base_label + indicator)
            else:
                dpg.configure_item(tag, label=base_label)

    # -------------------------------------------------------------------------
    # Preview functionality
    # -------------------------------------------------------------------------

    def _get_preview_type(self, obj: S3Object) -> str | None:
        """Determine preview type from object key/extension."""
        key_lower = obj.key.lower()

        # Text files
        text_extensions = {
            ".txt", ".md", ".json", ".xml", ".csv", ".log", ".py",
            ".js", ".html", ".css", ".yaml", ".yml", ".toml", ".ini", ".cfg",
            ".sh", ".bat", ".ps1", ".sql", ".java", ".c", ".cpp", ".h", ".hpp",
            ".rs", ".go", ".rb", ".php", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
        }
        if any(key_lower.endswith(ext) for ext in text_extensions):
            return "text"

        # Images
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        if any(key_lower.endswith(ext) for ext in image_extensions):
            return "image"

        # Archives
        archive_extensions = {".zip", ".tar", ".tar.gz", ".tgz", ".gz"}
        if any(key_lower.endswith(ext) for ext in archive_extensions):
            return "archive"

        return None

    def _show_preview(self, obj: S3Object, preview_type: str):
        """Download and display preview for an object."""
        import threading

        self.preview_object = obj
        self.preview_type = preview_type

        # Update header
        size_str = humanize.naturalsize(obj.size, binary=True)
        dpg.set_value(self.TAG_PREVIEW_HEADER, f"{obj.name} ({size_str})")

        # Adjust table container to make room for preview panel
        dpg.configure_item("table_container", width=-410)

        # Show panel
        self.preview_visible = True
        dpg.configure_item(self.TAG_PREVIEW_PANEL, show=True)

        # Clear existing content and show loading message
        self._clear_preview_content()
        dpg.add_text("Loading preview...", parent=self.TAG_PREVIEW_CONTENT, color=(150, 150, 150))

        self._set_status(f"Loading preview for {obj.name}...")

        # Download in background thread
        def do_preview():
            try:
                # Set size limit based on type
                max_size = 10_000_000 if preview_type == "text" else 50_000_000
                if preview_type == "archive":
                    max_size = 100_000_000

                content = self.s3_client.download_object_to_memory(
                    self.current_bucket, obj.key, max_size=max_size
                )
                # Schedule display on main thread
                dpg.split_frame()
                self._display_preview_content(content, preview_type, obj.key)
            except Exception as e:
                dpg.split_frame()
                self._display_preview_error(str(e))

        threading.Thread(target=do_preview, daemon=True).start()

    def _display_preview_content(self, content: bytes, preview_type: str, key: str):
        """Display preview content based on type."""
        if preview_type == "text":
            self._display_text_preview(content)
        elif preview_type == "image":
            self._display_image_preview(content)
        elif preview_type == "archive":
            self._display_archive_preview(content, key)

        self._set_status(f"Preview loaded: {self.preview_object.name if self.preview_object else 'unknown'}")

    def _display_text_preview(self, content: bytes):
        """Display text content in preview area."""
        self._clear_preview_content()

        # Decode with fallback
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        # Truncate if very large
        if len(text) > 100000:
            text = text[:100000] + "\n\n... (truncated, file too large for preview) ..."

        dpg.add_input_text(
            parent=self.TAG_PREVIEW_CONTENT,
            default_value=text,
            multiline=True,
            readonly=True,
            width=-1,
            height=-1,
            tab_input=False,
        )

    def _display_image_preview(self, content: bytes):
        """Display image in preview area."""
        import array
        import io

        from PIL import Image

        self._clear_preview_content()

        try:
            # Load image with Pillow
            img = Image.open(io.BytesIO(content))
            original_size = img.size
            img = img.convert("RGBA")

            # Scale to fit preview area (max 380px wide)
            max_width = 380
            max_height = 500
            if img.width > max_width or img.height > max_height:
                ratio = min(max_width / img.width, max_height / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to DearPyGui texture
            width, height = img.size

            # Normalize pixel data to 0-1 floats for DearPyGui
            img_data = img.tobytes()
            float_data = array.array('f', [b / 255.0 for b in img_data])

            # Create texture (clean up existing one first)
            texture_tag = "preview_texture"
            if dpg.does_item_exist(texture_tag):
                dpg.delete_item(texture_tag)

            # Create static texture in the default registry
            dpg.add_static_texture(
                width=width,
                height=height,
                default_value=float_data,
                tag=texture_tag,
                parent="texture_registry"
            )

            dpg.add_image(texture_tag, parent=self.TAG_PREVIEW_CONTENT)
            dpg.add_text(f"Original: {original_size[0]}x{original_size[1]}", parent=self.TAG_PREVIEW_CONTENT, color=(150, 150, 150))

        except Exception as e:
            dpg.add_text(f"Error loading image: {e}", parent=self.TAG_PREVIEW_CONTENT, color=(255, 100, 100))

    def _display_archive_preview(self, content: bytes, key: str):
        """Display archive contents listing."""
        import gzip
        import io
        import tarfile
        import zipfile

        self._clear_preview_content()

        files = []
        key_lower = key.lower()

        try:
            if key_lower.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    files = [(info.filename, info.file_size) for info in zf.infolist() if not info.is_dir()]
            elif key_lower.endswith((".tar", ".tar.gz", ".tgz")):
                mode = "r:gz" if key_lower.endswith((".tar.gz", ".tgz")) else "r"
                with tarfile.open(fileobj=io.BytesIO(content), mode=mode) as tf:
                    files = [(m.name, m.size) for m in tf.getmembers() if m.isfile()]
            elif key_lower.endswith(".gz"):
                # Single file gzip - just show compressed info
                with gzip.open(io.BytesIO(content)) as gf:
                    # Try to read and get uncompressed size
                    uncompressed = gf.read()
                    files = [("(compressed content)", len(uncompressed))]
        except Exception as e:
            dpg.add_text(f"Error reading archive: {e}", parent=self.TAG_PREVIEW_CONTENT, color=(255, 100, 100))
            return

        # Display file list
        dpg.add_text(f"Archive contents ({len(files)} files):", parent=self.TAG_PREVIEW_CONTENT)
        dpg.add_separator(parent=self.TAG_PREVIEW_CONTENT)

        # Create scrollable list
        with dpg.child_window(parent=self.TAG_PREVIEW_CONTENT, height=-1, border=False):
            for name, size in files[:500]:  # Limit to 500 entries
                size_str = humanize.naturalsize(size, binary=True)
                dpg.add_text(f"{name}  ({size_str})")

            if len(files) > 500:
                dpg.add_text(f"... and {len(files) - 500} more files", color=(150, 150, 150))

    def _display_preview_error(self, error: str):
        """Display an error message in the preview area."""
        self._clear_preview_content()
        dpg.add_text(f"Error: {error}", parent=self.TAG_PREVIEW_CONTENT, color=(255, 100, 100), wrap=380)
        self._set_status(f"Preview error: {error}")

    def _close_preview(self):
        """Close the preview panel."""
        self.preview_visible = False
        self.preview_object = None
        self.preview_type = None
        dpg.configure_item(self.TAG_PREVIEW_PANEL, show=False)
        # Restore table container to full width
        dpg.configure_item("table_container", width=-1)
        self._clear_preview_content()
        # Add placeholder text back
        dpg.add_text("Click an object to preview", parent=self.TAG_PREVIEW_CONTENT, color=(150, 150, 150))

    def _clear_preview_content(self):
        """Clear the preview content area."""
        for child in dpg.get_item_children(self.TAG_PREVIEW_CONTENT, 1) or []:
            dpg.delete_item(child)

        # Clean up texture if exists
        if dpg.does_item_exist("preview_texture"):
            dpg.delete_item("preview_texture")

    # -------------------------------------------------------------------------
    # Context menu helpers
    # -------------------------------------------------------------------------

    def _make_selectable_tag(self, key: str) -> str:
        """Create a valid DearPyGui tag from an object key."""
        import hashlib
        return f"obj_{hashlib.md5(key.encode()).hexdigest()[:12]}"

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard using tkinter."""
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()

    # -------------------------------------------------------------------------
    # Context menu handlers
    # -------------------------------------------------------------------------

    def _context_preview(self, sender, app_data, obj: S3Object):
        """Preview object from context menu."""
        preview_type = self._get_preview_type(obj)
        if preview_type:
            self._show_preview(obj, preview_type)
        else:
            self._set_status(f"No preview available for {obj.name}")

    def _context_download(self, sender, app_data, obj: S3Object):
        """Download single object from context menu."""
        def on_folder_selected(sender, app_data):
            folder = app_data.get("file_path_name", "")
            if folder:
                filename = obj.name
                local_path = os.path.join(folder, filename)
                self._do_download(obj.key, local_path)
            dpg.delete_item("context_folder_dialog")

        if dpg.does_item_exist("context_folder_dialog"):
            dpg.delete_item("context_folder_dialog")

        with dpg.file_dialog(
            tag="context_folder_dialog",
            directory_selector=True,
            show=True,
            callback=on_folder_selected,
            width=700,
            height=400,
        ):
            pass

    def _context_copy_url(self, sender, app_data, obj: S3Object):
        """Copy S3 URL to clipboard."""
        url = f"{self.current_connection.endpoint_url}/{self.current_bucket}/{obj.key}"
        self._copy_to_clipboard(url)
        self._set_status(f"Copied URL: {url}")

    def _context_copy_key(self, sender, app_data, obj: S3Object):
        """Copy object key to clipboard."""
        self._copy_to_clipboard(obj.key)
        self._set_status(f"Copied key: {obj.key}")

    def _context_rename(self, sender, app_data, obj: S3Object):
        """Show rename dialog for object."""
        self._show_rename_dialog(obj)

    def _context_delete(self, sender, app_data, obj: S3Object):
        """Delete single object from context menu."""
        self._show_confirm_dialog(
            "Delete Object",
            f"Are you sure you want to delete '{obj.name}'?\n\nThis cannot be undone!",
            lambda: self._do_context_delete(obj),
        )

    def _do_context_delete(self, obj: S3Object):
        """Actually delete a single object."""
        # Close preview if this object is being previewed
        if self.preview_visible and self.preview_object and self.preview_object.key == obj.key:
            self._close_preview()

        def on_complete(op: AsyncOperation):
            if op.status == OperationStatus.COMPLETED:
                self._set_status(f"Deleted {obj.name}")
                dpg.split_frame()
                self._refresh_object_list()
            elif op.status == OperationStatus.FAILED:
                self._set_status(f"Delete failed: {op.error}")

        op = self.s3_client.delete_objects_async(
            self.current_bucket,
            [obj.key],
            on_complete=on_complete,
        )
        self.active_operations.append(op)
        self._set_status(f"Deleting {obj.name}...")

    def _context_properties(self, sender, app_data, obj: S3Object):
        """Show properties dialog for object."""
        self._show_properties_dialog(obj)

    # -------------------------------------------------------------------------
    # Rename dialog
    # -------------------------------------------------------------------------

    def _show_rename_dialog(self, obj: S3Object):
        """Show dialog to rename an object."""
        dialog_tag = "rename_dialog"

        if dpg.does_item_exist(dialog_tag):
            dpg.delete_item(dialog_tag)

        # Get just the filename, preserve the prefix
        prefix = obj.key.rsplit(obj.name, 1)[0] if obj.name in obj.key else ""

        with dpg.window(
            label="Rename Object",
            tag=dialog_tag,
            modal=True,
            width=400,
            height=150,
            pos=(400, 300),
            no_resize=True,
        ):
            dpg.add_text(f"Rename: {obj.name}")
            dpg.add_spacer(height=10)
            dpg.add_input_text(
                tag="rename_input",
                default_value=obj.name,
                width=-1,
            )
            dpg.add_spacer(height=15)

            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Rename",
                    callback=lambda: self._do_rename(obj, prefix, dialog_tag),
                    width=100,
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item(dialog_tag),
                    width=100,
                )

    def _do_rename(self, obj: S3Object, prefix: str, dialog_tag: str):
        """Execute the rename (copy + delete)."""
        import threading

        new_name = dpg.get_value("rename_input").strip()

        if not new_name or new_name == obj.name:
            dpg.delete_item(dialog_tag)
            return

        new_key = prefix + new_name

        # Close preview if renaming previewed object
        if self.preview_visible and self.preview_object and self.preview_object.key == obj.key:
            self._close_preview()

        dpg.delete_item(dialog_tag)
        self._set_status(f"Renaming {obj.name} to {new_name}...")

        # S3 rename = copy + delete
        def do_rename():
            try:
                # Copy to new key
                self.s3_client._client.copy_object(
                    Bucket=self.current_bucket,
                    CopySource={"Bucket": self.current_bucket, "Key": obj.key},
                    Key=new_key,
                )
                # Delete old key
                self.s3_client._client.delete_object(
                    Bucket=self.current_bucket,
                    Key=obj.key,
                )
                dpg.split_frame()
                self._set_status(f"Renamed to {new_name}")
                self._refresh_object_list()
            except Exception as e:
                dpg.split_frame()
                self._set_status(f"Rename failed: {e}")

        threading.Thread(target=do_rename, daemon=True).start()

    # -------------------------------------------------------------------------
    # Properties dialog
    # -------------------------------------------------------------------------

    def _show_properties_dialog(self, obj: S3Object):
        """Show properties dialog for an object."""
        dialog_tag = "properties_dialog"

        if dpg.does_item_exist(dialog_tag):
            dpg.delete_item(dialog_tag)

        with dpg.window(
            label="Object Properties",
            tag=dialog_tag,
            modal=True,
            width=450,
            height=280,
            pos=(375, 250),
            no_resize=True,
        ):
            # Fetch additional metadata
            try:
                info = self.s3_client.get_object_info(self.current_bucket, obj.key)
                content_type = info.get("content_type", "Unknown")
            except Exception:
                content_type = "Unknown"

            with dpg.table(header_row=False, borders_innerH=True):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column()

                properties = [
                    ("Name:", obj.name),
                    ("Key:", obj.key),
                    ("Size:", humanize.naturalsize(obj.size, binary=True)),
                    ("Last Modified:", obj.last_modified.strftime("%Y-%m-%d %H:%M:%S")),
                    ("Content Type:", content_type),
                    ("Storage Class:", obj.storage_class),
                    ("ETag:", obj.etag),
                ]

                for label, value in properties:
                    with dpg.table_row():
                        dpg.add_text(label)
                        dpg.add_text(value)

            dpg.add_spacer(height=15)
            dpg.add_button(
                label="Close",
                callback=lambda: dpg.delete_item(dialog_tag),
                width=100,
            )

    # -------------------------------------------------------------------------
    # Connection dialogs
    # -------------------------------------------------------------------------

    def _show_new_connection_dialog(self):
        """Show dialog to create a new connection."""
        self._show_connection_dialog(None)

    def _show_edit_connection_dialog(self):
        """Show dialog to edit current connection."""
        connection_name = dpg.get_value(self.TAG_CONNECTION_COMBO)
        if not connection_name:
            return

        conn = self.connection_manager.get_connection(connection_name, load_credentials=True)
        if conn:
            self._show_connection_dialog(conn)

    def _show_connection_dialog(self, existing: Connection | None):
        """Show the connection edit dialog."""
        is_edit = existing is not None
        title = "Edit Connection" if is_edit else "New Connection"
        dialog_tag = "connection_dialog"

        # Delete existing dialog if any
        if dpg.does_item_exist(dialog_tag):
            dpg.delete_item(dialog_tag)

        with dpg.window(
            label=title,
            tag=dialog_tag,
            modal=True,
            width=500,
            height=400,
            pos=(350, 200),
            no_resize=True,
        ):
            dpg.add_text("Connection Name:")
            dpg.add_input_text(
                tag="conn_name",
                default_value=existing.name if existing else "",
                width=-1,
            )

            dpg.add_spacer(height=10)

            dpg.add_text("Endpoint URL:")
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="conn_endpoint",
                    default_value=existing.endpoint_url if existing else "",
                    width=-120,
                )
                dpg.add_combo(
                    items=["Custom"] + list(COMMON_ENDPOINTS.keys()),
                    default_value="Custom",
                    width=110,
                    callback=self._on_endpoint_preset_selected,
                )

            dpg.add_spacer(height=10)

            dpg.add_text("Region:")
            dpg.add_input_text(
                tag="conn_region",
                default_value=existing.region if existing else "us-east-1",
                width=-1,
            )

            dpg.add_spacer(height=10)

            dpg.add_text("Access Key:")
            dpg.add_input_text(
                tag="conn_access_key",
                default_value=existing.access_key if existing else "",
                width=-1,
            )

            dpg.add_spacer(height=10)

            dpg.add_text("Secret Key:")
            dpg.add_input_text(
                tag="conn_secret_key",
                default_value=existing.secret_key if existing else "",
                password=True,
                width=-1,
            )

            dpg.add_spacer(height=20)

            with dpg.group(horizontal=True):
                save_btn = dpg.add_button(
                    label="Save",
                    callback=lambda: self._save_connection_from_dialog(dialog_tag, existing.name if existing else None),
                    width=100,
                )
                dpg.bind_item_theme(save_btn, "success_theme")

                dpg.add_button(
                    label="Test Connection",
                    callback=self._test_connection_from_dialog,
                    width=120,
                )

                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item(dialog_tag),
                    width=100,
                )

            dpg.add_spacer(height=10)
            dpg.add_text("", tag="conn_dialog_status")

    def _on_endpoint_preset_selected(self, sender, app_data):
        """Handle endpoint preset selection."""
        if app_data == "Custom":
            return
        if app_data in COMMON_ENDPOINTS:
            dpg.set_value("conn_endpoint", COMMON_ENDPOINTS[app_data])

    def _test_connection_from_dialog(self):
        """Test connection with values from dialog."""
        endpoint = dpg.get_value("conn_endpoint")
        access_key = dpg.get_value("conn_access_key")
        secret_key = dpg.get_value("conn_secret_key")
        region = dpg.get_value("conn_region")

        dpg.set_value("conn_dialog_status", "Testing connection...")

        try:
            client = S3Client(
                endpoint_url=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                region=region,
                log_callback=self._add_log,
            )
            if client.test_connection():
                dpg.set_value("conn_dialog_status", "✅ Connection successful!")
            else:
                dpg.set_value("conn_dialog_status", "❌ Connection failed")
            client.close()
        except Exception as e:
            dpg.set_value("conn_dialog_status", f"❌ Error: {e}")

    def _save_connection_from_dialog(self, dialog_tag: str, old_name: str | None):
        """Save connection from dialog values."""
        name = dpg.get_value("conn_name").strip()
        endpoint = dpg.get_value("conn_endpoint").strip()
        access_key = dpg.get_value("conn_access_key").strip()
        secret_key = dpg.get_value("conn_secret_key").strip()
        region = dpg.get_value("conn_region").strip()

        if not all([name, endpoint, access_key, secret_key]):
            dpg.set_value("conn_dialog_status", "❌ All fields are required")
            return

        # If renaming, delete old connection
        if old_name and old_name != name:
            self.connection_manager.delete_connection(old_name)

        conn = Connection(
            name=name,
            endpoint_url=endpoint,
            region=region,
            access_key=access_key,
            secret_key=secret_key,
        )
        self.connection_manager.save_connection(conn)

        self._update_connection_combo()
        dpg.delete_item(dialog_tag)
        self._set_status(f"Connection '{name}' saved")

    def _delete_connection(self):
        """Delete the selected connection."""
        connection_name = dpg.get_value(self.TAG_CONNECTION_COMBO)
        if not connection_name:
            return

        self._show_confirm_dialog(
            "Delete Connection",
            f"Are you sure you want to delete connection '{connection_name}'?",
            lambda: self._do_delete_connection(connection_name),
        )

    def _do_delete_connection(self, name: str):
        """Actually delete a connection."""
        self.connection_manager.delete_connection(name)
        self._update_connection_combo()

        # Clear current connection if it was deleted
        if self.current_connection and self.current_connection.name == name:
            self.current_connection = None
            if self.s3_client:
                self.s3_client.close()
                self.s3_client = None

        self._set_status(f"Connection '{name}' deleted")

    # -------------------------------------------------------------------------
    # File operations
    # -------------------------------------------------------------------------

    def _upload_files(self):
        """Open file dialog to upload files."""
        # DearPyGui file dialog
        def on_file_selected(sender, app_data):
            selections = app_data.get("selections", {})
            for filename, filepath in selections.items():
                key = self.current_prefix + filename
                self._do_upload(filepath, key)
            dpg.delete_item("file_dialog")

        if dpg.does_item_exist("file_dialog"):
            dpg.delete_item("file_dialog")

        with dpg.file_dialog(
            tag="file_dialog",
            directory_selector=False,
            show=True,
            callback=on_file_selected,
            width=700,
            height=400,
        ):
            dpg.add_file_extension(".*", color=(255, 255, 255, 255))

    def _on_files_dropped(self, file_paths: list[str], keys):
        """Handle files dropped onto the viewport for upload."""
        # Check if we have a bucket selected
        if not self.s3_client or not self.current_bucket:
            self._set_status("Select a bucket before dropping files to upload")
            return

        # Filter to only files (not directories)
        files_to_upload = []
        for path in file_paths:
            if os.path.isfile(path):
                files_to_upload.append(path)

        if not files_to_upload:
            self._set_status("No files to upload (directories are not supported)")
            return

        # Upload each file
        count = len(files_to_upload)
        self._set_status(f"Uploading {count} file(s)...")

        for filepath in files_to_upload:
            filename = os.path.basename(filepath)
            key = self.current_prefix + filename
            self._do_upload(filepath, key)

    def _do_upload(self, local_path: str, key: str):
        """Upload a file."""
        if not self.s3_client or not self.current_bucket:
            return

        def on_complete(op: AsyncOperation):
            if op.status == OperationStatus.COMPLETED:
                self._set_status(f"Uploaded {key}")
                # Refresh on main thread
                dpg.split_frame()
                self._refresh_object_list()
            elif op.status == OperationStatus.FAILED:
                self._set_status(f"Upload failed: {op.error}")

        op = self.s3_client.upload_file_async(
            self.current_bucket,
            key,
            local_path,
            on_complete=on_complete,
        )
        self.active_operations.append(op)
        self._set_status(f"Uploading {key}...")

    def _download_selected(self):
        """Download selected objects."""
        if not self.selected_keys:
            return

        # Open folder dialog for download location
        def on_folder_selected(sender, app_data):
            folder = app_data.get("file_path_name", "")
            if folder:
                for key in list(self.selected_keys):
                    if not key.endswith("/"):  # Skip folders
                        filename = key.split("/")[-1]
                        local_path = os.path.join(folder, filename)
                        self._do_download(key, local_path)
            dpg.delete_item("folder_dialog")

        if dpg.does_item_exist("folder_dialog"):
            dpg.delete_item("folder_dialog")

        with dpg.file_dialog(
            tag="folder_dialog",
            directory_selector=True,
            show=True,
            callback=on_folder_selected,
            width=700,
            height=400,
        ):
            pass

    def _do_download(self, key: str, local_path: str):
        """Download a file."""
        if not self.s3_client or not self.current_bucket:
            return

        def on_complete(op: AsyncOperation):
            if op.status == OperationStatus.COMPLETED:
                self._set_status(f"Downloaded {key}")
            elif op.status == OperationStatus.FAILED:
                self._set_status(f"Download failed: {op.error}")

        op = self.s3_client.download_object_async(
            self.current_bucket,
            key,
            local_path,
            on_complete=on_complete,
        )
        self.active_operations.append(op)
        self._set_status(f"Downloading {key}...")

    def _delete_selected(self):
        """Delete selected objects after confirmation."""
        if not self.selected_keys:
            return

        count = len(self.selected_keys)
        self._show_confirm_dialog(
            "Delete Objects",
            f"Are you sure you want to delete {count} object(s)?\n\nThis cannot be undone!",
            self._do_delete_selected,
        )

    def _do_delete_selected(self):
        """Actually delete selected objects."""
        if not self.s3_client or not self.current_bucket or not self.selected_keys:
            return

        keys = list(self.selected_keys)

        # Close preview if the previewed file is being deleted
        if self.preview_visible and self.preview_object and self.preview_object.key in keys:
            self._close_preview()

        def on_complete(op: AsyncOperation):
            if op.status == OperationStatus.COMPLETED:
                self._set_status(f"Deleted {len(keys)} objects")
                dpg.split_frame()
                self._refresh_object_list()
            elif op.status == OperationStatus.FAILED:
                self._set_status(f"Delete failed: {op.error}")

        op = self.s3_client.delete_objects_async(
            self.current_bucket,
            keys,
            on_complete=on_complete,
        )
        self.active_operations.append(op)
        self._set_status(f"Deleting {len(keys)} objects...")

    def _empty_bucket(self):
        """Empty the entire bucket after confirmation."""
        if not self.s3_client or not self.current_bucket:
            return

        self._show_confirm_dialog(
            "🔥 DANGER: Empty Bucket",
            f"This will DELETE ALL OBJECTS in bucket '{self.current_bucket}'!\n\n"
            "This action CANNOT be undone.\n\n"
            "Type the bucket name to confirm:",
            self._do_empty_bucket,
            require_confirmation=self.current_bucket,
        )

    def _do_empty_bucket(self):
        """Actually empty the bucket."""
        if not self.s3_client or not self.current_bucket:
            return

        # Close preview since all files will be deleted
        if self.preview_visible:
            self._close_preview()

        def on_progress(op: AsyncOperation):
            pass  # Progress updated in main loop

        def on_complete(op: AsyncOperation):
            if op.status == OperationStatus.COMPLETED:
                self._set_status(f"Bucket '{self.current_bucket}' emptied ({op.completed_items} objects deleted)")
                dpg.split_frame()
                self._refresh_object_list()
            elif op.status == OperationStatus.FAILED:
                self._set_status(f"Empty bucket failed: {op.error}")
            elif op.status == OperationStatus.CANCELLED:
                self._set_status("Empty bucket cancelled")

        op = self.s3_client.empty_bucket_async(
            self.current_bucket,
            on_progress=on_progress,
            on_complete=on_complete,
        )
        self.active_operations.append(op)
        self._set_status(f"Emptying bucket '{self.current_bucket}'...")

    # -------------------------------------------------------------------------
    # Utility dialogs
    # -------------------------------------------------------------------------

    def _show_confirm_dialog(
        self,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        require_confirmation: str | None = None,
    ):
        """Show a confirmation dialog."""
        dialog_tag = "confirm_dialog"

        if dpg.does_item_exist(dialog_tag):
            dpg.delete_item(dialog_tag)

        with dpg.window(
            label=title,
            tag=dialog_tag,
            modal=True,
            width=450,
            height=200 if require_confirmation else 150,
            pos=(375, 300),
            no_resize=True,
        ):
            dpg.add_text(message, wrap=420)

            if require_confirmation:
                dpg.add_spacer(height=10)
                dpg.add_input_text(tag="confirm_input", width=-1)

            dpg.add_spacer(height=20)

            with dpg.group(horizontal=True):
                def do_confirm():
                    if require_confirmation and dpg.get_value("confirm_input") != require_confirmation:
                        return
                    dpg.delete_item(dialog_tag)
                    on_confirm()

                confirm_btn = dpg.add_button(label="Confirm", callback=do_confirm, width=100)
                dpg.bind_item_theme(confirm_btn, "danger_theme")
                dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item(dialog_tag), width=100)

    def _show_about_dialog(self):
        """Show the About dialog."""
        import webbrowser

        dialog_tag = "about_dialog"

        if dpg.does_item_exist(dialog_tag):
            dpg.delete_item(dialog_tag)

        # Theme for hyperlinks (create once)
        if not dpg.does_item_exist("link_theme"):
            with dpg.theme(tag="link_theme"), dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (100, 180, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0)

        with dpg.window(
            label="About lolrus",
            tag=dialog_tag,
            modal=True,
            width=400,
            height=380,
            pos=(400, 180),
            no_resize=True,
        ):
            # Title
            dpg.add_text("lolrus", color=(100, 180, 255))
            dpg.add_text(f"Version {__version__}")
            dpg.add_spacer(height=10)

            # Tagline
            dpg.add_text("I has a bucket!", color=(200, 200, 200))
            dpg.add_spacer(height=15)

            # Description
            dpg.add_text(
                "A desktop S3-compatible object storage browser.\n\n"
                "Connect to any S3-compatible storage provider:\n"
                "AWS S3, Linode, DigitalOcean, Backblaze B2,\n"
                "MinIO, Cloudflare R2, and more.",
                wrap=380,
            )
            dpg.add_spacer(height=10)

            # Developer info
            dpg.add_separator()
            dpg.add_spacer(height=8)
            with dpg.group(horizontal=True):
                dpg.add_text("Developed by Rob Zimmerman -")
                link_btn = dpg.add_button(
                    label="zimventures.com",
                    callback=lambda: webbrowser.open("https://zimventures.com"),
                )
                dpg.bind_item_theme(link_btn, "link_theme")

            with dpg.group(horizontal=True):
                dpg.add_text("Source code:")
                github_btn = dpg.add_button(
                    label="github.com/zimventures/lolrus",
                    callback=lambda: webbrowser.open("https://github.com/zimventures/lolrus"),
                )
                dpg.bind_item_theme(github_btn, "link_theme")

            dpg.add_spacer(height=10)

            # Credits
            dpg.add_separator()
            dpg.add_spacer(height=8)
            dpg.add_text("Built with:", color=(150, 150, 150))
            dpg.add_text("  DearPyGui  -  GPU-accelerated GUI")
            dpg.add_text("  boto3      -  AWS SDK for Python")
            dpg.add_text("  keyring    -  Secure credential storage")

            dpg.add_spacer(height=10)

            # Meme reference
            dpg.add_text("They be stealin' my bucket!", color=(150, 150, 150))

            dpg.add_spacer(height=15)

            # Close button
            dpg.add_button(
                label="Close",
                callback=lambda: dpg.delete_item(dialog_tag),
                width=100,
            )
