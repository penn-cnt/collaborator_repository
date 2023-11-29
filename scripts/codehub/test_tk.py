import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QRadioButton, QPushButton, QHBoxLayout, QButtonGroup

class RadioButtonWindow(QWidget):
    def __init__(self, label_options, default_selections, parent=None):
        super(RadioButtonWindow, self).__init__(parent)

        self.label_options = label_options
        self.default_selections = default_selections
        self.radio_button_groups = {}

        self.init_ui()

    def init_ui(self):
        # Set window size
        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('Radio Button Window')

        # Create layout
        layout = QVBoxLayout()

        for label_text in self.label_options:
            label = QLabel(label_text, self)
            layout.addWidget(label)

            # Create radio buttons
            radio_button_layout = QHBoxLayout()
            radio_group = QButtonGroup(self)
            self.radio_button_groups[label_text] = radio_group

            for i in range(3):
                radio_button = QRadioButton(f'Option {i+1}', self)
                radio_button_layout.addWidget(radio_button)
                radio_group.addButton(radio_button)

                # Set default selection
                if self.default_selections.get(label_text, -1) == i:
                    radio_button.setChecked(True)

            layout.addLayout(radio_button_layout)

        # Create Save button
        save_button = QPushButton('Save and Close', self)
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)

        # Set main layout
        self.setLayout(layout)

    def save_and_close(self):
        selections = {}
        for label_text, radio_group in self.radio_button_groups.items():
            selected_button = radio_group.checkedButton()
            if selected_button:
                selections[label_text] = radio_group.buttons().index(selected_button)

        print("Selections:", selections)
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    label_options = ['Label 1', 'Label 2', 'Label 3']
    default_selections = {'Label 1': 1, 'Label 2': 0, 'Label 3': 2}

    window = RadioButtonWindow(label_options, default_selections)
    window.show()

    sys.exit(app.exec_())
