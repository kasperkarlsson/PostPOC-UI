from appJar import gui
from html import escape
from subprocess import Popen
from urllib import parse

# Constants
VERSION = "0.1"
TITLE = "PostPOC GUI v{0}".format(VERSION)
FILENAME_DEFAULT = "poc.html"


class RequestData:
    def __init__(self, protocol: str, host: str, path: str, variables: list):
        self.full_url = "".join((protocol, "://", host, path))
        self.post_parameters = variables


def parse_request(raw_request: str, protocol: str = "https") -> RequestData:
    lines = raw_request.strip().splitlines()
    assert len(raw_request.strip()) > 0, "Request is blank"
    assert len(lines) > 1, "Missing lines in request"
    path_segments = lines[0].split(" ")
    assert len(path_segments) > 1, "Missing path in line 1"
    path = path_segments[1]
    host_segments = lines[1].split(" ")
    assert len(host_segments) > 1, "Missing host in line 2"
    host = host_segments[1]
    # Look for blank line between headers and POST parameters
    if lines[-2] == "":
        post_vars = lines[-1].split("&")
    else:
        post_vars = []
    request_data = RequestData(protocol, host, path, post_vars)
    return request_data


def generate_poc(request: RequestData, filename: str, output_size: str):
    def generate_input_field(name: str, value: str) -> str:
        input_elem = """  <tr>
    <td>{0}</td>
    <td><input type='text' name='{0}' value='{1}' size='70'/></td>
  </tr>""".format(name, value)
        return input_elem

    def generate_textarea_field(name: str, value: str) -> str:
        value.replace("\n\n", "\n")
        textarea_elem = """  <tr>
    <td>{0}</td>
    <td><textarea name='{0}' cols='30'>{1}</textarea></td>
  </tr>""".format(name, value)
        return textarea_elem

    def param_to_html(post_parameter: str) -> str:
        segments = list(map(lambda x: escape(parse.unquote(x)), post_parameter.replace("+", " ").split("=", 1)))
        name = segments[0]
        if len(segments) == 2:
            value = segments[1]
        else:
            value = ""
        # Multi-line parameter values (i.e. the ones containing CR+LF) are wrapped in a <textarea> tag...
        if "\n" in value:
            html = generate_textarea_field(name, value)
        # ...and all single-line ones are wrapped in an <input> tag
        else:
            html = generate_input_field(name, value)
        return html

    if len(request.post_parameters) == 0:
        input_fields = "[No POST parameters]"
    else:
        input_fields = "\n".join(map(param_to_html, request.post_parameters))
    with open(filename, "w") as f:
        page_source = ""
        if output_size == "full":
            page_source += """<!DOCTYPE html>
<html>
<head>
<title>PoC</title>
<style>
table{{
  border: 1px solid lightgray;
}}
</style>
</head>
<body>
"""
        page_source += """<b>POST target</b>
<pre>{0}</pre>
<b>POST parameters</b>
<br />
<form action='{0}' id='postForm' method='POST'>
<table>
{1}
</table>
<br />
<input type='submit' value='Submit' />
</form>"""

        if output_size == "full":
            page_source += """
</body>
</html>"""
        page_source = page_source.format(escape(request.full_url), input_fields)
        f.write(page_source)


# Button handler
def press(button):
    if button == "Close":
        app.stop()
    elif button == "Show":
        Popen("explorer .")
    elif button == "POC":
        raw_request = app.getTextArea("Request")
        filename = app.getEntry("Filename")
        protocol = app.getRadioButton("protocol").lower()
        output_size = app.getRadioButton("output_size").lower()
        if filename == "":
            filename = FILENAME_DEFAULT
        error = None
        try:
            req = parse_request(raw_request, protocol)
            generate_poc(req, filename, output_size)
        except AssertionError as e:
            error = e
        if error:
            app.setLabel("Status", "Error: {0}".format(error))
        else:
            app.setLabel("Status", "Created '{0}'".format(filename))
    else:
        print("Unknown button: '{0}'".format(button))


# Initialize GUI
app = gui(TITLE, "600x600")

# Create widgets
app.addLabel("title", TITLE, colspan=2)

app.addLabel("protocol_select", "Protocol", colspan=2)
app.addRadioButton("protocol", "HTTPS")
app.addRadioButton("protocol", "HTTP", column=1, row=2)
app.setRadioButton("protocol", "HTTPS")

app.addLabel("output_size_select", "Output file", colspan=2)
app.addRadioButton("output_size", "Full")
app.addRadioButton("output_size", "Small", column=1, row=4)
app.setRadioButton("output_size", "Full")

app.addLabelEntry("Filename", colspan=2)
app.setEntryDefault("Filename", FILENAME_DEFAULT)

app.addLabel("HTTP Request", colspan=2)
app.addScrolledTextArea("Request", colspan=2)
app.setInputFont(size=9, family="Lucida Console")

# All buttons map to the press function
app.addButtons(["POC", "Show", "Close"], press, colspan=2)

app.addLabel("Status", colspan=2)

# Start GUI
app.go()
