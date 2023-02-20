BUTTON = """
QPushButton:hover {
    color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f6eeff, stop:1 #ffffff);
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5dbe70, stop:1 #7bcf88);
    border-radius: 6px;
    border: 2px solid #0d3614;
}
QPushButton {
    color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f6eeff);
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a925e, stop:1 #317c4f);
    border-radius: 6px;
    border: 2px solid #0d3614;
}
QPushButton:pressed {
    color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f6eeff);
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #316849, stop:1 #315a43);
    border-radius: 6px;
    border: 2px solid #0d3614;
}
"""

BACKGROUND = """
background-color: #21252b;
"""

TEXT_AREA = """
background-color: #282c34;
color: #c5c9d8;
padding-top: 5px; padding-left: 10px;
border-radius: 7px;
"""

TEXT_AREA_SMALL = """
background-color: #282c34;
color: #c5c9d8;
border-radius: 2px;
"""

MESSAGES_MY = """
color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f6eeff);
background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a925e, stop:1 #317c4f);
border: 2px solid #3d3145;
border-radius: 15px;
padding-top: 8px;
padding-left: 7px;
padding-bottom: 8px;
padding-right: 7px;
"""

MESSAGES_OTHER = """
color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f6eeff);
background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6915bf, stop:1 #731ac2);
border: 1px solid #3d3145;
border-radius: 15px;
padding-top: 8px;
padding-left: 7px;
padding-bottom: 8px;
padding-right: 7px;
"""

LIST_AREA = """
QListWidget {
    background-color: #282c34;
    color: #c5c9d8;
    border-radius: 7px;
};
background-color: #282c34;
color: #c5c9d8;
border-radius: 0px;
"""

USER_SELECTED = """
color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f6eeff);
background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a925e, stop:1 #317c4f);
border: 2px solid #3d3145;
border-radius: 8px;
padding-top: 8px;
padding-left: 7px;
padding-bottom: 8px;
padding-right: 7px;
margin: 0px;
"""

USERS = """
color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f6eeff);
background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6915bf, stop:1 #731ac2);
border: 1px solid #270b47;
border-radius: 8px;
padding-top: 8px;
padding-left: 7px;
padding-bottom: 8px;
padding-right: 7px;
margin: 0px;
"""

WINDOW = """
QMainWindow {
    background-color: #21252b;
    color: #c5c9d8;
}
"""
