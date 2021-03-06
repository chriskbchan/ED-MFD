import math

def wrap_text(text, font, width):
    # https://github.com/ColdrickSotK/yamlui/blob/264bf37a3697f1a3e69a42475648a3ee9afeb664/yamlui/util.py#L82-L143
    """Wrap text to fit inside a given width when rendered.

    :param text: The text to be wrapped.
    :param font: The font the text will be rendered in.
    :param width: The width to wrap to.

    """
    text_lines = text.replace('\t', '    ').split('\n')
    if width is None or width == 0:
        return text_lines


    wrapped_lines = []
    for line in text_lines:
        line = line.rstrip() + ' '
        if line == ' ':
            wrapped_lines.append(line)
            continue


        # Get the leftmost space ignoring leading whitespace
        start = len(line) - len(line.lstrip())
        start = line.index(' ', start)
        while start + 1 < len(line):
            # Get the next potential splitting point
            next = line.index(' ', start + 1)
            if font.size(line[:next])[0] <= width:
                start = next
            else:
                wrapped_lines.append(line[:start])
                line = line[start+1:]
                start = line.index(' ')
        line = line[:-1]
        if line:
            wrapped_lines.append(line)
    return wrapped_lines

def distance(c1, c2):
    """ calculate 3d distance of c1 = (x1, y1, z1) and c2 = (x2, y2, z2)
    """
    x1, y1, z1 = c1
    x2, y2, z2 = c2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
