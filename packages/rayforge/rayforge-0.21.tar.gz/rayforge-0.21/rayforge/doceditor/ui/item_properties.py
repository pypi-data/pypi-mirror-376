import logging
from gi.repository import Gtk, Adw, Gio
from typing import Optional, Tuple, List, cast
from pathlib import Path

from ...core.stock import StockItem
from ...core.group import Group
from ...shared.ui.expander import Expander
from ...config import config
from ...core.workpiece import WorkPiece
from ...core.item import DocItem
from ...shared.util.adwfix import get_spinrow_float
from ...icons import get_icon
from ...undo import ChangePropertyCommand


logger = logging.getLogger(__name__)
default_dim = 100, 100


class DocItemPropertiesWidget(Expander):
    def __init__(
        self,
        items: Optional[List[DocItem]] = None,
        *args,
        **kwargs,
    ):
        # Initialize the parent Expander widget
        super().__init__(*args, **kwargs)

        self.items = items or []
        self._in_update = False

        # Set the title and default state on the Expander itself
        self.set_title(_("Item Properties"))
        self.set_expanded(True)  # Expanded by default

        # Create a ListBox to hold all the property rows. This replaces the
        # Adw.ExpanderRow's internal list.
        rows_container = Gtk.ListBox()
        rows_container.set_selection_mode(Gtk.SelectionMode.NONE)
        self.set_child(rows_container)

        # Source File Row
        self.source_file_row = Adw.ActionRow(
            title=_("Source File"),
            visible=False,  # Hidden by default
        )
        self.open_source_button = Gtk.Button()
        self.open_source_button.set_child(get_icon("open-in-new-symbolic"))
        self.open_source_button.set_valign(Gtk.Align.CENTER)
        self.open_source_button.set_tooltip_text(_("Show in File Browser"))
        self.open_source_button.connect(
            "clicked", self._on_open_source_file_clicked
        )
        self.source_file_row.add_suffix(self.open_source_button)
        rows_container.append(self.source_file_row)

        # X Position Entry
        self.x_row = Adw.SpinRow(
            title=_("X Position"),
            subtitle=_("Zero is on the left side"),
            adjustment=Gtk.Adjustment.new(0, -10000, 10000, 1.0, 1, 0),
        )
        self.x_row.set_digits(2)
        self.x_row.connect("notify::value", self._on_x_changed)
        rows_container.append(self.x_row)

        # Y Position Entry
        self.y_row = Adw.SpinRow(
            title=_("Y Position"),
            adjustment=Gtk.Adjustment.new(0, -10000, 10000, 1.0, 1, 0),
        )
        self.y_row.set_digits(2)
        self.y_row.connect("notify::value", self._on_y_changed)
        rows_container.append(self.y_row)

        # Fixed Ratio Switch
        self.fixed_ratio_switch = Adw.SwitchRow(
            title=_("Fixed Ratio"), active=True
        )
        self.fixed_ratio_switch.connect(
            "notify::active", self._on_fixed_ratio_toggled
        )
        rows_container.append(self.fixed_ratio_switch)

        # Width Entry
        self.width_row = Adw.SpinRow(
            title=_("Width"),
            adjustment=Gtk.Adjustment.new(10, 1, 10000, 1.0, 1, 0),
        )
        self.width_row.set_digits(2)
        self.width_row.connect("notify::value", self._on_width_changed)
        rows_container.append(self.width_row)

        # Height Entry
        self.height_row = Adw.SpinRow(
            title=_("Height"),
            adjustment=Gtk.Adjustment.new(10, 1, 10000, 1.0, 1, 0),
        )
        self.height_row.set_digits(2)
        self.height_row.connect("notify::value", self._on_height_changed)
        rows_container.append(self.height_row)

        # Angle Entry
        self.angle_row = Adw.SpinRow(
            title=_("Angle"),
            subtitle=_("Clockwise is positive"),
            adjustment=Gtk.Adjustment.new(0, -360, 360, 1, 10, 0),
            digits=2,
        )
        self.angle_row.connect("notify::value", self._on_angle_changed)
        rows_container.append(self.angle_row)

        # Shear Entry
        self.shear_row = Adw.SpinRow(
            title=_("Shear"),
            subtitle=_("Horizontal shear angle"),
            adjustment=Gtk.Adjustment.new(0, -85, 85, 1, 10, 0),
            digits=2,
        )
        self.shear_row.connect("notify::value", self._on_shear_changed)
        rows_container.append(self.shear_row)

        # --- Reset Buttons ---
        # Note: These are now added as suffixes to their respective rows.
        def create_reset_button(tooltip_text, on_clicked):
            button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
            button.set_valign(Gtk.Align.CENTER)
            button.set_tooltip_text(tooltip_text)
            button.connect("clicked", on_clicked)
            return button

        self.reset_width_button = create_reset_button(
            _("Reset to natural width"),
            lambda btn: self._on_reset_dimension_clicked(btn, "width"),
        )
        self.width_row.add_suffix(self.reset_width_button)

        self.reset_height_button = create_reset_button(
            _("Reset to natural height"),
            lambda btn: self._on_reset_dimension_clicked(btn, "height"),
        )
        self.height_row.add_suffix(self.reset_height_button)

        self.reset_aspect_button = create_reset_button(
            _("Reset to natural aspect ratio"), self._on_reset_aspect_clicked
        )
        self.fixed_ratio_switch.add_suffix(self.reset_aspect_button)

        self.reset_angle_button = create_reset_button(
            _("Reset angle to 0°"), self._on_reset_angle_clicked
        )
        self.angle_row.add_suffix(self.reset_angle_button)

        self.reset_shear_button = create_reset_button(
            _("Reset shear to 0°"), self._on_reset_shear_clicked
        )
        self.shear_row.add_suffix(self.reset_shear_button)

        self.set_items(items)

    def _calculate_new_size_with_ratio(
        self, item: DocItem, value: float, changed_dim: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculates new width and height maintaining aspect ratio."""
        # This now works for both WorkPiece and StockItem via duck-typing.
        aspect_ratio = None
        if isinstance(item, (WorkPiece, StockItem)):
            aspect_ratio = item.get_current_aspect_ratio()

        if not aspect_ratio:
            return None, None

        width_min = self.width_row.get_adjustment().get_lower()
        height_min = self.height_row.get_adjustment().get_lower()

        if changed_dim == "width":
            new_width = value
            new_height = new_width / aspect_ratio
            if new_height < height_min:
                new_height = height_min
                new_width = new_height * aspect_ratio
        else:  # changed_dim == 'height'
            new_height = value
            new_width = new_height * aspect_ratio
            if new_width < width_min:
                new_width = width_min
                new_height = new_width / aspect_ratio

        return new_width, new_height

    def _apply_and_add_resize_cmd(
        self, transaction, item: DocItem, new_size: Tuple[float, float]
    ):
        """
        Applies a resize to a single item and adds the corresponding
        undo command to the active transaction.
        """
        if not item or not item.doc:
            return

        old_matrix = item.matrix.copy()
        # The set_size method will rebuild the matrix, preserving pos/angle
        item.set_size(*new_size)
        new_matrix = item.matrix.copy()

        # If the matrix didn't actually change, do nothing.
        if old_matrix == new_matrix:
            return

        cmd = ChangePropertyCommand(
            target=item,
            property_name="matrix",
            new_value=new_matrix,
            old_value=old_matrix,
            name=_("Resize item"),
        )
        transaction.add(cmd)

    def _on_width_changed(self, spin_row, GParamSpec):
        logger.debug(f"Width changed to {spin_row.get_value()}")
        if self._in_update or not self.items:
            return
        self._in_update = True
        try:
            new_width_from_ui = get_spinrow_float(self.width_row)
            if new_width_from_ui is None:
                return

            doc = self.items[0].doc
            if not doc:
                return

            # Group all changes into a single transaction
            with doc.history_manager.transaction(_("Resize item(s)")) as t:
                # Use the first item to update the UI height if ratio is fixed
                if self.fixed_ratio_switch.get_active():
                    first_item = self.items[0]
                    w, h = self._calculate_new_size_with_ratio(
                        first_item, new_width_from_ui, "width"
                    )
                    if w is not None and h is not None:
                        self.height_row.set_value(h)
                        self.width_row.set_value(w)

                # Now apply to all items
                for item in self.items:
                    new_width = new_width_from_ui
                    new_height = item.size[1]

                    if self.fixed_ratio_switch.get_active():
                        w, h = self._calculate_new_size_with_ratio(
                            item, new_width, "width"
                        )
                        if w is not None and h is not None:
                            new_width, new_height = w, h

                    self._apply_and_add_resize_cmd(
                        t, item, (new_width, new_height)
                    )
        finally:
            self._in_update = False

    def _on_height_changed(self, spin_row, GParamSpec):
        logger.debug(f"Height changed to {spin_row.get_value()}")
        if self._in_update or not self.items:
            return
        self._in_update = True
        try:
            new_height_from_ui = get_spinrow_float(self.height_row)
            if new_height_from_ui is None:
                return

            doc = self.items[0].doc
            if not doc:
                return

            # Group all changes into a single transaction
            with doc.history_manager.transaction(_("Resize item(s)")) as t:
                # Use the first item to update UI width if ratio is fixed
                if self.fixed_ratio_switch.get_active():
                    first_item = self.items[0]
                    w, h = self._calculate_new_size_with_ratio(
                        first_item, new_height_from_ui, "height"
                    )
                    if w is not None and h is not None:
                        self.width_row.set_value(w)
                        self.height_row.set_value(h)

                # Now apply to all items
                for item in self.items:
                    new_height = new_height_from_ui
                    new_width = item.size[0]

                    if self.fixed_ratio_switch.get_active():
                        w, h = self._calculate_new_size_with_ratio(
                            item, new_height, "height"
                        )
                        if w is not None and h is not None:
                            new_width, new_height = w, h

                    self._apply_and_add_resize_cmd(
                        t, item, (new_width, new_height)
                    )
        finally:
            self._in_update = False

    def _on_x_changed(self, spin_row, GParamSpec):
        logger.debug(f"X position changed to {spin_row.get_value()}")
        if self._in_update or not self.items:
            return
        self._in_update = True
        try:
            new_x_machine = get_spinrow_float(self.x_row)
            if new_x_machine is None:
                return
            doc = self.items[0].doc
            if not doc:
                return

            with doc.history_manager.transaction(_("Move item")) as t:
                for item in self.items:
                    old_matrix = item.matrix.copy()
                    current_pos_world = item.pos
                    # X is the same in machine and model coordinates
                    new_pos_world = (new_x_machine, current_pos_world[1])
                    item.pos = new_pos_world
                    new_matrix = item.matrix.copy()

                    if old_matrix == new_matrix:
                        continue

                    cmd = ChangePropertyCommand(
                        item, "matrix", new_matrix, old_value=old_matrix
                    )
                    t.add(cmd)
        finally:
            self._in_update = False

    def _on_y_changed(self, spin_row, GParamSpec):
        logger.debug(f"Y position changed to {spin_row.get_value()}")
        if self._in_update or not self.items:
            return
        self._in_update = True
        try:
            new_y_machine = get_spinrow_float(self.y_row)
            if new_y_machine is None:
                return
            doc = self.items[0].doc
            if not doc:
                return

            with doc.history_manager.transaction(_("Move item")) as t:
                for item in self.items:
                    old_matrix = item.matrix.copy()
                    pos_world = item.pos
                    size_world = item.size

                    x_world = pos_world[0]
                    y_world = 0.0

                    if config.machine and config.machine.y_axis_down:
                        machine_height = config.machine.dimensions[1]
                        y_world = (
                            machine_height - new_y_machine - size_world[1]
                        )
                    else:
                        y_world = new_y_machine

                    item.pos = (x_world, y_world)
                    new_matrix = item.matrix.copy()

                    if old_matrix == new_matrix:
                        continue

                    cmd = ChangePropertyCommand(
                        item, "matrix", new_matrix, old_value=old_matrix
                    )
                    t.add(cmd)
        finally:
            self._in_update = False

    def _on_angle_changed(self, spin_row, GParamSpec):
        if self._in_update or not self.items:
            return
        self._in_update = True
        try:
            new_angle_from_ui = spin_row.get_value()
            new_angle = -new_angle_from_ui

            doc = self.items[0].doc
            if not doc:
                for item in self.items:
                    item.angle = new_angle
                return

            with doc.history_manager.transaction(_("Change item angle")) as t:
                for item in self.items:
                    old_matrix = item.matrix.copy()
                    item.angle = new_angle
                    new_matrix = item.matrix.copy()

                    if old_matrix == new_matrix:
                        continue

                    cmd = ChangePropertyCommand(
                        item, "matrix", new_matrix, old_value=old_matrix
                    )
                    t.add(cmd)
        finally:
            self._in_update = False

    def _on_shear_changed(self, spin_row, GParamSpec):
        if self._in_update or not self.items:
            return
        self._in_update = True
        try:
            new_shear_from_ui = spin_row.get_value()

            doc = self.items[0].doc
            if not doc:
                for item in self.items:
                    item.shear = new_shear_from_ui
                return

            with doc.history_manager.transaction(_("Change item shear")) as t:
                for item in self.items:
                    old_matrix = item.matrix.copy()
                    item.shear = new_shear_from_ui
                    new_matrix = item.matrix.copy()

                    if old_matrix == new_matrix:
                        continue

                    cmd = ChangePropertyCommand(
                        item, "matrix", new_matrix, old_value=old_matrix
                    )
                    t.add(cmd)
        finally:
            self._in_update = False

    def _on_fixed_ratio_toggled(self, switch_row, GParamSpec):
        logger.debug(f"Fixed ratio toggled: {switch_row.get_active()}")
        # Check if the primary selected item is a workpiece or stock item
        is_ratio_lockable = self.items and isinstance(
            self.items[0], (WorkPiece, StockItem)
        )
        if not is_ratio_lockable:
            # For groups or multi-select, lock-ratio doesn't have a clear
            # definition of 'natural aspect', so we disable it.
            switch_row.set_sensitive(False)
        else:
            switch_row.set_sensitive(True)

    def _on_open_source_file_clicked(self, button):
        if len(self.items) != 1 or not isinstance(self.items[0], WorkPiece):
            return

        workpiece = cast(WorkPiece, self.items[0])
        file_path = Path(workpiece.source_file)

        if file_path.is_file():
            try:
                gio_file = Gio.File.new_for_path(str(file_path.resolve()))
                launcher = Gtk.FileLauncher.new(gio_file)
                window = cast(Gtk.Window, self.get_ancestor(Gtk.Window))
                launcher.open_containing_folder(window, None, None)
            except Exception as e:
                logger.error(f"Failed to show file in browser: {e}")

    def _on_reset_aspect_clicked(self, button):
        if not self.items:
            return
        doc = self.items[0].doc
        if not doc:
            return

        with doc.history_manager.transaction(
            _("Reset item aspect ratio")
        ) as t:
            for item in self.items:
                if not isinstance(item, (WorkPiece, StockItem)):
                    continue

                current_size = item.size
                current_width = current_size[0]
                default_aspect = item.get_natural_aspect_ratio()
                if not default_aspect or default_aspect == 0:
                    continue

                new_height = current_width / default_aspect
                new_size = (current_width, new_height)

                if new_size == current_size:
                    continue

                self._apply_and_add_resize_cmd(t, item, new_size)

    def _on_reset_dimension_clicked(self, button, dimension_to_reset: str):
        if not self.items:
            return

        doc = self.items[0].doc
        if not doc:
            return

        transaction_name = (
            _("Reset item width")
            if dimension_to_reset == "width"
            else _("Reset item height")
        )
        with doc.history_manager.transaction(transaction_name) as t:
            bounds = (
                config.machine.dimensions if config.machine else default_dim
            )
            for item in self.items:
                if not isinstance(item, (WorkPiece, StockItem)):
                    continue

                natural_width, natural_height = item.get_default_size(*bounds)
                current_width, current_height = item.size

                new_width = current_width
                new_height = current_height

                if dimension_to_reset == "width":
                    new_width = natural_width
                    if self.fixed_ratio_switch.get_active():
                        aspect = item.get_natural_aspect_ratio()
                        if aspect and new_width > 1e-9:
                            new_height = new_width / aspect
                else:  # dimension_to_reset == "height"
                    new_height = natural_height
                    if self.fixed_ratio_switch.get_active():
                        aspect = item.get_natural_aspect_ratio()
                        if aspect and new_height > 1e-9:
                            new_width = new_height * aspect

                new_size = (new_width, new_height)

                if new_size == item.size:
                    continue

                self._apply_and_add_resize_cmd(t, item, new_size)

    def _on_reset_angle_clicked(self, button):
        if not self.items:
            return
        doc = self.items[0].doc
        if not doc:
            return

        with doc.history_manager.transaction(_("Reset item angle")) as t:
            for item in self.items:
                if item.angle == 0.0:
                    continue
                old_matrix = item.matrix.copy()
                item.angle = 0.0
                new_matrix = item.matrix.copy()
                cmd = ChangePropertyCommand(
                    item, "matrix", new_matrix, old_value=old_matrix
                )
                t.add(cmd)

    def _on_reset_shear_clicked(self, button):
        if not self.items:
            return
        doc = self.items[0].doc
        if not doc:
            return

        with doc.history_manager.transaction(_("Reset item shear")) as t:
            for item in self.items:
                if item.shear == 0.0:
                    continue
                old_matrix = item.matrix.copy()
                item.shear = 0.0
                new_matrix = item.matrix.copy()
                cmd = ChangePropertyCommand(
                    item, "matrix", new_matrix, old_value=old_matrix
                )
                t.add(cmd)

    def _on_item_data_changed(self, item):
        """
        Handles data changes from the DocItem model. This will now be
        triggered for both size and transform changes.
        """
        if self._in_update:
            return
        logger.debug(f"Item data changed: {item.name}")
        self._update_ui_from_items()

    def set_items(self, items: Optional[List[DocItem]]):
        for item in self.items:
            item.updated.disconnect(self._on_item_data_changed)
            item.transform_changed.disconnect(self._on_item_data_changed)

        self.items = items or []

        count = len(self.items)
        if count == 1:
            self.set_subtitle(_("1 item selected"))
        else:
            self.set_subtitle(_(f"{count} items selected"))

        for item in self.items:
            item.updated.connect(self._on_item_data_changed)
            item.transform_changed.connect(self._on_item_data_changed)

        self._update_ui_from_items()

    def _update_ui_from_items(self):
        logger.debug(f"Updating UI for items: {self.items}")
        if not self.items:
            self.set_sensitive(False)
            return

        self.set_sensitive(True)
        item = self.items[0]

        self._in_update = True
        try:
            # Determine selection type and update title
            if len(self.items) > 1:
                self.set_title(_("Multiple Items"))
            elif isinstance(item, StockItem):
                self.set_title(_("Stock Properties"))
            elif isinstance(item, WorkPiece):
                self.set_title(_("Workpiece Properties"))
            elif isinstance(item, Group):
                self.set_title(_("Group Properties"))
            else:
                self.set_title(_("Item Properties"))

            bounds = (
                config.machine.dimensions if config.machine else default_dim
            )
            y_axis_down = (
                config.machine.y_axis_down if config.machine else False
            )
            size_world = item.size
            pos_world = item.pos
            angle_local = item.angle
            shear_local = item.shear

            if y_axis_down:
                self.y_row.set_subtitle(_("Zero is at the top"))
                machine_height = bounds[1]
                pos_machine_x = pos_world[0]
                pos_machine_y = machine_height - pos_world[1] - size_world[1]
            else:
                self.y_row.set_subtitle(_("Zero is at the bottom"))
                pos_machine_x, pos_machine_y = pos_world

            self.width_row.set_value(size_world[0])
            self.height_row.set_value(size_world[1])
            self.x_row.set_value(pos_machine_x)
            self.y_row.set_value(pos_machine_y)
            self.angle_row.set_value(-angle_local)
            self.shear_row.set_value(shear_local)

            is_single_workpiece = len(self.items) == 1 and isinstance(
                item, WorkPiece
            )
            is_single_stockitem = len(self.items) == 1 and isinstance(
                item, StockItem
            )
            is_single_item_with_size = (
                is_single_workpiece or is_single_stockitem
            )

            # Show/hide controls based on selection type
            self.source_file_row.set_visible(is_single_workpiece)
            self.fixed_ratio_switch.set_sensitive(is_single_item_with_size)
            self.reset_width_button.set_sensitive(is_single_item_with_size)
            self.reset_height_button.set_sensitive(is_single_item_with_size)
            self.reset_aspect_button.set_sensitive(is_single_item_with_size)

            is_group = isinstance(item, Group)
            self.shear_row.set_visible(not is_group)

            if is_single_item_with_size:
                # This works for both WorkPiece and StockItem
                assert isinstance(item, (WorkPiece, StockItem))
                natural_width, natural_height = item.get_default_size(*bounds)
                self.width_row.set_subtitle(
                    _("Natural: {val:.2f}").format(val=natural_width)
                )
                self.height_row.set_subtitle(
                    _("Natural: {val:.2f}").format(val=natural_height)
                )
            else:
                self.width_row.set_subtitle("")
                self.height_row.set_subtitle("")

            if is_single_workpiece:
                workpiece = cast(WorkPiece, item)
                try:
                    file_path = Path(workpiece.source_file)
                    if file_path.is_file():
                        self.source_file_row.set_subtitle(file_path.name)
                        self.open_source_button.set_sensitive(True)
                    else:
                        self.source_file_row.set_subtitle(
                            _("{name} (not found)").format(name=file_path.name)
                        )
                        self.open_source_button.set_sensitive(False)
                except (TypeError, ValueError):
                    self.open_source_button.set_sensitive(False)

        finally:
            self._in_update = False
