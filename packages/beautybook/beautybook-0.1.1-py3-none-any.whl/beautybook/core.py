import uuid
from IPython.display import display, HTML

class BeautyBook:
    """
    A class to dynamically display data in a beautifully styled HTML table 
    in a Jupyter/Colab environment.

    Args:
        *column_names (str): A variable number of strings, where each string
                             is a header for a column in the table.
    """
    def __init__(self, *column_names):
        if not column_names:
            raise ValueError("BeautyBook must be initialized with at least one column name.")
        
        # We prepend an "Index" column for automatic numbering
        self.column_names = ("#",) + column_names
        self.rows = []
        self.display_id = f"bb-table-{uuid.uuid4().hex}"
        
        # Initialize column widths based on header length
        self._max_widths = [len(str(name)) for name in self.column_names]
        
        # Initial display of the header
        self._render_table()

    def log(self, *row_data):
        """
        Adds a new row of data to the table and updates the display.

        Args:
            *row_data: A variable number of data points corresponding to the
                       columns defined at initialization.
        """
        if len(row_data) != len(self.column_names) - 1:
            raise ValueError(f"Expected {len(self.column_names) - 1} data points, but got {len(row_data)}.")
        
        # Prepend the row index and add to our data store
        current_index = len(self.rows) + 1
        full_row = (current_index,) + row_data
        self.rows.append(full_row)
        
        # Update max column widths based on new data
        for i, cell_data in enumerate(full_row):
            self._max_widths[i] = max(self._max_widths[i], len(str(cell_data)))
        
        # Re-render the table with the new row
        self._render_table(update=True)

    def _get_css(self):
        """Generates the CSS for styling the table."""
        # Dynamically calculate column widths based on content, adding some padding
        # The 'ch' unit is approximately the width of the '0' character
        col_styles = ""
        for i, width in enumerate(self._max_widths):
            # Add a bit of padding to the calculated max width
            padded_width = width + 2 
            col_styles += f".bb-table th:nth-child({i+1}), .bb-table td:nth-child({i+1}) {{ width: {padded_width}ch; }}\n"

        return f"""
        <style>
            .bb-container {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                margin: 10px 0;
            }}
            .bb-table {{
                border-collapse: collapse;
                width: auto;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }}
            .bb-table th, .bb-table td {{
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            .bb-table th {{
                background-color: #007bff;
                color: white;
                font-weight: 600;
            }}
            .bb-table tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .bb-table tr:hover {{
                background-color: #f1f1f1;
            }}
            .bb-table td:first-child, .bb-table th:first-child {{
                text-align: center;
                font-weight: bold;
            }}
            {col_styles}
        </style>
        """

    def _render_table(self, update=False):
        """Constructs and displays the HTML table."""
        css = self._get_css()
        
        # Create table headers
        header_html = "<tr>" + "".join(f"<th>{name}</th>" for name in self.column_names) + "</tr>"
        
        # Create table rows
        rows_html = ""
        for row in self.rows:
            rows_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"

        # Combine all parts
        full_html = f"""
        <div class="bb-container">
            {css}
            <table class="bb-table">
                <thead>{header_html}</thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """
        
        # Use IPython's display with update=True for subsequent calls
        display(HTML(full_html), display_id=self.display_id, update=update)