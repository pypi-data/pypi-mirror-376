"""
Module to manage the processing of photoluminescence data.
"""
# pylint: disable=line-too-long,no-name-in-module, too-many-instance-attributes,import-error

import os
from PLApp.Processing.function_common import Common
from PLApp.Processing.photoluminescencegan import PhotoluminescenceGan
from PLApp.Layout.layouts_style import checkbox_style_present, checkbox_style_absent, checkbox_style_default

class PLProcessing:
    """
    Class to manage the processing of photoluminescence data.
    """
    def __init__(self, dirname, wafer_size, edge_exclusion, step, int_min,
                 int_max, ev_min, ev_max, area_min, area_max,
                 thickness_min, thickness_max, subdir, radio_buttons,
                 check_boxes, ex_and_timer, progress_dialog, wafer_slot, stats, selected_wafers):
        """
        Classe pour gérer le traitement de la photoluminescence.
        """
        self.dirname = dirname
        self.step = step
        self.radio_buttons = radio_buttons
        self.check_boxes = check_boxes
        self.check_vars = selected_wafers
        self.ex_and_timer = ex_and_timer
        self.progress_dialog = progress_dialog
        self.wafer_slot = wafer_slot
        self.stats = stats
        self.inc = None

        # Initialisation des classes de traitement
        self.common_class = Common(dirname, subdir)
        self.pl_class_gan = PhotoluminescenceGan(dirname, wafer_size,
                                                 edge_exclusion, step,
                                                 int_min, int_max, ev_min,
                                                 ev_max,
                                                 area_min, area_max,
                                                 thickness_min,
                                                 thickness_max, subdir)

    def process(self):
        "Executes the processing based on the selected radio buttons and checkboxes."
        self.inc = 0  # Progress tracker

        if self.radio_buttons["GaN - Area ratio"].isChecked():
            self.process_gan_area()
        elif self.radio_buttons["AlGaN - Al%"].isChecked():
            self.process_algan_al_percentage()
        elif self.radio_buttons["GaN - Thickness"].isChecked():
            self.process_gan_thickness()
        elif self.radio_buttons["nm to eV"].isChecked():
            self.process_conversion()
        elif self.radio_buttons["Clean"].isChecked():
            self.process_clean()
        elif self.radio_buttons["Create folders"].isChecked():
            self.process_create_folder()
            

    checkboxes = [
        ("Data processing", True), ("Autoscale mapping", True),
        ("Id. scale mapping", False), ("Id. scale mapping (auto)", True),
        ("Slot number", True), ("Stats", True)
    ]

    def update_wafers(self):
        """Update the appearance of checkboxes based on the existing
        subdirectories in the specified directory."""
        if self.dirname:
            # List the subdirectories in the specified directory
            subdirs = [d for d in os.listdir(self.dirname) if
                       os.path.isdir(os.path.join(self.dirname, d))]

            # Update the style of checkboxes based on the subdirectory presence
            for number in range(1, 27):
                checkbox = self.check_vars.get(number)
                if checkbox:
                    if str(number) in subdirs:
                        checkbox.setStyleSheet(checkbox_style_present())
                    else:
                        checkbox.setStyleSheet(checkbox_style_absent())
        else:
            # Default style for all checkboxes if no directory is specified
            for number in range(1, 27):
                checkbox = self.check_vars.get(number)
                checkbox.setStyleSheet(checkbox_style_default())

    def process_conversion(self):
        "Function to convert nm to eV."
        self.ex_and_timer("Cleaning of folders", self.common_class.reboot,
                     carac='photoluminescence')
        self.ex_and_timer("Conversion nm to eV", self.common_class.nm_to_ev,
                     ev_conversion=True)
    def process_clean(self):
        "Function to clean the folders."
        self.ex_and_timer("Cleaning of folders", self.common_class.reboot,
                         carac='photoluminescence')
    def process_create_folder(self):
        "Function to create the folders."
        self.common_class.organize_files_by_numbers()
        self.update_wafers()
    def process_gan_area(self):
        """Function to process the GaN area ratio."""
        if self.check_boxes["Data processing"].isChecked():
            self.ex_and_timer("Cleaning of folders", self.common_class.reboot,
                              carac='photoluminescence')
            self.ex_and_timer("Conversion nm to eV", self.common_class.nm_to_ev,
                              ev_conversion=True)

            if self.pl_class_gan.find_area():
                self.progress_dialog.setLabelText(
                    "Aborted : No YB")
                self.progress_dialog.setValue(self.progress_dialog.maximum())
                return
            self.inc += 1
            self.progress_dialog.setValue(self.inc)

            self.ex_and_timer("Boxplot plotting/Generate the .csv file",
                             self.common_class.plot_boxplot,mat="GaN_area")
            self.ex_and_timer("Stats files", self.common_class.stats)

        if self.check_boxes["Autoscale mapping"].isChecked():
            self.ex_and_timer("Plot AlGaN Al% w/ auto scale",
                             self.pl_class_gan.plot, "GaN_area", self.wafer_slot, False, self.stats)
            self.common_class.create_image_grid(zscale="Auto", mat="GaN_area")

        if self.check_boxes["Id. scale mapping"].isChecked():
            self.ex_and_timer("Mapping plotting (Identical scale)",
                             self.pl_class_gan.plot, "GaN_area", self.wafer_slot, 'Manual', self.stats)
            self.common_class.create_image_grid(zscale="Identical", mat="GaN_area")

        if self.check_boxes["Id. scale mapping (auto)"].isChecked():
            self.ex_and_timer("Mapping plotting (Identical scale)",
                             self.pl_class_gan.plot, "GaN_area", self.wafer_slot, 'Auto', self.stats)
            self.common_class.create_image_grid(zscale="Identical", mat="GaN_area")
    def process_gan_thickness(self):
        """Function to process the GaN thickness."""
        if self.check_boxes["Data processing"].isChecked():
            self.ex_and_timer("Cleaning of folders", self.common_class.reboot,
                              carac='photoluminescence')

            if self.pl_class_gan.plot_thickness(slot_number=self.wafer_slot):
                self.progress_dialog.setLabelText("No GaN thickness")
                self.progress_dialog.setValue(self.progress_dialog.maximum())
                return
            self.update_wafers()
            self.common_class.plot_boxplot(mat="Thickness")
            self.common_class.create_image_grid(zscale="Auto",
                                                mat="Thickness")

            self.ex_and_timer("Stats files", self.common_class.stats)

        if self.check_boxes["Id. scale mapping"].isChecked():
            self.ex_and_timer("Mapping plotting (Identical scale)",
                             self.pl_class_gan.plot, "Thickness", self.wafer_slot, 'Manual', self.stats)
            self.common_class.create_image_grid(zscale="Identical", mat="Thickness")

        if self.check_boxes["Id. scale mapping (auto)"].isChecked():
            self.ex_and_timer("Mapping plotting (Identical scale)",
                             self.pl_class_gan.plot, "Thickness", self.wafer_slot, 'Auto', self.stats)
            self.common_class.create_image_grid(zscale="Identical", mat="Thickness")
    def process_algan_al_percentage(self):
        """Traitement pour la cartographie 2D du pourcentage d'Aluminium dans AlGaN."""
        if self.check_boxes["Data processing"].isChecked():
            self.ex_and_timer("Cleaning of folders", self.common_class.reboot,
                              carac='photoluminescence')
            self.ex_and_timer("Conversion nm to eV", self.common_class.nm_to_ev,
                              ev_conversion=True)

            if self.pl_class_gan.find_xy_gan():
                self.progress_dialog.setLabelText(
                    "Aborted : No UV laser")
                self.progress_dialog.setValue(self.progress_dialog.maximum())
                return
            self.inc += 1
            self.progress_dialog.setValue(self.inc)

            self.ex_and_timer("Boxplot plotting/Generate the .csv file",
                             self.common_class.plot_boxplot, mat="AlGaN")
            self.ex_and_timer("Stats files", self.common_class.stats)

        if self.check_boxes["Autoscale mapping"].isChecked():
            self.ex_and_timer("Plot AlGaN Al% w/ auto scale",
                             self.pl_class_gan.plot, "AlGaN", self.wafer_slot, False, self.stats)
            self.common_class.create_image_grid(zscale="Auto", mat="AlGaN")

        if self.check_boxes["Id. scale mapping"].isChecked():
            self.ex_and_timer("Mapping plotting (Identical scale)",
                             self.pl_class_gan.plot, "AlGaN", self.wafer_slot, 'Manual', self.stats)
            self.common_class.create_image_grid(zscale="Identical", mat="AlGaN")

        if self.check_boxes["Id. scale mapping (auto)"].isChecked():
            self.ex_and_timer("Mapping plotting (Identical scale)",
                             self.pl_class_gan.plot, "AlGaN", self.wafer_slot, 'Identical', self.stats)
            self.common_class.create_image_grid(zscale="Identical", mat="AlGaN")

