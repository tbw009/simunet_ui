"""Application configuration dialog and defaults.

This module contains the `AppConfig` data container and the
`AppConfigDlg` dialog used to view and edit application settings
such as MQTT and AWS endpoints and Matplotlib defaults.
"""

from simunetcore.serializer import Serializer

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.dialogs import Dialog

from images import Images
from propertyeditors import *
from tkinter.font import Font


# Supported transports for MQTT
MQTT_TRANSPORT = [
    "tcp",
    "websockets",
]

# AWS regions available for selection
AWS_REGIONS = [
    "us-east-2",
    "us-east-1",
    "us-west-1",
    "us-west-2",
    "af-south-1",
    "ap-east-1",
    "ap-south-2",
    "ap-southeast-3",
    "ap-south-1",
    "ap-northeast-3",
    "ap-northeast-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ca-central-1",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-south-1",
    "eu-west-3",
    "eu-south-2",
    "eu-north-1",
    "eu-central-2",
    "me-south-1",
    "me-central-1",
    "sa-east-1",
    "us-gov-east-1",
    "us-gov-west-1",
]


class AppConfig(Serializer):
    """Container for application configuration defaults.

    Instances of this class hold editable configuration values for
    MQTT and AWS endpoints as well as plotting (Matplotlib) defaults
    and UI style values.
    """

    def __init__(self):
        """Create a new AppConfig with sensible defaults."""

        Serializer.__init__(self)

        # MQTT endpoint defaults
        self.mqtt_endpoint = {
            "broker": "mqtt.broker.url",
            "port": 8883,
            "transport": "tcp",
            "tls": True,
            "username": "username",
            "password": "password",
        }

        # AWS endpoint defaults
        self.aws_endpoint = {
            "aws_id": "aws_id",
            "aws_key": "aws_key",
            "region": "eu-central-1",
            "max_attempts": 0,
            "read_timeout": 900,
            "connect_timeout": 60,
        }

        # Matplotlib rcParams defaults
        self.rc_params = {
            "font.sans-serif": "TkDefaultFont",
            "font.size": 9,
        }

        # ttkbootstrap style defaults
        self.style = {"themename": "simunet"}

        # Pane settings
        self.pane_states = {
            "pane": [250, 900],
            "pane_middle": [500],
            "pane_right": [500]
        }

class AppConfigDlg(Dialog):
    """Dialog for viewing and editing the `AppConfig` values.

    The dialog exposes notebook pages for connections and chart
    settings and writes back values when the user accepts the dialog.
    """

    def __init__(self, parent=None, app_config=None):
        """Initialize the settings dialog.

        Args:
            parent: Parent widget for the dialog.
            app_config: Optional `AppConfig` instance to edit. If not
                provided a default `AppConfig` is created.
        """
        super().__init__(parent=parent, title="Settings")

        # Store app config if given or create a new default config
        if app_config:
            self.app_config = app_config
        else:
            self.app_config = AppConfig()

    def create_body(self, master):
        """Build the dialog body with a notebook and its pages."""

        # Create parent notebook
        self.notebook = ttk.Notebook(master, bootstyle=tk.LIGHT)
        self.notebook.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, padx=10, pady=(10, 0))

        # Create pages
        self.create_connections_page()
        self.create_matplotlib_page()

        # Set tool window attribute
        self._toplevel.wm_attributes("-toolwindow", "true")
    
    def create_matplotlib_page(self):
        """Create the Charts page with Matplotlib-related settings."""

        # Container frame
        container = ttk.Frame(self.notebook, padding=(5, 10))
        self.notebook.add(container, image=Images().system["Charts"], text="Charts", compound=tk.LEFT)

        # Matplotlib label frame
        matplotlib_frame = ttk.Labelframe(container, text="Chart settings", padding=(5, 10))
        matplotlib_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        # Insert labels
        lbl_font = ttk.Label(master=matplotlib_frame, text="Default font")
        lbl_font.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        # Insert entries
        self.entry_font = FontPopupEntry(
            matplotlib_frame,
            Font(
                family=self.app_config.rc_params["font.sans-serif"],
                size=self.app_config.rc_params["font.size"],
            ),
        )
        self.entry_font.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=2)

        # Configure grids
        matplotlib_frame.columnconfigure(1, weight=1)
        container.columnconfigure(0, weight=1)

    def create_connections_page(self):
        """Create the Connections page with MQTT and AWS settings."""

        # Container frame
        container = ttk.Frame(self.notebook, padding=(5, 10))
        self.notebook.add(container, image=Images().system["Security"], text="Connections", compound=tk.LEFT)

        # mqtt label frame
        mqtt_frame = ttk.Labelframe(container, text="MQTT settings", padding=(5, 10))
        mqtt_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        # Insert labels
        lbl_user = ttk.Label(master=mqtt_frame, text="Username")
        lbl_user.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        lbl_passwd = ttk.Label(master=mqtt_frame, text="Password")
        lbl_passwd.grid(row=1, column=0, sticky=tk.NSEW, padx=5)

        lbl_broker = ttk.Label(master=mqtt_frame, text="MQTT-Broker")
        lbl_broker.grid(row=2, column=0, sticky=tk.NSEW, padx=5)

        lbl_port = ttk.Label(master=mqtt_frame, text="MQTT-Port")
        lbl_port.grid(row=3, column=0, sticky=tk.NSEW, padx=5)

        lbl_transport = ttk.Label(master=mqtt_frame, text="Transport")
        lbl_transport.grid(row=4, column=0, sticky=tk.NSEW, padx=5)

        lbl_tls = ttk.Label(master=mqtt_frame, text="TLS")
        lbl_tls.grid(row=5, column=0, sticky=tk.NSEW, padx=5)

        # Insert entries
        self.entry_user = ttk.Entry(master=mqtt_frame)
        self.entry_user.insert(tk.END, self.app_config.mqtt_endpoint["username"])
        self.entry_user.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_passwd = ttk.Entry(master=mqtt_frame, show="•")
        self.entry_passwd.insert(tk.END, self.app_config.mqtt_endpoint["password"])
        self.entry_passwd.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_broker = ttk.Entry(master=mqtt_frame)
        self.entry_broker.insert(tk.END, self.app_config.mqtt_endpoint["broker"])
        self.entry_broker.grid(row=2, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_port = ttk.Spinbox(master=mqtt_frame, from_=1, to=9999)
        self.entry_port.set(self.app_config.mqtt_endpoint["port"])
        self.entry_port.grid(row=3, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_transport = ttk.Combobox(master=mqtt_frame, state=tk.READONLY, values=MQTT_TRANSPORT)
        self.entry_transport.current(MQTT_TRANSPORT.index(self.app_config.mqtt_endpoint["transport"]))
        self.entry_transport.grid(row=4, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_tls = ttk.Checkbutton(
            master=mqtt_frame,
            bootstyle="round-toggle",
            command=lambda: self.entry_tls.config(text=str(self.entry_tls.instate(["selected"]))),
        )
        if self.app_config.mqtt_endpoint["tls"]:
            self.entry_tls.state(["selected"])
        else:
            self.entry_tls.state(["!selected"])
        self.entry_tls.config(text=str(self.entry_tls.instate(["selected"])))
        self.entry_tls.grid(row=5, column=1, sticky=tk.NSEW, padx=5, pady=10)

        # aws lambda label frame
        lambda_frame = ttk.Labelframe(container, text="AWS settings", padding=(5, 10))
        lambda_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=5)

        # Insert labels
        lbl_id = ttk.Label(master=lambda_frame, text="AWS-Id")
        lbl_id.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        lbl_key = ttk.Label(master=lambda_frame, text="AWS-Key")
        lbl_key.grid(row=1, column=0, sticky=tk.NSEW, padx=5)

        lbl_region = ttk.Label(master=lambda_frame, text="Region")
        lbl_region.grid(row=2, column=0, sticky=tk.NSEW, padx=5)

        lbl_attempts = ttk.Label(master=lambda_frame, text="Max. attempts")
        lbl_attempts.grid(row=3, column=0, sticky=tk.NSEW, padx=5)

        lbl_read_timeout = ttk.Label(master=lambda_frame, text="Read timeout")
        lbl_read_timeout.grid(row=4, column=0, sticky=tk.NSEW, padx=5)

        lbl_connect_timeout = ttk.Label(master=lambda_frame, text="Connect timeout")
        lbl_connect_timeout.grid(row=5, column=0, sticky=tk.NSEW, padx=5)

        # Insert entries
        self.entry_id = ttk.Entry(master=lambda_frame)
        self.entry_id.insert(tk.END, self.app_config.aws_endpoint["aws_id"])
        self.entry_id.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_key = ttk.Entry(master=lambda_frame, show="•")
        self.entry_key.insert(tk.END, self.app_config.aws_endpoint["aws_key"])
        self.entry_key.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_region = ttk.Combobox(master=lambda_frame, state=tk.READONLY, values=AWS_REGIONS)
        self.entry_region.current(AWS_REGIONS.index(self.app_config.aws_endpoint["region"]))
        self.entry_region.grid(row=2, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_attepmts = ttk.Spinbox(master=lambda_frame, from_=0, to=10)
        self.entry_attepmts.set(self.app_config.aws_endpoint["max_attempts"])
        self.entry_attepmts.grid(row=3, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_read_timeout = ttk.Spinbox(master=lambda_frame, from_=0, to=900)
        self.entry_read_timeout.set(self.app_config.aws_endpoint["read_timeout"])
        self.entry_read_timeout.grid(row=4, column=1, sticky=tk.NSEW, padx=5, pady=2)

        self.entry_connect_timeout = ttk.Spinbox(master=lambda_frame, from_=0, to=60)
        self.entry_connect_timeout.set(self.app_config.aws_endpoint["connect_timeout"])
        self.entry_connect_timeout.grid(row=5, column=1, sticky=tk.NSEW, padx=5, pady=2)

        # Configure grids
        mqtt_frame.columnconfigure(1, weight=1)
        lambda_frame.columnconfigure(1, weight=1)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

    def create_buttonbox(self, master):
        """Create dialog buttons (OK/Cancel)."""

        container = ttk.Frame(master, padding=(5, 10))
        container.pack(side=tk.BOTTOM, fill=tk.X, anchor=tk.S)

        # OK button
        btn_ok = ttk.Button(
            container, 
            bootstyle=tk.PRIMARY, 
            takefocus=False, 
            width=6, 
            text="OK",
        )
        btn_ok.bind("<Return>", lambda _: btn_ok.invoke())
        btn_ok.configure(command=lambda b=btn_ok: self.on_button_press(b))
        btn_ok.pack(padx=5, side=tk.RIGHT)

        # Cancel button
        btn_cancel = ttk.Button(
            container, 
            bootstyle=tk.SECONDARY, 
            takefocus=False, 
            width=6, 
            text="Cancel",
        )
        btn_cancel.bind("<Return>", lambda _: btn_cancel.invoke())
        btn_cancel.configure(command=lambda b=btn_cancel: self.on_button_press(b))
        btn_cancel.pack(padx=5, side=tk.RIGHT)

    def on_button_press(self, button):
        """Handle button presses and persist values on OK."""

        self._result = button.cget("text")
        if self._result == "OK":
            # Store MQTT Endpoint
            self.app_config.mqtt_endpoint["broker"] = self.entry_broker.get()
            self.app_config.mqtt_endpoint["port"] = int(self.entry_port.get())
            self.app_config.mqtt_endpoint["username"] = self.entry_user.get()
            self.app_config.mqtt_endpoint["password"] = self.entry_passwd.get()
            self.app_config.mqtt_endpoint["transport"] = self.entry_transport.get()
            self.app_config.mqtt_endpoint["tls"] = self.entry_tls.instate(["selected"])

            # Store AWS Endpoint
            self.app_config.aws_endpoint["aws_id"] = self.entry_id.get()
            self.app_config.aws_endpoint["aws_key"] = self.entry_key.get()
            self.app_config.aws_endpoint["region"] = self.entry_region.get()
            self.app_config.aws_endpoint["max_attempts"] = int(self.entry_attepmts.get())
            self.app_config.aws_endpoint["read_timeout"] = int(self.entry_read_timeout.get())
            self.app_config.aws_endpoint["connect_timeout"] = int(self.entry_connect_timeout.get())

            # Store matplotlib params
            self.app_config.rc_params["font.sans-serif"] = self.entry_font.get_value()["family"]
            self.app_config.rc_params["font.size"] = int(self.entry_font.get_value()["size"])

        # Close window
        self.close()

if __name__ == "__main__":
    dlg = AppConfigDlg()
    dlg.show()
    print(dlg.app_config)

