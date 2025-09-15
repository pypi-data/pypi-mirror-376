import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Tuple, Callable
from gi.repository import Gtk, Gio, GLib
from ..core.item import DocItem
from ..importer import importers, importer_by_mime_type, importer_by_extension
from ..undo import ListItemCommand
from ..shared.tasker.context import ExecutionContext
from ..pipeline.job import generate_job_ops
from ..pipeline.encoder.gcode import GcodeEncoder

if TYPE_CHECKING:
    from ..mainwindow import MainWindow
    from .editor import DocEditor
    from ..shared.tasker.manager import TaskManager
    from ..config import ConfigManager


logger = logging.getLogger(__name__)


class FileCmd:
    """Handles file import and export operations."""

    def __init__(
        self,
        editor: "DocEditor",
        task_manager: "TaskManager",
        config_manager: "ConfigManager",
    ):
        self._editor = editor
        self._task_manager = task_manager
        self._config_manager = config_manager

    def _calculate_items_bbox(
        self,
        items: List[DocItem],
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Calculates the world-space bounding box that encloses a list of
        DocItems by taking the union of their individual bboxes.
        """
        if not items:
            return None

        # Get the bbox of the first item to initialize the bounds.
        min_x, min_y, w, h = items[0].bbox
        max_x = min_x + w
        max_y = min_y + h

        # Expand the bounds with the bboxes of the other items.
        for item in items[1:]:
            ix, iy, iw, ih = item.bbox
            min_x = min(min_x, ix)
            min_y = min(min_y, iy)
            max_x = max(max_x, ix + iw)
            max_y = max(max_y, iy + ih)

        return min_x, min_y, max_x - min_x, max_y - min_y

    def _center_imported_items(self, items: List[DocItem]):
        """
        Calculates the collective bounding box of the imported items and
        translates them to the center of the machine workspace.
        """
        machine = self._config_manager.config.machine
        if not machine:
            return  # Cannot center if machine dimensions are unknown

        bbox = self._calculate_items_bbox(items)
        if not bbox:
            return

        bbox_x, bbox_y, bbox_w, bbox_h = bbox
        machine_w, machine_h = machine.dimensions

        # Calculate the translation needed to move the bbox center to the
        # machine center
        delta_x = (machine_w / 2) - (bbox_x + bbox_w / 2)
        delta_y = (machine_h / 2) - (bbox_y + bbox_h / 2)

        # Apply the same translation to all top-level imported items
        for item in items:
            current_pos_x, current_pos_y = item.pos
            item.pos = (current_pos_x + delta_x, current_pos_y + delta_y)

    def import_file(self, win: "MainWindow"):
        """
        Shows the file chooser dialog and triggers the import process upon
        user selection.
        """
        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Open File"))

        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        all_supported = Gtk.FileFilter()
        all_supported.set_name(_("All supported"))
        for importer_class in importers:
            file_filter = Gtk.FileFilter()
            if importer_class.label:
                file_filter.set_name(_(importer_class.label))
            if importer_class.mime_types:
                for mime_type in importer_class.mime_types:
                    file_filter.add_mime_type(mime_type)
                    all_supported.add_mime_type(mime_type)
            filter_list.append(file_filter)
        filter_list.append(all_supported)

        dialog.set_filters(filter_list)
        dialog.set_default_filter(all_supported)

        dialog.open(win, None, self._on_import_dialog_response, win)

    def _on_import_dialog_response(self, dialog, result, win: "MainWindow"):
        """Callback for when the user selects a file from the dialog."""
        try:
            file = dialog.open_finish(result)
            if not file:
                return

            file_path = Path(file.get_path())
            file_info = file.query_info(
                Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
                Gio.FileQueryInfoFlags.NONE,
                None,
            )
            mime_type = file_info.get_content_type()
            self.load_file_from_path(file_path, mime_type)
            # Hide properties widget in case something was selected before
            # import
            win.item_revealer.set_reveal_child(False)
        except Exception:
            logger.exception("Error opening file")

    def load_file_from_path(self, filename: Path, mime_type: Optional[str]):
        """
        Orchestrates the loading of a specific file path using the
        importer.
        """
        importer_class = None
        if mime_type:
            importer_class = importer_by_mime_type.get(mime_type)
        if not importer_class:
            file_extension = filename.suffix.lower()
            if file_extension:
                importer_class = importer_by_extension.get(file_extension)

        if not importer_class:
            logger.error(f"No importer found for '{filename.name}'")
            return

        try:
            file_data = filename.read_bytes()
            importer = importer_class(file_data, source_file=filename)
        except Exception as e:
            logger.error(
                f"Failed to instantiate importer for {filename.name}: {e}"
            )
            return

        cmd_name = _("Import {name}").format(name=filename.name)

        imported_items = importer.get_doc_items()
        if imported_items:
            self._center_imported_items(imported_items)

            # Use the editor's helper to get the correct target layer
            target_layer = self._editor.default_workpiece_layer

            with self._editor.history_manager.transaction(cmd_name) as t:
                for item in imported_items:
                    command = ListItemCommand(
                        owner_obj=target_layer,
                        item=item,
                        undo_command="remove_child",
                        redo_command="add_child",
                    )
                    t.execute(command)
        else:
            logger.error(f"Failed to import any items from '{filename.name}'.")

    def export_gcode_to_path(
        self, file_path: Path, when_done: Optional[Callable] = None
    ):
        """
        Headless version of G-code export that writes to a specific path.
        This is used by the async facade on DocEditor and for testing.
        """

        def write_gcode_sync(path, gcode):
            """Blocking I/O function to be run in a thread."""
            with open(path, "w", encoding="utf-8") as f:
                f.write(gcode)

        async def export_coro(context: ExecutionContext):
            machine = self._config_manager.config.machine
            if not machine:
                context.set_message("Error: No machine configured.")
                raise ValueError("Cannot export G-code without a machine.")

            try:
                # 1. Generate Ops (async, reports progress)
                ops = await generate_job_ops(
                    self._editor.doc,
                    machine,
                    self._editor.ops_generator,
                    context,
                )

                # 2. Encode G-code (sync, but usually fast)
                context.set_message(_("Encoding G-code..."))
                encoder = GcodeEncoder.for_machine(machine)
                gcode = encoder.encode(ops, machine)

                # 3. Write to file (sync, potentially slow, run in thread)
                context.set_message(_(f"Saving to {file_path}..."))
                await asyncio.to_thread(write_gcode_sync, file_path, gcode)

                context.set_message(_("Export complete!"))
                context.set_progress(1.0)
                context.flush()

            except Exception:
                logger.error("Failed to export G-code", exc_info=True)
                raise  # Re-raise to be caught by the task manager

        # Add the coroutine to the task manager
        self._task_manager.add_coroutine(
            export_coro, key="export-gcode", when_done=when_done
        )

    def _on_save_dialog_response(self, dialog, result, win: "MainWindow"):
        try:
            file = dialog.save_finish(result)
            if not file:
                return
            file_path = Path(file.get_path())
        except GLib.Error as e:
            logger.error(f"Error saving file: {e.message}")
            return

        self.export_gcode_to_path(file_path)

    def export_gcode(self, win: "MainWindow"):
        """Shows the save file dialog and handles the G-code export process."""
        # Create a file chooser dialog for saving the file
        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Save G-code File"))

        # Set the default file name
        dialog.set_initial_name("output.gcode")

        # Create a Gio.ListModel for the filters
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        gcode_filter = Gtk.FileFilter()
        gcode_filter.set_name(_("G-code files"))
        gcode_filter.add_mime_type("text/x.gcode")
        filter_list.append(gcode_filter)

        # Set the filters for the dialog
        dialog.set_filters(filter_list)
        dialog.set_default_filter(gcode_filter)

        # Show the dialog and handle the response
        dialog.save(win, None, self._on_save_dialog_response, win)
