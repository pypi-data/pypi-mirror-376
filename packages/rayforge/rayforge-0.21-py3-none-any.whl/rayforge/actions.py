from typing import TYPE_CHECKING, Dict, Callable, Optional, cast
from gi.repository import Gtk, Gio, GLib
from .core.group import Group
from .core.item import DocItem
from .core.layer import Layer

if TYPE_CHECKING:
    from .mainwindow import MainWindow


class ActionManager:
    """Manages the creation and state of all Gio.SimpleActions for the app."""

    def __init__(self, win: "MainWindow"):
        self.win = win
        self.actions: Dict[str, Gio.SimpleAction] = {}
        # A convenient alias to the central controller
        self.editor = self.win.doc_editor
        self.doc = self.editor.doc

        # Connect to doc signals to update action states
        self.doc.descendant_added.connect(self.update_action_states)
        self.doc.descendant_removed.connect(self.update_action_states)

    def register_actions(self):
        """Creates all Gio.SimpleActions and adds them to the window."""
        # Menu & File Actions
        self._add_action("quit", self.win.on_quit_action)
        self._add_action("import", self.win.on_menu_import)
        self._add_action("export", self.win.on_export_clicked)
        self._add_action("about", self.win.show_about_dialog)
        self._add_action("preferences", self.win.show_preferences)
        self._add_action("machine_settings", self.win.show_machine_settings)

        # View Actions
        self._add_stateful_action(
            "show_3d_view",
            self.win.on_show_3d_view,
            GLib.Variant.new_boolean(False),
        )
        self._add_stateful_action(
            "show_workpieces",
            self.win.on_show_workpieces_state_change,
            GLib.Variant.new_boolean(True),  # Default is visible
        )

        # 3D View Control Actions
        self._add_action("view_top", self.win.on_view_top)
        self._add_action("view_front", self.win.on_view_front)
        self._add_action("view_iso", self.win.on_view_iso)
        self._add_stateful_action(
            "view_toggle_perspective",
            self.win.on_view_perspective_state_change,
            GLib.Variant.new_boolean(True),  # Default is perspective
        )

        # Edit & Clipboard Actions
        self._add_action(
            "undo", lambda a, p: self.editor.history_manager.undo()
        )
        self._add_action(
            "redo", lambda a, p: self.editor.history_manager.redo()
        )
        self._add_action("cut", self.win.on_menu_cut)
        self._add_action("copy", self.win.on_menu_copy)
        self._add_action("paste", self.win.on_paste_requested)
        self._add_action("select_all", self.win.on_select_all)
        self._add_action("duplicate", self.win.on_menu_duplicate)
        self._add_action("remove", self.win.on_menu_remove)
        self._add_action("clear", self.win.on_clear_clicked)

        # Layer Management Actions
        self._add_action("layer-move-up", self.on_layer_move_up)
        self._add_action("layer-move-down", self.on_layer_move_down)
        self._add_action("add_stock", self.on_add_stock)

        # Grouping Actions
        self._add_action("group", self.on_group_action)
        self._add_action("ungroup", self.on_ungroup_action)

        # Alignment Actions
        self._add_action("align-h-center", self.on_align_h_center)
        self._add_action("align-v-center", self.on_align_v_center)
        self._add_action("align-left", self.on_align_left)
        self._add_action("align-right", self.on_align_right)
        self._add_action("align-top", self.on_align_top)
        self._add_action("align-bottom", self.on_align_bottom)
        self._add_action("spread-h", self.on_spread_h)
        self._add_action("spread-v", self.on_spread_v)
        self._add_action("layout-pixel-perfect", self.on_layout_pixel_perfect)

        # Machine Control Actions
        self._add_action("home", self.win.on_home_clicked)
        self._add_action("frame", self.win.on_frame_clicked)
        self._add_action("send", self.win.on_send_clicked)
        self._add_action("cancel", self.win.on_cancel_clicked)
        self._add_action("clear_alarm", self.win.on_clear_alarm_clicked)

        # Stateful action for the hold/pause button
        self._add_stateful_action(
            "hold",
            self.win.on_hold_state_change,
            GLib.Variant.new_boolean(False),
        )

        self.update_action_states()

    def update_action_states(self, *args, **kwargs):
        """Updates the enabled state of actions based on document state."""
        # The "Add Stock" button should always be enabled.
        self.actions["add_stock"].set_enabled(True)

    def on_add_stock(self, action, param):
        """Handler for the 'add_stock' action."""
        self.editor.stock.add_stock_item()

    def set_accelerators(self, app: Gtk.Application):
        """Sets keyboard accelerators for the application's actions."""
        app.set_accels_for_action("win.import", ["<Primary>o"])
        app.set_accels_for_action("win.export", ["<Primary>e"])
        app.set_accels_for_action("win.quit", ["<Primary>q"])
        app.set_accels_for_action("win.undo", ["<Primary>z"])
        app.set_accels_for_action(
            "win.redo", ["<Primary>y", "<Primary><Shift>z"]
        )
        app.set_accels_for_action("win.cut", ["<Primary>x"])
        app.set_accels_for_action("win.copy", ["<Primary>c"])
        app.set_accels_for_action("win.paste", ["<Primary>v"])
        app.set_accels_for_action("win.select_all", ["<Primary>a"])
        app.set_accels_for_action("win.duplicate", ["<Primary>d"])
        app.set_accels_for_action("win.remove", ["Delete"])
        app.set_accels_for_action("win.group", ["<Primary>g"])
        app.set_accels_for_action("win.ungroup", ["<Primary><Shift>g"])
        app.set_accels_for_action("win.show_3d_view", ["F12"])
        app.set_accels_for_action("win.view_top", ["1"])
        app.set_accels_for_action("win.view_front", ["2"])
        app.set_accels_for_action("win.view_iso", ["7"])
        app.set_accels_for_action("win.view_toggle_perspective", ["p"])
        app.set_accels_for_action("win.layout-pixel-perfect", ["a"])
        app.set_accels_for_action("win.machine_settings", ["<Primary>less"])
        app.set_accels_for_action("win.preferences", ["<Primary>comma"])
        app.set_accels_for_action("win.about", ["F1"])

    def get_action(self, name: str) -> Gio.SimpleAction:
        """Retrieves a registered action by its name."""
        return self.actions[name]

    def on_layer_move_up(self, action, param):
        """Handler for the 'layer-move-up' action."""
        self.editor.layer.move_selected_to_adjacent_layer(
            self.win.surface, direction=-1
        )

    def on_layer_move_down(self, action, param):
        """Handler for the 'layer-move-down' action."""
        self.editor.layer.move_selected_to_adjacent_layer(
            self.win.surface, direction=1
        )

    def on_group_action(self, action, param):
        """Handler for the 'group' action."""
        selected_elements = self.win.surface.get_selected_elements()
        if len(selected_elements) < 2:
            return

        items_to_group = [
            elem.data
            for elem in selected_elements
            if isinstance(elem.data, DocItem)
        ]
        # All items must belong to the same layer to be grouped
        parent_layer = cast(Layer, items_to_group[0].parent)
        if not parent_layer or not all(
            item.parent is parent_layer for item in items_to_group
        ):
            return

        new_group = self.editor.group.group_items(parent_layer, items_to_group)
        if new_group:
            self.win.surface.select_items([new_group])

    def on_ungroup_action(self, action, param):
        """Handler for the 'ungroup' action."""
        selected_elements = self.win.surface.get_selected_elements()

        groups_to_ungroup = [
            elem.data
            for elem in selected_elements
            if isinstance(elem.data, Group)
        ]
        if not groups_to_ungroup:
            return

        self.editor.group.ungroup_items(groups_to_ungroup)
        # The selection will be automatically updated by the history changed
        # signal handler.

    # --- Alignment Action Handlers ---

    def on_align_h_center(self, action, param):
        items = list(self.win.surface.get_selected_items())
        w, _ = self.win.surface.get_size_mm()
        self.editor.layout.center_horizontally(items, w)

    def on_align_v_center(self, action, param):
        items = list(self.win.surface.get_selected_items())
        _, h = self.win.surface.get_size_mm()
        self.editor.layout.center_vertically(items, h)

    def on_align_left(self, action, param):
        items = list(self.win.surface.get_selected_items())
        self.editor.layout.align_left(items)

    def on_align_right(self, action, param):
        items = list(self.win.surface.get_selected_items())
        w, _ = self.win.surface.get_size_mm()
        self.editor.layout.align_right(items, w)

    def on_align_top(self, action, param):
        items = list(self.win.surface.get_selected_items())
        _, h = self.win.surface.get_size_mm()
        self.editor.layout.align_top(items, h)

    def on_align_bottom(self, action, param):
        items = list(self.win.surface.get_selected_items())
        self.editor.layout.align_bottom(items)

    def on_spread_h(self, action, param):
        items = list(self.win.surface.get_selected_items())
        self.editor.layout.spread_horizontally(items)

    def on_spread_v(self, action, param):
        items = list(self.win.surface.get_selected_items())
        self.editor.layout.spread_vertically(items)

    def on_layout_pixel_perfect(self, action, param):
        items = list(self.win.surface.get_selected_items())
        self.editor.layout.layout_pixel_perfect(items)

    def _add_action(
        self,
        name: str,
        callback: Callable,
        param: Optional[GLib.VariantType] = None,
    ):
        """Helper to create, register, and store a simple Gio.SimpleAction."""
        action = Gio.SimpleAction.new(name, param)
        action.connect("activate", callback)
        self.win.add_action(action)
        self.actions[name] = action

    def _add_stateful_action(
        self, name: str, callback: Callable, initial_state: GLib.Variant
    ):
        """Helper for a stateful action, typically for toggle buttons."""
        action = Gio.SimpleAction.new_stateful(name, None, initial_state)
        # For stateful actions, we ONLY connect to 'change-state'. The default
        # 'activate' handler for boolean actions will correctly call this for
        # us.
        action.connect("change-state", callback)
        self.win.add_action(action)
        self.actions[name] = action
