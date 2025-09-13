import ipywidgets as widgets
from IPython.display import display, HTML, Javascript
import os
import pathlib
from .custom_widgets import *
from .auxfuncs import *

module_dir = os.path.dirname(os.path.abspath(__file__))

#=====================================================================
def create_widget(key, value, fmt=None):
    """
    Create a widget based on the type of value.
    :param key: The key for the widget.
    :param value: The default value for the widget.
    :return: A widget object.
    """
    label = widgets.Label(value=key)
    
    box = widgets.Box([label])
    box.add_class('ifk-widget-box')
    box.add_class('widget-vbox')
    
    if callable(value):
        wid = widgets.Button(description=key)
        wid.on_click(value)
        box.children = box.children[1:]
    elif isinstance(value, range):
        wid = widgets.IntSlider(value=value.start, min=value.start, max=value.stop, step=value.step)
    elif isinstance(value, bool):
        wid = widgets.Checkbox(value=value, indent=False)
    elif isinstance(value, int):
        wid = widgets.IntText(value=value)
    elif isinstance(value, float):
        wid = widgets.FloatText(value=value)
    elif isinstance(value, pathlib.Path):
        wid = FileAutocomplete(root_path=value)
        box.add_class('ifk-widget-FileAutocomplete')
    elif isinstance(value, str):
        if 'password' in key.lower():
            wid = widgets.Password(placeholder=value)
        elif value.endswith('...'):
            wid = widgets.Textarea(placeholder=value[:-3])
        else:
            wid = widgets.Text(placeholder=value)
    elif isinstance(value, tuple):
        wid = widgets.Dropdown(options=value, value=value[0] if value else None)
    elif isinstance(value, list):
        wid = widgets.Select(options=value, value=value[0] if value else None, rows=min(10, len(value)))
    else:
        wid = widgets.Label(value=f"Unsupported type: {type(value).__name__}")

    if fmt and hasattr(wid, 'value'):
        formatted = fmt(value)
        if can_convert(formatted, type(wid.value)):
            wid.value = formatted
    
    if isinstance(wid, widgets.FloatText):
        step = 10**(-count_decimal_places(wid.value))
        wid.step = step
    
    box.children = list(box.children) + [wid,]
    
    if type(wid) == widgets.Checkbox:
        box.remove_class('widget-vbox')
        box.add_class('widget-hbox')
        box.children = box.children[::-1]

    box.label = label
    box.wid = wid
    return box

#=====================================================================
def dict_to_form(vbox, input_dict, fmt, title=None, collapsed=None, nested=False):
    """
    Convert a dictionary to a form with widgets.

    Parameters
    ----------
    input_dict : dict
        A dictionary containing the input fields and their default values.
        Keys represent field names, and values represent default values or options.
    title : str, optional
        The title of the form. Default is None.
    collapsed : bool, optional
        If True, the form will be collapsed by default.
        If None, the form won't have a collapse toggle button and title.
        Default is None.
    nested : bool, optional
        If True, the form will be nested. Default is False.

    Returns
    -------
    vbox : ipywidgets.VBox
        The main container widget for the form.
    widgets_dict : dict
        A dictionary mapping field names to their corresponding widgets.
    """
    widgets_list = []
    widgets_dict = {}
    inputs_dict = {}

    if collapsed is None and title is not None:
        title_widget = widgets.Label(value=title)
        title_widget.add_class('ifk-form-title')
        widgets_list.append(title_widget)

    for key, value in input_dict.items():
        hbox_items = []

        def new_widget(k, v):
            f = fmt[k] if k in fmt else None
            wid = create_widget(k, v, fmt=f)
            widgets_dict[k] = wid
            inputs_dict[k] = wid.wid
            hbox_items.append(wid)

        if isinstance(value, dict):
            # Case: nested dictionary group
            sub_vbox, sub_widgets_dict, sub_inputs_dict = dict_to_form(vbox, value, fmt, title=key, collapsed=True, nested=True)
            widgets_dict.update(sub_widgets_dict)
            inputs_dict.update(sub_inputs_dict)
            hbox_items.append(sub_vbox)

        # Case: nested tuple group
        elif isinstance(key, tuple) and isinstance(value, tuple):
            for sub_key, sub_val in zip(key, value):
                new_widget(sub_key, sub_val)
            
        else:
            new_widget(key, value)
            
        hbox = widgets.HBox(hbox_items)
        hbox.add_class('ifk-form-hbox')
        widgets_list.append(hbox)
        
    if collapsed is not None:
        vbox = CollapsibleVBox(widgets_list, title=title, collapsed=collapsed)
        vbox.toggle_button.add_class('ifk-form-toggle-button')
        vbox.label.add_class('ifk-widget-label')
        vbox.layout.width = '100%'
    else:
        vbox.children = widgets_list

    return vbox, widgets_dict, inputs_dict

#=====================================================================
class Form(widgets.VBox):
    def __init__(self, input_dict, title=None, collapsed=None, max_width=600,
                 mandatory=None, disable=None, hide=None, check=None, tooltips=None,
                 formatters=None):
        """
        A class to create and manage interactive forms using ipywidgets.

        Parameters
        ----------
        input_dict : dict
            A dictionary containing the input fields and their default values.
            Keys represent field names, and values represent default values or options.
        title : str, optional
            The title of the form. Default is None.
        collapsed : bool, optional
            If True, the form will be collapsed by default.
            If None, the form won't have a collapse toggle button and title.
            Default is None.
        max_width : int, optional
            The maximum width of the form in pixels. Default is 600.
        mandatory : list of str, optional
            A list of keys that are mandatory fields. Default is None.
        disable : dict, optional
            A dictionary where keys are field names and values are functions that
            return a boolean to determine if the field should be disabled. Default is None.
        hide : dict, optional
            A dictionary where keys are field names and values are functions that
            return a boolean to determine if the field should be hidden. Default is None.
        check : dict, optional
            A dictionary where keys are field names and values are functions that
            return a boolean to validate the field's value. Default is None.
        tooltips : dict, optional
            A dictionary where keys are field names and values are tooltips. Default is None.
        formatters : dict, optional
            A dictionary where keys are field names and values are formatting functions.
            Default is None.

        Attributes
        ----------
        widgets_dict : dict
            A dictionary mapping field names to their corresponding widgets.
        """
        super().__init__()
        
        self.title = title
        self._input_dict = input_dict
        self._mandatory = mandatory
        self._formatters = formatters if formatters else {}

        self.vbox, self.widgets_dict, self.inputs_dict = dict_to_form(self, input_dict, self._formatters, title=title, collapsed=collapsed)
        self.layout.max_width = f'{max_width}px'
        self.add_class('ifk-form')

        if isinstance(mandatory, list):
            for key in mandatory:
                wid = self.widgets_dict[key]
                wid.label.value = f"{wid.label.value} *"

        self._disable_conditions = self.add_observer(disable, self.update_disable)
        self._hide_conditions = self.add_observer(hide, self.update_hide)
        self._check_conditions = self.add_observer(check, self.update_check)

        # Set initial state for disable and hide conditions
        self.update_check()
        self.update_disable()
        self.update_hide()

        self.set_tooltips(tooltips)
        self.load_stylesheets()
        self.load_tooltip_script()

    #=====================================================================
    def add_observer(self, conditions, func):
        """
        Add observers to the widgets based on the provided conditions.
        :param conditions: A dictionary of widget keys and corresponding functions.
        :param func: The function to call when the widget value changes.
        :return: A dictionary of widgets and their corresponding functions.
        """
        # Store conditions as a dictionary of widgets and functions
        conditions_out = {}
        if isinstance(conditions, dict):
            for key, val in conditions.items():
                if key in self.widgets_dict:
                    wid = self.widgets_dict[key]
                    if callable(val):
                        conditions_out[wid] = val
                    elif isinstance(val, bool):
                        conditions_out[wid] = lambda d: val
                    else:
                        print(f"Warning: Condition for {key} should be a function or boolean. Got {type(val).__name__} instead.")

            # The function will be called when any of the widgets change
            for key, wid in self.inputs_dict.items():
                wid.observe(func, names='value')

        elif conditions:
            print(f"Warning: Conditions should be a dictionary. Got {type(conditions).__name__} instead.")

        return conditions_out
        
    #=====================================================================
    #@throttle(0.2)
    def update_disable(self, change=None):
        """
        Update the disable state of the widgets based on the provided conditions.
        :param change: is provided by observe, but not used here.
        """
        value_dict = self.get_values()
        for wid, condition in self._disable_conditions.items():
            try:
                disable = condition(value_dict)
                wid.wid.disabled = disable

                if disable:
                    wid.wid.add_class('ifk-widget-input-disabled')
                else:
                    wid.wid.remove_class('ifk-widget-input-disabled')

            except Exception as e:
                print(f"Error updating disable state for {wid.label.value}\n{type(e).__name__}:{e}")


    #=====================================================================
    #@throttle(0.2)
    def update_hide(self, change=None):
        """
        Update the display state of the widgets based on the provided conditions.
        :param change: is provided by observe, but not used here.
        """
        value_dict = self.get_values()
        for wid, condition in self._hide_conditions.items():
            try:
                hide = condition(value_dict)
                if hide:
                    wid.layout.display = 'none'
                else:
                    wid.layout.display = 'block'

            except Exception as e:
                print(f"Error updating hide state for {wid.label.value}\n{type(e).__name__}:{e}")

        
    #=====================================================================
    #@throttle(0.2)
    def update_check(self, change=None):
        """
        Update the check state of the widgets based on the provided conditions.
        :param change: is provided by observe, but not used here.
        """
        value_dict = self.get_values()
        for wid, condition in self._check_conditions.items():
            try:
                check = condition(value_dict)
                if check:
                    wid.wid.remove_class('ifk-widget-input-error')
                else:
                    wid.wid.add_class('ifk-widget-input-error')

            except Exception as e:
                print(f"Error updating check state for {wid.label.value}\n{type(e).__name__}:{e}")

    
    #=====================================================================
    def set_tooltips(self, tooltips):
        """
        Set tooltips for the widgets in the form.
        :param
        tooltips: A dictionary where keys are field names and values are tooltips.
        """
        if tooltips:
            for key, tip in tooltips.items():
                if key in self.widgets_dict:
                    wid = self.widgets_dict[key]
                    tooltip = widgets.HTML(f'<div class="ifk-tooltip">?<span class="ifk-tooltip-text">{tip}</span></div>')
                    hbox = widgets.HBox([wid.label, tooltip])
                    children = list(wid.children)
                    children[children.index(wid.label)] = hbox
                    wid.children = children

                else:
                    print(f"Warning: {key} is not a valid key in the form.")


    #=====================================================================
    def load_stylesheets(self):
        """
        Load custom stylesheets for the widgets.
        :return: A list of HTML elements containing the stylesheets.
        """
        # Get the directory of this file (core.py)
        stylesheets = [
            'assets/custom_widgets.css',
            'assets/ipyformkit.css'
        ]

        for stylesheet in stylesheets:
            stylesheet = StyleSheet(module_dir + os.sep + stylesheet)
            self.children = self.children + (stylesheet,)

    #=====================================================================
    def load_tooltip_script(self):
        self.js_output = widgets.Output(layout={'display': 'none'})
        self.children = self.children + (self.js_output,)

        with  self.js_output:
            script = module_dir + os.sep + 'assets/tooltip_script.js'
            if os.path.exists(script):
                with open(script, 'r') as f:
                    js = f.read()
                    display(Javascript(js))
            else:
                print(f"Warning: {script} not found. Tooltips will not be functional.")
                display(Javascript('console.warn("Tooltip script not found. Tooltips will not be functional.")'))


    #=====================================================================
    def get_values(self):
        """
        Get the values of the widgets in the form as a dictionary.
        :return: A dictionary of key-value pairs representing the widget values.
        """
        out = {key: wid.value for key, wid in self.inputs_dict.items() if hasattr(wid, 'value')}
        return out
    

    #=====================================================================
    def set_values(self, values):
        """
        Set the values of the widgets in the form.
        :param values: A dictionary of key-value pairs to set the widget values.
        :param verbose: If True, print warnings for invalid keys.
        """
        def set_key(key, value):
            if isinstance(value, (tuple, list)): value = value[0]
            self[key] = value

        for key, value in values.items():
            if isinstance(key, (tuple, list)):
                for sub_key, sub_value in zip(key, value):
                    set_key(sub_key, sub_value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    set_key(sub_key, sub_value)
            else:
                set_key(key, value)
    

    #=====================================================================
    def check_and_return_values(self, verbose=True, disabled_ok=False, hidden_ok=False):
        """
        Check the values of the widgets in the form and return them as a dictionary.
        :return: A dictionary of key-value pairs representing the widget values, or None if validation fails.
        """
        out = {}
        abort = False
        value_dict = self.get_values()
        for key, wid in self.widgets_dict.items():
            if hasattr(wid.wid, 'value'):
                value = wid.wid.value
                disabled = wid.wid.disabled
                hidden = wid.layout.display == 'none'
                mandatory = key in self._mandatory if self._mandatory else False
                check_func = self._check_conditions.get(wid, lambda d:True)
                valid = check_func(value_dict)
                
                if value == '' and mandatory:
                    if verbose: print(f"Mandatory field '{key}' is empty.")
                    wid.wid.add_class('ifk-widget-input-missing')
                    abort = True
                else:
                    wid.wid.remove_class('ifk-widget-input-missing')
                    
                if not valid:
                    if verbose: print(f"Invalid input in field '{key}'.")
                    abort = True
                
                ok = not disabled or disabled_ok
                ok = ok and (not hidden or hidden_ok)
                
                if ok:
                    out[key] = value
                    
        if abort:
            return None
        else:
            return out
        

    #=====================================================================
    def __getitem__(self, key):
        """
        Get the value corresponding to the given key.
        :param key: The key of the widget to retrieve.
        :return: The widget value.
        """
        if key in self.inputs_dict:
            wid = self.inputs_dict[key]
            if hasattr(wid, 'value'):
                return self.inputs_dict[key].value
            else:
                print(f"Warning: Widget for {key} does not have a 'value' attribute.")
        else:
            print(f"Warning: {key} is not a valid key in the form.")
    
    #=====================================================================
    def __setitem__(self, key, value):
        """
        Set the value of the widget corresponding to the given key.
        :param key: The key of the widget to set.
        :param value: The value to set the widget to.
        """
        if key in self.inputs_dict:
            wid = self.inputs_dict[key]

            if hasattr(wid, 'value'):
                if key in self._formatters:
                    value = self._formatters[key](value)

                if can_convert(value, type(wid.value)):
                    wid.value = value
                else:
                    print(f"Warning: Type mismatch for {key}. Expected {type(wid.value)}, got {type(value)}.")
            else:
                print(f"Warning: Widget for {key} does not have a 'value' attribute.")
        else:
            print(f"Warning: {key} is not a valid key in the form.")
    

#=====================================================================
class Masonry(widgets.Box):
    def __init__(self, forms):
        """
        Create a masonry layout with the provided forms.

        Parameters
        ----------
        forms : list of Form
            A list of Form objects to be displayed in the masonry layout.

        Attributes
        ----------
        forms : list of Form
            The list of Form objects.
        box : ipywidgets.Box
            The main container widget for the masonry layout.
        """
        super().__init__()
        self.forms = forms
        self.children = forms
        self.add_class('ifk-masonry')